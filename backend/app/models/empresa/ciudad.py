# app/models/ciudad.py

from typing import List
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, text, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base # Importación de la base declarativa

class Ciudad(Base):
    """
    Representa una ciudad de un departamento.
    """
    __tablename__ = 'ciudad'
    __table_args__ = (
        {'comment': 'Ciudades (ej. Asunción)'}
    )
    
    # El id_ciudad es de tipo BIGINT y se deja que la base de datos lo autogenere
    id_ciudad: Mapped[int] = Column(BigInteger, primary_key=True)
    nombre: Mapped[str] = Column(String(100), nullable=False)
    
    # Clave foránea al departamento, usando BIGINT
    id_departamento: Mapped[int] = Column(BigInteger, ForeignKey('departamento.id_departamento', ondelete='CASCADE'), nullable=False)
    
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))

    # Relaciones con otras tablas
    departamento: Mapped["Departamento"] = relationship("Departamento", back_populates='ciudad')
    barrio: Mapped[List["Barrio"]] = relationship("Barrio", back_populates='ciudad')