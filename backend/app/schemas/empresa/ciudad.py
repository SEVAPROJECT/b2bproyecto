# app/schemas/ciudad.py

from datetime import datetime
from pydantic import BaseModel

class CiudadIn(BaseModel):

    '''
    Este modelo es para validar los datos de entrada cuando se crea o actualiza una ciudad.
    '''
    nombre: str
    id_departamento: int

class CiudadOut(BaseModel):

    '''
    Este modelo se utiliza para serializar los datos de una ciudad cuando se envía como respuesta al cliente.
    '''
    id_ciudad: int
    nombre: str
    id_departamento: int
    created_at: datetime

    class Config:
        # Habilita la compatibilidad con modelos ORM de SQLAlchemy
        from_attributes = True