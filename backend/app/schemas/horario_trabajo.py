# backend/app/schemas/horario_trabajo.py
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, time, date
from typing import Optional, List

def validate_horario_times(hora_inicio: time, hora_fin: time) -> None:
    """
    Función helper para validar que hora_inicio sea menor que hora_fin.
    Lanza ValueError si la validación falla.
    
    Args:
        hora_inicio: Hora de inicio del horario
        hora_fin: Hora de fin del horario
    
    Raises:
        ValueError: Si hora_inicio >= hora_fin
    """
    if hora_inicio >= hora_fin:
        raise ValueError(
            f"La hora de inicio ({hora_inicio.strftime('%H:%M')}) debe ser menor que la hora de fin ({hora_fin.strftime('%H:%M')}). "
            f"Por favor, verifica que el horario de inicio sea anterior al horario de fin."
        )

class HorarioTrabajoIn(BaseModel):
    """
    Schema para crear un horario de trabajo.
    """
    dia_semana: int = Field(..., ge=0, le=6, description="Día de la semana (0=Lunes, 6=Domingo)")
    hora_inicio: time = Field(..., description="Hora de inicio")
    hora_fin: time = Field(..., description="Hora de fin")
    activo: bool = Field(True, description="Si el horario está activo")
    
    @model_validator(mode='after')
    def validate_horario(self):
        """Valida que hora_inicio sea menor que hora_fin"""
        validate_horario_times(self.hora_inicio, self.hora_fin)
        return self

class HorarioTrabajoOut(BaseModel):
    """
    Schema para la salida de datos de un horario de trabajo.
    """
    id_horario: int
    id_proveedor: int
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    activo: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class HorarioTrabajoUpdate(BaseModel):
    """
    Schema para actualizar un horario de trabajo.
    """
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    activo: Optional[bool] = None
    
    @model_validator(mode='after')
    def validate_horario(self):
        """Valida que hora_inicio sea menor que hora_fin cuando ambos están presentes"""
        if self.hora_inicio is not None and self.hora_fin is not None:
            validate_horario_times(self.hora_inicio, self.hora_fin)
        return self

class ExcepcionHorarioIn(BaseModel):
    """
    Schema para crear una excepción de horario.
    """
    fecha: date = Field(..., description="Fecha de la excepción")
    tipo: str = Field(..., description="Tipo de excepción: 'cerrado' o 'horario_especial'")
    hora_inicio: Optional[time] = Field(None, description="Hora de inicio (solo para horario_especial)")
    hora_fin: Optional[time] = Field(None, description="Hora de fin (solo para horario_especial)")
    motivo: Optional[str] = Field(None, max_length=500, description="Motivo de la excepción")
    
    @field_validator('fecha', mode='before')
    @classmethod
    def parse_fecha(cls, v):
        """
        Validador para asegurar que la fecha se parsea correctamente sin problemas de timezone.
        Si viene como string, se parsea como date puro (YYYY-MM-DD).
        Si viene como datetime, se extrae solo la parte de fecha.
        """
        if isinstance(v, str):
            # Si viene como string, tomar solo la parte de fecha (YYYY-MM-DD) sin hora ni timezone
            fecha_str = v.split('T')[0].split(' ')[0]
            return date.fromisoformat(fecha_str)
        elif isinstance(v, date):
            # Si ya es date, devolverlo directamente
            return v
        elif hasattr(v, 'date'):
            # Si es datetime, extraer solo la parte de fecha
            return v.date()
        return v
    
    @model_validator(mode='after')
    def validate_excepcion(self):
        """Valida que para horario_especial, hora_inicio sea menor que hora_fin"""
        if self.tipo == 'horario_especial':
            if self.hora_inicio is None or self.hora_fin is None:
                raise ValueError("Para horario_especial, tanto hora_inicio como hora_fin son requeridos")
            validate_horario_times(self.hora_inicio, self.hora_fin)
        return self

class ExcepcionHorarioOut(BaseModel):
    """
    Schema para la salida de datos de una excepción de horario.
    """
    id_excepcion: int
    id_proveedor: int
    fecha: date
    tipo: str
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    motivo: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class ExcepcionHorarioUpdate(BaseModel):
    """
    Schema para actualizar una excepción de horario.
    """
    tipo: Optional[str] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    motivo: Optional[str] = Field(None, max_length=500)
    
    @model_validator(mode='after')
    def validate_excepcion(self):
        """Valida que hora_inicio sea menor que hora_fin cuando ambos están presentes"""
        if self.hora_inicio is not None and self.hora_fin is not None:
            validate_horario_times(self.hora_inicio, self.hora_fin)
        # Si el tipo cambia a horario_especial, ambos horarios deben estar presentes
        if self.tipo == 'horario_especial' and (self.hora_inicio is None or self.hora_fin is None):
            # Esta validación se manejará en el endpoint al combinar con datos existentes
            pass
        return self

class HorarioDisponibleOut(BaseModel):
    """
    Schema para horarios disponibles generados automáticamente.
    """
    fecha: date
    hora_inicio: time
    hora_fin: time
    disponible: bool = True

class ConfiguracionHorarioCompletaIn(BaseModel):
    """
    Schema para configurar el horario completo de la semana.
    """
    horarios: List[HorarioTrabajoIn] = Field(..., description="Lista de horarios para cada día")
    excepciones: Optional[List[ExcepcionHorarioIn]] = Field(None, description="Excepciones opcionales")

class ConfiguracionHorarioCompletaOut(BaseModel):
    """
    Schema para la configuración completa del horario.
    """
    horarios: List[HorarioTrabajoOut]
    excepciones: List[ExcepcionHorarioOut]
