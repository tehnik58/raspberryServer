import os
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
        self.docker_available = False
        self.client = None
        self.docker_error_message = ""
        
        # Проверяем доступность Docker только если не в режиме эмуляции
        if not os.environ.get('FORCE_SIMULATION_MODE'):
            try:
                self.client = docker.from_env()
                # Простая проверка доступности Docker
                self.client.ping()
                self.docker_available = True
                print("✓ Docker connection established successfully")
            except docker.errors.DockerException as e:
                self.docker_error_message = str(e)
                print(f"✗ Docker is not available: {self.docker_error_message}")
                print("ℹ Falling back to simulation mode")
            except Exception as e:
                self.docker_error_message = f"Unexpected error: {str(e)}"
                print(f"✗ Docker initialization failed: {self.docker_error_message}")
                print("ℹ Falling back to simulation mode")
        else:
            print("ℹ Starting in forced simulation mode (FORCE_SIMULATION_MODE is set)")
        
        self.active_containers: Dict[str, docker.models.containers.Container] = {}
        self.gpio_state: Dict[int, Dict] = {}
        
    async def execute_code(self, client_id: str, code: str):
        """
        Выполнение Python кода в изолированном Docker контейнере или режиме эмуляции
        """
        websocket_manager = get_websocket_manager()
        
        # Всегда используем режим эмуляции, если Docker недоступен
        if not self.docker_available:
            await self._execute_with_simulation(client_id, code)
            return
            
        # Если Docker доступен, пытаемся использовать его
        try:
            await self._execute_with_docker(client_id, code)
        except Exception as e:
            print(f"✗ Docker execution failed, falling back to simulation: {e}")
            await websocket_manager.send_message(client_id, {
                "type": "status",
                "message": "Docker execution failed, using simulation mode",
                "timestamp": datetime.now().isoformat()
            })
            await self._execute_with_simulation(client_id, code)
    
    async def _execute_with_docker(self, client_id: str, code: str):
        """Выполнение кода с использованием Docker"""
        websocket_manager = get_websocket_manager()
        
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
            "message": "Execution started (Docker mode)",
            "timestamp": datetime.now().isoformat()
        })

        try:
            # Проверяем доступность образа
            try:
                self.client.images.get("raspberry-python-runner")
            except docker.errors.ImageNotFound:
                await websocket_manager.send_message(client_id, {
                    "type": "error",
                    "message": "Docker image not found. Please build the code runner image first.",
                    "timestamp": datetime.now().isoformat()
                })
                return

            # Создание и запуск контейнера
            container = self.client.containers.run(
                "raspberry-python-runner",
                detach=True,
                stdin_open=True,
                mem_limit=settings.DOCKER_MEMORY_LIMIT,
                network_mode="none",
                cpu_period=100000,
                cpu_quota=50000,
                pids_limit=100,
                remove=True,
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
    
    async def _execute_with_simulation(self, client_id: str, code: str):
        """Режим эмуляции выполнения кода без Docker"""
        websocket_manager = get_websocket_manager()
        
        await websocket_manager.send_message(client_id, {
            "type": "status",
            "message": "Execution started (simulation mode)",
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Анализируем код для определения GPIO операций
            gpio_operations = self._parse_code_for_gpio_operations(code)
            
            # Имитация выполнения кода с логированием
            logs = [
                "Starting execution in simulation mode",
                "GPIO library imported successfully",
                "Setting up GPIO mode...",
            ]
            
            # Добавляем логи в зависимости от операций в коде
            if "setmode" in gpio_operations:
                logs.append("GPIO mode set to BCM")
                
            if "setup" in gpio_operations:
                for pin in gpio_operations["setup"]:
                    logs.append(f"Pin {pin} set up as OUTPUT")
                    
            if "output" in gpio_operations:
                for pin, value in gpio_operations["output"]:
                    state = "HIGH" if value else "LOW"
                    logs.append(f"Pin {pin} set to {state}")
                    
            if "input" in gpio_operations:
                for pin in gpio_operations["input"]:
                    logs.append(f"Reading value from pin {pin}: 0 (simulated)")
                    
            logs.append("Execution completed successfully")
            logs.append("GPIO cleanup completed")
            
            # Отправляем логи
            for log in logs:
                await websocket_manager.send_message(client_id, {
                    "type": "log",
                    "message": log,
                    "timestamp": datetime.now().isoformat()
                })
                await asyncio.sleep(0.3)
            
            # Имитация GPIO событий
            if "output" in gpio_operations:
                for pin, value in gpio_operations["output"]:
                    await websocket_manager.send_message(client_id, {
                        "type": "gpio_update",
                        "pin": pin,
                        "value": 1 if value else 0,
                        "mode": "OUT",
                        "timestamp": datetime.now().isoformat()
                    })
                    await asyncio.sleep(0.5)
            
            await websocket_manager.send_message(client_id, {
                "type": "status",
                "message": "Execution completed (simulation mode)",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            await websocket_manager.send_message(client_id, {
                "type": "error",
                "message": f"Simulation error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    def _parse_code_for_gpio_operations(self, code: str) -> Dict:
        """Анализ кода для определения операций с GPIO"""
        operations = {
            "setmode": False,
            "setup": [],
            "output": [],
            "input": [],
            "cleanup": False
        }
        
        try:
            # Поиск операций с GPIO
            if "GPIO.setmode" in code:
                operations["setmode"] = True
                
            # Поиск setup операций
            setup_matches = re.findall(r"GPIO\.setup\((\d+),\s*GPIO\.(OUT|IN)", code)
            for pin, mode in setup_matches:
                operations["setup"].append(int(pin))
                
            # Поиск output операций
            output_matches = re.findall(r"GPIO\.output\((\d+),\s*GPIO\.(HIGH|LOW)", code)
            for pin, value in output_matches:
                operations["output"].append((int(pin), value == "HIGH"))
                
            # Поиск input операций
            input_matches = re.findall(r"GPIO\.input\((\d+)", code)
            for pin in input_matches:
                operations["input"].append(int(pin))
                
            if "GPIO.cleanup" in code:
                operations["cleanup"] = True
                
        except Exception as e:
            print(f"Error parsing code for GPIO operations: {e}")
            
        return operations

    def _sanitize_input(self, input_str: str, max_length: int = 10000) -> Optional[str]:
        """Очистка входных данных от потенциально опасных символов"""
        if not input_str or len(input_str) > max_length:
            return None
        
        # Удаляем потенциально опасные символы
        cleaned = re.sub(r'[<>{}[\]\\]', '', input_str)
        return cleaned

    async def _monitor_container_output(self, container, client_id: str):
        """Мониторинг вывода контейнера в реальном времени"""
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
        """Парсинг GPIO событий из логов"""
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
        """Обновление состояния GPIO"""
        if pin not in self.gpio_state:
            self.gpio_state[pin] = {}
        
        self.gpio_state[pin].update(updates)

    def stop_execution(self, client_id: str):
        """Принудительная остановка выполнения кода"""
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