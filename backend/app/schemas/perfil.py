# app/schemas/perfil.py
from pydantic import BaseModel
from uuid import UUID

class PerfilOut(BaseModel):
    id: UUID
    id_user: UUID
    nombre_contacto: str | None
    nombre_empresa: str | None

    class Config:
        orm_mode = True
