# app/models/empresa/verificacion_ruc.py

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.supabase.db.db_supabase import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.empresa.tipo_documento import TipoDocumento
    from app.models.perfil import UserModel

class VerificacionRUC(Base):
    """
    Representa la verificación del documento RUC durante el registro de usuario.
    El usuario debe subir su constancia de RUC al registrarse, y un administrador
    debe verificar su validez antes de activar la cuenta.
    """
    __tablename__ = 'verificacion_ruc'
    __table_args__ = (
        {'comment': 'Verificación de RUC durante el registro de usuarios'}
    )

    id_verificacion_ruc: Mapped[int] = Column(BigInteger, primary_key=True)
    
    # Referencia al usuario que se registró
    user_id: Mapped[UUID] = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Referencia al tipo de documento (ej. "Constancia de RUC")
    id_tip_documento: Mapped[int] = Column(
        BigInteger,
        ForeignKey('tipo_documento.id_tip_documento', ondelete='RESTRICT'),
        nullable=False
    )
    
    # URL del documento subido (almacenado en iDrive o storage)
    url_documento: Mapped[str] = Column(String(500), nullable=False)
    
    # Estado de la verificación: 'pendiente', 'aprobado', 'rechazado'
    estado: Mapped[str] = Column(String(20), nullable=False, server_default=text("'pendiente'"))
    
    # Fecha de creación de la solicitud
    fecha_creacion: Mapped[datetime] = Column(DateTime(True), nullable=False, server_default=text('now()'))
    
    # Fecha en que se verificó (aprobado o rechazado)
    fecha_verificacion: Mapped[Optional[datetime]] = Column(DateTime(True), nullable=True)
    
    # Fecha límite para verificación (72 horas hábiles desde fecha_creacion)
    fecha_limite_verificacion: Mapped[Optional[datetime]] = Column(DateTime(True), nullable=True)
    
    # Comentario del administrador al aprobar/rechazar
    comentario: Mapped[Optional[str]] = Column(String(1000), nullable=True)
    
    # ID del administrador que verificó
    id_admin_verificador: Mapped[Optional[UUID]] = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete='SET NULL'),
        nullable=True
    )
    
    # Token único para corrección de RUC rechazado
    token_correccion: Mapped[Optional[str]] = Column(String(100), nullable=True, unique=True, index=True)
    
    # Fecha de expiración del token de corrección (30 días desde rechazo)
    token_expiracion: Mapped[Optional[datetime]] = Column(DateTime(True), nullable=True)
    
    # Relaciones
    tipo_documento: Mapped["TipoDocumento"] = relationship(back_populates='verificacion_ruc')
    usuario: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[user_id],
        back_populates="verificacion_ruc"
    )
    admin_verificador: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        foreign_keys=[id_admin_verificador]
    )

