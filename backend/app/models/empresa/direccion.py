# app/models/direccion.py

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import BIGINT, Column, String, ForeignKey, text, DateTime
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.empresa.barrio import Barrio
from geoalchemy2 import Geometry
from app.supabase.db.db_supabase import Base 
from typing import TYPE_CHECKING
#from app.models.empresa.perfil_empresa import PerfilEmpresa
#from app.models.empresa.sucursal_empresa import SucursalEmpresa

if TYPE_CHECKING:
    from app.models.empresa.perfil_empresa import PerfilEmpresa
    from app.models.empresa.sucursal_empresa import SucursalEmpresa

class Direccion(Base):
    """
    Representa las direcciones con coordenadas geográficas usando PostGIS.
    """
    __tablename__ = "direccion"
    __table_args__ = (
        {"comment": "Direcciones con coordenadas geográficas (PostGIS)"}
    )

    # Usamos UUID para el id_direccion, con un valor por defecto generado
    id_direccion: Mapped[BIGINT] = Column(BIGINT, primary_key=True) 
    calle: Mapped[str] = Column(String(150), nullable=False)
    numero: Mapped[str] = Column(String(20), nullable=False)
    referencia: Mapped[str] = Column(String(150), nullable=True) # Hacemos referencia opcional
    
    # La columna de coordenadas ya está correctamente definida
    coordenadas: Mapped[str] = Column(Geometry("POINT", srid=4326), nullable=False)
    
    # El id_barrio debe ser BIGINT para la consistencia con el modelo Barrio
    id_barrio: Mapped[Optional[int]] = Column(BIGINT, ForeignKey('barrio.id_barrio', ondelete='CASCADE'), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text('now()'))

    # Relaciones
    barrio: Mapped["Barrio"] = relationship("Barrio", back_populates="direccion")
    perfil_empresa: Mapped[List["PerfilEmpresa"]] = relationship("PerfilEmpresa", back_populates="direccion")
    sucursal_empresa: Mapped[List["SucursalEmpresa"]] = relationship("SucursalEmpresa", back_populates="direccion")