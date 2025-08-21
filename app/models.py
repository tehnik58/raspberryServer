from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SessionCreate(BaseModel):
    """Модель для создания сессии"""
    pass

class SessionInfo(BaseModel):
    """Модель информации о сессии"""
    session_id: str
    status: str
    container_id: Optional[str] = None
    container_status: Optional[str] = None
    created_at: datetime
    last_activity: datetime

class CodeSubmission(BaseModel):
    """Модель для отправки кода"""
    code: str