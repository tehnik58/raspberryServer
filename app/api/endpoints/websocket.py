from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import websocket_manager

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # Принятие соединения
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Ожидание сообщений от клиента
            data = await websocket.receive_text()
            
            # Обработка входящих сообщений
            # Здесь будет логика обработки различных типов сообщений
            await websocket_manager.handle_message(client_id, data)
            
    except WebSocketDisconnect:
        # Обработка отключения клиента
        websocket_manager.disconnect(client_id)
        print(f"Client {client_id} disconnected")