# app/api/v1/routers/additional_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.publicar_servicio.moneda import Moneda
from app.models.publicar_servicio.tipo_tarifa_servicio import TipoTarifaServicio
from app.schemas.publicar_servicio.moneda import MonedaOut
from app.schemas.publicar_servicio.tipo_tarifa_servicio import TipoTarifaServicioOut

router = APIRouter(prefix="/additional", tags=["additional"])


@router.get(
    "/currencies",
    response_model=List[MonedaOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene todas las monedas activas disponibles."
)
async def get_active_currencies(db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todas las monedas activas del sistema.
    """
    result = await db.execute(
        select(Moneda).where(Moneda.estado == True)
    )

    currencies = result.scalars().all()

    if not currencies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron monedas activas."
        )
    return list(currencies)


@router.get(
    "/rate-types",
    response_model=List[TipoTarifaServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene todos los tipos de tarifa disponibles."
)
async def get_rate_types(db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todos los tipos de tarifa activos del sistema.
    """
    result = await db.execute(
        select(TipoTarifaServicio).where(TipoTarifaServicio.estado == True)
    )

    rate_types = result.scalars().all()

    if not rate_types:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron tipos de tarifa activos."
        )
    return list(rate_types)
