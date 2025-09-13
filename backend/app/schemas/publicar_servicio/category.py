# app/schemas/categoria.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


#Este modelo es para la validación de los datos de entrada cuando se crea o actualiza una categoría.
class CategoriaIn(BaseModel):
    nombre: str
    estado: bool = True


#Este modelo se utiliza para serializar los datos de una categoría cuando se envía como respuesta al cliente.

class CategoriaOut(BaseModel):
    id_categoria: int
    nombre: str
    estado: bool
    created_at: datetime
    
    class Config:
        from_attributes = True