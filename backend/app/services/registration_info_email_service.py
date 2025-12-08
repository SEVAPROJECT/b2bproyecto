"""
Servicio para envío de email informativo después del registro.
Este email explica el proceso de verificación de RUC en lugar de confirmación de cuenta.
"""

import logging
from typing import Tuple
import os
import asyncio

from app.services.gmail_smtp_service import gmail_smtp_service

logger = logging.getLogger(__name__)

# URL del frontend (puede configurarse por variable de entorno)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
COPYRIGHT_SEVA = "© 2025 SeVa Empresas. Todos los derechos reservados."


class RegistrationInfoEmailService:
    """Servicio para envío de email informativo después del registro"""
    
    @staticmethod
    def generar_contenido_email_registro(
        nombre_contacto: str,
        nombre_empresa: str,
        ruc: str = None
    ) -> Tuple[str, str, str]:
        """
        Genera el contenido HTML y texto del email informativo de registro.
        
        Args:
            nombre_contacto: Nombre de la persona que se registró
            nombre_empresa: Nombre de la empresa
            ruc: RUC de la empresa (opcional)
            
        Returns:
            Tuple con (subject, html_content, text_content)
        """
        subject = "Bienvenido a SeVa Empresas - Tu registro está en proceso"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
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
                    font-size: 28px;
                    font-weight: bold;
                    color: #2563eb;
                    margin-bottom: 10px;
                }}
                .tagline {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-bottom: 20px;
                }}
                .info-box {{
                    background-color: #EFF6FF;
                    border: 1px solid #3B82F6;
                    border-radius: 6px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .info-box h3 {{
                    color: #1E40AF;
                    margin-top: 0;
                    margin-bottom: 10px;
                }}
                .info-box p {{
                    color: #1E3A8A;
                    margin: 5px 0;
                }}
                .warning-box {{
                    background-color: #FEF3C7;
                    border: 1px solid #F59E0B;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 20px 0;
                    color: #92400E;
                }}
                .warning-box strong {{
                    display: block;
                    margin-bottom: 8px;
                }}
                .steps {{
                    background-color: #F9FAFB;
                    border-left: 4px solid #2563eb;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .steps ol {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                .steps li {{
                    margin: 8px 0;
                    color: #374151;
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
                    <div class="tagline">Conectando empresas, potenciando el crecimiento en Paraguay.</div>
                </div>
                
                <h2 style="color: #1F2937; margin-top: 0;">Bienvenido a SeVa Empresas</h2>
                
                <p>Hola <strong>{nombre_contacto}</strong>,</p>
                
                <p>¡Gracias por registrarte en SeVa Empresas! Hemos recibido tu solicitud de registro y tu constancia de RUC.</p>
                
                <div class="info-box">
                    <h3>📋 Información de tu registro</h3>
                    <p><strong>Empresa:</strong> {nombre_empresa}</p>
                    {f'<p><strong>RUC:</strong> {ruc}</p>' if ruc else ''}
                </div>
                
                <div class="warning-box">
                    <strong>⚠️ Importante: Proceso de verificación</strong>
                    <p>Tu cuenta está en proceso de verificación. Hemos recibido tu constancia de RUC y será revisada por nuestro equipo en un plazo máximo de <strong>72 horas hábiles</strong>.</p>
                    <p>Te notificaremos por email una vez que tu cuenta sea activada.</p>
                </div>
                
                <div class="steps">
                    <h3 style="color: #1F2937; margin-top: 0;">¿Qué sigue?</h3>
                    <ol>
                        <li>Nuestro equipo revisará tu constancia de RUC</li>
                        <li>Recibirás un email de notificación cuando tu cuenta sea activada</li>
                        <li>Una vez activada, podrás iniciar sesión en la plataforma</li>
                    </ol>
                </div>
                
                <div class="warning-box">
                    <strong>🔒 No podrás iniciar sesión hasta que tu RUC sea verificado</strong>
                    <p>Por favor, espera la notificación por email antes de intentar acceder a la plataforma.</p>
                </div>
                
                <p>Si tienes alguna pregunta o necesitas asistencia, no dudes en contactarnos.</p>
                
                <p>Saludos,</p>
                <p><strong>Equipo de SeVa Empresas</strong></p>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>{COPYRIGHT_SEVA}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Bienvenido a SeVa Empresas
        
        Hola {nombre_contacto},
        
        ¡Gracias por registrarte en SeVa Empresas! Hemos recibido tu solicitud de registro y tu constancia de RUC.
        
        Información de tu registro:
        - Empresa: {nombre_empresa}
        {f'- RUC: {ruc}' if ruc else ''}
        
        IMPORTANTE: Proceso de verificación
        
        Tu cuenta está en proceso de verificación. Hemos recibido tu constancia de RUC y será revisada por nuestro equipo en un plazo máximo de 72 horas hábiles.
        
        Te notificaremos por email una vez que tu cuenta sea activada.
        
        ¿Qué sigue?
        1. Nuestro equipo revisará tu constancia de RUC
        2. Recibirás un email de notificación cuando tu cuenta sea activada
        3. Una vez activada, podrás iniciar sesión en la plataforma
        
        IMPORTANTE: No podrás iniciar sesión hasta que tu RUC sea verificado.
        Por favor, espera la notificación por email antes de intentar acceder a la plataforma.
        
        Si tienes alguna pregunta o necesitas asistencia, no dudes en contactarnos.
        
        Saludos,
        Equipo de SeVa Empresas
        
        Este es un correo automático, por favor no respondas.
        {COPYRIGHT_SEVA}
        """
        
        return subject, html_content, text_content
    
    @staticmethod
    async def enviar_email_registro(
        to_email: str,
        nombre_contacto: str,
        nombre_empresa: str,
        ruc: str = None
    ) -> bool:
        """
        Envía el email informativo de registro.
        
        Args:
            to_email: Email del destinatario
            nombre_contacto: Nombre de la persona que se registró
            nombre_empresa: Nombre de la empresa
            ruc: RUC de la empresa (opcional)
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            subject, html_content, text_content = RegistrationInfoEmailService.generar_contenido_email_registro(
                nombre_contacto=nombre_contacto,
                nombre_empresa=nombre_empresa,
                ruc=ruc
            )
            
            # Enviar email usando gmail_smtp_service
            success = await asyncio.to_thread(
                gmail_smtp_service.send_email_with_fallback,
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"✅ Email informativo de registro enviado a {to_email}")
            else:
                logger.error(f"❌ Error enviando email informativo de registro a {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en enviar_email_registro: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

