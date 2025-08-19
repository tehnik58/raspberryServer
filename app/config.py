import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Основные настройки
    PROJECT_NAME: str = "Raspberry Pi Simulator API"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    # Настройки CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]
    
    # WebSocket настройки
    WS_MAX_CONNECTIONS: int = 100
    WS_KEEPALIVE_INTERVAL: int = 20
    
    # Настройки Docker для выполнения кода
    DOCKER_IMAGE: str = "python:3.9-slim"
    DOCKER_TIMEOUT: int = 30
    DOCKER_MEMORY_LIMIT: str = "100m"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()