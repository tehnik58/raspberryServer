import docker
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from .config import settings

logger = logging.getLogger(__name__)

class ContainerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def start_container(self, session_id: str) -> str:
        """Запуск контейнера для сессии"""
        try:
            # Определяем параметры контейнера
            container_config = {
                "image": settings.DOCKER_IMAGE,
                "detach": True,
                "mem_limit": settings.CONTAINER_MEMORY_LIMIT,
                "cpu_shares": settings.CONTAINER_CPU_SHARES,
                "network": settings.DOCKER_NETWORK,
                "environment": {
                    "SESSION_ID": session_id,
                    "REDIS_HOST": settings.REDIS_HOST,
                    "REDIS_PORT": str(settings.REDIS_PORT)
                },
                "name": f"vc-session-{session_id}",
                "auto_remove": False
            }

            # Запускаем контейнер
            container = self.client.containers.run(**container_config)
            logger.info(f"Container started for session {session_id}: {container.id}")
            
            return container.id
            
        except docker.errors.ImageNotFound:
            logger.error(f"Docker image {settings.DOCKER_IMAGE} not found")
            raise Exception(f"Docker image {settings.DOCKER_IMAGE} not found")
        except Exception as e:
            logger.error(f"Failed to start container for session {session_id}: {e}")
            raise

    def stop_container(self, container_id: str) -> bool:
        """Остановка контейнера"""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            logger.info(f"Container {container_id} stopped and removed")
            return True
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False

    def get_container_status(self, container_id: str) -> Optional[str]:
        """Получение статуса контейнера"""
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except Exception as e:
            logger.error(f"Failed to get status for container {container_id}: {e}")
            return None

    def upload_code(self, container_id: str, code: str) -> bool:
        """Загрузка кода в контейнер"""
        try:
            container = self.client.containers.get(container_id)
            
            # Создаем файл с кодом в контейнере
            exec_result = container.exec_run(
                f"sh -c 'echo \"{code}\" > /app/user_code.py'",
                workdir="/app"
            )
            
            if exec_result.exit_code == 0:
                logger.info(f"Code uploaded to container {container_id}")
                return True
            else:
                logger.error(f"Failed to upload code to container {container_id}: {exec_result.output}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to upload code to container {container_id}: {e}")
            return False