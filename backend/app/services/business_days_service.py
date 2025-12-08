# app/services/business_days_service.py
"""
Servicio para calcular días hábiles (lunes a viernes, excluyendo feriados).
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class BusinessDaysService:
    """
    Servicio para calcular días hábiles.
    Días hábiles = lunes a viernes, excluyendo feriados.
    """
    
    # Lista de feriados en Paraguay (puede expandirse o cargarse desde BD)
    # Formato: (mes, día)
    FERIADOS_PARAGUAY = [
        (1, 1),   # Año Nuevo
        (3, 1),   # Día de los Héroes
        (5, 1),   # Día del Trabajador
        (5, 14),  # Día de la Independencia
        (5, 15),  # Día de la Independencia (día siguiente)
        (6, 12),  # Día de la Paz del Chaco
        (8, 15),  # Fundación de Asunción
        (9, 29),  # Batalla de Boquerón
        (12, 8),  # Virgen de Caacupé
        (12, 25), # Navidad
    ]
    
    @staticmethod
    def is_feriado(fecha: datetime) -> bool:
        """
        Verifica si una fecha es feriado en Paraguay.
        
        Args:
            fecha: Fecha a verificar
            
        Returns:
            True si es feriado, False en caso contrario
        """
        return (fecha.month, fecha.day) in BusinessDaysService.FERIADOS_PARAGUAY
    
    @staticmethod
    def is_dia_habil(fecha: datetime) -> bool:
        """
        Verifica si una fecha es día hábil (lunes a viernes, no feriado).
        
        Args:
            fecha: Fecha a verificar
            
        Returns:
            True si es día hábil, False en caso contrario
        """
        # Verificar si es fin de semana (sábado=5, domingo=6)
        if fecha.weekday() >= 5:
            return False
        
        # Verificar si es feriado
        if BusinessDaysService.is_feriado(fecha):
            return False
        
        return True
    
    @staticmethod
    def calcular_horas_habiles(
        fecha_inicio: datetime,
        horas: int = 72,
        incluir_fecha_inicio: bool = False
    ) -> datetime:
        """
        Calcula la fecha límite sumando horas hábiles a partir de una fecha de inicio.
        
        Args:
            fecha_inicio: Fecha y hora de inicio
            horas: Número de horas hábiles a sumar (por defecto 72)
            incluir_fecha_inicio: Si True, incluye la fecha de inicio en el cálculo
            
        Returns:
            Fecha y hora límite después de sumar las horas hábiles
        """
        fecha_actual = fecha_inicio
        horas_restantes = horas
        
        # Si no se incluye la fecha de inicio, empezar desde el siguiente día hábil
        if not incluir_fecha_inicio:
            # Avanzar al siguiente día hábil si la fecha de inicio no es hábil
            while not BusinessDaysService.is_dia_habil(fecha_actual):
                fecha_actual += timedelta(days=1)
                fecha_actual = fecha_actual.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular horas por día hábil (8 horas por día, de 9:00 a 17:00)
        HORAS_POR_DIA_HABIL = 8
        
        while horas_restantes > 0:
            # Si es día hábil, restar horas
            if BusinessDaysService.is_dia_habil(fecha_actual):
                # Calcular cuántas horas del día hábil podemos usar
                hora_actual = fecha_actual.hour
                
                # Si estamos en horario laboral (9:00-17:00)
                if 9 <= hora_actual < 17:
                    horas_disponibles_hoy = 17 - hora_actual
                    horas_a_usar = min(horas_restantes, horas_disponibles_hoy)
                    fecha_actual += timedelta(hours=horas_a_usar)
                    horas_restantes -= horas_a_usar
                else:
                    # Si estamos fuera de horario laboral, avanzar al inicio del siguiente día hábil
                    if hora_actual < 9:
                        # Estamos antes de las 9:00, avanzar a las 9:00
                        fecha_actual = fecha_actual.replace(hour=9, minute=0, second=0, microsecond=0)
                    else:
                        # Estamos después de las 17:00, avanzar al siguiente día hábil a las 9:00
                        fecha_actual += timedelta(days=1)
                        fecha_actual = fecha_actual.replace(hour=9, minute=0, second=0, microsecond=0)
                        # Avanzar hasta el siguiente día hábil
                        while not BusinessDaysService.is_dia_habil(fecha_actual):
                            fecha_actual += timedelta(days=1)
            else:
                # No es día hábil, avanzar al siguiente día hábil a las 9:00
                fecha_actual += timedelta(days=1)
                fecha_actual = fecha_actual.replace(hour=9, minute=0, second=0, microsecond=0)
                # Avanzar hasta el siguiente día hábil
                while not BusinessDaysService.is_dia_habil(fecha_actual):
                    fecha_actual += timedelta(days=1)
        
        return fecha_actual
    
    @staticmethod
    def calcular_72_horas_habiles(fecha_inicio: datetime) -> datetime:
        """
        Calcula la fecha límite sumando 72 horas hábiles a partir de una fecha de inicio.
        Conveniencia para el caso específico de verificación de RUC.
        
        Args:
            fecha_inicio: Fecha y hora de inicio
            
        Returns:
            Fecha y hora límite después de 72 horas hábiles
        """
        return BusinessDaysService.calcular_horas_habiles(
            fecha_inicio,
            horas=72,
            incluir_fecha_inicio=False
        )
    
    @staticmethod
    def verificar_vencimiento(fecha_limite: datetime) -> bool:
        """
        Verifica si una fecha límite ya venció.
        
        Args:
            fecha_limite: Fecha límite a verificar (puede ser naive o aware)
            
        Returns:
            True si ya venció, False en caso contrario
        """
        # Normalizar ambas fechas a UTC para comparar
        if fecha_limite.tzinfo is not None:
            # Si fecha_limite tiene timezone, convertir a UTC
            fecha_limite_utc = fecha_limite.astimezone(timezone.utc)
            ahora = datetime.now(timezone.utc)
        else:
            # Si fecha_limite es naive, usar datetime.now() sin timezone
            fecha_limite_utc = fecha_limite
            ahora = datetime.now()
        return ahora > fecha_limite_utc
    
    @staticmethod
    def obtener_tiempo_restante(fecha_limite: datetime) -> Optional[timedelta]:
        """
        Obtiene el tiempo restante hasta la fecha límite.
        
        Args:
            fecha_limite: Fecha límite (puede ser naive o aware)
            
        Returns:
            timedelta con el tiempo restante, o None si ya venció
        """
        # Obtener fecha actual con el mismo timezone que fecha_limite
        if fecha_limite.tzinfo is not None:
            # Si fecha_limite tiene timezone, usar datetime.now con timezone UTC
            ahora = datetime.now(timezone.utc)
            # Asegurar que fecha_limite esté en UTC para comparar
            fecha_limite_utc = fecha_limite.astimezone(timezone.utc) if fecha_limite.tzinfo != timezone.utc else fecha_limite
        else:
            # Si fecha_limite es naive, usar datetime.now() sin timezone
            ahora = datetime.now()
            fecha_limite_utc = fecha_limite
        
        if ahora > fecha_limite_utc:
            return None
        return fecha_limite_utc - ahora

