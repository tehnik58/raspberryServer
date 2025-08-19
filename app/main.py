from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import uvicorn

from app.config import settings
from app.api.endpoints import health, websocket
from app.services.websocket_manager import websocket_manager
from app.services.code_execution_service import code_execution_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Raspberry Pi Simulator API")
    
    # Устанавливаем зависимость между сервисами (устраняем циклический импорт)
    websocket_manager.set_code_execution_service(code_execution_service)
    
    yield
    # Shutdown
    print("Shutting down Raspberry Pi Simulator API")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["health"])
app.include_router(websocket.router, prefix=settings.API_PREFIX, tags=["websocket"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Raspberry Pi Simulator API",
        "version": settings.VERSION,
        "docs": "/docs"
    }