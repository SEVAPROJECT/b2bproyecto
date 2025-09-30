"""
Servicio para manejar rate limiting de emails
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class EmailRateLimitService:
    """Servicio para manejar rate limiting de emails"""
    
    def __init__(self):
        # Cache en memoria para tracking de rate limits
        self.email_attempts: Dict[str, list] = {}
        self.rate_limit_window = 3600  # 1 hora en segundos
        self.max_attempts = 3  # Máximo 3 intentos por hora por email
        
    def _clean_old_attempts(self, email: str):
        """Limpiar intentos antiguos del cache"""
        now = datetime.now()
        if email in self.email_attempts:
            self.email_attempts[email] = [
                attempt_time for attempt_time in self.email_attempts[email]
                if (now - attempt_time).total_seconds() < self.rate_limit_window
            ]
    
    def can_send_email(self, email: str) -> bool:
        """Verificar si se puede enviar un email"""
        self._clean_old_attempts(email)
        
        if email not in self.email_attempts:
            return True
            
        return len(self.email_attempts[email]) < self.max_attempts
    
    def record_email_attempt(self, email: str):
        """Registrar un intento de envío de email"""
        if email not in self.email_attempts:
            self.email_attempts[email] = []
        
        self.email_attempts[email].append(datetime.now())
        logger.info(f"📧 Registrado intento de email para {email}")
    
    def get_remaining_attempts(self, email: str) -> int:
        """Obtener intentos restantes"""
        self._clean_old_attempts(email)
        
        if email not in self.email_attempts:
            return self.max_attempts
            
        return max(0, self.max_attempts - len(self.email_attempts[email]))
    
    def get_next_attempt_time(self, email: str) -> Optional[datetime]:
        """Obtener el tiempo del próximo intento permitido"""
        self._clean_old_attempts(email)
        
        if email not in self.email_attempts or len(self.email_attempts[email]) < self.max_attempts:
            return None
            
        # El próximo intento será cuando expire el primer intento
        oldest_attempt = min(self.email_attempts[email])
        return oldest_attempt + timedelta(seconds=self.rate_limit_window)

# Instancia global del servicio
email_rate_limit_service = EmailRateLimitService()


