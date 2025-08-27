import docker
import asyncio
from typing import Callable, Any
from websocket_manager import WebSocketManager  # Добавьте этот импорт
from fastapi import WebSocket
from typing import List

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            print("Docker connection successful")
        except Exception as e:
            print(f"Docker connection error: {e}")
            raise Exception(f"Cannot connect to Docker daemon: {str(e)}")

    async def execute_code_realtime(self, code: str, websocket: WebSocket) -> None:
        """Выполняет код с потоковой передачей вывода через WebSocket"""
        container = None
        try:
            print(f"Starting execution of code length: {len(code)}")
            
            # Отправляем сообщение о начале выполнения
            await websocket.send_json({
                "type": "execution_started",
                "message": "Выполнение началось"
            })

            # Запускаем контейнер
            container = self.client.containers.run(
                image="rpi-emulator",
                command=['python', '-c', code],
                detach=True,
                mem_limit='100m',
                network_mode='none',
                stdout=True,
                stderr=True
            )

            # Читаем логи в реальном времени с помощью генератора
            async for line in self._stream_container_logs(container):
                await websocket.send_json({
                    "type": "output",
                    "content": line
                })

            # Ждем завершения контейнера
            result = container.wait()
            
            if result['StatusCode'] != 0:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Ошибка: контейнер завершился с кодом {result['StatusCode']}"
                })

            # Отправляем сообщение о завершении
            await websocket.send_json({
                "type": "execution_completed",
                "message": "Выполнение завершено"
            })

        except docker.errors.ImageNotFound:
            await websocket.send_json({
                "type": "error",
                "content": "Ошибка: образ rpi-emulator не найден"
            })
        except Exception as e:
            error_msg = f"Ошибка выполнения: {str(e)}"
            print(error_msg)
            await websocket.send_json({
                "type": "error",
                "content": error_msg
            })
        finally:
            # Убеждаемся, что контейнер удален
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass

    async def _stream_container_logs(self, container):
        """Асинхронно читает логи контейнера"""
        try:
            # Получаем поток логов
            log_stream = container.logs(stream=True, follow=True)
            
            # Читаем логи в реальном времени
            for line in log_stream:
                output_line = line.decode('utf-8').strip()
                if output_line:
                    yield output_line
                    # Даем возможность другим задачам работать
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            yield f"Ошибка чтения логов: {str(e)}"