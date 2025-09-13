# app/models/usuario_rol.py
from typing import Optional
from uuid import UUID
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from app.supabase.db.db_supabase import Base
from typing import TYPE_CHECKING
#from app.models.rol  import RolModel
#from app.models.perfil import UserModel

# Importar modelos solo en tiempo de ejecución
#con esto evitamos problemas de importación circular
#circulares decimos por que auth.py importa usuario_rol.py, y usuario_rol.py importa auth.py
if TYPE_CHECKING:
    from app.models.rol import RolModel
    from app.models.perfil import UserModel


class UsuarioRolModel(Base):
    __tablename__ = "usuario_rol"  # Nombre de la tabla en Supabase
    
    # Clave primaria compuesta por las dos claves foráneas
    #id_usuario: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    id_usuario: Mapped[UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),  # 👈 schema correcto
        primary_key=True
    )

    id_rol: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey("rol.id"), primary_key=True)

    # Relaciones bidireccionales para acceder al usuario y al rol asociados
    
    #usuario: Mapped["UserModel"] = relationship(back_populates="roles")
    usuario: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="roles",
        primaryjoin="foreign(UsuarioRolModel.id_usuario) == UserModel.id"
        #primaryjoin="UsuarioRolModel.id_usuario == foreign(UserModel.id)"
        #remote_side="UserModel.id"
    )

    rol: Mapped["RolModel"] = relationship(back_populates="usuarios_asociados")
