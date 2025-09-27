# backend/app/schemas/reserva.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date
from typing import Optional

class ReservaIn(BaseModel):
    """
    Schema para la entrada de datos al crear una nueva reserva.
    """
    id_servicio: UUID
    descripcion: str = Field(..., max_length=500)
    observacion: Optional[str] = Field(None, max_length=1000)
    fecha: date
    id_disponibilidad: Optional[int] = Field(None, description="ID de la disponibilidad específica reservada")

class ReservaOut(BaseModel):
    """
    Schema para la salida de datos de una reserva.
    """
    id: UUID
    id_servicio: UUID
    id_usuario: UUID
    descripcion: str
    observacion: Optional[str]
    fecha: date
    estado: str
    id_disponibilidad: Optional[int] = None

    #class Config:
        #orm_mode = True
    class Config:
        from_attributes = True