# app/models/servicio.py

from typing import List
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION as Double
from app.supabase.db.db_supabase import Base # Importación de la base declarativa
from typing import TYPE_CHECKING
    
if TYPE_CHECKING:
    from app.models.publicar_servicio.category import CategoriaModel
    from app.models.publicar_servicio.moneda import Moneda
    from app.models.empresa.perfil_empresa import PerfilEmpresa
    from app.models.publicar_servicio.tarifa_servicio import TarifaServicio
    from app.models.reserva_servicio.reserva import ReservaModel

class ServicioModel(Base):
    """
    Representa los servicios ofrecidos por las empresas.
    """
    __tablename__ = 'servicio'
    
    # El id_servicio es de tipo BIGINT y se deja que la base de datos lo autogenere
    id_servicio: Mapped[int] = Column(BigInteger, primary_key=True)
    
    # Claves foráneas, usando BIGINT
    id_categoria: Mapped[int] = Column(BigInteger, ForeignKey('categoria.id_categoria', ondelete='SET NULL'), nullable=True)
    id_perfil: Mapped[int] = Column(BigInteger, ForeignKey('perfil_empresa.id_perfil', ondelete='CASCADE'), nullable=False)
    id_moneda: Mapped[int] = Column(BigInteger, ForeignKey('moneda.id_moneda', ondelete='SET NULL'), nullable=True)
    
    nombre: Mapped[str] = Column(String(60), nullable=False)
    descripcion: Mapped[str] = Column(String(500), nullable=False)
    precio: Mapped[float] = Column(Double(53), nullable=False)
    imagen: Mapped[str] = Column(String(500), nullable=True)  # Ruta de la imagen representativa
    estado: Mapped[bool] = Column(Boolean, nullable=False, default=True) # Estado por defecto: activo
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))

    # Relaciones con otras tablas
    categoria: Mapped["CategoriaModel"] = relationship('CategoriaModel', back_populates='servicio')
    moneda: Mapped["Moneda"] = relationship('Moneda', back_populates='servicio')
    perfil_empresa: Mapped["PerfilEmpresa"] = relationship('PerfilEmpresa', back_populates='servicio')
    tarifa_servicio: Mapped[List["TarifaServicio"]] = relationship('TarifaServicio', back_populates='servicio')
    reserva: Mapped[List["ReservaModel"]] = relationship('ReservaModel', back_populates='servicio')