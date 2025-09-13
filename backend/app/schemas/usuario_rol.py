# app/schemas/usuario_rol.py
from pydantic import BaseModel
from uuid import UUID
from app.schemas.rol import RolOut

class UsuarioRolOut(BaseModel):
    id: UUID
    id_user: UUID
    rol: RolOut   # ← Aquí usamos el relationship para retornar el rol asociado

    class Config:
        orm_mode = True
