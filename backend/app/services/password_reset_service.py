"""
Servicio para manejo de códigos de restablecimiento de contraseña
"""
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

class PasswordResetService:
    """Servicio para manejo de códigos de restablecimiento de contraseña"""
    
    def __init__(self):
        # Almacenamiento temporal de códigos (en producción usar Redis)
        self.reset_codes: Dict[str, Dict] = {}
        self.code_expiry_minutes = 1  # 1 minuto = 60 segundos
    
    def generate_reset_code(self) -> str:
        """
        Genera un código aleatorio de 4 dígitos
        
        Returns:
            str: Código de 4 dígitos
        """
        return f"{secrets.randbelow(10000):04d}"
    
    async def send_reset_code(self, email: str) -> Dict:
        """
        Envía código de restablecimiento por email
        
        Args:
            email: Email del usuario
        
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Generar código
            code = self.generate_reset_code()
            
            # Calcular expiración
            expires_at = datetime.now() + timedelta(minutes=self.code_expiry_minutes)
            
            # Almacenar código
            self.reset_codes[email] = {
                "code": code,
                "expires_at": expires_at,
                "attempts": 0,
                "max_attempts": 3
            }
            
            # Enviar email
            email_sent = await email_service.send_password_reset_code(
                email, 
                code, 
                self.code_expiry_minutes
            )
            
            if email_sent:
                logger.info(f"✅ Código de restablecimiento enviado a {email}")
                return {
                    "success": True,
                    "message": "Código enviado exitosamente",
                    "expires_in_seconds": self.code_expiry_minutes * 60
                }
            else:
                # Limpiar código si no se pudo enviar el email
                if email in self.reset_codes:
                    del self.reset_codes[email]
                
                logger.error(f"❌ Error enviando código a {email}")
                return {
                    "success": False,
                    "message": "Error enviando el código de verificación"
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
        """
        Verifica si el código ha sido verificado correctamente
        
        Args:
            email: Email del usuario
        
        Returns:
            bool: True si el código está verificado y no ha expirado
        """
        try:
            if email not in self.reset_codes:
                return False
            
            reset_data = self.reset_codes[email]
            
            # Verificar expiración
            if datetime.now() > reset_data["expires_at"]:
                del self.reset_codes[email]
                return False
            
            # Verificar si está verificado
            return reset_data.get("verified", False)
            
        except Exception as e:
            logger.error(f"❌ Error en is_code_verified para {email}: {str(e)}")
            return False
    
    def clear_reset_code(self, email: str) -> None:
        """
        Limpia el código de restablecimiento
        
        Args:
            email: Email del usuario
        """
        try:
            if email in self.reset_codes:
                del self.reset_codes[email]
                logger.info(f"🧹 Código de restablecimiento limpiado para {email}")
        except Exception as e:
            logger.error(f"❌ Error limpiando código para {email}: {str(e)}")
    
    async def send_password_change_confirmation(self, email: str) -> bool:
        """
        Envía confirmación de cambio de contraseña exitoso
        
        Args:
            email: Email del usuario
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            success = await email_service.send_password_reset_success(email)
            if success:
                logger.info(f"✅ Confirmación de cambio de contraseña enviada a {email}")
            else:
                logger.error(f"❌ Error enviando confirmación a {email}")
            return success
        except Exception as e:
            logger.error(f"❌ Error en send_password_change_confirmation para {email}: {str(e)}")
            return False
    
    def cleanup_expired_codes(self) -> None:
        """
        Limpia códigos expirados (llamar periódicamente)
        """
        try:
            current_time = datetime.now()
            expired_emails = []
            
            for email, reset_data in self.reset_codes.items():
                if current_time > reset_data["expires_at"]:
                    expired_emails.append(email)
            
            for email in expired_emails:
                del self.reset_codes[email]
            
            if expired_emails:
                logger.info(f"🧹 Limpiados {len(expired_emails)} códigos expirados")
                
        except Exception as e:
            logger.error(f"❌ Error en cleanup_expired_codes: {str(e)}")

# Instancia global del servicio
password_reset_service = PasswordResetService()

# Tarea de limpieza periódica
async def cleanup_task():
    """Tarea que limpia códigos expirados cada 5 minutos"""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutos
            password_reset_service.cleanup_expired_codes()
        except Exception as e:
            logger.error(f"❌ Error en cleanup_task: {str(e)}")
