import os
import tempfile
from typing import Annotated
import docker
from fastapi import FastAPI, HTTPException, UploadFile
import subprocess

app = FastAPI()
client = docker.from_env()

@app.post("/run_script/")
async def run_script(py_file: UploadFile, req_file: UploadFile):
    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Сохраняем полученные файлы
            py_path = os.path.join(temp_dir, "script.py")
            req_path = os.path.join(temp_dir, "requirements.txt")
            
            with open(py_path, "wb") as f:
                f.write(await py_file.read())
            
            with open(req_path, "wb") as f:
                f.write(await req_file.read())
            
            # Создаем Dockerfile
            dockerfile_content = f"""
            FROM python:3.11-slim
            WORKDIR /app
            COPY . .
            RUN pip install --no-cache-dir -r requirements.txt
            CMD ["python", "script.py"]
            """
            
            with open(os.path.join(temp_dir, "Dockerfile"), "w") as f:
                f.write(dockerfile_content)
        
            print("Start docker build")
            # Собираем Docker-образ
            image, build_logs = client.images.build(
                path=temp_dir,
                tag="user-script",
                rm=True,  # Удаляем промежуточные контейнеры
                forcerm=True
            )
            print("End docker build")
            print("Start up container")
            # Запускаем контейнер с ограничениями
            container = client.containers.run(
                image.id,
                detach=True,
                stdout=True,
                stderr=True,
                mem_limit="100m",  # Ограничение памяти
                cpu_quota=50000,    # Ограничение CPU (50% ядра)
                network_mode="none", # Запрет сетевого доступа
                #runtime="runsc",     # Используем gVisor для усиления изоляции (опционально)
            )
            # Ждем завершения и получаем логи
            result = container.wait(timeout=30)
            logs = container.logs().decode("utf-8")
            s_log = str(logs).replace("\n","\n\t")
            print(f'\nlogs:\n\t{s_log}')
            container.remove()
            print("delete container")
            
            # Проверяем статус завершения
            if result["StatusCode"] != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Script execution failed with code {result['StatusCode']}"
                )
            
            return {"output": logs}
        
        except docker.errors.BuildError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Build failed: {', '.join([item['stream'] for item in e.build_log if 'stream' in item])}"
            )
        
        except docker.errors.ContainerError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Container error: {e.stderr.decode('utf-8')}"
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal error: {str(e)}"
            )