# backend/app/models/disponibilidad.py
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP
from typing import TYPE_CHECKING

from app.supabase.db.db_supabase import Base

if TYPE_CHECKING:
    from app.models.servicio.service import ServicioModel
    from app.models.reserva_servicio.reserva import ReservaModel

class DisponibilidadModel(Base):
    __tablename__ = "disponibilidad"

    id_disponibilidad: Mapped[int] = Column(BigInteger, primary_key=True)
    id_servicio: Mapped[int] = Column(BigInteger, ForeignKey("servicio.id_servicio"), nullable=False)
    fecha_inicio: Mapped[datetime] = Column(TIMESTAMP(timezone=True), nullable=False)
    fecha_fin: Mapped[datetime] = Column(TIMESTAMP(timezone=True), nullable=False)
    disponible: Mapped[bool] = Column(Boolean, nullable=False, default=True)
    precio_adicional: Mapped[Optional[float]] = Column(Numeric(10, 2), default=0)
    observaciones: Mapped[Optional[str]] = Column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    

