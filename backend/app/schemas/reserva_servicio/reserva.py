# backend/app/schemas/reserva.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date
from typing import Optional

class ReservaIn(BaseModel):
    """
    Schema para la entrada de datos al crear una nueva reserva.
    """
    id_servicio: int  # Cambiado de UUID a int para compatibilidad con frontend
    descripcion: str = Field(..., max_length=500)
    observacion: Optional[str] = Field(None, max_length=1000)
    fecha: date
    hora_inicio: Optional[str] = Field(None, description="Hora de inicio en formato HH:MM")
    id_disponibilidad: Optional[int] = Field(None, description="ID de la disponibilidad específica reservada")

class ReservaOut(BaseModel):
    """
    Schema para la salida de datos de una reserva.
    """
    id: UUID  # Mapeado desde id_reserva
    id_servicio: int  # Cambiado de UUID a int
    user_id: UUID  # Mapeado desde user_id
    descripcion: str
    observacion: Optional[str]
    fecha: date  # Solo fecha, sin tiempo
    hora_inicio: Optional[str] = None  # Agregado para compatibilidad
    hora_fin: Optional[str] = None     # Agregado para compatibilidad
    estado: str
    id_disponibilidad: Optional[int] = None

    #class Config:
        #orm_mode = True
    class Config:
        from_attributes = True

class ReservaEstadoUpdate(BaseModel):
    """
    Schema para actualizar el estado de una reserva.
    """
    nuevo_estado: str = Field(..., description="Nuevo estado de la reserva")
    observacion: Optional[str] = Field(None, max_length=500, description="Observación opcional para el cambio de estado")
    
    class Config:
        from_attributes = True

class ReservaCancelacionData(BaseModel):
    """
    Schema para cancelar una reserva.
    El motivo es obligatorio.
    """
    motivo: str = Field(..., min_length=1, max_length=500, description="Motivo obligatorio para cancelar la reserva")
    
    class Config:
        from_attributes = True