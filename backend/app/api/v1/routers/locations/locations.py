# app/api/v1/routers/locations/locations.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from datetime import datetime

from app.services.direct_db_service import direct_db_service
from app.schemas.empresa.departamento import DepartamentoOut
from app.schemas.empresa.ciudad import CiudadOut
from app.schemas.empresa.barrio import BarrioOut

# Constantes para mensajes de error
MSG_ERROR_OBTENER_DEPARTAMENTOS = "Error al obtener departamentos de la base de datos"
MSG_ERROR_OBTENER_CIUDADES = "Error al obtener ciudades de la base de datos"
MSG_ERROR_OBTENER_BARRIOS = "Error al obtener barrios de la base de datos"

# Logger para errores
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get(
    "/departamentos",
    response_model=List[DepartamentoOut],
    status_code=status.HTTP_200_OK,
    description="Devuelve una lista de todos los departamentos."
)
async def get_departamentos() -> List[DepartamentoOut]:
    """
    Obtiene todos los departamentos de la base de datos.
    Devuelve una lista vacía si no hay departamentos disponibles.
    Usa direct_db_service para evitar problemas con PgBouncer.
    """
    try:
        conn = await direct_db_service.get_connection()
        try:
            query = "SELECT id_departamento, nombre, created_at FROM departamento ORDER BY nombre"
            rows = await conn.fetch(query)
            
            departamentos = [
                DepartamentoOut(
                    id_departamento=row['id_departamento'],
                    nombre=row['nombre'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
            
            logger.info(f"✅ Encontrados {len(departamentos)} departamentos")
            return departamentos
        finally:
            await direct_db_service.pool.release(conn)
    except Exception as e:
        logger.error(f"{MSG_ERROR_OBTENER_DEPARTAMENTOS}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_OBTENER_DEPARTAMENTOS
        )


@router.get(
    "/ciudades/{id_departamento}",
    response_model=List[CiudadOut],
    status_code=status.HTTP_200_OK,
    description="Devuelve una lista de ciudades para un departamento específico."
)
async def get_ciudades_por_departamento(
    id_departamento: int
) -> List[CiudadOut]:
    """
    Obtiene todas las ciudades de un departamento por su ID.
    Devuelve una lista vacía si no hay ciudades para el departamento.
    Usa direct_db_service para evitar problemas con PgBouncer.
    """
    try:
        logger.info(f"🔍 Buscando ciudades para departamento ID: {id_departamento}")
        
        conn = await direct_db_service.get_connection()
        try:
            query = """
                SELECT id_ciudad, nombre, id_departamento, created_at 
                FROM ciudad 
                WHERE id_departamento = $1 
                ORDER BY nombre
            """
            rows = await conn.fetch(query, id_departamento)
            
            ciudades = [
                CiudadOut(
                    id_ciudad=row['id_ciudad'],
                    nombre=row['nombre'],
                    id_departamento=row['id_departamento'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
            
            logger.info(f"✅ Encontradas {len(ciudades)} ciudades para departamento ID {id_departamento}")
            if ciudades:
                nombres_ciudades = [c.nombre for c in ciudades]
                logger.debug(f"📋 Ciudades encontradas: {nombres_ciudades}")
            
            return ciudades
        finally:
            await direct_db_service.pool.release(conn)
    except Exception as e:
        logger.error(f"{MSG_ERROR_OBTENER_CIUDADES}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_OBTENER_CIUDADES
        )


@router.get(
    "/barrios/{id_ciudad}",
    response_model=List[BarrioOut],
    status_code=status.HTTP_200_OK,
    description="Devuelve una lista de barrios para una ciudad específica."
)
async def get_barrios_por_ciudad(
    id_ciudad: int
) -> List[BarrioOut]:
    """
    Obtiene todos los barrios de una ciudad por su ID.
    Devuelve una lista vacía si no hay barrios para la ciudad.
    Usa direct_db_service para evitar problemas con PgBouncer.
    """
    try:
        conn = await direct_db_service.get_connection()
        try:
            query = """
                SELECT id_barrio, nombre, id_ciudad 
                FROM barrio 
                WHERE id_ciudad = $1 
                ORDER BY nombre
            """
            rows = await conn.fetch(query, id_ciudad)
            
            barrios = [
                BarrioOut(
                    id_barrio=row['id_barrio'],
                    nombre=row['nombre'],
                    id_ciudad=row['id_ciudad']
                )
                for row in rows
            ]
            
            logger.info(f"✅ Encontrados {len(barrios)} barrios para ciudad ID {id_ciudad}")
            return barrios
        finally:
            await direct_db_service.pool.release(conn)
    except Exception as e:
        logger.error(f"{MSG_ERROR_OBTENER_BARRIOS}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_OBTENER_BARRIOS
        )