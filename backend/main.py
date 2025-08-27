from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import asyncio
from websocket_manager import WebSocketManager
from docker_manager import DockerManager
from gpio_emulator import GPIOEmulator

app = FastAPI()

# Обслуживание статических файлов фронтенда
app.mount("/static", StaticFiles(directory="/app/frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    # Читаем index.html и заменяем пути к статическим файлам
    with open("/app/frontend/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Убеждаемся, что пути правильные
    html_content = html_content.replace('href="style.css"', 'href="/static/style.css"')
    html_content = html_content.replace('src="script.js"', 'src="/static/script.js"')
    html_content = html_content.replace('src="components.js"', 'src="/static/components.js"')
    html_content = html_content.replace('src="websocket-client.js"', 'src="/static/websocket-client.js"')
    
    return HTMLResponse(content=html_content)

# Инициализация менеджеров
ws_manager = WebSocketManager()
docker_manager = DockerManager()
gpio_emulator = GPIOEmulator()

@app.websocket("/ws/execute")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "execute":
                code = data.get("code", "")
                asyncio.create_task(docker_manager.execute_code_realtime(code, websocket))
                
            elif data.get("type") == "stop":
                await ws_manager.send_personal_message({
                    "type": "execution_stopped",
                    "message": "Выполнение остановлено"
                }, websocket)
                
            elif data.get("type") == "gpio_input":  # Новый обработчик
                pin = data.get("pin")
                state = data.get("state")
                if pin is not None and state is not None:
                    gpio_emulator.update_input_pin_state(pin, state)
                    await ws_manager.broadcast({
                        "type": "gpio_state_update",
                        "pin": pin,
                        "state": state,
                        "mode": "input"
                    })
                    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        await ws_manager.send_personal_message({
            "type": "error",
            "content": f"Ошибка: {str(e)}"
        }, websocket)