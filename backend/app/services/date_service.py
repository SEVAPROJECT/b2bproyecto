"""
Servicio centralizado para manejo de fechas con zona horaria GMT-3 fija (Paraguay)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DateService:
    """Servicio para manejo de fechas con zona horaria fija GMT-3 (Paraguay)"""
    
    # Zona horaria fija de Paraguay (GMT-3)
    PARAGUAY_TIMEZONE = timezone(timedelta(hours=-3))
    
    @classmethod
    def now(cls) -> datetime:
        """
        Obtiene la fecha y hora actual en zona horaria fija GMT-3 (Paraguay)
        
        Returns:
            datetime: Fecha y hora actual en GMT-3
        """
        return datetime.now(cls.PARAGUAY_TIMEZONE)
    
    @classmethod
    def now_for_database(cls) -> datetime:
        """
        Obtiene la fecha y hora actual en UTC para insertar en la base de datos
        La base de datos está configurada en UTC, por lo que enviamos fechas UTC
        
        Returns:
            datetime: Fecha y hora actual en UTC
        """
        # Obtener fecha en GMT-3 y convertir a UTC para la base de datos
        paraguay_time = datetime.now(cls.PARAGUAY_TIMEZONE)
        return paraguay_time.astimezone(timezone.utc)
    
    @classmethod
    def utcnow(cls) -> datetime:
        """
        Obtiene la fecha y hora actual en UTC (para compatibilidad)
        Nota: Se recomienda usar now() para nuevas implementaciones
        
        Returns:
            datetime: Fecha y hora actual en UTC
        """
        return DateService.now()
    
    @classmethod
    def paraguay_now(cls) -> datetime:
        """
        Obtiene la fecha y hora actual en zona horaria fija GMT-3 (Paraguay)
        Alias para now() para mayor claridad
        
        Returns:
            datetime: Fecha y hora actual en GMT-3
        """
        return cls.now()
    
    @classmethod
    def to_paraguay_timezone(cls, dt: datetime) -> datetime:
        """
        Convierte una fecha a zona horaria fija GMT-3 (Paraguay)
        
        Args:
            dt: Fecha a convertir
            
        Returns:
            datetime: Fecha en GMT-3
        """
        if dt.tzinfo is None:
            # Si no tiene zona horaria, asumir UTC
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.astimezone(cls.PARAGUAY_TIMEZONE)
    
    @classmethod
    def to_utc(cls, dt: datetime) -> datetime:
        """
        Convierte una fecha a UTC
        
        Args:
            dt: Fecha a convertir
            
        Returns:
            datetime: Fecha en UTC
        """
        if dt.tzinfo is None:
            # Si no tiene zona horaria, asumir que es de Paraguay
            dt = dt.replace(tzinfo=cls.PARAGUAY_TIMEZONE)
        
        return dt.astimezone(timezone.utc)
    
    @classmethod
    def format_paraguay_datetime(cls, dt: Optional[datetime] = None) -> str:
        """
        Formatea una fecha en formato legible para Paraguay
        
        Args:
            dt: Fecha a formatear (si es None, usa la fecha actual)
            
        Returns:
            str: Fecha formateada en formato DD/MM/YYYY HH:MM:SS
        """
        if dt is None:
            dt = cls.now()
        
        # Asegurar que esté en zona horaria de Paraguay
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=cls.PARAGUAY_TIMEZONE)
        elif dt.tzinfo != cls.PARAGUAY_TIMEZONE:
            dt = dt.astimezone(cls.PARAGUAY_TIMEZONE)
        
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    
    @classmethod
    def format_paraguay_date(cls, dt: Optional[datetime] = None) -> str:
        """
        Formatea una fecha en formato de fecha para Paraguay
        
        Args:
            dt: Fecha a formatear (si es None, usa la fecha actual)
            
        Returns:
            str: Fecha formateada en formato DD/MM/YYYY
        """
        if dt is None:
            dt = cls.now()
        
        # Asegurar que esté en zona horaria de Paraguay
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=cls.PARAGUAY_TIMEZONE)
        elif dt.tzinfo != cls.PARAGUAY_TIMEZONE:
            dt = dt.astimezone(cls.PARAGUAY_TIMEZONE)
        
        return dt.strftime("%d/%m/%Y")
    
    @classmethod
    def get_paraguay_timezone_info(cls) -> dict:
        """
        Obtiene información sobre la zona horaria de Paraguay
        
        Returns:
            dict: Información de la zona horaria
        """
        now = cls.now()
        return {
            "timezone": "GMT-3",
            "country": "Paraguay",
            "offset_hours": -3,
            "current_time": cls.format_paraguay_datetime(now),
            "current_date": cls.format_paraguay_date(now),
            "iso_format": now.isoformat()
        }
