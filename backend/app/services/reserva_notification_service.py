"""
Servicio de notificaciones por correo para eventos de reservas
Envía correos solo en eventos clave sin spam
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os
from app.services.gmail_smtp_service import gmail_smtp_service

logger = logging.getLogger(__name__)

class ReservaNotificationService:
    """Servicio para envío de notificaciones de reservas por correo"""
    
    def __init__(self):
        self.sender_name = "SEVA Reservas"
        # Email del administrador para CC en completadas
        self.admin_email = os.getenv("ADMIN_EMAIL", "admin@sevaempresas.com")
        # URL base del frontend
        self.frontend_url = os.getenv("FRONTEND_URL", "https://frontend-production-ee3b.up.railway.app")
        
        # Cache de notificaciones enviadas para evitar duplicados
        # Formato: {reserva_id}:{evento} -> timestamp
        self._sent_notifications = {}
    
    def _replace_placeholders(self, template: str, data: Dict[str, Any]) -> str:
        """
        Reemplaza placeholders en el template con los datos reales
        
        Args:
            template: String con placeholders {{variable}}
            data: Diccionario con los valores
            
        Returns:
            String con placeholders reemplazados
        """
        result = template
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value) if value else "")
        return result
    
    def _check_and_mark_sent(self, reserva_id: int, evento: str) -> bool:
        """
        Verifica si ya se envió una notificación para este evento
        Si no se envió, la marca como enviada
        
        Args:
            reserva_id: ID de la reserva
            evento: Nombre del evento (crear, confirmar, completar, cancelar, cancelar_auto)
            
        Returns:
            True si ya se envió, False si es la primera vez
        """
        key = f"{reserva_id}:{evento}"
        
        if key in self._sent_notifications:
            logger.warning(f"⚠️ Notificación ya enviada: {key}")
            return True
        
        # Marcar como enviada
        self._sent_notifications[key] = datetime.now().isoformat()
        return False
    
    def _generate_links(self, reserva_id: int) -> Dict[str, str]:
        """
        Genera los enlaces para los correos
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Diccionario con los enlaces
        """
        return {
            "link_detalle": f"{self.frontend_url}/#/dashboard/reservations?id={reserva_id}",
            "link_mis_reservas": f"{self.frontend_url}/#/dashboard/reservations",
            "link_panel_proveedor": f"{self.frontend_url}/#/dashboard/reservations"
        }
    
    def _send_notification(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        cc_email: Optional[str] = None
    ) -> bool:
        """
        Envía un correo de notificación usando el servicio SMTP
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML
            text_content: Contenido de texto plano
            cc_email: Email para copia (opcional)
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Por ahora, enviar solo al destinatario principal
            # Implementar CC si el servicio SMTP lo soporta
            result = gmail_smtp_service.send_email_with_fallback(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Si hay CC y el envío principal fue exitoso, enviar también al CC
            if result and cc_email:
                gmail_smtp_service.send_email_with_fallback(
                    to_email=cc_email,
                    subject=f"[CC] {subject}",
                    html_content=html_content,
                    text_content=text_content
                )
            
            return result
        except Exception as e:
            logger.error(f"❌ Error enviando notificación a {to_email}: {e}")
            return False
    
    # ========================================
    # 1) CREAR RESERVA (Pendiente)
    # ========================================
    
    def notify_reserva_creada(
        self,
        reserva_id: int,
        servicio_nombre: str,
        fecha: str,
        hora: str,
        cliente_nombre: str,
        cliente_email: str,
        proveedor_nombre: str,
        proveedor_email: str
    ) -> bool:
        """
        Notifica creación de reserva (estado: Pendiente)
        Destinatarios: Cliente y Proveedor
        """
        # Verificar si ya se envió
        if self._check_and_mark_sent(reserva_id, "crear"):
            return False
        
        logger.info(f"📧 Enviando notificación de reserva creada #{reserva_id}")
        
        # Generar enlaces
        links = self._generate_links(reserva_id)
        
        # Datos para placeholders
        data = {
            "reserva_id": reserva_id,
            "servicio_nombre": servicio_nombre,
            "fecha": fecha,
            "hora": hora,
            "cliente_nombre": cliente_nombre,
            "proveedor_nombre": proveedor_nombre,
            **links
        }
        
        # Plantilla HTML
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #2563eb; margin-bottom: 10px; }
                .info-box { background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0; }
                .cta-button { display: inline-block; padding: 12px 24px; background-color: #2563eb; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #6b7280; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">SEVA EMPRESAS</div>
                    <h2>Nueva reserva #{{reserva_id}}</h2>
                </div>
                
                <p>Se creó la reserva de <strong>{{servicio_nombre}}</strong> para el <strong>{{fecha}} {{hora}}</strong>.</p>
                
                <div class="info-box">
                    <p><strong>Cliente:</strong> {{cliente_nombre}}</p>
                    <p><strong>Proveedor:</strong> {{proveedor_nombre}}</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{{link_detalle}}" class="cta-button">Ver Detalles</a>
                </div>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>© 2025 Seva Empresas. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plantilla de texto plano
        text_template = """
        Nueva reserva #{{reserva_id}} - SEVA EMPRESAS
        
        Se creó la reserva de {{servicio_nombre}} para el {{fecha}} {{hora}}.
        
        Cliente: {{cliente_nombre}}
        Proveedor: {{proveedor_nombre}}
        
        Ver detalles: {{link_detalle}}
        
        Saludos,
        Equipo SEVA EMPRESAS
        """
        
        # Reemplazar placeholders
        html_content = self._replace_placeholders(html_template, data)
        text_content = self._replace_placeholders(text_template, data)
        subject = f"Nueva reserva #{reserva_id}"
        
        # Enviar a cliente y proveedor
        cliente_result = self._send_notification(cliente_email, subject, html_content, text_content)
        proveedor_result = self._send_notification(proveedor_email, subject, html_content, text_content)
        
        return cliente_result and proveedor_result
    
    # ========================================
    # 2) CONFIRMAR RESERVA (Confirmada)
    # ========================================
    
    def notify_reserva_confirmada(
        self,
        reserva_id: int,
        servicio_nombre: str,
        fecha: str,
        hora: str,
        cliente_nombre: str,
        cliente_email: str,
        proveedor_nombre: str,
        proveedor_email: str
    ) -> bool:
        """
        Notifica confirmación de reserva (estado: Confirmada)
        Destinatarios: Cliente y Proveedor
        """
        # Verificar si ya se envió
        if self._check_and_mark_sent(reserva_id, "confirmar"):
            return False
        
        logger.info(f"📧 Enviando notificación de reserva confirmada #{reserva_id}")
        
        # Generar enlaces
        links = self._generate_links(reserva_id)
        
        # Datos para placeholders
        data = {
            "reserva_id": reserva_id,
            "servicio_nombre": servicio_nombre,
            "fecha": fecha,
            "hora": hora,
            "cliente_nombre": cliente_nombre,
            "proveedor_nombre": proveedor_nombre,
            **links
        }
        
        # Plantilla HTML
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #10b981; margin-bottom: 10px; }
                .success-box { background-color: #d1fae5; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; }
                .cta-button { display: inline-block; padding: 12px 24px; background-color: #10b981; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #6b7280; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">✅ SEVA EMPRESAS</div>
                    <h2>Reserva confirmada #{{reserva_id}}</h2>
                </div>
                
                <div class="success-box">
                    <p>La reserva de <strong>{{servicio_nombre}}</strong> quedó confirmada para <strong>{{fecha}} {{hora}}</strong>.</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{{link_detalle}}" class="cta-button">Ver Detalles</a>
                </div>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>© 2025 Seva Empresas. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plantilla de texto plano
        text_template = """
        Reserva confirmada #{{reserva_id}} - SEVA EMPRESAS
        
        La reserva de {{servicio_nombre}} quedó confirmada para {{fecha}} {{hora}}.
        
        Ver detalles: {{link_detalle}}
        
        Saludos,
        Equipo SEVA EMPRESAS
        """
        
        # Reemplazar placeholders
        html_content = self._replace_placeholders(html_template, data)
        text_content = self._replace_placeholders(text_template, data)
        subject = f"Reserva confirmada #{reserva_id}"
        
        # Enviar a cliente y proveedor
        cliente_result = self._send_notification(cliente_email, subject, html_content, text_content)
        proveedor_result = self._send_notification(proveedor_email, subject, html_content, text_content)
        
        return cliente_result and proveedor_result
    
    # ========================================
    # 3) COMPLETAR RESERVA (Completada)
    # ========================================
    
    def notify_reserva_completada(
        self,
        reserva_id: int,
        servicio_nombre: str,
        fecha: str,
        hora: str,
        cliente_nombre: str,
        cliente_email: str,
        proveedor_nombre: str,
        proveedor_email: str
    ) -> bool:
        """
        Notifica finalización de reserva (estado: Completada)
        Destinatarios: Cliente, Proveedor, y Admin (CC)
        """
        # Verificar si ya se envió
        if self._check_and_mark_sent(reserva_id, "completar"):
            return False
        
        logger.info(f"📧 Enviando notificación de reserva completada #{reserva_id}")
        
        # Generar enlaces
        links = self._generate_links(reserva_id)
        
        # Datos para placeholders
        data = {
            "reserva_id": reserva_id,
            "servicio_nombre": servicio_nombre,
            "fecha": fecha,
            "hora": hora,
            "cliente_nombre": cliente_nombre,
            "proveedor_nombre": proveedor_nombre,
            **links
        }
        
        # Plantilla HTML para CLIENTE
        html_cliente = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #8b5cf6; margin-bottom: 10px; }
                .info-box { background-color: #f3e8ff; border-left: 4px solid #8b5cf6; padding: 15px; margin: 20px 0; }
                .cta-button { display: inline-block; padding: 12px 24px; background-color: #8b5cf6; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #6b7280; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">⭐ SEVA EMPRESAS</div>
                    <h2>Reserva completada #{{reserva_id}}</h2>
                </div>
                
                <div class="info-box">
                    <p>Tu servicio <strong>{{servicio_nombre}}</strong> finalizó.</p>
                    <p><strong>¡Calificá ahora tu experiencia!</strong></p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{{link_mis_reservas}}" class="cta-button">Calificar Servicio</a>
                </div>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>© 2025 Seva Empresas. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plantilla HTML para PROVEEDOR
        html_proveedor = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #8b5cf6; margin-bottom: 10px; }
                .info-box { background-color: #f3e8ff; border-left: 4px solid #8b5cf6; padding: 15px; margin: 20px 0; }
                .cta-button { display: inline-block; padding: 12px 24px; background-color: #8b5cf6; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #6b7280; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">⭐ SEVA EMPRESAS</div>
                    <h2>Reserva completada #{{reserva_id}}</h2>
                </div>
                
                <div class="info-box">
                    <p>El servicio <strong>{{servicio_nombre}}</strong> finalizó.</p>
                    <p><strong>¡Calificá al cliente ahora!</strong></p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{{link_panel_proveedor}}" class="cta-button">Calificar Cliente</a>
                </div>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>© 2025 Seva Empresas. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plantilla HTML para ADMIN (auditoría)
        html_admin = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #64748b; margin-bottom: 10px; }
                .audit-box { background-color: #f1f5f9; border-left: 4px solid #64748b; padding: 15px; margin: 20px 0; font-size: 14px; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #6b7280; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">📋 AUDITORÍA - SEVA</div>
                    <h3>Reserva completada #{{reserva_id}}</h3>
                </div>
                
                <div class="audit-box">
                    <p><strong>Proveedor:</strong> {{proveedor_nombre}}</p>
                    <p><strong>Cliente:</strong> {{cliente_nombre}}</p>
                    <p><strong>Servicio:</strong> {{servicio_nombre}}</p>
                    <p><strong>Fecha:</strong> {{fecha}} {{hora}}</p>
                </div>
                
                <div class="footer">
                    <p>Copia de auditoría - Reserva completada</p>
                    <p>© 2025 Seva Empresas</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Texto plano cliente
        text_cliente = """
        Reserva completada #{{reserva_id}} - SEVA EMPRESAS
        
        Tu servicio {{servicio_nombre}} finalizó. ¡Calificá ahora!
        
        Calificar servicio: {{link_mis_reservas}}
        
        Saludos,
        Equipo SEVA EMPRESAS
        """
        
        # Texto plano proveedor
        text_proveedor = """
        Reserva completada #{{reserva_id}} - SEVA EMPRESAS
        
        El servicio {{servicio_nombre}} finalizó. ¡Calificá al cliente!
        
        Calificar cliente: {{link_panel_proveedor}}
        
        Saludos,
        Equipo SEVA EMPRESAS
        """
        
        # Reemplazar placeholders
        html_cliente_final = self._replace_placeholders(html_cliente, data)
        html_proveedor_final = self._replace_placeholders(html_proveedor, data)
        html_admin_final = self._replace_placeholders(html_admin, data)
        text_cliente_final = self._replace_placeholders(text_cliente, data)
        text_proveedor_final = self._replace_placeholders(text_proveedor, data)
        subject = f"Reserva completada #{reserva_id}"
        
        # Enviar correos
        cliente_result = self._send_notification(cliente_email, subject, html_cliente_final, text_cliente_final)
        proveedor_result = self._send_notification(proveedor_email, subject, html_proveedor_final, text_proveedor_final)
        
        # Enviar copia a admin (auditoría, no afecta el resultado)
        self._send_notification(self.admin_email, f"[AUDITORÍA] {subject}", html_admin_final, f"Auditoría - Proveedor: {proveedor_nombre} | Cliente: {cliente_nombre} | Fecha: {fecha} {hora}")
        
        return cliente_result and proveedor_result
    
    # ========================================
    # 4) CANCELACIÓN MANUAL (Cancelada)
    # ========================================
    
    def notify_reserva_cancelada(
        self,
        reserva_id: int,
        servicio_nombre: str,
        fecha: str,
        hora: str,
        cliente_nombre: str,
        cliente_email: str,
        proveedor_nombre: str,
        proveedor_email: str,
        motivo: str
    ) -> bool:
        """
        Notifica cancelación manual de reserva (estado: Cancelada)
        Destinatarios: Cliente y Proveedor
        """
        # Verificar si ya se envió
        if self._check_and_mark_sent(reserva_id, "cancelar"):
            return False
        
        logger.info(f"📧 Enviando notificación de reserva cancelada #{reserva_id}")
        
        # Generar enlaces
        links = self._generate_links(reserva_id)
        
        # Datos para placeholders
        data = {
            "reserva_id": reserva_id,
            "servicio_nombre": servicio_nombre,
            "fecha": fecha,
            "hora": hora,
            "cliente_nombre": cliente_nombre,
            "proveedor_nombre": proveedor_nombre,
            "motivo": motivo,
            **links
        }
        
        # Plantilla HTML
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #ef4444; margin-bottom: 10px; }
                .warning-box { background-color: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; }
                .cta-button { display: inline-block; padding: 12px 24px; background-color: #64748b; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #6b7280; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">❌ SEVA EMPRESAS</div>
                    <h2>Reserva cancelada #{{reserva_id}}</h2>
                </div>
                
                <div class="warning-box">
                    <p>La reserva de <strong>{{servicio_nombre}}</strong> para el <strong>{{fecha}} {{hora}}</strong> fue cancelada.</p>
                    <p><strong>Motivo:</strong> {{motivo}}</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{{link_detalle}}" class="cta-button">Ver Detalles</a>
                </div>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>© 2025 Seva Empresas. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plantilla de texto plano
        text_template = """
        Reserva cancelada #{{reserva_id}} - SEVA EMPRESAS
        
        La reserva de {{servicio_nombre}} para el {{fecha}} {{hora}} fue cancelada.
        
        Motivo: {{motivo}}
        
        Ver detalles: {{link_detalle}}
        
        Saludos,
        Equipo SEVA EMPRESAS
        """
        
        # Reemplazar placeholders
        html_content = self._replace_placeholders(html_template, data)
        text_content = self._replace_placeholders(text_template, data)
        subject = f"Reserva cancelada #{reserva_id}"
        
        # Enviar a cliente y proveedor
        cliente_result = self._send_notification(cliente_email, subject, html_content, text_content)
        proveedor_result = self._send_notification(proveedor_email, subject, html_content, text_content)
        
        return cliente_result and proveedor_result
    
    # ========================================
    # 5) CANCELACIÓN AUTOMÁTICA
    # ========================================
    
    def notify_reserva_cancelada_automatica(
        self,
        reserva_id: int,
        servicio_nombre: str,
        fecha: str,
        hora: str,
        cliente_nombre: str,
        cliente_email: str,
        proveedor_nombre: str,
        proveedor_email: str
    ) -> bool:
        """
        Notifica cancelación automática por falta de confirmación
        Destinatarios: Cliente y Proveedor
        """
        # Verificar si ya se envió
        if self._check_and_mark_sent(reserva_id, "cancelar_auto"):
            return False
        
        logger.info(f"📧 Enviando notificación de cancelación automática #{reserva_id}")
        
        # Generar enlaces
        links = self._generate_links(reserva_id)
        
        # Datos para placeholders
        data = {
            "reserva_id": reserva_id,
            "servicio_nombre": servicio_nombre,
            "fecha": fecha,
            "hora": hora,
            "cliente_nombre": cliente_nombre,
            "proveedor_nombre": proveedor_nombre,
            **links
        }
        
        # Plantilla HTML
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #f59e0b; margin-bottom: 10px; }
                .warning-box { background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }
                .cta-button { display: inline-block; padding: 12px 24px; background-color: #64748b; color: #ffffff; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #6b7280; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">⚠️ SEVA EMPRESAS</div>
                    <h2>Reserva cancelada automáticamente #{{reserva_id}}</h2>
                </div>
                
                <div class="warning-box">
                    <p>Se canceló la reserva de <strong>{{servicio_nombre}}</strong> por falta de confirmación dentro del plazo.</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{{link_detalle}}" class="cta-button">Ver Detalles</a>
                </div>
                
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                    <p>© 2025 Seva Empresas. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plantilla de texto plano
        text_template = """
        Reserva cancelada automáticamente #{{reserva_id}} - SEVA EMPRESAS
        
        Se canceló la reserva de {{servicio_nombre}} por falta de confirmación dentro del plazo.
        
        Ver detalles: {{link_detalle}}
        
        Saludos,
        Equipo SEVA EMPRESAS
        """
        
        # Reemplazar placeholders
        html_content = self._replace_placeholders(html_template, data)
        text_content = self._replace_placeholders(text_template, data)
        subject = f"Reserva cancelada automáticamente #{reserva_id}"
        
        # Enviar a cliente y proveedor
        cliente_result = self._send_notification(cliente_email, subject, html_content, text_content)
        proveedor_result = self._send_notification(proveedor_email, subject, html_content, text_content)
        
        return cliente_result and proveedor_result

# Instancia global del servicio
reserva_notification_service = ReservaNotificationService()

