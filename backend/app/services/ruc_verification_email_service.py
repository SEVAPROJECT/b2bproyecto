# app/services/ruc_verification_email_service.py
"""
Servicio para envío de emails de verificación de RUC (aprobado/rechazado).
"""

import logging
from typing import Optional, Tuple
import os

from app.services.gmail_smtp_service import gmail_smtp_service

logger = logging.getLogger(__name__)

# URL del frontend (puede configurarse por variable de entorno)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
LOGIN_URL = f"{FRONTEND_URL}/#/login"

def get_frontend_url() -> str:
    """
    Detecta automáticamente la URL del frontend según el entorno.
    
    Returns:
        str: URL del frontend (local o producción)
    """
    # Si hay variable de entorno, usarla
    if os.getenv("FRONTEND_URL"):
        return os.getenv("FRONTEND_URL")
    
    # Detectar si estamos en producción (Railway, etc.)
    is_production = (
        os.getenv("RAILWAY_ENVIRONMENT") is not None or
        os.getenv("RAILWAY_PUBLIC_DOMAIN") is not None or
        os.getenv("VERCEL") is not None or
        os.getenv("RENDER") is not None or
        os.getenv("ENVIRONMENT") == "production" or
        os.getenv("NODE_ENV") == "production"
    )
    
    if is_production:
        # En producción, intentar obtener la URL de Railway o usar una por defecto
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if railway_domain:
            # Railway proporciona el dominio público
            return f"https://{railway_domain}"
        else:
            # Si no hay dominio específico, usar la variable de entorno o un valor por defecto
            return os.getenv("FRONTEND_URL", "https://seva-empresas.railway.app")
    else:
        # En local, usar localhost
        return "http://localhost:5173"


class RUCVerificationEmailService:
    """Servicio para envío de emails de verificación de RUC"""
    
    @staticmethod
    def generar_contenido_email(
        nombre_contacto: str,
        estado_registro: str,  # 'aprobado' o 'rechazado'
        mensaje_detalle: str,
        url_login: str = LOGIN_URL,
        token_correccion: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Genera el contenido HTML y texto del email de verificación de RUC.
        
        Args:
            nombre_contacto: Nombre del contacto/usuario
            estado_registro: 'aprobado' o 'rechazado'
            mensaje_detalle: Mensaje detallado según el estado
            url_login: URL de la página de login
            
        Returns:
            tuple: (html_content, text_content)
        """
        # Determinar color y emoji según el estado
        if estado_registro == "aprobada":
            color_principal = "#10b981"  # Verde
            emoji_estado = "✅"
            bg_color = "#d1fae5"
            border_color = "#10b981"
        else:  # rechazado
            color_principal = "#ef4444"  # Rojo
            emoji_estado = "❌"
            bg_color = "#fee2e2"
            border_color = "#ef4444"
        
        # Obtener la URL del frontend según el entorno
        frontend_url = get_frontend_url()
        url_login_actual = f"{frontend_url}/#/login"
        
        # Si se proporciona una URL de login personalizada, usarla
        if url_login != LOGIN_URL:
            url_login_actual = url_login
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Estado de tu registro en SeVa Empresas</title>
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
                .estado-box {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .estado-texto {{
                    font-size: 18px;
                    font-weight: bold;
                    color: {color_principal};
                    margin: 10px 0;
                }}
                .mensaje-detalle {{
                    background-color: #f8fafc;
                    border-left: 4px solid {color_principal};
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .boton-login {{
                    display: inline-block;
                    background-color: #2563eb;
                    color: #ffffff;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    margin: 20px 0;
                    text-align: center;
                }}
                .boton-login:hover {{
                    background-color: #1d4ed8;
                }}
                .url-info {{
                    background-color: #eff6ff;
                    border: 1px solid #bfdbfe;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .url-info strong {{
                    color: #1e40af;
                    display: block;
                    margin-bottom: 8px;
                    font-size: 14px;
                }}
                .url-info a {{
                    color: #2563eb;
                    word-break: break-all;
                    text-decoration: none;
                    font-size: 14px;
                }}
                .url-info a:hover {{
                    text-decoration: underline;
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
                    <div class="logo">🏢 SeVa Empresas</div>
                    <h1>Estado de tu registro</h1>
                </div>
                
                <p>Hola {nombre_contacto},</p>
                
                <div class="estado-box">
                    <div style="font-size: 32px; margin-bottom: 10px;">{emoji_estado}</div>
                    <div class="estado-texto">
                        Tu registro en SeVa Empresas ha sido {estado_registro}.
                    </div>
                </div>
                
                <div class="mensaje-detalle">
                    {mensaje_detalle}
                </div>
                
                <div class="url-info">
                    <strong>🌐 Accede a la plataforma:</strong>
                    <a href="{frontend_url}">{frontend_url}</a>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    {f'<a href="{frontend_url}/#/register?token={token_correccion}" class="boton-login">Corregir y reenviar RUC</a>' if estado_registro == "rechazada" and token_correccion else f'<a href="{url_login_actual}" class="boton-login">Acceder a la plataforma</a>'}
                </div>
                
                <p style="text-align: center; color: #6b7280; font-size: 14px;">
                    {f'O copiá y pegá este enlace en tu navegador:<br><a href="{frontend_url}/#/register?token={token_correccion}" style="color: #2563eb; word-break: break-all;">{frontend_url}/#/register?token={token_correccion}</a>' if estado_registro == "rechazada" and token_correccion else f'O copiá y pegá este enlace en tu navegador:<br><a href="{url_login_actual}" style="color: #2563eb; word-break: break-all;">{url_login_actual}</a>'}
                </p>
                
                <div class="footer">
                    <p>Saludos,</p>
                    <p><strong>Equipo de SeVa Empresas</strong></p>
                    <p style="font-size: 12px; color: #9ca3af; margin-top: 15px;">
                        Este es un correo automático, por favor no respondas.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Obtener la URL del frontend según el entorno para el texto plano
        frontend_url_text = get_frontend_url()
        url_login_text = f"{frontend_url_text}/#/login"
        if url_login != LOGIN_URL:
            url_login_text = url_login
        
        text_content = f"""
        Estado de tu registro en SeVa Empresas
        
        Hola {nombre_contacto},
        
        Tu registro en SeVa Empresas ha sido {estado_registro}.
        
        {mensaje_detalle}
        
        🌐 Accede a la plataforma: {frontend_url_text}
        
        {f'Corregir y reenviar: {frontend_url_text}/#/register?token={token_correccion}' if estado_registro == "rechazada" and token_correccion else f'Acceso: {url_login_text}'}
        
        Saludos,
        Equipo de SeVa Empresas
        """
        
        return html_content, text_content
    
    @staticmethod
    def enviar_email_aprobacion(
        to_email: str,
        nombre_contacto: str,
        url_login: str = LOGIN_URL
    ) -> bool:
        """
        Envía email de aprobación de RUC.
        
        Args:
            to_email: Email del destinatario
            nombre_contacto: Nombre del contacto/usuario
            url_login: URL de la página de login
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            estado_registro = "aprobada"
            mensaje_detalle = (
                "Tu empresa fue verificada y tu cuenta ya está activa. "
                "Ya podés ingresar y utilizar la plataforma normalmente."
            )
            
            html_content, text_content = RUCVerificationEmailService.generar_contenido_email(
                nombre_contacto=nombre_contacto,
                estado_registro=estado_registro,
                mensaje_detalle=mensaje_detalle,
                url_login=url_login
            )
            
            subject = "Estado de tu registro en SeVa Empresas"
            
            # Enviar email usando gmail_smtp_service
            success = gmail_smtp_service.send_email_with_fallback(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"✅ Email de aprobación de RUC enviado a {to_email}")
            else:
                logger.error(f"❌ Error enviando email de aprobación de RUC a {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en enviar_email_aprobacion: {str(e)}")
            return False
    
    @staticmethod
    def enviar_email_rechazo(
        to_email: str,
        nombre_contacto: str,
        token_correccion: str,
        url_login: str = LOGIN_URL
    ) -> bool:
        """
        Envía email de rechazo de RUC.
        
        Args:
            to_email: Email del destinatario
            nombre_contacto: Nombre del contacto/usuario
            url_login: URL de la página de login
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            estado_registro = "rechazada"
            mensaje_detalle = (
                "No pudimos completar la verificación de tu empresa. "
                "Por favor revisá los datos y documentos enviados y volvé a intentarlo."
            )
            
            html_content, text_content = RUCVerificationEmailService.generar_contenido_email(
                nombre_contacto=nombre_contacto,
                estado_registro=estado_registro,
                mensaje_detalle=mensaje_detalle,
                url_login=url_login,
                token_correccion=token_correccion
            )
            
            subject = "Estado de tu registro en SeVa Empresas"
            
            # Enviar email usando gmail_smtp_service
            success = gmail_smtp_service.send_email_with_fallback(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"✅ Email de rechazo de RUC enviado a {to_email}")
            else:
                logger.error(f"❌ Error enviando email de rechazo de RUC a {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en enviar_email_rechazo: {str(e)}")
            return False

