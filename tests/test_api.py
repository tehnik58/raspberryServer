import pytest
from fastapi import status
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_create_session(client, mock_session_manager, mock_session_info):
    """Тест создания сессии"""
    response = await client.post("/sessions", json={})
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    assert data["session_id"] == mock_session_info.session_id
    assert data["status"] == mock_session_info.status
    assert data["container_id"] == mock_session_info.container_id
    
    # Проверяем, что метод был вызван
    mock_session_manager.create_session.assert_called_once()

@pytest.mark.asyncio
async def test_get_session(client, mock_session_manager, mock_session_info):
    """Тест получения информации о сессии"""
    response = await client.get(f"/sessions/{mock_session_info.session_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["session_id"] == mock_session_info.session_id
    assert data["status"] == mock_session_info.status
    assert data["container_id"] == mock_session_info.container_id
    
    # Проверяем, что метод был вызван
    mock_session_manager.get_session.assert_called_once_with(mock_session_info.session_id)

@pytest.mark.asyncio
async def test_get_nonexistent_session(client, mock_session_manager):
    """Тест получения информации о несуществующей сессии"""
    # Настраиваем мок для возврата None (сессия не найдена)
    mock_session_manager.get_session.return_value = None
    
    response = await client.get("/sessions/nonexistent-session-id")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    
    assert "detail" in data
    assert data["detail"] == "Session not found"

@pytest.mark.asyncio
async def test_delete_session(client, mock_session_manager):
    """Тест удаления сессии"""
    response = await client.delete("/sessions/test_session_id")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert "message" in data
    assert data["message"] == "Session terminated"
    
    # Проверяем, что метод был вызван
    mock_session_manager.terminate_session.assert_called_once_with("test_session_id")

@pytest.mark.asyncio
async def test_delete_nonexistent_session(client, mock_session_manager):
    """Тест удаления несуществующей сессии"""
    # Настраиваем мок для неудачного удаления
    mock_session_manager.terminate_session.return_value = False
    
    response = await client.delete("/sessions/nonexistent-session-id")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    
    assert "detail" in data
    assert data["detail"] == "Session not found"

@pytest.mark.asyncio
async def test_health_check(client, mock_container_manager):
    """Тест проверки состояния сервера"""
    response = await client.get("/health")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert "status" in data
    assert "docker" in data
    assert data["status"] == "healthy"
    assert data["docker"] == "connected"
    
    # Проверяем, что метод был вызван
    mock_container_manager.client.ping.assert_called_once()

@pytest.mark.asyncio
async def test_health_check(client, mock_container_manager):
    """Тест проверки состояния сервера"""
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "docker" in data
    assert data["status"] == "healthy"
    assert data["docker"] == "connected"
    
    # Проверяем, что метод был вызван
    mock_container_manager.client.ping.assert_called_once()