# app/models/rol.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from app.supabase.db.db_supabase import Base
from app.models.usuario_rol import UsuarioRolModel

class RolModel(Base):
    __tablename__ = "rol"  # Nombre de la tabla en Supabase

    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True)
    nombre: Mapped[str] = Column(String(100), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = Column(String(200), nullable=True)
    
    # Relación con la tabla de unión UsuarioRol (relación inversa)
    usuarios_asociados: Mapped[List["UsuarioRolModel"]] = relationship(back_populates="rol")
