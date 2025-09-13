# app/schemas/verificacion.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TipoDocumentoIn(BaseModel):
    nombre: str
    es_requerido: bool


class TipoDocumentoOut(BaseModel):
    id_tip_documento: int
    nombre: str
    es_requerido: bool
    created_at: datetime
    
    class Config:
        #
        from_attributes = True