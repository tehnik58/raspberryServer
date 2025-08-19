from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Проверка состояния сервера
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "message": "Server is running"}
    )