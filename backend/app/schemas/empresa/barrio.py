# app/schemas/barrio.py

from pydantic import BaseModel

class BarrioIn(BaseModel):

    '''
    Este modelo se utiliza para validar los datos de entrada cuando se crea o actualiza un barrio.
    '''

    nombre: str
    id_ciudad: int

class BarrioOut(BaseModel):

    '''
    Este modelo se utiliza para serializar los datos de un barrio cuando se envía como respuesta al cliente.
    '''

    id_barrio: int
    nombre: str
    id_ciudad: int

    class Config:
        # Habilita la compatibilidad con modelos ORM de SQLAlchemy
        from_attributes = True
        #orm_mode = True version vieja