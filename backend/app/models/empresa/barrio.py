# app/models/barrio.py

from typing import List
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base # Importación de la base declarativa
from app.models.empresa.ciudad import Ciudad # Asegúrate de que esta importación sea correcta

class Barrio(Base):
    """
    Representa un barrio de una ciudad.
    """
    __tablename__ = 'barrio'
    __table_args__ = (
        {'comment': 'Barrios (ej. San Vicente)'}
    )

    # El id_barrio es de tipo BIGINT y se deja que la base de datos lo autogenere
    id_barrio: Mapped[int] = Column(BigInteger, primary_key=True)
    nombre: Mapped[str] = Column(String(100), nullable=False)
    
    # Clave foránea a la ciudad, usando BIGINT
    id_ciudad: Mapped[int] = Column(BigInteger, ForeignKey('ciudad.id_ciudad', ondelete='CASCADE'), nullable=False)
    
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))

    # Relaciones con otras tablas
    ciudad: Mapped["Ciudad"] = relationship("Ciudad", back_populates='barrio')
    direccion: Mapped[List["Direccion"]] = relationship("Direccion", back_populates='barrio')