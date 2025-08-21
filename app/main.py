from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from .models import SessionCreate, SessionInfo, CodeSubmission
from .session_manager import SessionManager
from .container_manager import ContainerManager
from .config import settings
from fastapi import Depends

# Измените функции-зависимости:
def get_session_manager() -> SessionManager:
    return session_manager

def get_container_manager() -> ContainerManager:
    return container_manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация менеджеров
container_manager = ContainerManager()
session_manager = SessionManager(container_manager)

@app.post("/sessions", response_model=SessionInfo, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_create: SessionCreate,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Создание новой сессии эмуляции"""
    try:
        session_info = session_manager.create_session()
        
        if session_info.status == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session container"
            )
            
        return session_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Удаление сессии"""
    if not session_manager.terminate_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"message": "Session terminated"}

@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Получение информации о сессии"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session

@app.post("/sessions/{session_id}/code")
async def upload_code(
    session_id: str,
    code_submission: CodeSubmission,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Загрузка кода в сессию"""
    success = session_manager.upload_code_to_session(session_id, code_submission.code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload code to session"
        )
    
    return {"message": "Code uploaded successfully"}

@app.get("/health")
async def health_check(
    container_manager: ContainerManager = Depends(get_container_manager)
):
    """Проверка состояния сервера и Docker"""
    try:
        # Проверяем соединение с Docker
        container_manager.client.ping()
        return {"status": "healthy", "docker": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "docker": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)