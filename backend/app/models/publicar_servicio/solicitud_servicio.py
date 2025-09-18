# app/models/solicitud_servicio.py

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, text, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base
from app.models.empresa.perfil_empresa import PerfilEmpresa

if TYPE_CHECKING:
    from app.models.publicar_servicio.category import CategoriaModel

class SolicitudServicio(Base):
    """
    Tabla para almacenar las solicitudes de los proveedores para agregar nuevos servicios.
    """
    __tablename__ = 'solicitud_servicio'
    __table_args__ = ({'comment': 'Solicitudes de servicios pendientes de aprobación'})

    id_solicitud: Mapped[int] = Column(BigInteger, primary_key=True)
    id_perfil: Mapped[int] = Column(BigInteger, ForeignKey('perfil_empresa.id_perfil', ondelete='CASCADE'), nullable=False)
    id_categoria: Mapped[int] = Column(BigInteger, ForeignKey('categoria.id_categoria', ondelete='SET NULL'), nullable=True)
    nombre_servicio: Mapped[str] = Column(String(60), nullable=False)
    descripcion: Mapped[str] = Column(String(500), nullable=False)
    estado_aprobacion: Mapped[str] = Column(String(20), nullable=False, default='pendiente') # 'pendiente', 'aprobada', 'rechazada'
    comentario_admin: Mapped[str] = Column(String(500), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))
    
    perfil_empresa: Mapped["PerfilEmpresa"] = relationship("PerfilEmpresa", back_populates="solicitudes_servicio")
    categoria: Mapped["CategoriaModel"] = relationship("CategoriaModel", back_populates="solicitudes_servicio")