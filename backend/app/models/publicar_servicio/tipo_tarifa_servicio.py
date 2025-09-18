# app/models/tipo_tarifa_servicio.py

from typing import List
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, text
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base
from app.models_backup import TarifaServicio

class TipoTarifaServicio(Base):
    """
    Representa los tipos de tarifa disponibles para los servicios.
    Ej: por hora, por día, por proyecto, etc.
    """
    __tablename__ = 'tipo_tarifa_servicio'
    __table_args__ = (
        {'comment': 'Tipos de tarifa disponibles para servicios'}
    )

    id_tarifa: Mapped[int] = Column(BigInteger, primary_key=True)
    nombre: Mapped[str] = Column(String(50), nullable=False)  # ej: "Por hora", "Por día", "Por proyecto"
    descripcion: Mapped[str] = Column(String(200), nullable=False)
    estado: Mapped[bool] = Column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))

    # Relación con tarifa_servicio
    tarifa_servicio: Mapped[List["TarifaServicio"]] = relationship('TarifaServicio', back_populates='tipo_tarifa_servicio')

