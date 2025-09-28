# backend/app/api/v1/routers/categories.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.publicar_servicio.category import CategoriaModel
from app.schemas.publicar_servicio.category import CategoriaOut, CategoriaIn
from pydantic import BaseModel
from app.api.v1.dependencies.auth_user import get_admin_user
from app.schemas.user import UserProfileAndRolesOut

router = APIRouter(prefix="/categories", tags=["categories"])

# Esquema para actualizar categoría
class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    estado: Optional[bool] = None

@router.get(
    "/",
    response_model=List[CategoriaOut],
    status_code=status.HTTP_200_OK,
    description="Devuelve una lista de todas las categorías de servicios."
)
async def get_all_categories(
    active_only: bool = True
):
    """
    Obtiene todas las categorías de la base de datos.
    Para administradores: muestra todas las categorías.
    Para otros usuarios: muestra solo las activas.
    """
    try:
        from app.services.direct_db_service import direct_db_service
        
        # Usar direct_db_service para evitar problemas con PgBouncer
        conn = await direct_db_service.get_connection()
        try:
            # Construir consulta SQL
            if active_only:
                query = """
                    SELECT id_categoria, nombre, estado, created_at
                    FROM categoria
                    WHERE estado = true
                    ORDER BY nombre
                """
            else:
                query = """
                    SELECT id_categoria, nombre, estado, created_at
                    FROM categoria
                    ORDER BY nombre
                """
            
            categories_data = await conn.fetch(query)
            
            if not categories_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No se encontraron categorías."
                )
            
            # Convertir a objetos CategoriaOut
            categories = []
            for row in categories_data:
                categories.append(CategoriaOut(
                    id_categoria=row['id_categoria'],
                    nombre=row['nombre'],
                    estado=row['estado'],
                    created_at=row['created_at']
                ))
            
            return categories
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo categorías: {str(e)}"
        )


@router.post(
    "/",
    response_model=CategoriaOut,
    status_code=status.HTTP_201_CREATED,
    description="Crea una nueva categoría de servicios."
)
async def create_category(
    category_in: CategoriaIn,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea una nueva categoría de servicios.
    """
    try:
        nueva_categoria = CategoriaModel(
            nombre=category_in.nombre,
            estado=category_in.estado
        )
        db.add(nueva_categoria)
        await db.commit()
        await db.refresh(nueva_categoria)

        return nueva_categoria
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la categoría: {str(e)}"
        )


@router.put(
    "/{category_id}",
    response_model=CategoriaOut,
    status_code=status.HTTP_200_OK,
    description="Actualiza una categoría existente."
)
async def update_category(
    category_id: int,
    category_update: CategoriaUpdate,
    current_admin: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza una categoría existente (solo para administradores).
    """
    try:
        # Buscar la categoría
        result = await db.execute(
            select(CategoriaModel).where(CategoriaModel.id_categoria == category_id)
        )
        categoria = result.scalars().first()

        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada."
            )

        # Actualizar solo los campos proporcionados
        if category_update.nombre is not None:
            categoria.nombre = category_update.nombre
        if category_update.estado is not None:
            categoria.estado = category_update.estado

        await db.commit()
        await db.refresh(categoria)

        return categoria
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la categoría: {str(e)}"
        )