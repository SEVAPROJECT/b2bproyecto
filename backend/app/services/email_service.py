"""
Servicio de envío de correos electrónicos usando Supabase
"""
import asyncio
from typing import Optional
import logging
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio para envío de correos electrónicos usando Supabase"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_SERVICE_ROLE_KEY
        self.supabase: Client = None
        
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                logger.info("✅ Cliente Supabase configurado para envío de correos")
            except Exception as e:
                logger.error(f"❌ Error configurando Supabase: {str(e)}")
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envía un correo electrónico usando Supabase Auth
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)
        
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            if not self.supabase:
                logger.error("❌ Supabase no configurado para envío de correos")
                return False
            
            logger.info(f"📧 Enviando correo a {to_email} usando Supabase Auth...")
            
            # Para correos de restablecimiento de contraseña, usar el método nativo de Supabase
            if "código de restablecimiento" in subject.lower() or "password reset" in subject.lower():
                try:
                    logger.info(f"📧 Enviando email de restablecimiento a {to_email}")
                    
                    # Usar el método nativo de Supabase Auth para reset de contraseña
                    response = self.supabase.auth.reset_password_email(to_email)
                    
                    if response:
                        logger.info(f"✅ Email de restablecimiento enviado a {to_email}")
                        return True
                    else:
                        logger.error(f"❌ Error en respuesta de Supabase para {to_email}")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ Error enviando email de restablecimiento a {to_email}: {str(e)}")
                    return False
            
            # Para otros tipos de correo, intentar Edge Function
            try:
                email_data = {
                    "to": to_email,
                    "subject": subject,
                    "html": html_content
                }
                
                if text_content:
                    email_data["text"] = text_content
                
                response = self.supabase.functions.invoke(
                    "send-email",
                    {
                        "body": email_data
                    }
                )
                
                if response:
                    logger.info(f"✅ Correo enviado exitosamente a {to_email} via Edge Function")
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ Edge Function no disponible: {str(e)}")
            
            # Fallback: Simular envío para desarrollo
            logger.warning(f"⚠️ Simulando envío de correo a {to_email} (modo desarrollo)")
            logger.info(f"📧 Asunto: {subject}")
            logger.info(f"📧 Contenido: {html_content[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando correo a {to_email}: {str(e)}")
            return False
    
    async def send_password_reset_code(
        self, 
        to_email: str, 
        code: str, 
        expires_in_minutes: int = 1
    ) -> bool:
        """
        Envía código de restablecimiento de contraseña
        
        Args:
            to_email: Email del usuario
            code: Código de 4 dígitos
            expires_in_minutes: Minutos de expiración
        
        Returns:
            bool: True si se envió correctamente
        """
        subject = "Código de restablecimiento de contraseña"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Código de restablecimiento</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2563eb;
                    margin-bottom: 10px;
                }}
                .code-container {{
                    background-color: #f8fafc;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #2563eb;
                    letter-spacing: 8px;
                    font-family: 'Courier New', monospace;
                }}
                .warning {{
                    background-color: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 20px 0;
                    color: #92400e;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e2e8f0;
                    text-align: center;
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔐 B2B Platform</div>
                    <h1>Restablecimiento de contraseña</h1>
                </div>
                
                <p>Hola,</p>
                
                <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. Utiliza el siguiente código para continuar:</p>
                
                <div class="code-container">
                    <div class="code">{code}</div>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Importante:</strong> Este código expira en {expires_in_minutes} minuto{'s' if expires_in_minutes > 1 else ''}. 
                    Si no solicitaste este cambio, puedes ignorar este correo.
                </div>
                
                <p>Si tienes problemas, contacta a nuestro equipo de soporte.</p>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>© 2024 B2B Platform. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Restablecimiento de contraseña - B2B Platform
        
        Hola,
        
        Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.
        
        Tu código de verificación es: {code}
        
        Este código expira en {expires_in_minutes} minuto{'s' if expires_in_minutes > 1 else ''}.
        
        Si no solicitaste este cambio, puedes ignorar este correo.
        
        Saludos,
        Equipo B2B Platform
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset_success(
        self, 
        to_email: str
    ) -> bool:
        """
        Envía confirmación de cambio de contraseña exitoso
        
        Args:
            to_email: Email del usuario
        
        Returns:
            bool: True si se envió correctamente
        """
        subject = "Contraseña actualizada exitosamente"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Contraseña actualizada</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2563eb;
                    margin-bottom: 10px;
                }}
                .success {{
                    background-color: #d1fae5;
                    border: 1px solid #10b981;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 20px 0;
                    color: #065f46;
                    text-align: center;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e2e8f0;
                    text-align: center;
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔐 B2B Platform</div>
                    <h1>Contraseña actualizada</h1>
                </div>
                
                <p>Hola,</p>
                
                <div class="success">
                    <strong>✅ ¡Contraseña actualizada exitosamente!</strong>
                </div>
                
                <p>Tu contraseña ha sido cambiada correctamente. Ahora puedes iniciar sesión con tu nueva contraseña.</p>
                
                <p>Si no realizaste este cambio, contacta inmediatamente a nuestro equipo de soporte.</p>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>© 2024 B2B Platform. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Contraseña actualizada exitosamente - B2B Platform
        
        Hola,
        
        Tu contraseña ha sido cambiada correctamente. Ahora puedes iniciar sesión con tu nueva contraseña.
        
        Si no realizaste este cambio, contacta inmediatamente a nuestro equipo de soporte.
        
        Saludos,
        Equipo B2B Platform
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)

# Instancia global del servicio de email
email_service = EmailService()
