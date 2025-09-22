"""
Servicio de envío de correos usando SMTP de Gmail o API HTTP como fallback
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
import os
import httpx
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class GmailSMTPService:
    """Servicio para envío de correos usando SMTP de Gmail"""
    
    def __init__(self):
        # Configuración SMTP - Intenta múltiples configuraciones para superar restricciones de Railway
        self.configurations = [
            {
                "server": "smtp.gmail.com",
                "port": 587,
                "use_tls": True,
                "name": "Gmail TLS"
            },
            {
                "server": "smtp.gmail.com",
                "port": 465,
                "use_ssl": True,
                "name": "Gmail SSL"
            },
            {
                "server": "smtp-mail.outlook.com",
                "port": 587,
                "use_tls": True,
                "name": "Outlook TLS"
            },
            {
                "server": "smtp-mail.outlook.com",
                "port": 25,
                "use_tls": False,
                "name": "Outlook Plain"
            }
        ]

        # Para credenciales, permite ambas nomenclaturas por retrocompatibilidad
        self.sender_email = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or os.getenv("GMAIL_EMAIL")
        self.sender_password = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
        self.sender_name = os.getenv("SMTP_FROM_NAME") or os.getenv("SENDER_NAME") or os.getenv("GMAIL_SENDER_NAME", "B2B Platform")

        # Configuración API HTTP (SendGrid o similar) - opcional
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.api_enabled = bool(self.sendgrid_api_key)

        # Verificar configuración
        smtp_configurado = bool(self.sender_email and self.sender_password)

        if smtp_configurado:
            logger.info(f"✅ SMTP configurado para: {self.sender_email}")
            logger.info(f"🔄 Configuraciones disponibles: {len(self.configurations)} (intentará todas hasta que una funcione)")
        else:
            logger.warning("⚠️ SMTP no configurado. Faltan variables (SMTP_USER/GMAIL_EMAIL o SMTP_PASSWORD/GMAIL_APP_PASSWORD)")

        if self.api_enabled:
            logger.info("✅ API Email (SendGrid) configurada como respaldo")
        else:
            logger.info("ℹ️ API Email no configurada - solo SMTP disponible")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envía un correo electrónico intentando múltiples configuraciones SMTP

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            # Verificar configuración básica
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

            # Intentar cada configuración disponible
            for config in self.configurations:
                try:
                    logger.info(f"🔄 Intentando configuración: {config['name']} ({config['server']}:{config['port']})")

                    # Crear contexto SSL para todas las configuraciones
                    context = ssl.create_default_context()

                    # Intentar conexión según la configuración
                    if config.get("use_ssl"):
                        # Conexión SSL directa (puerto 465)
                        with smtplib.SMTP_SSL(config["server"], config["port"], context=context) as server:
                            server.login(self.sender_email, self.sender_password)
                            server.sendmail(self.sender_email, to_email, message.as_string())
                    else:
                        # Conexión estándar con STARTTLS (puerto 587) o sin cifrado (puerto 25)
                        with smtplib.SMTP(config["server"], config["port"]) as server:
                            if config.get("use_tls", True):
                                server.starttls(context=context)
                            server.login(self.sender_email, self.sender_password)
                            server.sendmail(self.sender_email, to_email, message.as_string())

                    logger.info(f"✅ Correo enviado exitosamente a {to_email} usando {config['name']}")
                    return True

                except Exception as e:
                    logger.warning(f"⚠️ Configuración {config['name']} falló: {str(e)}")
                    continue

            # Si ninguna configuración funcionó
            logger.error(f"❌ Todas las configuraciones SMTP fallaron para {to_email}")
            return False

        except Exception as e:
            logger.error(f"❌ Error general enviando correo a {to_email}: {str(e)}")
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
        
        return self.send_email_with_fallback(to_email, subject, html_content, text_content)
    
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
        
        return self.send_email_with_fallback(to_email, subject, html_content, text_content)

    def send_email_via_api(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envía un correo electrónico usando SendGrid API (HTTP)

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            if not self.api_enabled:
                logger.warning("❌ API Email no configurada")
                return False

            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }

            # Construir el payload para SendGrid
            personalizations = [{
                "to": [{"email": to_email}],
                "subject": subject
            }]

            from_email = {
                "email": self.sender_email,
                "name": self.sender_name
            }

            content = []
            if text_content:
                content.append({
                    "type": "text/plain",
                    "value": text_content
                })
            content.append({
                "type": "text/html",
                "value": html_content
            })

            payload = {
                "personalizations": personalizations,
                "from": from_email,
                "content": content
            }

            # Enviar usando httpx (debe ser async, pero lo hago sync para compatibilidad)
            async def send_async():
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload)
                    return response

            # Ejecutar de forma síncrona
            response = asyncio.run(send_async())

            if response.status_code == 202:  # SendGrid aceptó el email
                logger.info(f"✅ Correo enviado exitosamente via API a {to_email}")
                return True
            else:
                logger.error(f"❌ Error en API SendGrid: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error enviando correo via API a {to_email}: {str(e)}")
            return False

    def send_email_with_fallback(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envía email intentando múltiples configuraciones SMTP

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        # Intentar con múltiples configuraciones SMTP (sin servicios externos)
        if self.sender_email and self.sender_password:
            logger.info("🔄 Intentando envío via SMTP con múltiples configuraciones...")
            smtp_result = self.send_email(to_email, subject, html_content, text_content)
            if smtp_result:
                return True

        # Si todas las configuraciones SMTP fallan, intentar API solo si está configurada
        if self.api_enabled:
            logger.warning("⚠️ Todas las configuraciones SMTP fallaron, intentando SendGrid como último recurso...")
            api_result = self.send_email_via_api(to_email, subject, html_content, text_content)
            if api_result:
                return True

        # Si todo falla
        logger.error("❌ No se pudo enviar el correo - revisa configuración SMTP o agrega SENDGRID_API_KEY")
        return False

# Instancia global del servicio
gmail_smtp_service = GmailSMTPService()
