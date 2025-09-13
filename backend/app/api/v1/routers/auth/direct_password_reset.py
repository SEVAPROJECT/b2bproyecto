"""
Router para restablecimiento de contraseña directo (sin SMTP)
"""
from fastapi import APIRouter, HTTPException
import logging
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetCodeVerify,
    PasswordResetNewPassword,
    PasswordResetResponse
)
from app.services.direct_password_reset import direct_password_reset_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/password-reset-direct", tags=["Password Reset Direct"])

@router.post("/request", response_model=PasswordResetResponse)
async def request_password_reset_direct(request: PasswordResetRequest):
    """
    Solicita restablecimiento de contraseña (devuelve código directamente)
    """
    try:
        email = request.email.lower().strip()
        
        # Generar y devolver código directamente
        result = await direct_password_reset_service.send_reset_code(email)
        
        if result["success"]:
            logger.info(f"✅ Código de restablecimiento generado para {email}")
            return PasswordResetResponse(
                success=True,
                message=result["message"],
                expires_in_seconds=result.get("expires_in_seconds")
            )
        else:
            logger.error(f"❌ Error generando código para {email}: {result['message']}")
            return PasswordResetResponse(
                success=False,
                message=result["message"]
            )
            
    except Exception as e:
        logger.error(f"❌ Error en request_password_reset_direct: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.post("/verify-code", response_model=PasswordResetResponse)
async def verify_reset_code_direct(request: PasswordResetCodeVerify):
    """
    Verifica el código de restablecimiento
    """
    try:
        email = request.email.lower().strip()
        code = request.code.strip()
        
        # Verificar código
        result = direct_password_reset_service.verify_reset_code(email, code)
        
        if result["success"]:
            logger.info(f"✅ Código verificado correctamente para {email}")
            return PasswordResetResponse(
                success=True,
                message=result["message"]
            )
        else:
            logger.warning(f"⚠️ Código incorrecto para {email}: {result['message']}")
            return PasswordResetResponse(
                success=False,
                message=result["message"],
                remaining_attempts=result.get("remaining_attempts"),
                expired=result.get("expired"),
                max_attempts_reached=result.get("max_attempts_reached")
            )
            
    except Exception as e:
        logger.error(f"❌ Error en verify_reset_code_direct: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.post("/set-new-password", response_model=PasswordResetResponse)
async def set_new_password_direct(request: PasswordResetNewPassword):
    """
    Establece nueva contraseña después de verificar el código
    """
    try:
        email = request.email.lower().strip()
        code = request.code.strip() if request.code else None
        new_password = request.new_password
        
        # Verificar que el código esté verificado
        if not direct_password_reset_service.is_code_verified(email):
            logger.warning(f"⚠️ Intento de cambiar contraseña sin código verificado para {email}")
            return PasswordResetResponse(
                success=False,
                message="Debes verificar el código primero"
            )
        
        # Actualizar contraseña
        result = await direct_password_reset_service.update_user_password(email, new_password)
        
        if result["success"]:
            logger.info(f"✅ Contraseña actualizada exitosamente para {email}")
            return PasswordResetResponse(
                success=True,
                message="Tu contraseña se cambió correctamente. Ahora podés iniciar sesión con tu nueva contraseña."
            )
        else:
            logger.error(f"❌ Error actualizando contraseña para {email}: {result['message']}")
            return PasswordResetResponse(
                success=False,
                message=result["message"]
            )
            
    except Exception as e:
        logger.error(f"❌ Error en set_new_password_direct: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.get("/status/{email}")
async def get_reset_status_direct(email: str):
    """
    Obtiene el estado del restablecimiento de contraseña
    """
    try:
        email = email.lower().strip()
        
        # Verificar si hay un código activo
        if email in direct_password_reset_service.reset_codes:
            reset_data = direct_password_reset_service.reset_codes[email]
            
            # Verificar expiración
            from datetime import datetime
            if datetime.now() > reset_data["expires_at"]:
                direct_password_reset_service.clear_reset_code(email)
                return {
                    "has_active_code": False,
                    "message": "No hay código activo"
                }
            
            return {
                "has_active_code": True,
                "is_verified": reset_data.get("verified", False),
                "attempts": reset_data["attempts"],
                "max_attempts": reset_data["max_attempts"],
                "expires_at": reset_data["expires_at"].isoformat()
            }
        else:
            return {
                "has_active_code": False,
                "message": "No hay código activo"
            }
            
    except Exception as e:
        logger.error(f"❌ Error en get_reset_status_direct: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )
