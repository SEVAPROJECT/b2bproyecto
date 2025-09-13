# app/schemas/rol.py
from pydantic import BaseModel
from uuid import UUID

class RolBase(BaseModel):
    nombre: str
    descripcion: str | None = None

class RolOut(RolBase):
    id: UUID

    class Config:
        orm_mode = True
