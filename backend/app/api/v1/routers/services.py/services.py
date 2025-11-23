# app/api/v1/routers/services.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.api.v1.dependencies.database_supabase import get_async_db
from b2bproyecto.backend.app.models.publicar_servicio.service import Servicio
from b2bproyecto.backend.app.schemas.publicar_servicio.service import ServicioOut


# Constantes para mensajes de error
MSG_NO_SERVICIOS_ACTIVOS = "No se encontraron servicios activos."

# Asegúrate de que los routers se importen en main.py
router = APIRouter(prefix="/services", tags=["services"])


@router.get(
    "/list",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de todos los servicios activos disponibles en la plataforma."
)
async def get_all_services_list(db: AsyncSession = Depends(get_async_db)):
    """
    Este endpoint devuelve una lista de todos los servicios activos.
    """
    result = await db.execute(
        select(Servicio).where(Servicio.estado)
    )
    
    services = result.scalars().all()
    
    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_NO_SERVICIOS_ACTIVOS
        )
    return list(services)