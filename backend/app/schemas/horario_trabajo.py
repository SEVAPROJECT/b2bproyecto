# backend/app/schemas/horario_trabajo.py
from pydantic import BaseModel, Field
from datetime import datetime, time, date
from typing import Optional, List

class HorarioTrabajoIn(BaseModel):
    """
    Schema para crear un horario de trabajo.
    """
    dia_semana: int = Field(..., ge=0, le=6, description="Día de la semana (0=Lunes, 6=Domingo)")
    hora_inicio: time = Field(..., description="Hora de inicio")
    hora_fin: time = Field(..., description="Hora de fin")
    activo: bool = Field(True, description="Si el horario está activo")

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

class ExcepcionHorarioIn(BaseModel):
    """
    Schema para crear una excepción de horario.
    """
    fecha: date = Field(..., description="Fecha de la excepción")
    tipo: str = Field(..., description="Tipo de excepción: 'cerrado' o 'horario_especial'")
    hora_inicio: Optional[time] = Field(None, description="Hora de inicio (solo para horario_especial)")
    hora_fin: Optional[time] = Field(None, description="Hora de fin (solo para horario_especial)")
    motivo: Optional[str] = Field(None, max_length=500, description="Motivo de la excepción")

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
