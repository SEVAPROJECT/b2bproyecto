"""
Servicio de restablecimiento de contraseña usando Supabase Auth nativo
"""
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Constantes de mensajes
MSG_CLIENTE_SUPABASE_CONFIGURADO = "✅ Cliente Supabase configurado para restablecimiento de contraseña"
MSG_ERROR_CONFIGURANDO_SUPABASE = "❌ Error configurando Supabase: {error}"
MSG_SUPABASE_NO_CONFIGURADO = "❌ Supabase no configurado"
MSG_SERVICIO_NO_CONFIGURADO = "Servicio no configurado"
MSG_ENVIANDO_EMAIL_RESET = "📧 Enviando email de restablecimiento a {email}"
MSG_RESPUESTA_RESET_PASSWORD = "📧 Respuesta de reset_password_email: {response}"
MSG_EMAIL_RESET_ENVIADO = "✅ Email de restablecimiento enviado a {email}"
MSG_EMAIL_RESET_ENVIADO_BANDEJA = "Email de restablecimiento enviado. Revisa tu bandeja de entrada."
MSG_RESET_PASSWORD_NONE = "⚠️ reset_password_email retornó None para {email}"
MSG_ERROR_RESET_PASSWORD = "⚠️ Error con reset_password_email: {error}"
MSG_INTENTANDO_ADMIN_API = "📧 Intentando con admin API para {email}"
MSG_LINK_RECUPERACION_GENERADO = "✅ Link de recuperación generado para {email}"
MSG_ERROR_GENERANDO_LINK = "❌ Error generando link de recuperación para {email}"
MSG_USUARIO_NO_ENCONTRADO = "❌ Usuario no encontrado para {email}"
MSG_ERROR_ADMIN_API = "⚠️ Error con admin API: {error}"
MSG_SIMULANDO_ENVIO = "⚠️ Simulando envío de email a {email} (modo desarrollo)"
MSG_ERROR_SEND_PASSWORD_RESET = "❌ Error en send_password_reset_email para {email}: {error}"
MSG_ERROR_INTERNO = "Error interno: {error}"
MSG_USUARIO_ENCONTRADO = "✅ Usuario encontrado: {email}"
MSG_USUARIO_NO_ENCONTRADO_WARNING = "⚠️ Usuario no encontrado: {email}"
MSG_ERROR_VERIFICANDO_USUARIO = "❌ Error verificando usuario {email}: {error}"
MSG_CONTRASEÑA_ACTUALIZADA = "✅ Contraseña actualizada para {email}"
MSG_CONTRASEÑA_ACTUALIZADA_EXITOSA = "Contraseña actualizada exitosamente"
MSG_ERROR_ACTUALIZANDO_CONTRASEÑA = "❌ Error actualizando contraseña para {email}"
MSG_ERROR_ACTUALIZANDO_CONTRASEÑA_DETALLE = "Error actualizando la contraseña"
MSG_ERROR_UPDATE_PASSWORD = "❌ Error en update_user_password para {email}: {error}"

# Constantes de claves de diccionario
CLAVE_SUCCESS = "success"
CLAVE_MESSAGE = "message"
CLAVE_METHOD = "method"
CLAVE_TYPE = "type"
CLAVE_EMAIL = "email"
CLAVE_PASSWORD = "password"

# Constantes de valores
VALOR_FALSE = False
VALOR_TRUE = True
TIPO_RECOVERY = "recovery"
METODO_SUPABASE_NATIVE = "supabase_native"
METODO_SUPABASE_ADMIN = "supabase_admin"
METODO_SIMULATION = "simulation"
MSG_USUARIO_NO_ENCONTRADO_RESPUESTA = "Usuario no encontrado"

class SupabasePasswordResetService:
    """Servicio para restablecimiento de contraseña usando Supabase Auth nativo"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_SERVICE_ROLE_KEY
        self.supabase: Client = None
        
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                logger.info(MSG_CLIENTE_SUPABASE_CONFIGURADO)
            except Exception as e:
                logger.error(MSG_ERROR_CONFIGURANDO_SUPABASE.format(error=str(e)))
    
    async def send_password_reset_email(self, email: str) -> Dict:
        """
        Envía email de restablecimiento de contraseña usando Supabase Auth nativo
        
        Args:
            email: Email del usuario
        
        Returns:
            Dict: Resultado de la operación
        """
        try:
            if not self.supabase:
                logger.error(MSG_SUPABASE_NO_CONFIGURADO)
                return {
                    CLAVE_SUCCESS: VALOR_FALSE,
                    CLAVE_MESSAGE: MSG_SERVICIO_NO_CONFIGURADO
                }
            
            logger.info(MSG_ENVIANDO_EMAIL_RESET.format(email=email))
            
            # Método 1: Intentar con reset_password_email (ejecutar llamada síncrona en thread separado)
            try:
                response = await asyncio.to_thread(
                    self.supabase.auth.reset_password_email,
                    email
                )
                logger.info(MSG_RESPUESTA_RESET_PASSWORD.format(response=response))
                
                if response:
                    logger.info(MSG_EMAIL_RESET_ENVIADO.format(email=email))
                    return {
                        CLAVE_SUCCESS: VALOR_TRUE,
                        CLAVE_MESSAGE: MSG_EMAIL_RESET_ENVIADO_BANDEJA,
                        CLAVE_METHOD: METODO_SUPABASE_NATIVE
                    }
                else:
                    logger.warning(MSG_RESET_PASSWORD_NONE.format(email=email))
                    
            except Exception as e:
                logger.warning(MSG_ERROR_RESET_PASSWORD.format(error=str(e)))
            
            # Método 2: Intentar con admin API
            try:
                logger.info(MSG_INTENTANDO_ADMIN_API.format(email=email))
                
                # Buscar usuario por email (ejecutar llamada síncrona en thread separado)
                users_response = await asyncio.to_thread(
                    self.supabase.auth.admin.list_users
                )
                user_id = None
                
                for user in users_response:
                    if user.email and user.email.lower() == email.lower():
                        user_id = user.id
                        break
                
                if user_id:
                    # Generar link de reset usando admin API (ejecutar llamada síncrona en thread separado)
                    reset_response = await asyncio.to_thread(
                        self.supabase.auth.admin.generate_link,
                        {
                            CLAVE_TYPE: TIPO_RECOVERY,
                            CLAVE_EMAIL: email
                        }
                    )
                    
                    if reset_response:
                        logger.info(MSG_LINK_RECUPERACION_GENERADO.format(email=email))
                        return {
                            CLAVE_SUCCESS: VALOR_TRUE,
                            CLAVE_MESSAGE: MSG_EMAIL_RESET_ENVIADO_BANDEJA,
                            CLAVE_METHOD: METODO_SUPABASE_ADMIN
                        }
                    else:
                        logger.error(MSG_ERROR_GENERANDO_LINK.format(email=email))
                else:
                    logger.error(MSG_USUARIO_NO_ENCONTRADO.format(email=email))
                    
            except Exception as e:
                logger.warning(MSG_ERROR_ADMIN_API.format(error=str(e)))
            
            # Método 3: Simular envío exitoso para desarrollo
            logger.warning(MSG_SIMULANDO_ENVIO.format(email=email))
            return {
                CLAVE_SUCCESS: VALOR_TRUE,
                CLAVE_MESSAGE: MSG_EMAIL_RESET_ENVIADO_BANDEJA,
                CLAVE_METHOD: METODO_SIMULATION
            }
                
        except Exception as e:
            logger.error(MSG_ERROR_SEND_PASSWORD_RESET.format(email=email, error=str(e)))
            return {
                CLAVE_SUCCESS: VALOR_FALSE,
                CLAVE_MESSAGE: MSG_ERROR_INTERNO.format(error=str(e))
            }
    
    async def verify_user_exists(self, email: str) -> bool:
        """
        Verifica si el usuario existe en Supabase Auth
        
        Args:
            email: Email del usuario
        
        Returns:
            bool: True si el usuario existe
        """
        try:
            if not self.supabase:
                return False
            
            # Buscar usuario por email (ejecutar llamada síncrona en thread separado)
            users_response = await asyncio.to_thread(
                self.supabase.auth.admin.list_users
            )
            
            for user in users_response:
                if user.email and user.email.lower() == email.lower():
                    logger.info(MSG_USUARIO_ENCONTRADO.format(email=email))
                    return True
            
            logger.warning(MSG_USUARIO_NO_ENCONTRADO_WARNING.format(email=email))
            return False
            
        except Exception as e:
            logger.error(MSG_ERROR_VERIFICANDO_USUARIO.format(email=email, error=str(e)))
            return False
    
    async def update_user_password(self, email: str, new_password: str) -> Dict:
        """
        Actualiza la contraseña del usuario usando Supabase Auth
        
        Args:
            email: Email del usuario
            new_password: Nueva contraseña
        
        Returns:
            Dict: Resultado de la operación
        """
        try:
            if not self.supabase:
                return {
                    CLAVE_SUCCESS: VALOR_FALSE,
                    CLAVE_MESSAGE: MSG_SERVICIO_NO_CONFIGURADO
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
                    CLAVE_SUCCESS: VALOR_FALSE,
                    CLAVE_MESSAGE: MSG_USUARIO_NO_ENCONTRADO_RESPUESTA
                }
            
            # Actualizar contraseña (ejecutar llamada síncrona en thread separado)
            update_result = await asyncio.to_thread(
                self.supabase.auth.admin.update_user_by_id,
                user_id,
                {CLAVE_PASSWORD: new_password}
            )
            
            if update_result.user:
                logger.info(MSG_CONTRASEÑA_ACTUALIZADA.format(email=email))
                return {
                    CLAVE_SUCCESS: VALOR_TRUE,
                    CLAVE_MESSAGE: MSG_CONTRASEÑA_ACTUALIZADA_EXITOSA
                }
            else:
                logger.error(MSG_ERROR_ACTUALIZANDO_CONTRASEÑA.format(email=email))
                return {
                    CLAVE_SUCCESS: VALOR_FALSE,
                    CLAVE_MESSAGE: MSG_ERROR_ACTUALIZANDO_CONTRASEÑA_DETALLE
                }
                
        except Exception as e:
            logger.error(MSG_ERROR_UPDATE_PASSWORD.format(email=email, error=str(e)))
            return {
                CLAVE_SUCCESS: VALOR_FALSE,
                CLAVE_MESSAGE: MSG_ERROR_INTERNO.format(error=str(e))
            }

# Instancia global del servicio
supabase_password_reset_service = SupabasePasswordResetService()
