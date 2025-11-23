# app/models/documento.py

from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.empresa.tipo_documento import TipoDocumento
    from app.models.empresa.verificacion_solicitud import VerificacionSolicitud

class Documento(Base):
    """
    Representa un documento cargado para una solicitud de verificación.
    """
    __tablename__ = 'documento'
    __table_args__ = (
        {'comment': 'Documentos cargados para la verificación de perfiles'}
    )

    id_documento: Mapped[int] = Column(BigInteger, primary_key=True)
    
    # Claves foráneas a otras tablas, usando BIGINT
    id_tip_documento: Mapped[int] = Column(BigInteger, ForeignKey('tipo_documento.id_tip_documento', ondelete='CASCADE'), nullable=False)
    id_verificacion: Mapped[int] = Column(BigInteger, ForeignKey('verificacion_solicitud.id_verificacion', ondelete='CASCADE'), nullable=False, index=True)

    estado_revision: Mapped[str] = Column(String(20), nullable=False)  # ej. 'pendiente', 'aprobado', 'rechazado'
    
    # URL del archivo subido por el usuario
    url_archivo: Mapped[str] = Column(String(500), nullable=False, default='temp://pending')
    
    # La fecha de verificación se establece cuando se revisa el documento
    fecha_verificacion: Mapped[datetime] = Column(DateTime(True), nullable=False, server_default=text('now()'))
    
    observacion: Mapped[Optional[str]] = Column(String(1000), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))
    
    # Relaciones con otras tablas
    tipo_documento: Mapped["TipoDocumento"] = relationship(back_populates='documento')
    verificacion_solicitud: Mapped["VerificacionSolicitud"] = relationship(back_populates='documento')