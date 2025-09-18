# app/models/moneda.py

from typing import List
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base # Importación de la base declarativa
from b2bproyecto.backend.app.models.publicar_servicio.service import Servicio

class Moneda(Base):
    """
    Representa una moneda para precios y transacciones.
    """
    __tablename__ = 'moneda'
    __table_args__ = (
        {'comment': 'Tabla para almacenar las monedas (ej. USD, PYG)'}
    )

    # El id_moneda es de tipo BIGINT y se deja que la base de datos lo autogenere
    id_moneda: Mapped[int] = Column(BigInteger, primary_key=True)
    
    # El código ISO debe ser único
    codigo_iso_moneda: Mapped[str] = Column(String(4), nullable=False, unique=True)
    
    nombre: Mapped[str] = Column(String(50), nullable=False)
    simbolo: Mapped[str] = Column(String(3), nullable=False)

    # Campo estado (comentado temporalmente si no existe en BD)
    # estado: Mapped[bool] = Column(Boolean, nullable=False, server_default=text('true'))

    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))

    # Relaciones con otras tablas
    servicio: Mapped[List["Servicio"]] = relationship('Servicio', back_populates='moneda')