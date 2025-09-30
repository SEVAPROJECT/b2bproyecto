# backend/app/schemas/reserva_servicio/reserva_detallada.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional

class ReservaDetalladaOut(BaseModel):
    """
    Schema para la salida detallada de reservas con información del servicio, empresa y contacto.
    Optimizado para la página "Mis Reservas" del cliente.
    """
    # Información de la reserva
    id_reserva: int
    id_servicio: int
    id_usuario: UUID
    descripcion: str
    observacion: Optional[str]
    fecha: date
    hora_inicio: Optional[str]
    hora_fin: Optional[str]
    estado: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Información del servicio
    nombre_servicio: str
    descripcion_servicio: Optional[str]
    precio_servicio: float
    imagen_servicio: Optional[str]
    
    # Información de la empresa/proveedor
    nombre_empresa: str
    razon_social: Optional[str]
    id_perfil: int
    
    # Información de contacto
    nombre_contacto: str
    email_contacto: Optional[str]
    telefono_contacto: Optional[str]
    
    # Información de categoría
    nombre_categoria: Optional[str]
    
    class Config:
        from_attributes = True


class ReservasPaginadasOut(BaseModel):
    """
    Schema para respuesta paginada de reservas.
    """
    reservas: list[ReservaDetalladaOut]
    pagination: dict = Field(..., description="Información de paginación")
    
    class Config:
        from_attributes = True

