# app/schemas/verificacion_solicitud.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.schemas.empresa.documento import DocumentoOut

class VerificacionSolicitudIn(BaseModel):
    # La fecha de solicitud y el estado se manejan en el backend
    comentario: Optional[str] = None
    
    # Se espera que el ID del perfil esté presente en la llamada de la API
    id_perfil: int


# Opcionalmente, importa el schema de la tabla relacionada si la quieres anidar
# from .documento import DocumentoOut

class VerificacionSolicitudOut(BaseModel):
    id_verificacion: int
    fecha_solicitud: datetime
    fecha_revision: Optional[datetime]
    estado: str
    comentario: Optional[str]
    id_perfil: int
    created_at: datetime
    
    # Si quieres incluir los documentos asociados, puedes descomentar y usar este campo
    documento: Optional[List["DocumentoOut"]] = None

    class Config:
        # Habilita la compatibilidad con modelos ORM de SQLAlchemy
        from_attributes = True