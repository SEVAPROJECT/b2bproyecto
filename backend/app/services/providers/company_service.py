# app/services/providers/company_service.py
"""
Servicio para gestión de empresas y sucursales de proveedores.
"""

import uuid
from typing import Optional
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.sucursal_empresa import SucursalEmpresa
from app.api.v1.routers.providers.constants import (
    ESTADO_PENDIENTE,
    ESTADO_VERIFICADO_FALSE,
    NOMBRE_SUCURSAL_DEFAULT
)


class CompanyService:
    """Servicio para gestión de empresas y sucursales"""
    

    @staticmethod
    async def update_or_create_sucursal_orm(
        db: AsyncSession,
        perfil_data: dict,
        nuevo_perfil: PerfilEmpresa,
        nueva_direccion_id: int
    ) -> None:
        """Crea o actualiza la sucursal si hay datos usando ORM"""
        if not perfil_data.get('sucursal'):
            return
        
        sucursal_data = perfil_data['sucursal']
        sucursal_existente_query = select(SucursalEmpresa).where(
            SucursalEmpresa.id_perfil == nuevo_perfil.id_perfil
        )
        sucursal_existente_result = await db.execute(sucursal_existente_query)
        sucursal_existente = sucursal_existente_result.scalars().first()
        
        if sucursal_existente:
            sucursal_existente.nombre = sucursal_data.get('nombre', NOMBRE_SUCURSAL_DEFAULT)
            sucursal_existente.telefono = sucursal_data.get('telefono', '')
            sucursal_existente.email = sucursal_data.get('email', '')
            sucursal_existente.id_direccion = nueva_direccion_id
        else:
            nueva_sucursal = SucursalEmpresa(
                id_perfil=nuevo_perfil.id_perfil,
                nombre=sucursal_data.get('nombre', NOMBRE_SUCURSAL_DEFAULT),
                telefono=sucursal_data.get('telefono', ''),
                email=sucursal_data.get('email', ''),
                id_direccion=nueva_direccion_id,
                es_principal=True
            )
            db.add(nueva_sucursal)
        
        await db.flush()

    @staticmethod
    def get_sucursal_data(empresa: PerfilEmpresa) -> Optional[dict]:
        """Obtiene los datos de la sucursal principal de la empresa"""
        print(f"🔍 Sucursales encontradas: {len(empresa.sucursal_empresa) if empresa.sucursal_empresa else 0}")
        
        if not empresa.sucursal_empresa:
            print("⚠️ No se encontraron sucursales para esta empresa")
            return None
        
        print(f"🔍 Lista de sucursales: {[s.nombre for s in empresa.sucursal_empresa]}")
        sucursal = empresa.sucursal_empresa[0]
        
        if not sucursal:
            print("⚠️ No se encontró sucursal principal")
            return None
        
        print(f"✅ Sucursal encontrada: {sucursal.nombre}")
        return {
            "nombre": sucursal.nombre,
            "telefono": sucursal.telefono,
            "email": sucursal.email
        }

    @staticmethod
    def build_empresa_data(empresa: PerfilEmpresa, sucursal_data: Optional[dict]) -> dict:
        """Construye los datos de empresa para la respuesta"""
        return {
            "razon_social": empresa.razon_social,
            "nombre_fantasia": empresa.nombre_fantasia,
            "telefono_contacto": sucursal_data["telefono"] if sucursal_data else None,
            "email_contacto": sucursal_data["email"] if sucursal_data else None,
            "nombre_sucursal": sucursal_data["nombre"] if sucursal_data else None
        }

