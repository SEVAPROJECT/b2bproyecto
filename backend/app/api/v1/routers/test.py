from fastapi import APIRouter, Depends
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test", tags=["test"])

@router.get("/health")
async def test_health():
    """
    Endpoint de prueba para verificar que el backend funciona.
    """
    return {
        "status": "ok",
        "message": "Backend funcionando correctamente",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@router.get("/auth")
async def test_auth(current_user: SupabaseUser = Depends(get_current_user)):
    """
    Endpoint de prueba para verificar autenticación.
    """
    return {
        "status": "ok",
        "message": "Autenticación funcionando",
        "user_id": current_user.id,
        "user_email": current_user.email
    }
