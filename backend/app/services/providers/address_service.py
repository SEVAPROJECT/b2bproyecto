# app/services/providers/address_service.py
"""
Servicio para gestión de direcciones de proveedores.
"""

import asyncpg
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError

from app.models.empresa.direccion import Direccion
from app.repositories.providers.provider_repository import ProviderRepository
from app.api.v1.routers.providers.constants import (
    COORDENADAS_ASUNCION_WKT,
    COORDENADAS_ASUNCION_SRID
)


class AddressService:
    """Servicio para gestión de direcciones"""
    
    @staticmethod
    async def sync_direccion_sequence(db: AsyncSession) -> None:
        """Sincroniza la secuencia de direccion"""
        await db.execute(text("""
            SELECT setval(
                pg_get_serial_sequence('direccion', 'id_direccion'),
                COALESCE((SELECT MAX(id_direccion) FROM direccion), 0) + 1,
                false
            )
        """))
        await db.flush()

    @staticmethod
    async def create_direccion_with_retry(
        db: AsyncSession,
        direccion_data: dict,
        departamento,
        ciudad,
        barrio
    ) -> Direccion:
        """Crea una dirección con manejo de errores de secuencia usando ORM"""
        nueva_direccion = Direccion(
            calle=direccion_data['calle'],
            numero=direccion_data['numero'],
            referencia=direccion_data['referencia'],
            id_departamento=departamento.id_departamento,
            id_ciudad=ciudad.id_ciudad if ciudad else None,
            id_barrio=barrio.id_barrio if barrio else None,
            coordenadas=None  # Se manejará con WKTElement si es necesario
        )
        db.add(nueva_direccion)
        
        try:
            await db.flush()
        except IntegrityError as e:
            if 'duplicate key value violates unique constraint "direccion_pkey"' in str(e):
                print("⚠️ Secuencia de direccion desincronizada, sincronizando...")
                db.expunge(nueva_direccion)
                await AddressService.sync_direccion_sequence(db)
                # Recrear el objeto dirección
                nueva_direccion = Direccion(
                    calle=direccion_data['calle'],
                    numero=direccion_data['numero'],
                    referencia=direccion_data['referencia'],
                    id_departamento=departamento.id_departamento,
                    id_ciudad=ciudad.id_ciudad if ciudad else None,
                    id_barrio=barrio.id_barrio if barrio else None,
                    coordenadas=None
                )
                db.add(nueva_direccion)
                await db.flush()
            else:
                raise
        
        return nueva_direccion


    @staticmethod
    async def get_direccion_data(db: AsyncSession, direccion_id: int) -> Optional[dict]:
        """Obtiene los datos de dirección con sus relaciones usando ORM"""
        if not direccion_id:
            return None
        
        from app.models.empresa.departamento import Departamento
        from app.models.empresa.ciudad import Ciudad
        from sqlalchemy.orm import selectinload
        
        direccion_query = select(Direccion).options(
            selectinload(Direccion.departamento).selectinload(Departamento.ciudad).selectinload(Ciudad.barrio)
        ).where(Direccion.id_direccion == direccion_id)
        direccion_result = await db.execute(direccion_query)
        direccion = direccion_result.scalars().first()
        
        if not direccion or not direccion.departamento:
            return None
        
        # Extraer datos de ciudad y barrio
        ciudad_data = None
        barrio_data = None
        
        if direccion.departamento.ciudad and len(direccion.departamento.ciudad) > 0:
            ciudad = direccion.departamento.ciudad[0]
            ciudad_data = {"nombre": ciudad.nombre}
            
            if ciudad.barrio and len(ciudad.barrio) > 0:
                barrio = ciudad.barrio[0]
                barrio_data = {"nombre": barrio.nombre}
        
        return {
            "calle": direccion.calle,
            "numero": direccion.numero,
            "referencia": direccion.referencia,
            "departamento": direccion.departamento.nombre,
            "ciudad": ciudad_data["nombre"] if ciudad_data else None,
            "barrio": barrio_data["nombre"] if barrio_data else None
        }

