# app/models/departamento.py

from typing import List
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, text
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base # Importación de la base declarativa

class Departamento(Base):
    """
    Representa un departamento de un país.
    """
    __tablename__ = 'departamento'
    __table_args__ = (
        {'comment': 'Departamentos (ej. San Lorenzo)'}
    )

    # El id_departamento es de tipo BIGINT y se deja que la base de datos lo autogenere
    id_departamento: Mapped[int] = Column(BigInteger, primary_key=True)
    nombre: Mapped[str] = Column(String(100), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))
    
    # Relación con la tabla 'ciudad'
    ciudad: Mapped[List["Ciudad"]] = relationship("Ciudad", back_populates='departamento')