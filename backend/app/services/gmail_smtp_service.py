"""
Servicio de envío de correos usando SMTP de Gmail directamente
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class GmailSMTPService:
    """Servicio para envío de correos usando SMTP de Gmail"""
    
    def __init__(self):
        # Configuración SMTP - Prioriza variables genéricas, luego específicas de Gmail
        self.smtp_server = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        
        # Para credenciales, permite ambas nomenclaturas por retrocompatibilidad
        self.sender_email = os.getenv("SMTP_USER") or os.getenv("GMAIL_EMAIL")
        self.sender_password = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
        self.sender_name = os.getenv("SENDER_NAME") or os.getenv("GMAIL_SENDER_NAME", "B2B Platform")
        
        # Verificar configuración
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ SMTP no configurado. Faltan variables (SMTP_USER/GMAIL_EMAIL o SMTP_PASSWORD/GMAIL_APP_PASSWORD)")
        else:
            logger.info(f"✅ SMTP configurado para: {self.sender_email} en {self.smtp_server}:{self.smtp_port}")
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envía un correo electrónico usando SMTP de Gmail
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)
        
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            # Verificar configuración
            if not self.sender_email or not self.sender_password:
                logger.error("❌ SMTP no configurado. Verifica las variables de entorno.")
                return False
            
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            
            # Agregar contenido de texto plano si se proporciona
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # Agregar contenido HTML
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Enviar correo
            logger.info(f"📧 Enviando correo a {to_email} usando Gmail SMTP...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            logger.info(f"✅ Correo enviado exitosamente a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando correo a {to_email}: {str(e)}")
            return False
    
    def send_password_reset_code(
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
        subject = "Código de restablecimiento de contraseña - SEVA EMPRESAS"
        
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
                    margin-bottom: 5px;
                }}
                .tagline {{
                    font-size: 14px;
                    color: #64748b;
                    font-style: italic;
                    margin-bottom: 15px;
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
                    <div class="logo">SEVA EMPRESAS</div>
                    <p class="tagline">Conectando empresas, potenciando el crecimiento en Paraguay.</p>
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
                    <p>© 2025 Seva Empresas. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Restablecimiento de contraseña - SEVA EMPRESAS
        
        Hola,
        
        Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.
        
        Tu código de verificación es: {code}
        
        Este código expira en {expires_in_minutes} minuto{'s' if expires_in_minutes > 1 else ''}.
        
        Si no solicitaste este cambio, puedes ignorar este correo.
        
        Saludos,
        Equipo SEVA EMPRESAS
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_success(
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
        subject = "Contraseña actualizada exitosamente - SEVA EMPRESAS"
        
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
                    <div class="logo">SEVA EMPRESAS</div>
                    <p class="tagline">Conectando empresas, potenciando el crecimiento en Paraguay.</p>
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
                    <p>© 2025 Seva Empresas. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Contraseña actualizada exitosamente - SEVA EMPRESAS
        
        Hola,
        
        Tu contraseña ha sido cambiada correctamente. Ahora puedes iniciar sesión con tu nueva contraseña.
        
        Si no realizaste este cambio, contacta inmediatamente a nuestro equipo de soporte.
        
        Saludos,
        Equipo SEVA EMPRESAS
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

# Instancia global del servicio
gmail_smtp_service = GmailSMTPService()
