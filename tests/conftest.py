import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import FastAPI
from app.main import app, get_session_manager, get_container_manager
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from datetime import datetime

# Базовый URL для тестирования
BASE_URL = "http://test"

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Создание event loop для сессии тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def mock_container_manager():
    """Фикстура для мокового менеджера контейнеров"""
    mock = MagicMock()
    mock.start_container.return_value = "mock_container_id"
    mock.get_container_status.return_value = "running"
    mock.upload_code.return_value = True
    mock.stop_container.return_value = True
    
    # Мок для client.ping()
    mock.client = MagicMock()
    mock.client.ping.return_value = True
    return mock

@pytest.fixture(scope="function")
def mock_session_info():
    """Фикстура для моковой информации о сессии"""
    from app.models import SessionInfo
    return SessionInfo(
        session_id="test_session_id",
        status="running",
        container_id="test_container_id",
        container_status="running",
        created_at=datetime.now(),
        last_activity=datetime.now()
    )

@pytest.fixture(scope="function")
def mock_session_manager(mock_container_manager, mock_session_info):
    """Фикстура для мокового менеджера сессий"""
    mock = MagicMock()
    mock.create_session.return_value = mock_session_info
    mock.get_session.return_value = mock_session_info
    mock.terminate_session.return_value = True
    mock.upload_code_to_session.return_value = True
    return mock

@pytest_asyncio.fixture(scope="function")
async def client(mock_session_manager, mock_container_manager):
    """Фикстура для создания асинхронного HTTP клиента с моками"""
    
    # Создаем патчи для зависимостей
    with patch('app.main.get_session_manager') as mock_get_session, \
         patch('app.main.get_container_manager') as mock_get_container:
        
        mock_get_session.return_value = mock_session_manager
        mock_get_container.return_value = mock_container_manager
        
        # Переопределяем зависимости в приложении
        app.dependency_overrides[get_session_manager] = lambda: mock_session_manager
        app.dependency_overrides[get_container_manager] = lambda: mock_container_manager
        
        async with AsyncClient(app=app, base_url=BASE_URL) as client:
            yield client
    
    # Очищаем переопределения после теста
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def test_code():
    """Фикстура с тестовым кодом"""
    return "print('Hello from test code!')"