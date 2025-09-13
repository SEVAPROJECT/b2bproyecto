# app/models/tipo_documento.py

from typing import List
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, text
from sqlalchemy.orm import relationship, Mapped
from app.supabase.db.db_supabase import Base 

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.empresa.documento import Documento

class TipoDocumento(Base):
    """
    Representa los tipos de documentos requeridos para la verificación.
    """
    __tablename__ = 'tipo_documento'
    __table_args__ = (
        {'comment': 'Tipos de documentos requeridos para la verificación de proveedores'}
    )

    # El id_tip_documento es de tipo BIGINT y se deja que la base de datos lo autogenere
    id_tip_documento: Mapped[int] = Column(BigInteger, primary_key=True)
    
    # Este campo describe el tipo de documento (ej. 'Cédula de Identidad')
    nombre: Mapped[str] = Column('tipo_documento', String(60), nullable=False)
    
    # es_requerido indica si el documento es obligatorio para el proceso de verificación
    es_requerido: Mapped[bool] = Column(Boolean, nullable=False)
    
    created_at: Mapped[datetime] = Column(DateTime(True), server_default=text('now()'))

    # Relación con la tabla 'documento'
    documento: Mapped[List["Documento"]] = relationship("Documento", back_populates='tipo_documento')