"""
Router para restablecimiento de contraseña
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetCodeVerify,
    PasswordResetNewPassword,
    PasswordResetResponse
)
from app.services.password_reset_service import password_reset_service
from app.supabase.auth_service import supabase_admin
from app.core.config import SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)

# Constantes de mensajes
MSG_ERROR_INTERNO_SERVIDOR = "Error interno del servidor"

router = APIRouter(prefix="/password-reset", tags=["Password Reset"])

@router.post("/request", response_model=PasswordResetResponse)
async def request_password_reset(request: PasswordResetRequest):
    """
    Solicita restablecimiento de contraseña enviando código por email
    """
    try:
        email = request.email.lower().strip()
        
        # Verificar si el email existe en Supabase Auth
        try:
            # Buscar usuario por email en Supabase Auth
            users_response = supabase_admin.auth.admin.list_users()
            user_exists = False
            
            for user in users_response:
                if user.email and user.email.lower() == email:
                    user_exists = True
                    break
            
            if not user_exists:
                logger.warning(f"⚠️ Intento de restablecimiento para email no registrado: {email}")
                return PasswordResetResponse(
                    success=False,
                    message="No se encontró una cuenta con este email"
                )
            
        except Exception as e:
            logger.error(f"❌ Error verificando usuario en Supabase: {str(e)}")
            return PasswordResetResponse(
                success=False,
                message="Error verificando la cuenta"
            )
        
        # Enviar código de restablecimiento
        result = await password_reset_service.send_reset_code(email)
        
        if result["success"]:
            logger.info(f"✅ Código de restablecimiento enviado a {email}")
            return PasswordResetResponse(
                success=True,
                message=result["message"],
                expires_in_seconds=result.get("expires_in_seconds")
            )
        else:
            logger.error(f"❌ Error enviando código a {email}: {result['message']}")
            return PasswordResetResponse(
                success=False,
                message=result["message"]
            )
            
    except Exception as e:
        logger.error(f"❌ Error en request_password_reset: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )

@router.post("/verify-code", response_model=PasswordResetResponse)
async def verify_reset_code(request: PasswordResetCodeVerify):
    """
    Verifica el código de restablecimiento
    """
    try:
        email = request.email.lower().strip()
        code = request.code.strip()
        
        # Verificar código
        result = password_reset_service.verify_reset_code(email, code)
        
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
        logger.error(f"❌ Error en verify_reset_code: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )

@router.post("/set-new-password", response_model=PasswordResetResponse)
async def set_new_password(request: PasswordResetNewPassword):
    """
    Establece nueva contraseña después de verificar el código
    """
    try:
        email = request.email.lower().strip()
        new_password = request.new_password
        
        # Verificar que el código esté verificado
        if not password_reset_service.is_code_verified(email):
            logger.warning(f"⚠️ Intento de cambiar contraseña sin código verificado para {email}")
            return PasswordResetResponse(
                success=False,
                message="Debes verificar el código primero"
            )
        
        # Buscar usuario en Supabase Auth
        try:
            users_response = supabase_admin.auth.admin.list_users()
            user_id = None
            
            for user in users_response:
                if user.email and user.email.lower() == email:
                    user_id = user.id
                    break
            
            if not user_id:
                logger.error(f"❌ Usuario no encontrado en Supabase para {email}")
                return PasswordResetResponse(
                    success=False,
                    message="Usuario no encontrado"
                )
            
            # Actualizar contraseña en Supabase Auth
            update_result = supabase_admin.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password}
            )
            
            if update_result.user:
                # Limpiar código de restablecimiento
                password_reset_service.clear_reset_code(email)
                
                # Enviar confirmación por email
                await password_reset_service.send_password_change_confirmation(email)
                
                logger.info(f"✅ Contraseña actualizada exitosamente para {email}")
                return PasswordResetResponse(
                    success=True,
                    message="Tu contraseña se cambió correctamente. Ahora podés iniciar sesión con tu nueva contraseña."
                )
            else:
                logger.error(f"❌ Error actualizando contraseña en Supabase para {email}")
                return PasswordResetResponse(
                    success=False,
                    message="Error actualizando la contraseña"
                )
                
        except Exception as e:
            logger.error(f"❌ Error actualizando contraseña en Supabase para {email}: {str(e)}")
            return PasswordResetResponse(
                success=False,
                message="Error actualizando la contraseña"
            )
            
    except Exception as e:
        logger.error(f"❌ Error en set_new_password: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )

@router.get("/status/{email}")
async def get_reset_status(email: str):
    """
    Obtiene el estado del restablecimiento de contraseña
    """
    try:
        email = email.lower().strip()
        
        # Verificar si hay un código activo
        if email in password_reset_service.reset_codes:
            reset_data = password_reset_service.reset_codes[email]
            
            # Verificar expiración
            from datetime import datetime
            if datetime.now() > reset_data["expires_at"]:
                password_reset_service.clear_reset_code(email)
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
        logger.error(f"❌ Error en get_reset_status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )
