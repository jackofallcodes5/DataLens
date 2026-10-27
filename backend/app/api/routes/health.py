from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "debug": settings.DEBUG,
        "storage": "connected"
    }
