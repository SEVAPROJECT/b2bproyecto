# app/schemas/solicitud_servicio.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class SolicitudServicioIn(BaseModel):
    nombre_servicio: str = Field(..., min_length=1, max_length=60, description="Nombre del servicio")
    descripcion: str = Field(..., min_length=1, max_length=500, description="Descripción del servicio (máximo 500 caracteres)")
    id_categoria: int
    comentario_admin: Optional[str] = None

    @field_validator('descripcion')
    @classmethod
    def validate_descripcion_length(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError('La descripción no puede superar los 500 caracteres')
        return v

class SolicitudServicioOut(BaseModel):
    id_solicitud: int
    id_perfil: int
    nombre_servicio: str
    descripcion: str
    estado_aprobacion: str
    comentario_admin: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True