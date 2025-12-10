# app/services/provider_verification_email_service.py
"""
Servicio para envío de emails de verificación de proveedores (aprobado/rechazado).
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
    
    IMPORTANTE: NO usa RAILWAY_PUBLIC_DOMAIN porque puede ser del backend.
    Siempre prioriza FRONTEND_URL si está configurada.
    
    Returns:
        str: URL del frontend (local o producción)
    """
    # SIEMPRE priorizar FRONTEND_URL si está configurada
    frontend_url_env = os.getenv("FRONTEND_URL")
    if frontend_url_env:
        logger.info(f"🌐 Usando FRONTEND_URL de variable de entorno: {frontend_url_env}")
        return frontend_url_env
    
    # Detectar si estamos en producción (Railway, etc.)
    is_production = (
        os.getenv("RAILWAY_ENVIRONMENT") is not None or
        os.getenv("VERCEL") is not None or
        os.getenv("RENDER") is not None or
        os.getenv("ENVIRONMENT") == "production" or
        os.getenv("NODE_ENV") == "production"
    )
    
    if is_production:
        # En producción, usar un valor por defecto
        # NO usar RAILWAY_PUBLIC_DOMAIN porque puede ser del backend
        default_prod_url = "https://seva-empresas.railway.app"
        logger.warning(f"⚠️ FRONTEND_URL no configurada. Usando URL por defecto: {default_prod_url}")
        logger.warning(f"⚠️ IMPORTANTE: Configura FRONTEND_URL en las variables de entorno para usar la URL correcta del frontend")
        return default_prod_url
    else:
        # En local, usar localhost
        local_url = "http://localhost:5173"
        logger.info(f"🌐 Entorno local detectado. Usando: {local_url}")
        return local_url


class ProviderVerificationEmailService:
    """Servicio para envío de emails de verificación de proveedores"""
    
    @staticmethod
    def generar_contenido_email(
        nombre_contacto: str,
        nombre_empresa: str,
        estado_verificacion: str,  # 'aprobada' o 'rechazada'
        mensaje_detalle: str,
        comentario: Optional[str] = None,
        url_login: str = LOGIN_URL
    ) -> Tuple[str, str]:
        """
        Genera el contenido HTML y texto del email de verificación de proveedores.
        
        Args:
            nombre_contacto: Nombre del contacto/usuario
            nombre_empresa: Nombre de la empresa
            estado_verificacion: 'aprobada' o 'rechazada'
            mensaje_detalle: Mensaje detallado según el estado
            comentario: Comentario del administrador (opcional, principalmente para rechazos)
            url_login: URL de la página de login
            
        Returns:
            tuple: (html_content, text_content)
        """
        # Determinar color y emoji según el estado
        if estado_verificacion == "aprobada":
            color_principal = "#10b981"  # Verde
            emoji_estado = "✅"
            bg_color = "#d1fae5"
            border_color = "#10b981"
            titulo_estado = "Solicitud Aprobada"
        else:  # rechazada
            color_principal = "#ef4444"  # Rojo
            emoji_estado = "❌"
            bg_color = "#fee2e2"
            border_color = "#ef4444"
            titulo_estado = "Solicitud Rechazada"
        
        # Obtener la URL del frontend según el entorno
        frontend_url = get_frontend_url()
        url_login_actual = f"{frontend_url}/#/login"
        
        # Si se proporciona una URL de login personalizada, usarla
        if url_login != LOGIN_URL:
            url_login_actual = url_login
        
        # Construir mensaje con comentario si existe
        mensaje_completo = mensaje_detalle
        if comentario and comentario.strip():
            mensaje_completo += f"\n\n<strong>Comentario del administrador:</strong><br>{comentario}"
        
        # Log para debugging
        logger.info(f"📧 Generando email de verificación de proveedor - Frontend URL: {frontend_url}")
        logger.info(f"📧 URL de login: {url_login_actual}")
        logger.info(f"📧 Estado: {estado_verificacion}, Empresa: {nombre_empresa}")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Estado de tu verificación de proveedor - SeVa Empresas</title>
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
                .empresa-nombre {{
                    font-size: 16px;
                    color: #4b5563;
                    margin-top: 10px;
                    font-weight: 500;
                }}
                .mensaje-detalle {{
                    background-color: #f8fafc;
                    border-left: 4px solid {color_principal};
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .comentario-admin {{
                    background-color: #fff7ed;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                    font-style: italic;
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
                    <h1>Estado de tu verificación de proveedor</h1>
                </div>
                
                <p>Hola {nombre_contacto},</p>
                
                <div class="estado-box">
                    <div style="font-size: 32px; margin-bottom: 10px;">{emoji_estado}</div>
                    <div class="estado-texto">
                        {titulo_estado}
                    </div>
                    <div class="empresa-nombre">
                        Empresa: {nombre_empresa}
                    </div>
                </div>
                
                <div class="mensaje-detalle">
                    {mensaje_completo}
                </div>
                
                {f'<div class="comentario-admin"><strong>📝 Comentario del administrador:</strong><br>{comentario}</div>' if comentario and comentario.strip() else ''}
                
                <div class="url-info">
                    <strong>🌐 Accede a la plataforma:</strong>
                    <a href="{frontend_url}">{frontend_url}</a>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_login_actual}" class="boton-login">Acceder a la plataforma</a>
                </div>
                
                <p style="text-align: center; color: #6b7280; font-size: 14px;">
                    O copiá y pegá este enlace en tu navegador:<br>
                    <a href="{url_login_actual}" style="color: #2563eb; word-break: break-all;">{url_login_actual}</a>
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
        
        # Construir mensaje de texto plano
        mensaje_texto = mensaje_detalle
        if comentario and comentario.strip():
            mensaje_texto += f"\n\nComentario del administrador:\n{comentario}"
        
        text_content = f"""
        Estado de tu verificación de proveedor - SeVa Empresas
        
        Hola {nombre_contacto},
        
        Tu solicitud de verificación de proveedor para la empresa "{nombre_empresa}" ha sido {estado_verificacion}.
        
        {mensaje_texto}
        
        🌐 Accede a la plataforma: {frontend_url_text}
        Acceso: {url_login_text}
        
        Saludos,
        Equipo de SeVa Empresas
        """
        
        return html_content, text_content
    
    @staticmethod
    def enviar_email_aprobacion(
        to_email: str,
        nombre_contacto: str,
        nombre_empresa: str,
        comentario: Optional[str] = None,
        url_login: str = LOGIN_URL
    ) -> bool:
        """
        Envía email de aprobación de verificación de proveedor.
        
        Args:
            to_email: Email del destinatario
            nombre_contacto: Nombre del contacto/usuario
            nombre_empresa: Nombre de la empresa
            comentario: Comentario del administrador (opcional)
            url_login: URL de la página de login
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            estado_verificacion = "aprobada"
            mensaje_detalle = (
                "¡Felicitaciones! Tu solicitud de verificación de proveedor ha sido aprobada. "
                "Tu empresa ahora está verificada y podés comenzar a ofrecer tus servicios en la plataforma. "
                "Ya podés ingresar y gestionar tus servicios normalmente."
            )
            
            html_content, text_content = ProviderVerificationEmailService.generar_contenido_email(
                nombre_contacto=nombre_contacto,
                nombre_empresa=nombre_empresa,
                estado_verificacion=estado_verificacion,
                mensaje_detalle=mensaje_detalle,
                comentario=comentario,
                url_login=url_login
            )
            
            subject = "✅ Tu solicitud de verificación de proveedor ha sido aprobada - SeVa Empresas"
            
            # Enviar email usando gmail_smtp_service
            success = gmail_smtp_service.send_email_with_fallback(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"✅ Email de aprobación de verificación de proveedor enviado a {to_email}")
            else:
                logger.error(f"❌ Error enviando email de aprobación de verificación de proveedor a {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en enviar_email_aprobacion: {str(e)}")
            return False
    
    @staticmethod
    def enviar_email_rechazo(
        to_email: str,
        nombre_contacto: str,
        nombre_empresa: str,
        comentario: str,
        url_login: str = LOGIN_URL
    ) -> bool:
        """
        Envía email de rechazo de verificación de proveedor.
        
        Args:
            to_email: Email del destinatario
            nombre_contacto: Nombre del contacto/usuario
            nombre_empresa: Nombre de la empresa
            comentario: Comentario del administrador explicando el rechazo (obligatorio)
            url_login: URL de la página de login
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            estado_verificacion = "rechazada"
            mensaje_detalle = (
                "Lamentamos informarte que tu solicitud de verificación de proveedor no pudo ser aprobada. "
                "Por favor revisá los documentos y datos enviados, corregí los problemas indicados y volvé a enviar tu solicitud."
            )
            
            html_content, text_content = ProviderVerificationEmailService.generar_contenido_email(
                nombre_contacto=nombre_contacto,
                nombre_empresa=nombre_empresa,
                estado_verificacion=estado_verificacion,
                mensaje_detalle=mensaje_detalle,
                comentario=comentario,
                url_login=url_login
            )
            
            subject = "❌ Tu solicitud de verificación de proveedor ha sido rechazada - SeVa Empresas"
            
            # Enviar email usando gmail_smtp_service
            success = gmail_smtp_service.send_email_with_fallback(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"✅ Email de rechazo de verificación de proveedor enviado a {to_email}")
            else:
                logger.error(f"❌ Error enviando email de rechazo de verificación de proveedor a {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en enviar_email_rechazo: {str(e)}")
            return False

