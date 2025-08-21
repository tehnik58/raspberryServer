import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_create_session_with_container(client, mock_session_manager, mock_session_info):
    """Тест создания сессии с контейнером"""
    response = await client.post("/sessions", json={})
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    assert data["session_id"] == mock_session_info.session_id
    assert data["container_id"] == mock_session_info.container_id
    assert data["status"] == mock_session_info.status
    
    # Проверяем, что метод был вызван
    mock_session_manager.create_session.assert_called_once()

@pytest.mark.asyncio
async def test_upload_code_to_session(client, mock_session_manager, test_code):
    """Тест загрузки кода в сессию"""
    response = await client.post(
        "/sessions/test_session_id/code",
        json={"code": test_code}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["message"] == "Code uploaded successfully"
    
    # Проверяем, что метод был вызван
    mock_session_manager.upload_code_to_session.assert_called_once_with("test_session_id", test_code)

@pytest.mark.asyncio
async def test_upload_code_to_nonexistent_session(client, mock_session_manager, test_code):
    """Тест загрузки кода в несуществующую сессию"""
    # Настраиваем мок для неудачной загрузки кода
    mock_session_manager.upload_code_to_session.return_value = False
    
    response = await client.post(
        "/sessions/nonexistent-session/code",
        json={"code": test_code}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    
    assert "detail" in data
    assert data["detail"] == "Failed to upload code to session"