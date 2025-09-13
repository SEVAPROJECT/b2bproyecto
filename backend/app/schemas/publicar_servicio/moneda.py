# app/schemas/moneda.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MonedaOut(BaseModel):
    id_moneda: int
    codigo_iso_moneda: str
    nombre: str
    simbolo: str
    estado: bool
    created_at: datetime

    class Config:
        from_attributes = True