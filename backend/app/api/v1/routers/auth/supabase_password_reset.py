"""
Router para restablecimiento de contraseña usando Supabase Auth nativo
"""
from fastapi import APIRouter, HTTPException, status
import logging
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetNewPassword,
    PasswordResetResponse
)
from app.services.supabase_password_reset import supabase_password_reset_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/password-reset-native", tags=["Password Reset Native"])

# Constantes para mensajes
ERROR_INTERNO_SERVIDOR = "Error interno del servidor"
MENSAJE_USUARIO_NO_ENCONTRADO = "Usuario no encontrado"
MENSAJE_USUARIO_ENCONTRADO = "Usuario encontrado"
MENSAJE_NO_CUENTA_EMAIL = "No se encontró una cuenta con este email"
MENSAJE_CONTRASENAS_NO_COINCIDEN = "Las contraseñas no coinciden"
MENSAJE_CONTRASENA_CAMBIADA = "Tu contraseña se cambió correctamente. Ahora podés iniciar sesión con tu nueva contraseña."

# Constantes para claves de diccionario
KEY_SUCCESS = "success"
KEY_MESSAGE = "message"

@router.post("/request", response_model=PasswordResetResponse)
async def request_password_reset_native(request: PasswordResetRequest):
    """
    Solicita restablecimiento de contraseña usando Supabase Auth nativo
    """
    try:
        email = request.email.lower().strip()
        
        # Verificar si el usuario existe
        user_exists = await supabase_password_reset_service.verify_user_exists(email)
        
        if not user_exists:
            logger.warning(f"⚠️ Intento de restablecimiento para email no registrado: {email}")
            return PasswordResetResponse(
                success=False,
                message=MENSAJE_NO_CUENTA_EMAIL
            )
        
        # Enviar email de restablecimiento usando Supabase Auth nativo
        result = await supabase_password_reset_service.send_password_reset_email(email)
        
        if result[KEY_SUCCESS]:
            logger.info(f"✅ Email de restablecimiento enviado a {email}")
            return PasswordResetResponse(
                success=True,
                message=result[KEY_MESSAGE]
            )
        else:
            logger.error(f"❌ Error enviando email a {email}: {result[KEY_MESSAGE]}")
            return PasswordResetResponse(
                success=False,
                message=result[KEY_MESSAGE]
            )
            
    except Exception as e:
        logger.error(f"❌ Error en request_password_reset_native: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_INTERNO_SERVIDOR
        )

@router.post("/set-new-password", response_model=PasswordResetResponse)
async def set_new_password_native(request: PasswordResetNewPassword):
    """
    Establece nueva contraseña usando Supabase Auth nativo
    """
    try:
        email = request.email.lower().strip()
        new_password = request.new_password
        
        # Verificar que las contraseñas coincidan
        if request.new_password != request.confirm_password:
            return PasswordResetResponse(
                success=False,
                message=MENSAJE_CONTRASENAS_NO_COINCIDEN
            )
        
        # Verificar que el usuario existe
        user_exists = await supabase_password_reset_service.verify_user_exists(email)
        
        if not user_exists:
            return PasswordResetResponse(
                success=False,
                message=MENSAJE_USUARIO_NO_ENCONTRADO
            )
        
        # Actualizar contraseña
        result = await supabase_password_reset_service.update_user_password(email, new_password)
        
        if result[KEY_SUCCESS]:
            logger.info(f"✅ Contraseña actualizada para {email}")
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
        logger.error(f"❌ Error en set_new_password_native: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_INTERNO_SERVIDOR
        )

@router.get("/status/{email}")
async def get_reset_status_native(email: str):
    """
    Obtiene el estado del restablecimiento de contraseña
    """
    try:
        email = email.lower().strip()
        
        # Verificar si el usuario existe
        user_exists = await supabase_password_reset_service.verify_user_exists(email)
        
        return {
            "user_exists": user_exists,
            "message": MENSAJE_USUARIO_ENCONTRADO if user_exists else MENSAJE_USUARIO_NO_ENCONTRADO
        }
            
    except Exception as e:
        logger.error(f"❌ Error en get_reset_status_native: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_INTERNO_SERVIDOR
        )
