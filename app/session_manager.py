from typing import Dict, Optional
import uuid
from datetime import datetime
from .models import SessionInfo

class SessionManager:
    def __init__(self, container_manager):
        self.sessions: Dict[str, SessionInfo] = {}
        self.container_manager = container_manager

    def create_session(self) -> SessionInfo:
        """Создание новой сессии с запуском контейнера"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        try:
            # Запускаем контейнер
            container_id = self.container_manager.start_container(session_id)
            
            session_info = SessionInfo(
                session_id=session_id,
                status="running",
                container_id=container_id,
                container_status="running",
                created_at=now,
                last_activity=now
            )
            
            self.sessions[session_id] = session_info
            return session_info
            
        except Exception as e:
            # Если не удалось запустить контейнер, создаем сессию с ошибкой
            session_info = SessionInfo(
                session_id=session_id,
                status="error",
                container_id=None,
                container_status="failed",
                created_at=now,
                last_activity=now
            )
            
            self.sessions[session_id] = session_info
            return session_info

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Получение информации о сессии"""
        session = self.sessions.get(session_id)
        if session and session.container_id:
            # Обновляем статус контейнера
            container_status = self.container_manager.get_container_status(session.container_id)
            if container_status:
                session.container_status = container_status
                session.last_activity = datetime.now()
        
        return session

    def terminate_session(self, session_id: str) -> bool:
        """Удаление сессии и остановка контейнера"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # Останавливаем контейнер, если он существует
        if session.container_id:
            self.container_manager.stop_container(session.container_id)
        
        # Удаляем сессию из памяти
        del self.sessions[session_id]
        return True

    def upload_code_to_session(self, session_id: str, code: str) -> bool:
        """Загрузка кода в контейнер сессии"""
        session = self.sessions.get(session_id)
        if not session or not session.container_id:
            return False
        
        # Загружаем код в контейнер
        success = self.container_manager.upload_code(session.container_id, code)
        if success:
            session.last_activity = datetime.now()
        
        return success