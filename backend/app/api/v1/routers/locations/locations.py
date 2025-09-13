# app/api/v1/routers/locations.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.empresa.departamento import Departamento
from app.models.empresa.ciudad import Ciudad
from app.models.empresa.barrio import Barrio
from app.schemas.empresa.departamento import DepartamentoOut
from app.schemas.empresa.ciudad import CiudadOut
from app.schemas.empresa.barrio import BarrioOut

router = APIRouter(prefix="/locations", tags=["locations"])

@router.get(
    "/departamentos",
    response_model=List[DepartamentoOut],
    status_code=status.HTTP_200_OK,
    description="Devuelve una lista de todos los departamentos."
)
async def get_departamentos(db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todos los departamentos de la base de datos.
    """
    result = await db.execute(select(Departamento))
    departamentos = result.scalars().all()
    if not departamentos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron departamentos."
        )
    return list(departamentos)

@router.get(
    "/ciudades/{id_departamento}",
    response_model=List[CiudadOut],
    status_code=status.HTTP_200_OK,
    description="Devuelve una lista de ciudades para un departamento específico."
)
async def get_ciudades_por_departamento(id_departamento: int, db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todas las ciudades de un departamento por su ID.
    """
    result = await db.execute(
        select(Ciudad).where(Ciudad.id_departamento == id_departamento)
    )
    ciudades = result.scalars().all()
    if not ciudades:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron ciudades para el departamento con ID {id_departamento}."
        )
    return list(ciudades)

@router.get(
    "/barrios/{id_ciudad}",
    response_model=List[BarrioOut],
    status_code=status.HTTP_200_OK,
    description="Devuelve una lista de barrios para una ciudad específica."
)
async def get_barrios_por_ciudad(id_ciudad: int, db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todos los barrios de una ciudad por su ID.
    """
    result = await db.execute(
        select(Barrio).where(Barrio.id_ciudad == id_ciudad)
    )
    barrios = result.scalars().all()
    if not barrios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron barrios para la ciudad con ID {id_ciudad}."
        )
    return list(barrios)