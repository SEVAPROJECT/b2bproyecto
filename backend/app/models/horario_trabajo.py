# backend/app/models/horario_trabajo.py
from typing import Optional, List
from datetime import datetime, time, date
from sqlalchemy import Column, String, Boolean, BigInteger, Integer, Time, Date, ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP
from typing import TYPE_CHECKING

from app.supabase.db.db_supabase import Base

if TYPE_CHECKING:
    from app.models.empresa.perfil_empresa import PerfilEmpresa

class HorarioTrabajoModel(Base):
    """
    Horario de trabajo semanal del proveedor.
    Aplica a TODOS sus servicios automáticamente.
    """
    __tablename__ = "horario_trabajo"

    id_horario: Mapped[int] = Column(BigInteger, primary_key=True)
    id_proveedor: Mapped[int] = Column(BigInteger, ForeignKey("perfil_empresa.id_perfil"), nullable=False)
    dia_semana: Mapped[int] = Column(Integer, nullable=False)
    hora_inicio: Mapped[time] = Column(Time, nullable=False)
    hora_fin: Mapped[time] = Column(Time, nullable=False)
    activo: Mapped[bool] = Column(Boolean, nullable=False, default=True)
    created_at: Mapped[Optional[datetime]] = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    
    # Relaciones
    proveedor = relationship("PerfilEmpresa", back_populates="horarios_trabajo")

class ExcepcionHorarioModel(Base):
    """
    Excepciones al horario normal (días cerrados, horarios especiales).
    """
    __tablename__ = "excepciones_horario"

    id_excepcion: Mapped[int] = Column(BigInteger, primary_key=True)
    id_proveedor: Mapped[int] = Column(BigInteger, ForeignKey("perfil_empresa.id_perfil"), nullable=False)
    fecha: Mapped[date] = Column(Date, nullable=False)
    tipo: Mapped[str] = Column(String(20), nullable=False)  # 'cerrado', 'horario_especial'
    hora_inicio: Mapped[Optional[time]] = Column(Time, nullable=True)
    hora_fin: Mapped[Optional[time]] = Column(Time, nullable=True)
    motivo: Mapped[Optional[str]] = Column(String(500), nullable=True)
    created_at: Mapped[Optional[datetime]] = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    
    # Relaciones
    proveedor = relationship("PerfilEmpresa", back_populates="excepciones_horario")
