"""
Servicio directo de restablecimiento de contraseña con Gmail SMTP
"""
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client
from app.services.gmail_smtp_service import gmail_smtp_service

logger = logging.getLogger(__name__)

class DirectPasswordResetService:
    """Servicio directo para restablecimiento de contraseña"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_SERVICE_ROLE_KEY
        self.supabase: Client = None
        
        # Almacenamiento temporal de códigos (en producción usar Redis)
        self.reset_codes: Dict[str, Dict] = {}
        self.code_expiry_seconds = 60  # 60 segundos como solicitado
        
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                logger.info("✅ Cliente Supabase configurado para restablecimiento directo")
            except Exception as e:
                logger.error(f"❌ Error configurando Supabase: {str(e)}")
    
    def generate_reset_code(self) -> str:
        """Genera un código aleatorio de 4 dígitos"""
        return f"{secrets.randbelow(10000):04d}"
    
    async def send_reset_code(self, email: str) -> Dict:
        """
        Genera y envía código de restablecimiento por Gmail SMTP
        
        Args:
            email: Email del usuario
        
        Returns:
            Dict: Resultado de la operación
        """
        try:
            if not self.supabase:
                return {
                    "success": False,
                    "message": "Servicio no configurado"
                }
            
            # Verificar si el usuario existe
            user_exists = await self.verify_user_exists(email)
            if not user_exists:
                return {
                    "success": False,
                    "message": "No se encontró una cuenta con este email"
                }
            
            # Generar código
            code = self.generate_reset_code()
            
            # Calcular expiración (60 segundos)
            expires_at = datetime.now() + timedelta(seconds=self.code_expiry_seconds)
            
            # Almacenar código
            self.reset_codes[email] = {
                "code": code,
                "expires_at": expires_at,
                "attempts": 0,
                "max_attempts": 5
            }
            
            # Enviar código por Gmail SMTP
            email_sent = gmail_smtp_service.send_password_reset_code(
                email, 
                code, 
                expires_in_minutes=1  # 1 minuto para mostrar en el email
            )
            
            if email_sent:
                logger.info(f"✅ Código de restablecimiento enviado a {email}: {code}")
                return {
                    "success": True,
                    "message": "Código de restablecimiento enviado a tu correo electrónico",
                    "expires_in_seconds": self.code_expiry_seconds,
                    "expires_at": expires_at.isoformat()
                }
            else:
                # Si falla el envío, limpiar el código
                del self.reset_codes[email]
                logger.error(f"❌ Error enviando código a {email}")
                return {
                    "success": False,
                    "message": "Error enviando el código. Verifica tu configuración de Gmail SMTP."
                }
                
        except Exception as e:
            logger.error(f"❌ Error en send_reset_code para {email}: {str(e)}")
            return {
                "success": False,
                "message": "Error interno del servidor"
            }
    
    def verify_reset_code(self, email: str, code: str) -> Dict:
        """
        Verifica el código de restablecimiento
        
        Args:
            email: Email del usuario
            code: Código ingresado
        
        Returns:
            Dict: Resultado de la verificación
        """
        try:
            # Verificar si existe el código para este email
            if email not in self.reset_codes:
                return {
                    "success": False,
                    "message": "No hay código de restablecimiento para este email"
                }
            
            reset_data = self.reset_codes[email]
            
            # Verificar expiración
            if datetime.now() > reset_data["expires_at"]:
                # Limpiar código expirado
                del self.reset_codes[email]
                return {
                    "success": False,
                    "message": "El código ha expirado. Solicita uno nuevo.",
                    "expired": True
                }
            
            # Verificar intentos máximos
            if reset_data["attempts"] >= reset_data["max_attempts"]:
                # Limpiar código por demasiados intentos
                del self.reset_codes[email]
                return {
                    "success": False,
                    "message": "Demasiados intentos fallidos. Solicita un nuevo código.",
                    "max_attempts_reached": True
                }
            
            # Verificar código
            if reset_data["code"] == code:
                # Código correcto - marcar como verificado
                reset_data["verified"] = True
                reset_data["verified_at"] = datetime.now()
                
                logger.info(f"✅ Código verificado correctamente para {email}")
                return {
                    "success": True,
                    "message": "Código verificado correctamente"
                }
            else:
                # Código incorrecto - incrementar intentos
                reset_data["attempts"] += 1
                remaining_attempts = reset_data["max_attempts"] - reset_data["attempts"]
                
                logger.warning(f"⚠️ Código incorrecto para {email}. Intentos restantes: {remaining_attempts}")
                return {
                    "success": False,
                    "message": f"Código incorrecto. Te quedan {remaining_attempts} intentos.",
                    "remaining_attempts": remaining_attempts
                }
                
        except Exception as e:
            logger.error(f"❌ Error en verify_reset_code para {email}: {str(e)}")
            return {
                "success": False,
                "message": "Error interno del servidor"
            }
    
    def is_code_verified(self, email: str) -> bool:
        """Verifica si el código ha sido verificado correctamente"""
        try:
            if email not in self.reset_codes:
                return False
            
            reset_data = self.reset_codes[email]
            
            # Verificar si está verificado
            is_verified = reset_data.get("verified", False)
            
            # Si está verificado, mantenerlo activo independientemente de la expiración
            if is_verified:
                return True
            
            # Si no está verificado, verificar expiración
            if datetime.now() > reset_data["expires_at"]:
                del self.reset_codes[email]
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error en is_code_verified para {email}: {str(e)}")
            return False
    
    def clear_reset_code(self, email: str) -> None:
        """Limpia el código de restablecimiento"""
        try:
            if email in self.reset_codes:
                del self.reset_codes[email]
                logger.info(f"🧹 Código de restablecimiento limpiado para {email}")
        except Exception as e:
            logger.error(f"❌ Error limpiando código para {email}: {str(e)}")
    
    async def verify_user_exists(self, email: str) -> bool:
        """Verifica si el usuario existe en Supabase Auth"""
        try:
            if not self.supabase:
                return False
            
            # Buscar usuario por email (ejecutar llamada síncrona en thread separado)
            users_response = await asyncio.to_thread(
                self.supabase.auth.admin.list_users
            )
            
            for user in users_response:
                if user.email and user.email.lower() == email.lower():
                    logger.info(f"✅ Usuario encontrado: {email}")
                    return True
            
            logger.warning(f"⚠️ Usuario no encontrado: {email}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verificando usuario {email}: {str(e)}")
            return False
    
    async def update_user_password(self, email: str, new_password: str) -> Dict:
        """Actualiza la contraseña del usuario usando Supabase Auth"""
        try:
            if not self.supabase:
                return {
                    "success": False,
                    "message": "Servicio no configurado"
                }
            
            # Buscar usuario por email (ejecutar llamada síncrona en thread separado)
            users_response = await asyncio.to_thread(
                self.supabase.auth.admin.list_users
            )
            user_id = None
            
            for user in users_response:
                if user.email and user.email.lower() == email.lower():
                    user_id = user.id
                    break
            
            if not user_id:
                return {
                    "success": False,
                    "message": "Usuario no encontrado"
                }
            
            # Actualizar contraseña (ejecutar llamada síncrona en thread separado)
            update_result = await asyncio.to_thread(
                self.supabase.auth.admin.update_user_by_id,
                user_id,
                {"password": new_password}
            )
            
            if update_result.user:
                # Enviar correo de confirmación
                gmail_smtp_service.send_password_reset_success(email)
                
                # Limpiar código de restablecimiento
                self.clear_reset_code(email)
                
                logger.info(f"✅ Contraseña actualizada para {email}")
                return {
                    "success": True,
                    "message": "Contraseña actualizada exitosamente"
                }
            else:
                logger.error(f"❌ Error actualizando contraseña para {email}")
                return {
                    "success": False,
                    "message": "Error actualizando la contraseña"
                }
                
        except Exception as e:
            logger.error(f"❌ Error en update_user_password para {email}: {str(e)}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}"
            }

# Instancia global del servicio
direct_password_reset_service = DirectPasswordResetService()
