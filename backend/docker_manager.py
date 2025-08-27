import time
import docker
import asyncio
import tempfile
from fastapi import WebSocket
import os
import json
import re

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            print("Docker connection successful")
            
            # Находим запущенный контейнер emulation-docker
            self.emulation_container = None
            containers = self.client.containers.list()
            for container in containers:
                if 'emulation-docker' in container.name or 'raspberry-emulation' in container.name:
                    self.emulation_container = container
                    break
            
            if self.emulation_container:
                print(f"Found emulation container: {self.emulation_container.name}")
            else:
                print("Emulation container not found")
                
        except Exception as e:
            print(f"Docker connection error: {e}")
            raise Exception(f"Cannot connect to Docker daemon: {str(e)}")

    async def execute_code_realtime(self, code: str, websocket: WebSocket) -> None:
        """Выполняет код с потоковой передачей вывода через WebSocket"""
        try:
            print(f"Starting execution of code length: {len(code)}")

            # Отправляем сообщение о начале выполнения
            await websocket.send_json({
                "type": "execution_started",
                "message": "Выполнение началось"
            })

            if self.emulation_container:
                # Используем скрипт-обертку в запущенном контейнере
                await self._execute_via_container(code, websocket)
            else:
                # Альтернативный способ (должен работать, но лучше через контейнер)
                await self._execute_direct(code, websocket)

        except Exception as e:
            error_msg = f"Ошибка выполнения: {str(e)}"
            print(error_msg)
            await websocket.send_json({
                "type": "error",
                "content": error_msg
            })

    async def _execute_via_container(self, code: str, websocket: WebSocket):
        """Выполняет код через запущенный контейнер"""
        # Создаем временный файл с кодом
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Копируем файл в контейнер
            with open(temp_file, 'rb') as f:
                # Создаем tar-архив
                import tarfile
                import io
                
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    file_data = code.encode('utf-8')
                    tarinfo = tarfile.TarInfo(name='user_code.py')
                    tarinfo.size = len(file_data)
                    tarinfo.mtime = time.time()
                    tar.addfile(tarinfo, io.BytesIO(file_data))
                
                tar_stream.seek(0)
                self.emulation_container.put_archive('/tmp', tar_stream)

            # Выполняем код через скрипт-обертку
            exec_command = ['python', '/app/execute.py', '/tmp/user_code.py']
            exec_result = self.emulation_container.exec_run(
                exec_command,
                stream=True,
                demux=True
            )

            # Читаем вывод в реальном времени
            for line in exec_result.output:
                if line:
                    stdout, stderr = line
                    if stdout:
                        output_text = stdout.decode('utf-8').strip()
                        if output_text:
                            await websocket.send_json({
                                "type": "output",
                                "content": output_text
                            })
                    if stderr:
                        error_text = stderr.decode('utf-8').strip()
                        if error_text:
                            await websocket.send_json({
                                "type": "error",
                                "content": error_text
                            })
                
                await asyncio.sleep(0.01)

            # Отправляем сообщение о завершении
            await websocket.send_json({
                "type": "execution_completed",
                "message": "Выполнение завершено"
            })

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    async def _execute_direct(self, code: str, websocket: WebSocket):
        """Альтернативный способ выполнения (если контейнер не найден)"""
        # Создаем временный файл с кодом
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Запускаем процесс с правильным PYTHONPATH
            process = await asyncio.create_subprocess_exec(
                'python', '/app/execute.py', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'PYTHONPATH': '/app'}
            )

            # Читаем stdout
            async for line in process.stdout:
                output_line = line.decode('utf-8').strip()
                if output_line:
                    await websocket.send_json({
                        "type": "output",
                        "content": output_line
                    })

            # Читаем stderr
            async for line in process.stderr:
                error_line = line.decode('utf-8').strip()
                if error_line:
                    await websocket.send_json({
                        "type": "error",
                        "content": error_line
                    })

            # Ждем завершения процесса
            exit_code = await process.wait()

            if exit_code != 0:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Ошибка: процесс завершился с кодом {exit_code}"
                })

            # Отправляем сообщение о завершении
            await websocket.send_json({
                "type": "execution_completed",
                "message": "Выполнение завершено"
            })

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file):
                os.unlink(temp_file)
# В класс DockerManager добавляем метод для обработки событий
async def _stream_container_logs(self, container):
    """Асинхронно читает логи контейнера и парсит события"""
    try:
        # Получаем поток логов
        log_stream = container.logs(stream=True, follow=True)
        
        # Регулярное выражение для поиска событий эмуляции
        event_pattern = re.compile(r'@@EMU_EVENT:(\{.*\})')
        
        # Читаем логи в реальном времени
        for line in log_stream:
            output_line = line.decode('utf-8').strip()
            if output_line:
                # Проверяем, является ли строка событием эмуляции
                event_match = event_pattern.search(output_line)
                if event_match:
                    try:
                        event_data = json.loads(event_match.group(1))
                        yield {'type': 'event', 'data': event_data}
                    except json.JSONDecodeError:
                        yield {'type': 'output', 'data': output_line}
                else:
                    yield {'type': 'output', 'data': output_line}
            
            # Даем возможность другим задачам работать
            await asyncio.sleep(0.01)
    except Exception as e:
        yield {'type': 'output', 'data': f"Ошибка чтения логов: {str(e)}"}

# Обновляем execute_code_realtime для обработки событий
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

        # Запускаем контейнер и передаем код через stdin
        container = self.client.containers.run(
            image="rpi-emulator",
            command=['python', '-c', code],
            detach=True,
            mem_limit='100m',
            network_mode='none',
            stdout=True,
            stderr=True,
            remove=True
        )

        # Читаем логи в реальном времени
        async for log_item in self._stream_container_logs(container):
            if log_item['type'] == 'output':
                await websocket.send_json({
                    "type": "output",
                    "content": log_item['data']
                })
            elif log_item['type'] == 'event':
                # Отправляем событие эмуляции на фронтенд
                await websocket.send_json({
                    "type": "emu_event",
                    "event": log_item['data']
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