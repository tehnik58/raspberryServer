import time
import docker
import asyncio
import tempfile
from fastapi import WebSocket
import os
import json
import re
from system_model import SystemModel

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            print("Docker connection successful")

            # Проверяем, запущен ли контейнер
            self.emulation_container = None
            containers = self.client.containers.list()
            for container in containers:
                if 'emulation-docker' in container.name or 'raspberry-emulation' in container.name:
                    self.emulation_container = container
                    break

            if not self.emulation_container:
                print("Emulation container not found. Starting...")
                # Запускаем через docker-compose или вручную
                # Или бросаем исключение
                raise Exception("Контейнер emulation-docker не запущен. Выполните: docker-compose up --build")
            else:
                print(f"Found emulation container: {self.emulation_container.name}")

        except Exception as e:
            print(f"Docker connection error: {e}")
            raise

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
            try:
                exec_result = self.emulation_container.exec_run(
                    exec_command,
                    stream=True,
                    demux=True,
                    socket=False
                )
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Ошибка выполнения команды: {str(e)}"
                })
                return
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

    async def _execute_via_container(self, code: str, websocket: WebSocket):
        """Выполняет код через запущенный контейнер (альтернативный способ)"""
        # Создаем временный файл с кодом
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        try:
            # Копируем файл в контейнер
            with open(temp_file, 'rb') as f:
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
            # Выполняем код через execute.py
            exec_command = ['python', '/app/execute.py', '/tmp/user_code.py']
            exec_result = self.emulation_container.exec_run(
                exec_command,
                stream=True,
                demux=True
            )
            # Чтение вывода
            for stdout_chunk, stderr_chunk in exec_result.output:
                if stdout_chunk:
                    await websocket.send_json({
                        "type": "output",
                        "content": stdout_chunk.decode('utf-8').strip()
                    })
                if stderr_chunk:
                    await websocket.send_json({
                        "type": "error",
                        "content": stderr_chunk.decode('utf-8').strip()
                    })
                await asyncio.sleep(0.01)
            await websocket.send_json({
                "type": "execution_completed",
                "message": "Выполнение завершено"
            })
        finally:
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

    async def _stream_container_logs(self, container):
        """Асинхронно читает логи контейнера и парсит события"""
        try:
            log_stream = container.logs(stream=True, follow=True)
            event_pattern = re.compile(r'@@EMU_EVENT:(\{.*\})')
            for line in log_stream:
                output_line = line.decode('utf-8').strip()
                if output_line:
                    event_match = event_pattern.search(output_line)
                    if event_match:
                        try:
                            event_data = json.loads(event_match.group(1))
                            yield {'type': 'event', 'data': event_data}
                        except json.JSONDecodeError:
                            yield {'type': 'output', 'data': output_line}
                    else:
                        yield {'type': 'output', 'data': output_line}
                await asyncio.sleep(0.01)
        except Exception as e:
            yield {'type': 'output', 'data': f"Ошибка чтения логов: {str(e)}"}

    # backend/docker_manager.py

    async def execute_code_realtime(self, code: str, websocket: WebSocket, system_model=None) -> None:
        """Выполняет код через запущенный контейнер emulation-docker"""
        if not self.emulation_container:
            await websocket.send_json({
                "type": "error",
                "content": "Ошибка: контейнер эмуляции не запущен"
            })
            return

        temp_file = None
        try:
            # Отправляем начало выполнения
            await websocket.send_json({
                "type": "execution_started",
                "message": "Выполнение началось"
            })

            # Создаём временный файл
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Копируем файл в контейнер как tar-архив
            import tarfile
            import io
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tarinfo = tarfile.TarInfo(name='user_code.py')
                tarinfo.size = len(code.encode('utf-8'))
                tar.addfile(tarinfo, io.BytesIO(code.encode('utf-8')))
            tar_stream.seek(0)
            self.emulation_container.put_archive('/tmp', tar_stream)

            # Выполняем через execute.py
            exec_command = ['python', '/app/execute.py', '/tmp/user_code.py']
            exec_result = self.emulation_container.exec_run(
                exec_command,
                stream=True,
                demux=True
            )

            # Читаем вывод в реальном времени
            for stdout_chunk, stderr_chunk in exec_result.output:
                if stdout_chunk:
                    output_line = stdout_chunk.decode('utf-8').strip()
                    if output_line:
                        if output_line.startswith('@@EMU_EVENT:'):
                            try:
                                event_data = json.loads(output_line.replace('@@EMU_EVENT:', '', 1))
                                await websocket.send_json({
                                    "type": "emu_event",
                                    "event": event_data
                                })
                            except json.JSONDecodeError:
                                await websocket.send_json({
                                    "type": "output",
                                    "content": output_line
                                })
                        else:
                            await websocket.send_json({
                                "type": "output",
                                "content": output_line
                            })
                if stderr_chunk:
                    error_line = stderr_chunk.decode('utf-8').strip()
                    if error_line:
                        await websocket.send_json({
                            "type": "error",
                            "content": error_line
                        })
                await asyncio.sleep(0.01)
            # Только после завершения цикла проверяем exit_code
            if exec_result.exit_code == 0:
                await websocket.send_json({
                    "type": "execution_completed",
                    "message": "Выполнение завершено"
                })
            elif exec_result.exit_code is None:
                # Это не ошибка — команда выполнилась, но код не пришёл
                await websocket.send_json({
                    "type": "execution_completed",
                    "message": "Выполнение завершено (статус не получен)"
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Ошибка: контейнер завершился с кодом {exec_result.exit_code}"
                })

        except docker.errors.APIError as e:
            await websocket.send_json({
                "type": "error",
                "content": f"Docker API ошибка: {str(e)}"
            })
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "content": f"Ошибка выполнения: {str(e)}"
            })
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)