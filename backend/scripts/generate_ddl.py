#!/usr/bin/env python3
"""
Script para generar el DDL (Data Definition Language) de todas las tablas
basado en los modelos SQLAlchemy.

Uso:
    python scripts/generate_ddl.py > database_schema.sql
"""

import sys
import os

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.schema import CreateTable
from app.supabase.db.db_supabase import async_engine
from app.models import (
    Departamento, Ciudad, Barrio, Direccion,
    TipoDocumento, Documento, PerfilEmpresa, SucursalEmpresa,
    VerificacionSolicitud
)
from app.models.perfil import UserModel
from app.models.rol import RolModel
from app.models.usuario_rol import UsuarioRolModel
from app.models.horario_trabajo import HorarioTrabajoModel
from app.models.disponibilidad import DisponibilidadModel
from app.models.publicar_servicio.category import CategoriaModel
from app.models.publicar_servicio.moneda import MonedaModel
from app.models.publicar_servicio.tipo_tarifa_servicio import TipoTarifaServicioModel
from app.models.publicar_servicio.tarifa_servicio import TarifaServicioModel
from app.models.publicar_servicio.solicitud_servicio import SolicitudServicioModel
from app.models.servicio.service import ServicioModel
from app.models.reserva_servicio.reserva import ReservaModel

def generate_ddl():
    """Genera el DDL para todas las tablas."""
    print("-- ============================================")
    print("-- DDL generado desde modelos SQLAlchemy")
    print("-- Fecha de generación: " + str(__import__('datetime').datetime.now()))
    print("-- ============================================\n")
    
    # Lista de todos los modelos
    models = [
        Departamento, Ciudad, Barrio, Direccion,
        TipoDocumento, Documento, PerfilEmpresa, SucursalEmpresa,
        VerificacionSolicitud, UserModel, RolModel, UsuarioRolModel,
        HorarioTrabajoModel, DisponibilidadModel, CategoriaModel,
        MonedaModel, TipoTarifaServicioModel, TarifaServicioModel,
        SolicitudServicioModel, ServicioModel, ReservaModel
    ]
    
    # Generar CREATE TABLE para cada modelo
    for model in models:
        try:
            create_table = CreateTable(model.__table__)
            ddl = str(create_table.compile(compile_kwargs={"literal_binds": True}))
            print(f"-- Tabla: {model.__tablename__}")
            print(ddl)
            print(";")
            print()
        except Exception as e:
            print(f"-- ERROR generando DDL para {model.__tablename__}: {e}")
            print()

if __name__ == "__main__":
    generate_ddl()



