from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_handlers = {
            "ping": self._handle_ping,
            "code_execution": self._handle_code_execution,
            "stop_execution": self._handle_stop_execution,
            "gpio_status_request": self._handle_gpio_status_request
        }
        self.code_execution_service = None  # Будет установлено позже

    def set_code_execution_service(self, service):
        """Устанавливает сервис выполнения кода (для избежания циклического импорта)"""
        self.code_execution_service = service

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected")
        
        # Отправка приветственного сообщения
        await self.send_message(client_id, {
            "type": "connection_established",
            "message": f"Connected as client {client_id}",
            "client_id": client_id
        })

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            # Останавливаем выполнение кода при отключении
            if self.code_execution_service:
                self.code_execution_service.stop_execution(client_id)
            del self.active_connections[client_id]
            print(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        disconnected_clients = []
        for client_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception:
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def handle_message(self, client_id: str, data: str):
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](client_id, message)
            else:
                await self.send_message(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "allowed_types": list(self.message_handlers.keys())
                })
                
        except json.JSONDecodeError:
            await self.send_message(client_id, {
                "type": "error",
                "message": "Invalid JSON format"
            })
        except Exception as e:
            await self.send_message(client_id, {
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            })

    async def _handle_ping(self, client_id: str, message: dict):
        """Обработка ping сообщения"""
        await self.send_message(client_id, {
            "type": "pong",
            "timestamp": message.get("timestamp")
        })

    async def _handle_code_execution(self, client_id: str, message: dict):
        """Обработка запроса на выполнение кода"""
        if not self.code_execution_service:
            await self.send_message(client_id, {
                "type": "error",
                "message": "Code execution service not available"
            })
            return
            
        code = message.get("code", "")
        
        if not code:
            await self.send_message(client_id, {
                "type": "error",
                "message": "No code provided for execution"
            })
            return
        
        # Запуск выполнения кода в отдельной task
        asyncio.create_task(
            self.code_execution_service.execute_code(client_id, code)
        )

    async def _handle_stop_execution(self, client_id: str, message: dict):
        """Обработка запроса на остановку выполнения"""
        if not self.code_execution_service:
            await self.send_message(client_id, {
                "type": "error",
                "message": "Code execution service not available"
            })
            return
            
        success = self.code_execution_service.stop_execution(client_id)
        await self.send_message(client_id, {
            "type": "execution_stopped",
            "success": success,
            "message": "Execution stopped" if success else "No active execution to stop"
        })

    async def _handle_gpio_status_request(self, client_id: str, message: dict):
        """Обработка запроса статуса GPIO"""
        if not self.code_execution_service:
            await self.send_message(client_id, {
                "type": "error",
                "message": "Code execution service not available"
            })
            return
            
        pin = message.get("pin")
        
        if pin is not None:
            # Запрос статуса конкретного пина
            pin_state = self.code_execution_service.gpio_state.get(pin, {})
            await self.send_message(client_id, {
                "type": "gpio_status",
                "pin": pin,
                "mode": pin_state.get("mode", "NOT_CONFIGURED"),
                "value": pin_state.get("value", 0)
            })
        else:
            # Запрос статуса всех пинов
            await self.send_message(client_id, {
                "type": "gpio_status_all",
                "pins": self.code_execution_service.gpio_state
            })

# Глобальный экземпляр менеджера WebSocket
websocket_manager = WebSocketManager()