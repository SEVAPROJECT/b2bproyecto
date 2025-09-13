# app/schemas/tarifa_servicio.py

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class TarifaServicioIn(BaseModel):
    monto: float
    descripcion: str
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    id_servicio: int
    id_tarifa: Optional[int] = None



class TarifaServicioOut(BaseModel):
    id_tarifa_servicio: int
    monto: float
    descripcion: str
    fecha_inicio: date
    fecha_fin: Optional[date]
    id_servicio: int
    id_tarifa: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True