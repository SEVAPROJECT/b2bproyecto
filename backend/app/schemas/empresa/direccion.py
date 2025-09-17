# app/schemas/direccion.py

from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from sqlalchemy import BIGINT

class DireccionIn(BaseModel):

    '''
    Este schema es para recibir datos del frontend cuando se crea o modifica una dirección.
    '''
    calle: str
    numero: str
    referencia: Optional[str] = None
    coordenadas: str # La coordenada vendrá como un string (ej. 'SRID=4326;POINT(x y)')
    id_departamento: Optional[int] = None


class DireccionOut(BaseModel):
    '''
    Este schema se utiliza para la respuesta del backend. Contiene todos los datos relevantes, 
    incluidos los IDs y las marcas de tiempo
    '''
    id_direccion: BIGINT
    calle: str
    numero: str
    referencia: Optional[str]
    coordenadas: str # Podría ser un string para la salida
    id_departamento: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True