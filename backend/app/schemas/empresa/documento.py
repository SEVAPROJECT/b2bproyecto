# app/schemas/documento.py

from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class DocumentoIn(BaseModel):
    '''
    Este modelo se utiliza para validar la información cuando un proveedor sube 
    un documento para una solicitud.
    '''
    id_tip_documento: int
    archivo_url: str  # Aquí se espera la URL o el path del archivo en iDrive

    
class DocumentoOut(BaseModel):
    id_documento: int
    id_tip_documento: int
    id_verificacion: int
    estado_revision: str
    fecha_verificacion: Optional[datetime]
    observacion: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
