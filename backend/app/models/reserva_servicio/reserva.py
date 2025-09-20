# backend/app/models/reserva.py
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from sqlalchemy import Column, String, ForeignKey, Date
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from typing import TYPE_CHECKING

from app.supabase.db.db_supabase import Base

if TYPE_CHECKING:
    from app.models.perfil import UserModel  
    from app.models.servicio.service import ServicioModel 

class ReservaModel(Base):
    __tablename__ = "reserva"

    id: Mapped[UUID] = Column(PG_UUID(as_uuid=True), primary_key=True)
    id_servicio: Mapped[UUID] = Column(PG_UUID(as_uuid=True), ForeignKey("servicio.id"), nullable=False)
    id_usuario: Mapped[UUID] = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    descripcion: Mapped[str] = Column(String(500), nullable=False)
    observacion: Mapped[Optional[str]] = Column(String(1000), nullable=True)
    fecha: Mapped[date] = Column(Date, nullable=False)
    estado: Mapped[str] = Column(String(20), nullable=False, default="pendiente")
    
    #relaciones para acceder al usuario y servicio
    usuario = relationship("UserModel", back_populates="reserva")
    #usuario = Mapped["UserModel"] = relationship("UserModel", back_populates="reserva")
    #servicio = Mapped["ServicioModel"] = relationship("ServicioModel", back_populates="reserva")
    servicio = relationship("ServicioModel", back_populates="reserva")