"""
Servicio de notificaciones para calificaciones
Envía emails cuando un usuario recibe una calificación
"""

import logging
from typing import Optional
from datetime import datetime
import os
from app.services.gmail_smtp_service import gmail_smtp_service

logger = logging.getLogger(__name__)

class CalificacionNotificationService:
    """Servicio para envío de notificaciones de calificaciones por correo"""
    
    def __init__(self):
        self._sent_notifications = set()  # Cache para evitar duplicados
        self.frontend_url = os.getenv("FRONTEND_URL", "https://frontend-production-ee3b.up.railway.app")
    
    def _get_frontend_links(self) -> dict:
        """Genera links dinámicos al frontend"""
        return {
            "mis_reservas": f"{self.frontend_url}/#/dashboard/reservations",
            "panel_proveedor": f"{self.frontend_url}/#/dashboard/reservations",
            "marketplace": f"{self.frontend_url}/#/dashboard/marketplace"
        }
    
    def _get_nps_label(self, nps: int) -> str:
        """
        Determina la etiqueta NPS basada en el puntaje
        
        Args:
            nps: Puntuación NPS (1-10)
            
        Returns:
            Etiqueta del tipo de NPS (Promotor, Neutral, Detractor)
        """
        if nps >= 9:
            return "😊 Promotor"
        elif nps >= 7:
            return "😐 Neutral"
        else:
            return "😟 Detractor"
    
    def _get_nps_recommendation_text(self, nps: int) -> str:
        """
        Determina el texto de recomendación basado en el puntaje NPS
        
        Args:
            nps: Puntuación NPS (1-10)
            
        Returns:
            Texto de recomendación apropiado
        """
        if nps >= 9:
            return "recomendaría"
        elif nps >= 7:
            return "podría recomendar"
        else:
            return "no recomendaría"
    
    def _send_notification(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        notification_key: str
    ) -> bool:
        """
        Envía una notificación por email con lógica anti-spam
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML
            text_content: Contenido texto plano
            notification_key: Clave única para evitar duplicados
        """
        # Anti-spam: verificar si ya se envió
        if notification_key in self._sent_notifications:
            logger.info(f"⚠️ Notificación ya enviada: {notification_key}")
            return False
        
        try:
            result = gmail_smtp_service.send_email_with_fallback(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if result:
                self._sent_notifications.add(notification_key)
                logger.info(f"✅ Email enviado a {to_email}: {subject}")
                return True
            else:
                logger.error(f"❌ Error enviando email a {to_email}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción enviando email: {e}")
            return False
    
    # ========================================
    # CALIFICACIÓN DE CLIENTE A PROVEEDOR
    # ========================================
    
    def notify_calificacion_a_proveedor(
        self,
        reserva_id: int,
        servicio_nombre: str,
        proveedor_nombre: str,
        proveedor_email: str,
        cliente_nombre: str,
        puntaje: int,
        comentario: str,
        nps: int,
        fecha: str,
        hora: str
    ):
        """
        Notifica al proveedor que recibió una calificación del cliente
        
        Args:
            reserva_id: ID de la reserva
            servicio_nombre: Nombre del servicio
            proveedor_nombre: Nombre del proveedor
            proveedor_email: Email del proveedor
            cliente_nombre: Nombre del cliente
            puntaje: Puntuación (1-5 estrellas)
            comentario: Comentario del cliente
            nps: Puntuación NPS (1-10)
            fecha: Fecha del servicio
            hora: Hora del servicio
        """
        links = self._get_frontend_links()
        notification_key = f"{reserva_id}:calificacion_cliente"
        
        # Generar estrellas visuales
        estrellas = "⭐" * puntaje + "☆" * (5 - puntaje)
        
        # Subject
        subject = f"🌟 Recibiste {puntaje} estrellas - Reserva #{reserva_id}"
        
        # HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .rating-box {{ background: white; border-left: 4px solid #10b981; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stars {{ font-size: 24px; margin: 10px 0; }}
                .nps-badge {{ display: inline-block; background: #3b82f6; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin: 10px 0; }}
                .info-row {{ margin: 12px 0; padding: 10px; background: #f3f4f6; border-radius: 6px; }}
                .cta-button {{ display: inline-block; background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌟 ¡Recibiste una Nueva Calificación!</h1>
                    <p style="margin: 0; font-size: 16px;">Un cliente valoró tu servicio</p>
                </div>
                
                <div class="content">
                    <p><strong>Hola {proveedor_nombre},</strong></p>
                    
                    <p>El cliente <strong>{cliente_nombre}</strong> te ha calificado por el servicio que brindaste. ¡Conocé su opinión!</p>
                    
                    <div class="rating-box">
                        <h3 style="margin-top: 0; color: #10b981;">📊 Detalles de la Calificación</h3>
                        
                        <div class="info-row">
                            <strong>🎯 Servicio:</strong> {servicio_nombre}
                        </div>
                        
                        <div class="info-row">
                            <strong>📅 Fecha del servicio:</strong> {fecha} a las {hora}
                        </div>
                        
                        <div class="info-row">
                            <strong>👤 Cliente:</strong> {cliente_nombre}
                        </div>
                        
                        <div class="stars">
                            <strong>⭐ Puntuación:</strong> {estrellas} ({puntaje}/5)
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <strong>💬 Comentario:</strong>
                            <p style="background: white; padding: 15px; border-radius: 6px; margin: 10px 0; font-style: italic; border-left: 3px solid #10b981;">
                                "{comentario}"
                            </p>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <strong>📈 NPS (Net Promoter Score):</strong>
                            <div class="nps-badge">
                                {nps}/10 - {self._get_nps_label(nps)}
                            </div>
                            <p style="font-size: 13px; color: #6b7280; margin: 5px 0;">
                                {cliente_nombre} {self._get_nps_recommendation_text(nps)} tu servicio a otros.
                            </p>
                        </div>
                        
                        <div class="info-row">
                            <strong>🔖 Reserva ID:</strong> #{reserva_id}
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{links['panel_proveedor']}" class="cta-button">
                            Ver Mis Reservas →
                        </a>
                    </div>
                    
                    <p style="margin-top: 25px; font-size: 14px; color: #6b7280;">
                        💡 <strong>Consejo:</strong> Las calificaciones positivas ayudan a mejorar tu visibilidad en el marketplace. ¡Seguí brindando un excelente servicio!
                    </p>
                </div>
                
                <div class="footer">
                    <p>Este es un email automático de SEVA Empresas</p>
                    <p>Reserva #{reserva_id} | {servicio_nombre}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text content (fallback)
        text_content = f"""
        🌟 NUEVA CALIFICACIÓN RECIBIDA
        
        Hola {proveedor_nombre},
        
        El cliente {cliente_nombre} te ha calificado:
        
        📊 DETALLES:
        - Servicio: {servicio_nombre}
        - Fecha: {fecha} a las {hora}
        - Cliente: {cliente_nombre}
        - Puntuación: {puntaje}/5 estrellas
        - NPS: {nps}/10
        - Comentario: "{comentario}"
        - Reserva ID: #{reserva_id}
        
        Ver más detalles: {links['panel_proveedor']}
        
        ---
        SEVA Empresas - Reserva #{reserva_id}
        """
        
        self._send_notification(
            to_email=proveedor_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            notification_key=notification_key
        )
    
    # ========================================
    # CALIFICACIÓN DE PROVEEDOR A CLIENTE
    # ========================================
    
    def notify_calificacion_a_cliente(
        self,
        reserva_id: int,
        servicio_nombre: str,
        cliente_nombre: str,
        cliente_email: str,
        proveedor_nombre: str,
        proveedor_empresa: str,
        puntaje: int,
        comentario: str,
        fecha: str,
        hora: str
    ):
        """
        Notifica al cliente que recibió una calificación del proveedor
        
        Args:
            reserva_id: ID de la reserva
            servicio_nombre: Nombre del servicio
            cliente_nombre: Nombre del cliente
            cliente_email: Email del cliente
            proveedor_nombre: Nombre del proveedor
            proveedor_empresa: Nombre de la empresa del proveedor
            puntaje: Puntuación (1-5 estrellas)
            comentario: Comentario del proveedor
            fecha: Fecha del servicio
            hora: Hora del servicio
        """
        links = self._get_frontend_links()
        notification_key = f"{reserva_id}:calificacion_proveedor"
        
        # Generar estrellas visuales
        estrellas = "⭐" * puntaje + "☆" * (5 - puntaje)
        
        # Subject
        subject = f"🌟 Recibiste {puntaje} estrellas de {proveedor_empresa} - Reserva #{reserva_id}"
        
        # HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .rating-box {{ background: white; border-left: 4px solid #3b82f6; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stars {{ font-size: 24px; margin: 10px 0; }}
                .info-row {{ margin: 12px 0; padding: 10px; background: #f3f4f6; border-radius: 6px; }}
                .cta-button {{ display: inline-block; background: #3b82f6; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌟 ¡Recibiste una Nueva Calificación!</h1>
                    <p style="margin: 0; font-size: 16px;">Un proveedor valoró tu experiencia</p>
                </div>
                
                <div class="content">
                    <p><strong>Hola {cliente_nombre},</strong></p>
                    
                    <p>El proveedor <strong>{proveedor_empresa}</strong> ({proveedor_nombre}) te ha calificado como cliente. ¡Conocé su opinión!</p>
                    
                    <div class="rating-box">
                        <h3 style="margin-top: 0; color: #3b82f6;">📊 Detalles de la Calificación</h3>
                        
                        <div class="info-row">
                            <strong>🎯 Servicio:</strong> {servicio_nombre}
                        </div>
                        
                        <div class="info-row">
                            <strong>📅 Fecha del servicio:</strong> {fecha} a las {hora}
                        </div>
                        
                        <div class="info-row">
                            <strong>🏢 Proveedor:</strong> {proveedor_empresa} ({proveedor_nombre})
                        </div>
                        
                        <div class="stars">
                            <strong>⭐ Puntuación:</strong> {estrellas} ({puntaje}/5)
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <strong>💬 Comentario:</strong>
                            <p style="background: white; padding: 15px; border-radius: 6px; margin: 10px 0; font-style: italic; border-left: 3px solid #3b82f6;">
                                "{comentario}"
                            </p>
                        </div>
                        
                        <div class="info-row">
                            <strong>🔖 Reserva ID:</strong> #{reserva_id}
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{links['mis_reservas']}" class="cta-button">
                            Ver Mis Reservas →
                        </a>
                    </div>
                    
                    <p style="margin-top: 25px; font-size: 14px; color: #6b7280;">
                        💡 <strong>Consejo:</strong> Las calificaciones positivas reflejan tu excelente comportamiento como cliente. ¡Seguí contratando servicios de calidad!
                    </p>
                </div>
                
                <div class="footer">
                    <p>Este es un email automático de SEVA Empresas</p>
                    <p>Reserva #{reserva_id} | {servicio_nombre}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text content (fallback)
        text_content = f"""
        🌟 NUEVA CALIFICACIÓN RECIBIDA
        
        Hola {cliente_nombre},
        
        El proveedor {proveedor_empresa} ({proveedor_nombre}) te ha calificado:
        
        📊 DETALLES:
        - Servicio: {servicio_nombre}
        - Fecha: {fecha} a las {hora}
        - Proveedor: {proveedor_empresa} ({proveedor_nombre})
        - Puntuación: {puntaje}/5 estrellas
        - Comentario: "{comentario}"
        - Reserva ID: #{reserva_id}
        
        Ver más detalles: {links['mis_reservas']}
        
        ---
        SEVA Empresas - Reserva #{reserva_id}
        """
        
        self._send_notification(
            to_email=cliente_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            notification_key=notification_key
        )


# Instancia global del servicio
calificacion_notification_service = CalificacionNotificationService()

