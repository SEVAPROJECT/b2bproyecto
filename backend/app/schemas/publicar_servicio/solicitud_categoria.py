# app/schemas/solicitud_categoria.py

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SolicitudCategoriaIn(BaseModel):
    """Schema para crear una nueva solicitud de categoría"""
    nombre_categoria: str = Field(..., min_length=1, max_length=100, description="Nombre de la categoría solicitada")
    descripcion: str = Field(..., min_length=1, max_length=500, description="Descripción de la categoría solicitada")

class SolicitudCategoriaOut(BaseModel):
    """Schema para retornar información de una solicitud de categoría"""
    id_solicitud: int
    id_perfil: int
    nombre_categoria: str
    descripcion: str
    estado_aprobacion: str
    comentario_admin: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SolicitudCategoriaWithDetails(BaseModel):
    """Schema para retornar solicitud de categoría con información adicional"""
    id_solicitud: int
    id_perfil: int
    nombre_categoria: str
    descripcion: str
    estado_aprobacion: str
    comentario_admin: Optional[str] = None
    created_at: datetime
    
    # Información adicional
    nombre_empresa: Optional[str] = None
    nombre_contacto: Optional[str] = None
    email_contacto: Optional[str] = None
    user_id: Optional[str] = None  # ✅ AGREGAR user_id

    class Config:
        from_attributes = True

class SolicitudCategoriaUpdate(BaseModel):
    """Schema para actualizar una solicitud de categoría"""
    estado_aprobacion: str = Field(..., description="Nuevo estado de la solicitud")
    comentario_admin: Optional[str] = Field(None, max_length=500, description="Comentario del administrador")

class SolicitudCategoriaDecision(BaseModel):
    """Schema para decisiones del administrador"""
    comentario: Optional[str] = Field(None, max_length=500, description="Comentario del administrador")
