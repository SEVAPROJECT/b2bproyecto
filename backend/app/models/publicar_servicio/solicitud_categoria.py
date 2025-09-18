# app/models/solicitud_categoria.py

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base
from app.models.empresa.perfil_empresa import PerfilEmpresa

if TYPE_CHECKING:
    from app.models.publicar_servicio.category import CategoriaModel

class SolicitudCategoria(Base):
    """
    Tabla para almacenar las solicitudes de los proveedores para agregar nuevas categorías.
    Sigue el principio de responsabilidad única y mejores prácticas de normalización.
    """
    __tablename__ = 'solicitud_categoria'
    __table_args__ = (
        CheckConstraint(
            "estado_aprobacion IN ('pendiente', 'aprobada', 'rechazada')",
            name='check_estado_aprobacion'
        ),
        {'comment': 'Solicitudes de nuevas categorías pendientes de aprobación'}
    )

    id_solicitud: Mapped[int] = Column(BigInteger, primary_key=True, autoincrement=True)
    id_perfil: Mapped[int] = Column(BigInteger, ForeignKey('perfil_empresa.id_perfil', ondelete='CASCADE'), nullable=False)
    nombre_categoria: Mapped[str] = Column(String(100), nullable=False)
    descripcion: Mapped[str] = Column(String(500), nullable=False)
    estado_aprobacion: Mapped[str] = Column(String(20), nullable=False, default='pendiente')
    comentario_admin: Mapped[Optional[str]] = Column(String(500), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))
    
    # Relaciones
    perfil_empresa: Mapped["PerfilEmpresa"] = relationship("PerfilEmpresa", back_populates="solicitudes_categoria")

    def __repr__(self) -> str:
        return f"<SolicitudCategoria(id_solicitud={self.id_solicitud}, nombre_categoria='{self.nombre_categoria}', estado='{self.estado_aprobacion}')>"
