import docker
import asyncio
from typing import Callable, Any
import select

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            self.client.ping()
            print("Docker connection successful")
        except Exception as e:
            print(f"Docker connection error: {e}")
            raise Exception(f"Cannot connect to Docker daemon: {str(e)}")
    
    async def execute_code_realtime(self, code: str, output_callback: Callable[[str], Any]) -> None:
        """Выполняет код с настоящим потоковым выводом"""
        try:
            print(f"Starting realtime execution of code length: {len(code)}")
            
            # Запускаем контейнер с TTY для интерактивного вывода
            container = self.client.containers.run(
                image="rpi-emulator",
                command=['python', '-u', '-c', code],  # -u для unbuffered output
                detach=True,
                mem_limit='100m',
                network_mode='none',
                tty=True,  # Включаем TTY для интерактивности
            )
            
            # Подключаемся к контейнеру для потокового вывода
            stream = container.attach(stream=True, logs=True, stdout=True, stderr=True)
            
            # Читаем вывод в реальном времени
            while True:
                try:
                    # Читаем данные из потока
                    data = next(stream)
                    if data:
                        output_line = data.decode('utf-8').strip()
                        if output_line:
                            await output_callback(output_line)
                    await asyncio.sleep(0.01)  # Небольшая задержка
                except StopIteration:
                    break
                except Exception as e:
                    print(f"Stream reading error: {e}")
                    break
            
            # Ждем завершения контейнера
            result = container.wait()
            container.remove()
            
            if result['StatusCode'] != 0:
                await output_callback(f"Ошибка: контейнер завершился с кодом {result['StatusCode']}")
                
        except Exception as e:
            error_msg = f"Ошибка выполнения: {str(e)}"
            print(error_msg)
            await output_callback(error_msg)