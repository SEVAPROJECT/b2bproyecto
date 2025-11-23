"""
Router para restablecimiento de contraseña directo (sin SMTP)
"""
from fastapi import APIRouter, HTTPException, status
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

# Constantes para mensajes de error
ERROR_INTERNO_SERVIDOR = "Error interno del servidor"
MENSAJE_NO_CODIGO_ACTIVO = "No hay código activo"
MENSAJE_VERIFICAR_CODIGO_PRIMERO = "Debes verificar el código primero"
MENSAJE_CONTRASENA_CAMBIADA = "Tu contraseña se cambió correctamente. Ahora podés iniciar sesión con tu nueva contraseña."

# Constantes para claves de diccionario
KEY_HAS_ACTIVE_CODE = "has_active_code"
KEY_MESSAGE = "message"
KEY_IS_VERIFIED = "is_verified"
KEY_ATTEMPTS = "attempts"
KEY_MAX_ATTEMPTS = "max_attempts"
KEY_EXPIRES_AT = "expires_at"
KEY_SUCCESS = "success"
KEY_VERIFIED = "verified"

@router.post("/request", response_model=PasswordResetResponse)
async def request_password_reset_direct(request: PasswordResetRequest):
    """
    Solicita restablecimiento de contraseña (devuelve código directamente)
    """
    try:
        email = request.email.lower().strip()
        
        # Generar y devolver código directamente
        result = await direct_password_reset_service.send_reset_code(email)
        
        if result[KEY_SUCCESS]:
            logger.info(f"✅ Código de restablecimiento generado para {email}")
            return PasswordResetResponse(
                success=True,
                message=result[KEY_MESSAGE],
                expires_in_seconds=result.get("expires_in_seconds")
            )
        else:
            logger.error(f"❌ Error generando código para {email}: {result[KEY_MESSAGE]}")
            return PasswordResetResponse(
                success=False,
                message=result[KEY_MESSAGE]
            )
            
    except Exception as e:
        logger.error(f"❌ Error en request_password_reset_direct: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_INTERNO_SERVIDOR
        )

@router.post("/verify-code", response_model=PasswordResetResponse)
async def verify_reset_code_direct(request: PasswordResetCodeVerify):
    """
    Verifica el código de restablecimiento
    """
    try:
        email = request.email.lower().strip()
        
        # Verificar código
        result = direct_password_reset_service.verify_reset_code(email, request.code.strip())
        
        if result[KEY_SUCCESS]:
            logger.info(f"✅ Código verificado correctamente para {email}")
            return PasswordResetResponse(
                success=True,
                message=result[KEY_MESSAGE]
            )
        else:
            logger.warning(f"⚠️ Código incorrecto para {email}: {result[KEY_MESSAGE]}")
            return PasswordResetResponse(
                success=False,
                message=result[KEY_MESSAGE],
                remaining_attempts=result.get("remaining_attempts"),
                expired=result.get("expired"),
                max_attempts_reached=result.get("max_attempts_reached")
            )
            
    except Exception as e:
        logger.error(f"❌ Error en verify_reset_code_direct: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_INTERNO_SERVIDOR
        )

@router.post("/set-new-password", response_model=PasswordResetResponse)
async def set_new_password_direct(request: PasswordResetNewPassword):
    """
    Establece nueva contraseña después de verificar el código
    """
    try:
        email = request.email.lower().strip()
        new_password = request.new_password
        
        # Verificar que el código esté verificado
        if not direct_password_reset_service.is_code_verified(email):
            logger.warning(f"⚠️ Intento de cambiar contraseña sin código verificado para {email}")
            return PasswordResetResponse(
                success=False,
                message=MENSAJE_VERIFICAR_CODIGO_PRIMERO
            )
        
        # Actualizar contraseña
        result = await direct_password_reset_service.update_user_password(email, new_password)
        
        if result[KEY_SUCCESS]:
            logger.info(f"✅ Contraseña actualizada exitosamente para {email}")
            return PasswordResetResponse(
                success=True,
                message=MENSAJE_CONTRASENA_CAMBIADA
            )
        else:
            logger.error(f"❌ Error actualizando contraseña para {email}: {result[KEY_MESSAGE]}")
            return PasswordResetResponse(
                success=False,
                message=result[KEY_MESSAGE]
            )
            
    except Exception as e:
        logger.error(f"❌ Error en set_new_password_direct: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_INTERNO_SERVIDOR
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
            if datetime.now() > reset_data[KEY_EXPIRES_AT]:
                direct_password_reset_service.clear_reset_code(email)
                return {
                    KEY_HAS_ACTIVE_CODE: False,
                    KEY_MESSAGE: MENSAJE_NO_CODIGO_ACTIVO
                }
            
            return {
                KEY_HAS_ACTIVE_CODE: True,
                KEY_IS_VERIFIED: reset_data.get(KEY_VERIFIED, False),
                KEY_ATTEMPTS: reset_data[KEY_ATTEMPTS],
                KEY_MAX_ATTEMPTS: reset_data[KEY_MAX_ATTEMPTS],
                KEY_EXPIRES_AT: reset_data[KEY_EXPIRES_AT].isoformat()
            }
        else:
            return {
                KEY_HAS_ACTIVE_CODE: False,
                KEY_MESSAGE: MENSAJE_NO_CODIGO_ACTIVO
            }
            
    except Exception as e:
        logger.error(f"❌ Error en get_reset_status_direct: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_INTERNO_SERVIDOR
        )
