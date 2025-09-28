# backend/app/models/reserva.py
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from sqlalchemy import Column, String, ForeignKey, Date, BigInteger
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from typing import TYPE_CHECKING

from app.supabase.db.db_supabase import Base

if TYPE_CHECKING:
    from app.models.perfil import UserModel  
    from app.models.servicio.service import ServicioModel
    from app.models.disponibilidad import DisponibilidadModel 

class ReservaModel(Base):
    __tablename__ = "reserva"

    id: Mapped[UUID] = Column(PG_UUID(as_uuid=True), primary_key=True)
    id_servicio: Mapped[int] = Column(BigInteger, ForeignKey("servicio.id_servicio"), nullable=False)
    id_usuario: Mapped[UUID] = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    descripcion: Mapped[str] = Column(String(500), nullable=False)
    observacion: Mapped[Optional[str]] = Column(String(1000), nullable=True)
    fecha: Mapped[date] = Column(Date, nullable=False)
    estado: Mapped[str] = Column(String(20), nullable=False, default="pendiente")
    id_disponibilidad: Mapped[Optional[int]] = Column(BigInteger, ForeignKey("disponibilidad.id_disponibilidad"), nullable=True)
    
    #relaciones para acceder al usuario, servicio y disponibilidad
    usuario = relationship("UserModel", back_populates="reserva")
    servicio = relationship("ServicioModel", back_populates="reserva")
    disponibilidad = relationship("DisponibilidadModel", back_populates="reservas")