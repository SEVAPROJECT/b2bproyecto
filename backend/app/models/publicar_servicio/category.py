# app/models/categoria.py

from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, text, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base # Importación de la base declarativa
from b2bproyecto.backend.app.models.publicar_servicio.service import Servicio

if TYPE_CHECKING:
    from app.models.publicar_servicio.solicitud_servicio import SolicitudServicio

class CategoriaModel(Base):
    """
    Representa las categorías de servicios.
    """
    __tablename__ = 'categoria'
    __table_args__ = (
        PrimaryKeyConstraint('id_categoria', name='categoria_pkey'),
        {'comment': 'Categorías de servicios'}
    )

    # El id_categoria es de tipo BIGINT y se deja que la base de datos lo autogenere
    id_categoria: Mapped[int] = Column(BigInteger, primary_key=True)
    
    # Este campo describe el tipo de categoria (ej. 'Catering', 'Transporte', 'Salud', 'Educación', etc.)
    nombre: Mapped[str] = Column(String(100), nullable=False)
    
    estado: Mapped[bool] = Column(Boolean, nullable=False, server_default=text('true'))
    
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))

    # Relación con la tabla 'servicio'
    servicio: Mapped[List["Servicio"]] = relationship('Servicio', back_populates='categoria')
    solicitudes_servicio: Mapped[List["SolicitudServicio"]] = relationship('SolicitudServicio', back_populates='categoria')