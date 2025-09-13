# app/models/sucursal_empresa.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import BIGINT, BigInteger, Column, String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.supabase.db.db_supabase import Base # Importación de la base declarativa
from typing import TYPE_CHECKING
#from app.models.empresa.perfil_empresa import PerfilEmpresa
#from app.models.empresa.direccion import Direccion


if TYPE_CHECKING:
    from app.models.empresa.perfil_empresa import PerfilEmpresa
    from app.models.empresa.direccion import Direccion

class SucursalEmpresa(Base):
    """
    Representa una sucursal de una empresa.
    """
    __tablename__ = 'sucursal_empresa'

    # Usamos BIGINT para el id de la sucursal
    id_sucursal: Mapped[int] = Column(BigInteger, primary_key=True)

    nombre: Mapped[str] = Column(String(100), nullable=False)
    telefono: Mapped[str] = Column(String(30), nullable=False)
    email: Mapped[str] = Column(String(100), nullable=False)
    
    # La clave foránea al perfil debe ser BIGINT
    id_perfil: Mapped[int] = Column(BigInteger, ForeignKey('perfil_empresa.id_perfil', ondelete='CASCADE'), nullable=False, index=True)
    # La clave foránea a la dirección también debe ser UUID
    #id_direccion: Mapped[UUID] = Column(PG_UUID(as_uuid=True), ForeignKey('direccion.id_direccion', ondelete='SET NULL'), nullable=True)
    id_direccion: Mapped[int] = Column(BigInteger, ForeignKey('direccion.id_direccion', ondelete='SET NULL'), nullable=True)
    es_principal: Mapped[bool] = Column(Boolean, nullable=False, server_default=text('false'))
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))

    # Relaciones con otras tablas
    direccion: Mapped['Direccion'] = relationship('Direccion', back_populates='sucursal_empresa')
    perfil_empresa: Mapped['PerfilEmpresa'] = relationship('PerfilEmpresa', back_populates='sucursal_empresa')