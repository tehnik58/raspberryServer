import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Virtual Constructor API"
    PROJECT_VERSION: str = "1.0.0"
    
    # Docker settings
    DOCKER_IMAGE: str = os.getenv("DOCKER_IMAGE", "virtual-constructor-emulator:latest")
    DOCKER_NETWORK: str = os.getenv("DOCKER_NETWORK", "virtual-constructor-network")
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # Container settings
    CONTAINER_MEMORY_LIMIT: str = os.getenv("CONTAINER_MEMORY_LIMIT", "512m")
    CONTAINER_CPU_SHARES: int = int(os.getenv("CONTAINER_CPU_SHARES", 1024))

settings = Settings()