# app/schemas/perfil_empresa.py

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.schemas.empresa.documento import DocumentoIn

# Importar schemas de tablas relacionadas
# from .direccion import DireccionOut
# from .plan_suscripcion import PlanSuscripcionOut
# from .servicio import ServicioOut
# from .sucursal_empresa import SucursalEmpresaOut
# from .verificacion_solicitud import VerificacionSolicitudOut

class PerfilEmpresaIn(BaseModel):
    #razon_social: este campo ya no se espera del frontend
    nombre_fantasia: str
    id_direccion: str

class solicitudCompletaIn(BaseModel):
    perfil_empresa : PerfilEmpresaIn
    comentario_solicitud : str
    documentos : List[DocumentoIn]

class PerfilEmpresaOut(BaseModel):
    id_perfil: UUID
    user_id: UUID
    verificado: bool
    fecha_verificacion: Optional[datetime]
    razon_social: str
    nombre_fantasia: str
    estado: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime]
    
    # Aquí puedes incluir los schemas de las relaciones si quieres mostrarlas
    # direccion: Optional[DireccionOut]
    # sucursal_empresa: List[SucursalEmpresaOut] = []
    # servicio: List[ServicioOut] = []
    # verificacion_solicitud: List[VerificacionSolicitudOut] = []

    class Config:
        from_attributes = True