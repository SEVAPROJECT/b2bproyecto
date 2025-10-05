# app/models/perfil_empresa.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import BigInteger, Column, String, Boolean, DateTime, text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.supabase.db.db_supabase import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.perfil import UserModel
    from app.models.empresa.direccion import Direccion
    from app.models.empresa.sucursal_empresa import SucursalEmpresa
    from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
    from app.models.publicar_servicio.solicitud_servicio import SolicitudServicio
    from app.models.publicar_servicio.solicitud_categoria import SolicitudCategoria
    from app.models.servicio.service import ServicioModel
    from app.models.horario_trabajo import HorarioTrabajoModel, ExcepcionHorarioModel

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"

    id_perfil: Mapped[int] = Column(BigInteger, primary_key=True)
    
    # ForeignKey apuntando a users.id
    user_id: Mapped[UUID] = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    verificado: Mapped[bool] = Column(Boolean, nullable=False, server_default=text('false'))
    fecha_verificacion: Mapped[Optional[DateTime]] = Column(DateTime(True), nullable=True)
    razon_social: Mapped[str] = Column(String(80), nullable=False)
    nombre_fantasia: Mapped[str] = Column(String(80), nullable=False)
    estado: Mapped[str] = Column(String(20), nullable=False)
    fecha_inicio: Mapped[DateTime] = Column(DateTime(True), nullable=False, server_default=text('now()'))
    fecha_fin: Mapped[Optional[DateTime]] = Column(DateTime(True), nullable=True)

    id_direccion: Mapped[Optional[int]] = Column(
        BigInteger, ForeignKey('direccion.id_direccion', ondelete='SET NULL'), nullable=True
    )

    # Relaciones
    direccion: Mapped["Direccion"] = relationship(back_populates="perfil_empresa")
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="perfil_empresa",
        primaryjoin="PerfilEmpresa.user_id == UserModel.id"
    )
    sucursal_empresa: Mapped[List["SucursalEmpresa"]] = relationship(back_populates="perfil_empresa")
    verificacion_solicitud: Mapped[List["VerificacionSolicitud"]] = relationship(back_populates="perfil_empresa")
    solicitudes_servicio: Mapped[List["SolicitudServicio"]] = relationship(back_populates="perfil_empresa")
    solicitudes_categoria: Mapped[List["SolicitudCategoria"]] = relationship(back_populates="perfil_empresa")
    servicio: Mapped[List["ServicioModel"]] = relationship(back_populates="perfil_empresa")
    horarios_trabajo: Mapped[List["HorarioTrabajoModel"]] = relationship("HorarioTrabajoModel", back_populates="proveedor")
    excepciones_horario: Mapped[List["ExcepcionHorarioModel"]] = relationship("ExcepcionHorarioModel", back_populates="proveedor")