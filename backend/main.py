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
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "execute":
                code = data.get("code", "")
                
                # Отправляем подтверждение начала выполнения
                await websocket.send_json({
                    "type": "execution_started",
                    "message": "Выполнение началось"
                })
                
                # Функция для отправки вывода
                async def send_output(output):
                    await websocket.send_json({
                        "type": "output",
                        "content": output
                    })
                
                # Выполняем код с потоковой передачей
                await docker_manager.execute_code_realtime(code, send_output)
                
                # Отправляем подтверждение завершения
                await websocket.send_json({
                    "type": "execution_completed",
                    "message": "Выполнение завершено"
                })
                
            elif data.get("type") == "stop":
                await websocket.send_json({
                    "type": "output",
                    "content": "Выполнение остановлено по запросу пользователя"
                })
                
    except WebSocketDisconnect:
        print("Клиент отключился")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"Ошибка соединения: {str(e)}"
        })