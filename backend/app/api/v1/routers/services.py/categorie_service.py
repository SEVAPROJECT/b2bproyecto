# backend/app/api/v1/routers/categories.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.publicar_servicio.category import Categoria
from app.schemas.publicar_servicio.category import CategoriaOut

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get(
    "/",
    response_model=List[CategoriaOut],
    status_code=status.HTTP_200_OK,
    description="Devuelve una lista de todas las categorías de servicios activas."
)
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todas las categorías de la base de datos que están activas.
    """
    result = await db.execute(
        select(Categoria).where(Categoria.estado == True)
    )

    categories = result.scalars().all()
    
    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron categorías activas."
        )
    return list(categories)