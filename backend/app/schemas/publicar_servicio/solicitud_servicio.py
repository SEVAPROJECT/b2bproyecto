# app/schemas/solicitud_servicio.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SolicitudServicioIn(BaseModel):
    nombre_servicio: str
    descripcion: str
    id_categoria: int
    comentario_admin: Optional[str] = None

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