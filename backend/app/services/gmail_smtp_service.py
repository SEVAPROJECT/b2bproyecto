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

# Constantes de configuración SMTP
SMTP_SERVER_GMAIL = "smtp.gmail.com"
SMTP_PORT_TLS = 587
SMTP_PORT_SSL = 465
CONFIG_NAME_GMAIL_TLS = "Gmail TLS"
CONFIG_NAME_GMAIL_SSL = "Gmail SSL"
SENDER_NAME_DEFAULT = "B2B Platform"

# Constantes de marca
MARCA_SEVA_EMPRESAS = "SEVA EMPRESAS"
TAGLINE_SEVA = "Conectando empresas, potenciando el crecimiento en Paraguay."
COPYRIGHT_SEVA = "© 2025 Seva Empresas. Todos los derechos reservados."
MENSAJE_CORREO_AUTOMATICO = "Este es un correo automático, por favor no respondas."
EQUIPO_SEVA = "Equipo SEVA EMPRESAS"

# Constantes de asuntos de email
ASUNTO_RESET_PASSWORD = "Código de restablecimiento de contraseña - SEVA EMPRESAS"
ASUNTO_PASSWORD_SUCCESS = "Contraseña actualizada exitosamente - SEVA EMPRESAS"

# Constantes de URLs de APIs
URL_BREVO_API = "https://api.brevo.com/v3/smtp/email"
URL_MAILGUN_API_TEMPLATE = "https://api.mailgun.net/v3/{domain}/messages"
URL_RESEND_API = "https://api.resend.com/emails"
URL_SENDGRID_API = "https://api.sendgrid.com/v3/mail/send"

# Constantes de headers HTTP
HEADER_API_KEY = "api-key"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_AUTHORIZATION = "Authorization"
CONTENT_TYPE_JSON = "application/json"
BEARER_PREFIX = "Bearer "

# Constantes de status codes HTTP
STATUS_CODE_BREVO_SUCCESS = 201
STATUS_CODE_MAILGUN_SUCCESS = 200
STATUS_CODE_RESEND_SUCCESS = 200
STATUS_CODE_SENDGRID_SUCCESS = 202

# Constantes de timeouts
TIMEOUT_API_REQUEST = 30.0

# Constantes de tipos MIME
MIME_TYPE_PLAIN = "text/plain"
MIME_TYPE_HTML = "text/html"
MIME_CHARSET_UTF8 = "utf-8"

# Constantes de mensajes de log
MSG_SMTP_CONFIGURADO = "✅ SMTP configurado para: {email}"
MSG_CONFIGURACIONES_DISPONIBLES = "🔄 Configuraciones disponibles: {count} (Gmail TLS/SSL rápidas)"
MSG_SMTP_NO_CONFIGURADO = "⚠️ SMTP no configurado. Faltan variables (SMTP_USER/GMAIL_EMAIL o SMTP_PASSWORD/GMAIL_APP_PASSWORD)"
MSG_API_BREVO_CONFIGURADA = "✅ API Email (Brevo) configurada - gratuito sin tarjeta"
MSG_API_SENDGRID_CONFIGURADA = "✅ API Email (SendGrid) configurada - requiere verificación"
MSG_API_MAILGUN_CONFIGURADA = "✅ API Email (Mailgun) configurada - requiere tarjeta"
MSG_API_RESEND_CONFIGURADA = "✅ API Email (Resend) configurada - no funciona con Gmail"
MSG_API_EMAIL_NO_CONFIGURADA = "⚠️ API Email no configurada - Railway bloquea SMTP en planes gratuitos"
MSG_SMTP_NO_CONFIGURADO_ERROR = "❌ SMTP no configurado. Verifica las variables de entorno."
MSG_INTENTANDO_CONFIGURACION = "🔄 Intentando configuración: {name} ({server}:{port})"
MSG_CORREO_ENVIADO_EXITOSO = "✅ Correo enviado exitosamente a {email} usando {config}"
MSG_CONFIGURACION_FALLO = "⚠️ Configuración {name} falló: {error}"
MSG_TODAS_CONFIGURACIONES_FALLARON = "❌ Todas las configuraciones SMTP fallaron para {email}"
MSG_ERROR_GENERAL_ENVIANDO = "❌ Error general enviando correo a {email}: {error}"
MSG_BREVO_API_NO_CONFIGURADA = "❌ Brevo API no configurada"
MSG_CORREO_ENVIADO_BREVO = "✅ Correo enviado exitosamente via Brevo a {email}"
MSG_ERROR_API_BREVO = "❌ Error en API Brevo: {status} - {text}"
MSG_TIMEOUT_BREVO = "❌ Timeout enviando correo via Brevo a {email}"
MSG_ERROR_CONEXION_BREVO = "❌ Error de conexión via Brevo a {email}: {error}"
MSG_ERROR_ENVIANDO_BREVO = "❌ Error enviando correo via Brevo a {email}: {error}"
MSG_MAILGUN_API_NO_CONFIGURADA = "❌ Mailgun API no configurada"
MSG_CORREO_ENVIADO_MAILGUN = "✅ Correo enviado exitosamente via Mailgun a {email}"
MSG_ERROR_API_MAILGUN = "❌ Error en API Mailgun: {status} - {text}"
MSG_TIMEOUT_MAILGUN = "❌ Timeout enviando correo via Mailgun a {email}"
MSG_ERROR_CONEXION_MAILGUN = "❌ Error de conexión via Mailgun a {email}: {error}"
MSG_ERROR_ENVIANDO_MAILGUN = "❌ Error enviando correo via Mailgun a {email}: {error}"
MSG_RESEND_API_NO_CONFIGURADA = "❌ Resend API no configurada"
MSG_CORREO_ENVIADO_RESEND = "✅ Correo enviado exitosamente via Resend a {email}"
MSG_ERROR_API_RESEND = "❌ Error en API Resend: {status} - {text}"
MSG_TIMEOUT_RESEND = "❌ Timeout enviando correo via Resend a {email}"
MSG_ERROR_CONEXION_RESEND = "❌ Error de conexión via Resend a {email}: {error}"
MSG_ERROR_ENVIANDO_RESEND = "❌ Error enviando correo via Resend a {email}: {error}"
MSG_SENDGRID_API_NO_CONFIGURADA = "❌ SendGrid API no configurada"
MSG_CORREO_ENVIADO_SENDGRID = "✅ Correo enviado exitosamente via SendGrid a {email}"
MSG_ERROR_API_SENDGRID = "❌ Error en API SendGrid: {status} - {text}"
MSG_TIMEOUT_SENDGRID = "❌ Timeout enviando correo via SendGrid a {email}"
MSG_ERROR_CONEXION_SENDGRID = "❌ Error de conexión via SendGrid a {email}: {error}"
MSG_ERROR_ENVIANDO_SENDGRID = "❌ Error enviando correo via SendGrid a {email}: {error}"
MSG_INTENTANDO_BREVO = "📧 Intentando Brevo (gratuito sin tarjeta)..."
MSG_BREVO_NO_DISPONIBLE = "📧 Brevo no disponible, intentando SendGrid..."
MSG_SENDGRID_NO_DISPONIBLE = "📧 SendGrid no disponible, intentando Mailgun..."
MSG_MAILGUN_NO_DISPONIBLE = "📧 SendGrid no disponible, intentando Mailgun..."
MSG_RESEND_NO_DISPONIBLE = "🚂 Mailgun no disponible, intentando Resend..."
MSG_APIS_FALLARON = "⚠️ APIs fallaron, intentando Gmail TLS/SSL como último recurso..."
MSG_NO_SE_PUDO_ENVIAR = "❌ No se pudo enviar el correo - configura BREVO_API_KEY (gratuito sin tarjeta) o SENDGRID_API_KEY"

class GmailSMTPService:
    """Servicio para envío de correos usando SMTP de Gmail"""
    
    def __init__(self):
        # Configuración SMTP - Solo Gmail TLS/SSL (rápido), luego directo a API
        self.configurations = [
            {
                "server": SMTP_SERVER_GMAIL,
                "port": SMTP_PORT_TLS,
                "use_tls": True,
                "name": CONFIG_NAME_GMAIL_TLS
            },
            {
                "server": SMTP_SERVER_GMAIL,
                "port": SMTP_PORT_SSL,
                "use_ssl": True,
                "name": CONFIG_NAME_GMAIL_SSL
            }
        ]

        # Para credenciales, permite ambas nomenclaturas por retrocompatibilidad
        self.sender_email = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or os.getenv("GMAIL_EMAIL")
        self.sender_password = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
        self.sender_name = os.getenv("SMTP_FROM_NAME") or os.getenv("SENDER_NAME") or os.getenv("GMAIL_SENDER_NAME", SENDER_NAME_DEFAULT)

        # Configuración API HTTP (Brevo recomendado - gratuito sin tarjeta)
        self.brevo_api_key = os.getenv("BREVO_API_KEY")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        self.mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        self.resend_api_key = os.getenv("RESEND_API_KEY")  # último respaldo
        self.api_enabled = bool(self.brevo_api_key or self.sendgrid_api_key or self.mailgun_api_key or self.resend_api_key)
        
        # Verificar configuración
        smtp_configurado = bool(self.sender_email and self.sender_password)

        if smtp_configurado:
            logger.info(MSG_SMTP_CONFIGURADO.format(email=self.sender_email))
            logger.info(MSG_CONFIGURACIONES_DISPONIBLES.format(count=len(self.configurations)))
        else:
            logger.warning(MSG_SMTP_NO_CONFIGURADO)

        if self.brevo_api_key:
            logger.info(MSG_API_BREVO_CONFIGURADA)
        elif self.sendgrid_api_key:
            logger.info(MSG_API_SENDGRID_CONFIGURADA)
        elif self.mailgun_api_key and self.mailgun_domain:
            logger.info(MSG_API_MAILGUN_CONFIGURADA)
        elif self.resend_api_key:
            logger.info(MSG_API_RESEND_CONFIGURADA)
        else:
            logger.warning(MSG_API_EMAIL_NO_CONFIGURADA)
    
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
                logger.error(MSG_SMTP_NO_CONFIGURADO_ERROR)
                return False
            
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            
            # Agregar contenido de texto plano si se proporciona
            if text_content:
                text_part = MIMEText(text_content, MIME_TYPE_PLAIN, MIME_CHARSET_UTF8)
                message.attach(text_part)
            
            # Agregar contenido HTML
            html_part = MIMEText(html_content, MIME_TYPE_HTML, MIME_CHARSET_UTF8)
            message.attach(html_part)
            
            # Intentar cada configuración disponible
            for config in self.configurations:
                try:
                    logger.info(MSG_INTENTANDO_CONFIGURACION.format(
                        name=config['name'],
                        server=config['server'],
                        port=config['port']
                    ))

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
                    
                    logger.info(MSG_CORREO_ENVIADO_EXITOSO.format(
                        email=to_email,
                        config=config['name']
                    ))
                    return True
                    
                except Exception as e:
                    logger.warning(MSG_CONFIGURACION_FALLO.format(
                        name=config['name'],
                        error=str(e)
                    ))
                    continue

            # Si ninguna configuración funcionó
            logger.error(MSG_TODAS_CONFIGURACIONES_FALLARON.format(email=to_email))
            return False

        except Exception as e:
            logger.error(MSG_ERROR_GENERAL_ENVIANDO.format(email=to_email, error=str(e)))
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
        subject = ASUNTO_RESET_PASSWORD
        
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
                    <div class="logo">{MARCA_SEVA_EMPRESAS}</div>
                    <p class="tagline">{TAGLINE_SEVA}</p>
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
                    <p>{MENSAJE_CORREO_AUTOMATICO}</p>
                    <p>{COPYRIGHT_SEVA}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Restablecimiento de contraseña - {MARCA_SEVA_EMPRESAS}
        
        Hola,
        
        Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.
        
        Tu código de verificación es: {code}
        
        Este código expira en {expires_in_minutes} minuto{'s' if expires_in_minutes > 1 else ''}.
        
        Si no solicitaste este cambio, puedes ignorar este correo.
        
        Saludos,
        {EQUIPO_SEVA}
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
        subject = ASUNTO_PASSWORD_SUCCESS
        
        html_content = """
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
                    <div class="logo">{MARCA_SEVA_EMPRESAS}</div>
                    <p class="tagline">{TAGLINE_SEVA}</p>
                    <h1>Contraseña actualizada</h1>
                </div>
                
                <p>Hola,</p>
                
                <div class="success">
                    <strong>✅ ¡Contraseña actualizada exitosamente!</strong>
                </div>
                
                <p>Tu contraseña ha sido cambiada correctamente. Ahora puedes iniciar sesión con tu nueva contraseña.</p>
                
                <p>Si no realizaste este cambio, contacta inmediatamente a nuestro equipo de soporte.</p>
                
                <div class="footer">
                    <p>{MENSAJE_CORREO_AUTOMATICO}</p>
                    <p>{COPYRIGHT_SEVA}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Contraseña actualizada exitosamente - {MARCA_SEVA_EMPRESAS}
        
        Hola,
        
        Tu contraseña ha sido cambiada correctamente. Ahora puedes iniciar sesión con tu nueva contraseña.
        
        Si no realizaste este cambio, contacta inmediatamente a nuestro equipo de soporte.
        
        Saludos,
        {EQUIPO_SEVA}
        """
        
        return self.send_email_with_fallback(to_email, subject, html_content, text_content)

    def send_email_via_brevo(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envía un correo electrónico usando Brevo API (gratuito sin tarjeta)

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            if not self.brevo_api_key:
                logger.warning(MSG_BREVO_API_NO_CONFIGURADA)
                return False

            url = URL_BREVO_API
            headers = {
                HEADER_API_KEY: self.brevo_api_key,
                HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON
            }

            payload = {
                "sender": {
                    "name": self.sender_name,
                    "email": self.sender_email
                },
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_content
            }

            if text_content:
                payload["textContent"] = text_content

            # Enviar usando httpx de forma síncrona
            try:
                response = httpx.post(url, headers=headers, json=payload, timeout=TIMEOUT_API_REQUEST)

                if response.status_code == STATUS_CODE_BREVO_SUCCESS:  # Brevo aceptó el email
                    logger.info(MSG_CORREO_ENVIADO_BREVO.format(email=to_email))
                    return True
                else:
                    logger.error(MSG_ERROR_API_BREVO.format(status=response.status_code, text=response.text))
                    return False
            except httpx.TimeoutException:
                logger.error(MSG_TIMEOUT_BREVO.format(email=to_email))
                return False
            except Exception as e:
                logger.error(MSG_ERROR_CONEXION_BREVO.format(email=to_email, error=str(e)))
                return False

        except Exception as e:
            logger.error(MSG_ERROR_ENVIANDO_BREVO.format(email=to_email, error=str(e)))
            return False

    def send_email_via_mailgun(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envía un correo electrónico usando Mailgun API (compatible con Gmail)

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            if not self.mailgun_api_key or not self.mailgun_domain:
                logger.warning(MSG_MAILGUN_API_NO_CONFIGURADA)
                return False

            url = URL_MAILGUN_API_TEMPLATE.format(domain=self.mailgun_domain)
            auth = ("api", self.mailgun_api_key)

            data = {
                "from": f"{self.sender_name} <{self.sender_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }

            if text_content:
                data["text"] = text_content

            # Enviar usando httpx de forma síncrona
            try:
                response = httpx.post(url, auth=auth, data=data, timeout=TIMEOUT_API_REQUEST)

                if response.status_code == STATUS_CODE_MAILGUN_SUCCESS:
                    logger.info(MSG_CORREO_ENVIADO_MAILGUN.format(email=to_email))
                    return True
                else:
                    logger.error(MSG_ERROR_API_MAILGUN.format(status=response.status_code, text=response.text))
                    return False
            except httpx.TimeoutException:
                logger.error(MSG_TIMEOUT_MAILGUN.format(email=to_email))
                return False
            except Exception as e:
                logger.error(MSG_ERROR_CONEXION_MAILGUN.format(email=to_email, error=str(e)))
                return False

        except Exception as e:
            logger.error(MSG_ERROR_ENVIANDO_MAILGUN.format(email=to_email, error=str(e)))
            return False

    def send_email_via_resend(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envía un correo electrónico usando Resend API (síncrono, compatible con FastAPI)

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            if not self.resend_api_key:
                logger.warning(MSG_RESEND_API_NO_CONFIGURADA)
                return False

            url = URL_RESEND_API
            headers = {
                HEADER_AUTHORIZATION: f"{BEARER_PREFIX}{self.resend_api_key}",
                HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON
            }

            payload = {
                "from": f"{self.sender_name} <{self.sender_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }

            if text_content:
                payload["text"] = text_content

            # Enviar usando httpx de forma síncrona (compatible con FastAPI)
            try:
                response = httpx.post(url, headers=headers, json=payload, timeout=TIMEOUT_API_REQUEST)

                if response.status_code == STATUS_CODE_RESEND_SUCCESS:
                    logger.info(MSG_CORREO_ENVIADO_RESEND.format(email=to_email))
                    return True
                else:
                    logger.error(MSG_ERROR_API_RESEND.format(status=response.status_code, text=response.text))
                    return False
            except httpx.TimeoutException:
                logger.error(MSG_TIMEOUT_RESEND.format(email=to_email))
                return False
            except Exception as e:
                logger.error(MSG_ERROR_CONEXION_RESEND.format(email=to_email, error=str(e)))
                return False

        except Exception as e:
            logger.error(MSG_ERROR_ENVIANDO_RESEND.format(email=to_email, error=str(e)))
            return False

    def send_email_via_api(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envía un correo electrónico usando SendGrid API (síncrono, compatible con FastAPI)

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            if not self.sendgrid_api_key:
                logger.warning(MSG_SENDGRID_API_NO_CONFIGURADA)
                return False

            url = URL_SENDGRID_API
            headers = {
                HEADER_AUTHORIZATION: f"{BEARER_PREFIX}{self.sendgrid_api_key}",
                HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON
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
                    "type": MIME_TYPE_PLAIN,
                    "value": text_content
                })
            content.append({
                "type": MIME_TYPE_HTML,
                "value": html_content
            })

            payload = {
                "personalizations": personalizations,
                "from": from_email,
                "content": content
            }

            # Enviar usando httpx de forma síncrona (compatible con FastAPI)
            try:
                response = httpx.post(url, headers=headers, json=payload, timeout=TIMEOUT_API_REQUEST)

                if response.status_code == STATUS_CODE_SENDGRID_SUCCESS:  # SendGrid aceptó el email
                    logger.info(MSG_CORREO_ENVIADO_SENDGRID.format(email=to_email))
                    return True
                else:
                    logger.error(MSG_ERROR_API_SENDGRID.format(status=response.status_code, text=response.text))
                    return False
            except httpx.TimeoutException:
                logger.error(MSG_TIMEOUT_SENDGRID.format(email=to_email))
                return False
            except Exception as e:
                logger.error(MSG_ERROR_CONEXION_SENDGRID.format(email=to_email, error=str(e)))
                return False

        except Exception as e:
            logger.error(MSG_ERROR_ENVIANDO_SENDGRID.format(email=to_email, error=str(e)))
            return False

    def _try_send_via_brevo(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Intenta enviar correo vía Brevo"""
        if not self.brevo_api_key:
            return False
        logger.info(MSG_INTENTANDO_BREVO)
        return self.send_email_via_brevo(to_email, subject, html_content, text_content)

    def _try_send_via_sendgrid(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Intenta enviar correo vía SendGrid"""
        if not self.sendgrid_api_key:
            return False
        logger.info(MSG_BREVO_NO_DISPONIBLE)
        return self.send_email_via_api(to_email, subject, html_content, text_content)

    def _try_send_via_mailgun(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Intenta enviar correo vía Mailgun"""
        if not self.mailgun_api_key or not self.mailgun_domain:
            return False
        logger.info(MSG_SENDGRID_NO_DISPONIBLE)
        return self.send_email_via_mailgun(to_email, subject, html_content, text_content)

    def _try_send_via_resend(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Intenta enviar correo vía Resend"""
        if not self.resend_api_key:
            return False
        logger.info(MSG_RESEND_NO_DISPONIBLE)
        return self.send_email_via_resend(to_email, subject, html_content, text_content)

    def _try_send_via_smtp(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Intenta enviar correo vía SMTP Gmail como último respaldo"""
        if not self.sender_email or not self.sender_password:
            return False
        logger.warning(MSG_APIS_FALLARON)
        return self.send_email(to_email, subject, html_content, text_content)

    def send_email_with_fallback(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envía email: Brevo → SendGrid → Mailgun → Resend → Gmail TLS/SSL (último respaldo)

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        # Intentar cada servicio en orden de prioridad
        services = [
            self._try_send_via_brevo,
            self._try_send_via_sendgrid,
            self._try_send_via_mailgun,
            self._try_send_via_resend,
            self._try_send_via_smtp
        ]
        
        for service_func in services:
            if service_func(to_email, subject, html_content, text_content):
                return True
        
        # Si todo falla
        logger.error(MSG_NO_SE_PUDO_ENVIAR)
        return False

# Instancia global del servicio
gmail_smtp_service = GmailSMTPService()
