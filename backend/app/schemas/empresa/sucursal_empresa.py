# app/schemas/sucursal_empresa.py

from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy import BIGINT

class SucursalEmpresaIn(BaseModel):
    nombre: str
    telefono: str
    email: EmailStr  # Utiliza EmailStr para validación automática de formato de email
    es_principal: bool
    
    # Para el caso de crear una sucursal, se podría necesitar la dirección,
    # aunque en un flujo real podría ser un objeto anidado.
    # Por ahora, se asume que se recibe el ID de dirección.
    id_direccion: Optional[int] = None

class SucursalEmpresaOut(BaseModel):
    id_sucursal: int
    nombre: str
    telefono: str
    email: EmailStr
    id_perfil: int
    id_direccion: int
    es_principal: bool
    created_at: datetime

    class Config:
        # Habilita la compatibilidad con modelos ORM de SQLAlchemy
        from_attributes = True