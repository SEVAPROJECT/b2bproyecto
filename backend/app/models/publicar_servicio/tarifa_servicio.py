# app/models/tarifa_servicio.py

from typing import List, Optional
from datetime import datetime, date
from sqlalchemy import Column, String, BigInteger, Date, Numeric, text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base
from b2bproyecto.backend.app.models.publicar_servicio.service import Servicio
from app.models.publicar_servicio.tipo_tarifa_servicio import TipoTarifaServicio

# Importar Base para asegurar que esté disponible
from app.supabase.db.db_supabase import Base

class TarifaServicio(Base):
    """
    Representa las tarifas de un servicio.
    """
    __tablename__ = 'tarifa_servicio'

    id_tarifa_servicio: Mapped[int] = Column(BigInteger, primary_key=True)
    
    monto: Mapped[float] = Column(Numeric(12, 2), nullable=False)
    descripcion: Mapped[str] = Column(String(200), nullable=False)
    fecha_inicio: Mapped[date] = Column(Date, nullable=False)
    fecha_fin: Mapped[Optional[date]] = Column(Date, nullable=True)
    
    id_servicio: Mapped[int] = Column(BigInteger, ForeignKey('servicio.id_servicio', ondelete='CASCADE'), nullable=False)
    id_tarifa: Mapped[int] = Column(BigInteger, ForeignKey('tipo_tarifa_servicio.id_tarifa', ondelete='SET NULL'), nullable=True)
    
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))
    
    servicio: Mapped["Servicio"] = relationship('Servicio', back_populates='tarifa_servicio')
    tipo_tarifa_servicio: Mapped["TipoTarifaServicio"] = relationship('TipoTarifaServicio', back_populates='tarifa_servicio')