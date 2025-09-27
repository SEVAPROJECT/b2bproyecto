# backend/app/schemas/disponibilidad.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DisponibilidadIn(BaseModel):
    """
    Schema para la entrada de datos al crear una nueva disponibilidad.
    """
    id_servicio: int = Field(..., description="ID del servicio")
    fecha_inicio: datetime = Field(..., description="Fecha y hora de inicio")
    fecha_fin: datetime = Field(..., description="Fecha y hora de fin")
    disponible: bool = Field(True, description="Si está disponible para reservas")
    precio_adicional: Optional[float] = Field(0, ge=0, description="Precio adicional para este horario")
    observaciones: Optional[str] = Field(None, max_length=500, description="Observaciones adicionales")

class DisponibilidadOut(BaseModel):
    """
    Schema para la salida de datos de una disponibilidad.
    """
    id_disponibilidad: int
    id_servicio: int
    fecha_inicio: datetime
    fecha_fin: datetime
    disponible: bool
    precio_adicional: Optional[float]
    observaciones: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class DisponibilidadUpdate(BaseModel):
    """
    Schema para actualizar una disponibilidad existente.
    """
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    disponible: Optional[bool] = None
    precio_adicional: Optional[float] = Field(None, ge=0)
    observaciones: Optional[str] = Field(None, max_length=500)
