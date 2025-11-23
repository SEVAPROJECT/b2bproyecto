# app/models/perfil.py
from typing import List
from uuid import UUID
from sqlalchemy import String, Column
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.supabase.db.db_supabase import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.empresa.perfil_empresa import PerfilEmpresa
    from app.models.usuario_rol import UsuarioRolModel
    from app.models.reserva_servicio.reserva import ReservaModel

class UserModel(Base):
    __tablename__ = "users"

    # Clave primaria coincidente con auth.users.id
    id: Mapped[UUID] = Column(PG_UUID(as_uuid=True), primary_key=True)
    nombre_persona: Mapped[str] = Column(String(100), nullable=False)
    nombre_empresa: Mapped[str] = Column(String(100), nullable=True)
    ruc: Mapped[str] = Column(String(20), nullable=True)
    estado: Mapped[str] = Column(String(20), nullable=False, default="ACTIVO")
    foto_perfil: Mapped[str] = Column(String(500), nullable=True)

    # Relaciones
    roles: Mapped[List["UsuarioRolModel"]] = relationship(
        "UsuarioRolModel", back_populates="usuario",
        primaryjoin="UsuarioRolModel.id_usuario == UserModel.id"
    )

    '''perfil_empresa: Mapped[List["PerfilEmpresa"]] = relationship(
        "PerfilEmpresa", back_populates="user"
    )'''
    perfil_empresa: Mapped[List["PerfilEmpresa"]] = relationship(
        "PerfilEmpresa", 
        back_populates="user",
        primaryjoin="PerfilEmpresa.user_id == UserModel.id"
    )
    
    # Relación con reservas
    reserva: Mapped[List["ReservaModel"]] = relationship(
        "ReservaModel", 
        back_populates="usuario",
        primaryjoin="ReservaModel.user_id == UserModel.id"
    )

