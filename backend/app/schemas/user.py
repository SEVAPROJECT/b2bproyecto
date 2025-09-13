from pydantic import BaseModel, EmailStr
from uuid import UUID
import uuid

class UserProfileAndRolesOut(BaseModel):
    """
    Modelo de salida para representar los datos públicos del usuario.
    Usado por endpoints como /me.
    Modelo publico para exponer los datos del usuario autenticado.
    
    """
    id: uuid.UUID
    email: EmailStr
    nombre_persona: str
    nombre_empresa: str
    ruc: str | None = None
    roles: list[str]
    foto_perfil: str | None = None

