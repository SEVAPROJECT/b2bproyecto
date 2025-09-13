# app/schemas/tipo_tarifa_servicio.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TipoTarifaServicioOut(BaseModel):
    id_tarifa: int
    nombre: str
    descripcion: str
    estado: bool
    created_at: datetime

    class Config:
        from_attributes = True

