# app/schemas/servicio.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ServicioIn(BaseModel):
    nombre: str
    descripcion: str
    precio: float
    id_categoria: int
    id_moneda: int
    imagen: Optional[str] = None


class ServicioOut(BaseModel):
    id_servicio: int
    id_categoria: Optional[int]
    id_perfil: int
    id_moneda: Optional[int]
    nombre: str
    descripcion: str
    precio: float
    imagen: Optional[str]
    estado: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ServicioCreate(BaseModel):
    nombre: str
    descripcion: str
    precio: float
    id_categoria: Optional[int] = None
    id_moneda: Optional[int] = None
    imagen: Optional[str] = None

class ServicioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    id_categoria: Optional[int] = None
    id_moneda: Optional[int] = None
    imagen: Optional[str] = None
    estado: Optional[bool] = None

class TarifaServicio(BaseModel):
    id_tarifa_servicio: int
    monto: float
    descripcion: str
    fecha_inicio: str
    fecha_fin: Optional[str] = None
    id_tarifa: Optional[int] = None
    nombre_tipo_tarifa: Optional[str] = None

class ServicioWithProvider(BaseModel):
    id_servicio: int
    id_categoria: Optional[int]
    id_perfil: int
    id_moneda: Optional[int]
    nombre: str
    descripcion: str
    precio: float
    imagen: Optional[str]
    estado: bool
    created_at: datetime
    # Información del proveedor
    razon_social: Optional[str] = None
    nombre_contacto: Optional[str] = None
    ciudad: Optional[str] = None  # Ciudad de la empresa
    departamento: Optional[str] = None  # Departamento de la empresa
    # Información de moneda
    codigo_iso_moneda: Optional[str] = None  # Código ISO de la moneda (ej: PYG, USD)
    nombre_moneda: Optional[str] = None  # Nombre de la moneda (ej: Guaraní, Dólar)
    simbolo_moneda: Optional[str] = None  # Símbolo de la moneda (ej: ₲, $)
    # Tarifas del servicio
    tarifas: List[TarifaServicio] = []

    class Config:
        from_attributes = True