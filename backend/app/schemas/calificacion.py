from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CalificacionClienteData(BaseModel):
    """
    Schema para calificación de cliente (con NPS)
    """
    puntaje: int = Field(..., ge=1, le=5, description="Puntaje de 1 a 5 estrellas")
    comentario: str = Field(..., min_length=1, max_length=500, description="Comentario obligatorio")
    satisfaccion_nps: int = Field(..., ge=1, le=10, description="Puntuación NPS de 1 a 10")
    
    class Config:
        from_attributes = True

class CalificacionProveedorData(BaseModel):
    """
    Schema para calificación de proveedor (sin NPS)
    """
    puntaje: int = Field(..., ge=1, le=5, description="Puntaje de 1 a 5 estrellas")
    comentario: str = Field(..., min_length=1, max_length=500, description="Comentario obligatorio")
    
    class Config:
        from_attributes = True

class CalificacionOut(BaseModel):
    """
    Schema de respuesta para calificaciones
    """
    id_calificacion: int
    id_reserva: int
    puntaje: int
    comentario: str
    fecha: datetime
    rol_emisor: str
    usuario_id: str
    satisfaccion_nps: Optional[int] = None
    
    class Config:
        from_attributes = True

class CalificacionExistenteOut(BaseModel):
    """
    Schema para verificar si ya existe calificación
    """
    existe: bool
    calificacion: Optional[CalificacionOut] = None
    
    class Config:
        from_attributes = True
