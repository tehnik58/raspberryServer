import docker
import asyncio
import json
import re
from typing import Dict, List, Callable, Optional
from datetime import datetime
from app.config import settings

# Импортируем websocket_manager через функцию, чтобы избежать циклического импорта
def get_websocket_manager():
    from app.services.websocket_manager import websocket_manager
    return websocket_manager

class CodeExecutionService:
    def __init__(self):
        try:
            self.client = docker.from_env()
            # Проверяем подключение к Docker
            self.client.ping()
            self.docker_available = True
            print("Docker connection established successfully")
        except docker.errors.DockerException as e:
            print(f"Docker is not available: {e}")
            self.client = None
            self.docker_available = False
        
        self.active_containers: Dict[str, docker.models.containers.Container] = {}
        self.gpio_state: Dict[int, Dict] = {}  # {pin: {mode: "IN/OUT", value: 0/1}}
        
    async def execute_code(self, client_id: str, code: str):
        """
        Выполнение Python кода в изолированном Docker контейнере
        """
        websocket_manager = get_websocket_manager()
        
        # Проверяем доступность Docker
        if not self.docker_available:
            await websocket_manager.send_message(client_id, {
                "type": "error",
                "message": "Docker is not available. Please ensure Docker is installed and running.",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Очистка входных данных
        sanitized_code = self._sanitize_input(code, 10000)
        if not sanitized_code:
            await websocket_manager.send_message(client_id, {
                "type": "error",
                "message": "Invalid code input"
            })
            return

        # Отправка сообщения о начале выполнения
        await websocket_manager.send_message(client_id, {
            "type": "status",
            "message": "Execution started",
            "timestamp": datetime.now().isoformat()
        })

        try:
            # Создание и запуск контейнера
            container = self.client.containers.run(
                "raspberry-python-runner",  # Используем собранный образ
                detach=True,
                stdin_open=True,
                mem_limit=settings.DOCKER_MEMORY_LIMIT,
                network_mode="none",
                cpu_period=100000,
                cpu_quota=50000,  # Ограничение CPU до 50%
                pids_limit=100,
                remove=True,  # Автоматическое удаление контейнера после завершения
            )

            self.active_containers[client_id] = container

            # Отправка кода в контейнер
            socket = container.attach_socket(params={'stdin': 1, 'stream': 1})
            try:
                socket._sock.sendall((sanitized_code + "\n").encode('utf-8'))
                socket._sock.sendall(b"__END_OF_CODE__\n")
            finally:
                socket.close()

            # Мониторинг вывода контейнера в реальном времени
            await self._monitor_container_output(container, client_id)

            # Ожидание завершения контейнера
            result = container.wait()
            
            await websocket_manager.send_message(client_id, {
                "type": "status",
                "message": f"Execution completed with exit code: {result['StatusCode']}",
                "timestamp": datetime.now().isoformat()
            })

        except docker.errors.ImageNotFound:
            await websocket_manager.send_message(client_id, {
                "type": "error",
                "message": "Docker image not found. Please build the code runner image first.",
                "timestamp": datetime.now().isoformat()
            })
        except docker.errors.DockerException as e:
            await websocket_manager.send_message(client_id, {
                "type": "error",
                "message": f"Docker error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            await websocket_manager.send_message(client_id, {
                "type": "error",
                "message": f"Unexpected error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        finally:
            if client_id in self.active_containers:
                del self.active_containers[client_id]

    def _sanitize_input(self, input_str: str, max_length: int = 1000) -> Optional[str]:
        """
        Очистка входных данных от потенциально опасных символов
        """
        if not input_str or len(input_str) > max_length:
            return None
        
        # Удаляем потенциально опасные символы
        cleaned = re.sub(r'[<>{}[\]\\]', '', input_str)
        return cleaned

    async def _monitor_container_output(self, container, client_id: str):
        """
        Мониторинг вывода контейнера в реальном времени
        """
        websocket_manager = get_websocket_manager()
        
        try:
            for line in container.logs(stream=True, follow=True):
                line_text = line.decode('utf-8').strip()
                if line_text:
                    # Парсинг GPIO событий
                    gpio_event = self._parse_gpio_event(line_text)
                    if gpio_event:
                        await websocket_manager.send_message(client_id, {
                            "type": "gpio_update",
                            "pin": gpio_event["pin"],
                            "value": gpio_event["value"],
                            "mode": gpio_event["mode"],
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        # Отправка обычного лога
                        await websocket_manager.send_message(client_id, {
                            "type": "log",
                            "message": line_text,
                            "timestamp": datetime.now().isoformat()
                        })
        except Exception as e:
            await websocket_manager.send_message(client_id, {
                "type": "error",
                "message": f"Log monitoring error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    def _parse_gpio_event(self, log_line: str) -> Optional[Dict]:
        """
        Парсинг GPIO событий из логов
        """
        patterns = [
            r"GPIO_ACTION: SETMODE (\w+)",
            r"GPIO_ACTION: SETUP pin=(\d+), mode=(\w+)",
            r"GPIO_ACTION: OUTPUT pin=(\d+), value=(\d+)",
            r"GPIO_ACTION: INPUT pin=(\d+), value=(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_line)
            if match:
                if "SETMODE" in pattern:
                    return {"action": "setmode", "mode": match.group(1)}
                elif "SETUP" in pattern:
                    pin = int(match.group(1))
                    mode = "OUT" if match.group(2) == "0" else "IN"
                    self._update_gpio_state(pin, {"mode": mode})
                    return {"pin": pin, "mode": mode, "value": 0}
                elif "OUTPUT" in pattern or "INPUT" in pattern:
                    pin = int(match.group(1))
                    value = int(match.group(2))
                    self._update_gpio_state(pin, {"value": value})
                    return {"pin": pin, "value": value, "mode": self.gpio_state.get(pin, {}).get("mode", "OUT")}
        
        return None

    def _update_gpio_state(self, pin: int, updates: Dict):
        """
        Обновление состояния GPIO
        """
        if pin not in self.gpio_state:
            self.gpio_state[pin] = {}
        
        self.gpio_state[pin].update(updates)

    def stop_execution(self, client_id: str):
        """
        Принудительная остановка выполнения кода
        """
        if client_id in self.active_containers:
            try:
                container = self.active_containers[client_id]
                container.stop(timeout=2)
                del self.active_containers[client_id]
                return True
            except Exception:
                return False
        return False

# Глобальный экземпляр сервиса выполнения кода
code_execution_service = CodeExecutionService()