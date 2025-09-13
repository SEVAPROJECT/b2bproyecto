# app/schemas/departamento.py

from pydantic import BaseModel
from datetime import datetime


class DepartamentoIn(BaseModel):


    '''
    Este modelo es para validar los datos de entrada cuando se crea o actualiza un departamento. 
    '''
    nombre: str


class DepartamentoOut(BaseModel):

    '''
    Este modelo se utiliza para serializar los datos de un departamento cuando se envía como respuesta al cliente.
    '''

    id_departamento: int
    nombre: str
    created_at: datetime
    
    class Config:
        # Habilita la compatibilidad con modelos ORM de SQLAlchemy
        from_attributes = True