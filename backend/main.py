# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import asyncio
import json

# Импорты из проекта
from websocket_manager import WebSocketManager
from docker_manager import DockerManager
from gpio_emulator import GPIOEmulator
from system_model import SystemModel  # Новый импорт

app = FastAPI()

# Обслуживание статических файлов фронтенда
app.mount("/static", StaticFiles(directory="/app/frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("/app/frontend/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    # Исправляем пути к статике
    html_content = html_content.replace('href="style.css"', 'href="/static/style.css"')
    html_content = html_content.replace('src="script.js"', 'src="/static/script.js"')
    html_content = html_content.replace('src="components.js"', 'src="/static/components.js"')
    html_content = html_content.replace('src="websocket-client.js"', 'src="/static/websocket-client.js"')
    return HTMLResponse(content=html_content)

# === Инициализация менеджеров ===
ws_manager = WebSocketManager()
docker_manager = DockerManager()
gpio_emulator = GPIOEmulator()
system_model = SystemModel()  # Централизованная модель системы


# === Запуск/остановка фоновых процессов ===
@app.on_event("startup")
async def startup_event():
    system_model.start()

@app.on_event("shutdown")
async def shutdown_event():
    system_model.stop()


# === WebSocket endpoint ===
@app.websocket("/ws/execute")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    # Подписка на события модели (для отправки клиенту)
    def on_model_event(event: str, data: dict):
        message = {
            "type": "system_event",
            "event": event,
            "data": data
        }
        # Отправляем только этому клиенту
        asyncio.create_task(ws_manager.send_personal_message(message, websocket))

    system_model.on("state_update", on_model_event)
    system_model.on("component_added", on_model_event)
    system_model.on("component_removed", on_model_event)
    system_model.on("connection_added", on_model_event)
    system_model.on("connection_removed", on_model_event)

    try:
        while True:
            data = await websocket.receive_json()

            # --- Выполнение кода ---
            if data.get("type") == "execute":
                code = data.get("code", "")
                asyncio.create_task(docker_manager.execute_code_realtime(code, websocket, system_model))

            # --- Остановка ---
            elif data.get("type") == "stop":
                await ws_manager.send_personal_message({
                    "type": "execution_stopped",
                    "message": "Выполнение остановлено"
                }, websocket)

            # --- Управление GPIO (вход) ---
            elif data.get("type") == "gpio_input":
                pin = data.get("pin")
                state = data.get("state")
                if pin is not None and state is not None:
                    # Обновляем состояние в SystemModel
                    system_model.update_component_state(f"GPIO{pin}", value=state)
                    # Для обратной совместимости — отправляем старое сообщение
                    await ws_manager.send_personal_message({
                        "type": "gpio_state_update",
                        "pin": pin,
                        "state": state,
                        "mode": "input"
                    }, websocket)

            # --- Управление PWM ---
            elif data.get("type") == "pwm_control":
                pin = data.get("pin")
                duty_cycle = data.get("duty_cycle")
                frequency = data.get("frequency")
                action = data.get("action")

                # Обновляем в SystemModel
                if pin is not None:
                    pwm_id = f"PWM{pin}"
                    if action == "start" or action == "duty_change":
                        system_model.update_component_state(
                            pwm_id,
                            duty_cycle=duty_cycle,
                            frequency=frequency,
                            active=True
                        )
                    elif action == "stop":
                        system_model.update_component_state(pwm_id, active=False)

                # Отправляем совместимое сообщение
                await ws_manager.send_personal_message({
                    "type": "pwm_state_update",
                    "pin": pin,
                    "duty_cycle": duty_cycle,
                    "frequency": frequency
                }, websocket)

            # --- Управление мотором ---
            elif data.get("type") == "motor_control":
                name = data.get("name")
                speed = data.get("speed")
                if name and speed is not None:
                    system_model.update_component_state(name, speed=speed, running=True)
                    await ws_manager.send_personal_message({
                        "type": "motor_state_update",
                        "name": name,
                        "speed": speed
                    }, websocket)

            # --- Управление шаговым мотором ---
            elif data.get("type") == "stepper_control":
                name = data.get("name")
                steps = data.get("steps")
                if name and steps is not None:
                    pos = system_model.components.get(name, {}).get("state", {}).get("position", 0)
                    new_pos = pos + steps
                    system_model.update_component_state(name, position=new_pos)
                    await ws_manager.send_personal_message({
                        "type": "stepper_position_update",  # (новое, опционально)
                        "name": name,
                        "position": new_pos
                    }, websocket)

            # --- Создание компонента (например, из Unity) ---
            elif data.get("type") == "create_component":
                cid = data["id"]
                ctype = data["type"]
                system_model.add_component(
                    id=cid,
                    type=ctype,
                    state=data.get("state", {}),
                    config=data.get("config", {})
                )

            # --- Соединение компонентов ---
            elif data.get("type") == "connect_components":
                from_id = data["from"]
                to_id = data["to"]
                system_model.connect(from_id, to_id)

            # --- Обновление конфигурации ---
            elif data.get("type") == "config_update":
                config = data.get("config", {})
                # Можно обновить системные настройки
                print(f"Config updated: {config}")

            # --- Переподключение ---
            elif data.get("type") == "reconnect":
                await ws_manager.send_personal_message({
                    "type": "connection_status",
                    "status": "connected",
                    "message": "Переподключение успешно"
                }, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        await ws_manager.send_personal_message({
            "type": "error",
            "content": f"Ошибка: {str(e)}"
        }, websocket)