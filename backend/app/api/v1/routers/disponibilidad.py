# backend/app/api/v1/routers/disponibilidad.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.schemas.disponibilidad import DisponibilidadIn, DisponibilidadOut, DisponibilidadUpdate
from app.models.disponibilidad import DisponibilidadModel
from app.models.servicio.service import ServicioModel
from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
import logging
from typing import List, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disponibilidades", tags=["disponibilidades"])

@router.post(
    "/",
    response_model=DisponibilidadOut,
    status_code=status.HTTP_201_CREATED,
    description="Crea una nueva disponibilidad para un servicio (solo proveedores)."
)
async def crear_disponibilidad(
    disponibilidad: DisponibilidadIn,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea una nueva disponibilidad para un servicio.
    Solo el proveedor del servicio puede crear disponibilidades.
    """
    logger.info(f"Creando disponibilidad para servicio {disponibilidad.id_servicio} por usuario {current_user.id}")
    
    # Verificar que el servicio existe y pertenece al usuario
    servicio_query = select(ServicioModel).where(
        and_(
            ServicioModel.id_servicio == disponibilidad.id_servicio,
            ServicioModel.id_perfil == current_user.id,
            ServicioModel.estado == True
        )
    )
    servicio_result = await db.execute(servicio_query)
    servicio = servicio_result.scalar_one_or_none()
    
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no tienes permisos para gestionarlo."
        )
    
    # Verificar que no hay solapamiento de horarios
    solapamiento_query = select(DisponibilidadModel).where(
        and_(
            DisponibilidadModel.id_servicio == disponibilidad.id_servicio,
            DisponibilidadModel.disponible == True,
            or_(
                and_(
                    DisponibilidadModel.fecha_inicio <= disponibilidad.fecha_inicio,
                    DisponibilidadModel.fecha_fin > disponibilidad.fecha_inicio
                ),
                and_(
                    DisponibilidadModel.fecha_inicio < disponibilidad.fecha_fin,
                    DisponibilidadModel.fecha_fin >= disponibilidad.fecha_fin
                ),
                and_(
                    DisponibilidadModel.fecha_inicio >= disponibilidad.fecha_inicio,
                    DisponibilidadModel.fecha_fin <= disponibilidad.fecha_fin
                )
            )
        )
    )
    solapamiento_result = await db.execute(solapamiento_query)
    solapamiento = solapamiento_result.scalar_one_or_none()
    
    if solapamiento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una disponibilidad en ese horario."
        )
    
    # Crear nueva disponibilidad
    nueva_disponibilidad = DisponibilidadModel(
        id_servicio=disponibilidad.id_servicio,
        fecha_inicio=disponibilidad.fecha_inicio,
        fecha_fin=disponibilidad.fecha_fin,
        disponible=disponibilidad.disponible,
        precio_adicional=disponibilidad.precio_adicional or 0,
        observaciones=disponibilidad.observaciones
    )
    
    try:
        db.add(nueva_disponibilidad)
        await db.commit()
        await db.refresh(nueva_disponibilidad)
        logger.info(f"Disponibilidad {nueva_disponibilidad.id_disponibilidad} creada exitosamente.")
        return nueva_disponibilidad
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al crear la disponibilidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar la disponibilidad."
        )

@router.get(
    "/",
    response_model=List[DisponibilidadOut],
    description="Obtiene las disponibilidades de los servicios del proveedor autenticado."
)
async def obtener_mis_disponibilidades(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    id_servicio: Optional[int] = Query(None, description="Filtrar por servicio específico"),
    disponible: Optional[bool] = Query(None, description="Filtrar por disponibilidad"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Obtiene las disponibilidades de los servicios del proveedor autenticado.
    """
    # Obtener servicios del proveedor
    servicios_query = select(ServicioModel.id_servicio).where(
        ServicioModel.id_perfil == current_user.id
    )
    servicios_result = await db.execute(servicios_query)
    servicio_ids = [row[0] for row in servicios_result.fetchall()]
    
    if not servicio_ids:
        return []
    
    # Filtrar por servicio específico si se proporciona
    if id_servicio:
        if id_servicio not in servicio_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver disponibilidades de este servicio."
            )
        servicio_ids = [id_servicio]
    
    # Obtener disponibilidades
    query = select(DisponibilidadModel).where(
        DisponibilidadModel.id_servicio.in_(servicio_ids)
    )
    
    if disponible is not None:
        query = query.where(DisponibilidadModel.disponible == disponible)
    
    query = query.order_by(DisponibilidadModel.fecha_inicio.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    disponibilidades = result.scalars().all()
    
    return disponibilidades

@router.get(
    "/servicio/{servicio_id}",
    response_model=List[DisponibilidadOut],
    description="Obtiene las disponibilidades de un servicio específico (público)."
)
async def obtener_disponibilidades_servicio(
    servicio_id: int,
    db: AsyncSession = Depends(get_async_db),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Obtiene las disponibilidades de un servicio específico (público).
    """
    # Verificar que el servicio existe y está activo
    servicio_query = select(ServicioModel).where(
        and_(
            ServicioModel.id_servicio == servicio_id,
            ServicioModel.estado == True
        )
    )
    servicio_result = await db.execute(servicio_query)
    servicio = servicio_result.scalar_one_or_none()
    
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no disponible."
        )
    
    # Obtener disponibilidades
    query = select(DisponibilidadModel).where(
        and_(
            DisponibilidadModel.id_servicio == servicio_id,
            DisponibilidadModel.disponible == True
        )
    )
    
    if fecha_desde:
        query = query.where(DisponibilidadModel.fecha_inicio >= fecha_desde)
    
    if fecha_hasta:
        query = query.where(DisponibilidadModel.fecha_fin <= fecha_hasta)
    
    query = query.order_by(DisponibilidadModel.fecha_inicio.asc()).limit(limit)
    
    result = await db.execute(query)
    disponibilidades = result.scalars().all()
    
    return disponibilidades

@router.put(
    "/{disponibilidad_id}",
    response_model=DisponibilidadOut,
    description="Actualiza una disponibilidad existente (solo proveedores)."
)
async def actualizar_disponibilidad(
    disponibilidad_id: int,
    disponibilidad_update: DisponibilidadUpdate,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza una disponibilidad existente.
    Solo el proveedor del servicio puede actualizar disponibilidades.
    """
    # Obtener la disponibilidad con el servicio
    query = select(DisponibilidadModel).options(
        selectinload(DisponibilidadModel.servicio)
    ).where(DisponibilidadModel.id_disponibilidad == disponibilidad_id)
    
    result = await db.execute(query)
    disponibilidad = result.scalar_one_or_none()
    
    if not disponibilidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disponibilidad no encontrada."
        )
    
    # Verificar que el usuario es el proveedor del servicio
    if disponibilidad.servicio.id_perfil != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta disponibilidad."
        )
    
    # Actualizar campos proporcionados
    update_data = disponibilidad_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(disponibilidad, field, value)
    
    disponibilidad.updated_at = datetime.utcnow()
    
    try:
        await db.commit()
        await db.refresh(disponibilidad)
        logger.info(f"Disponibilidad {disponibilidad_id} actualizada exitosamente.")
        return disponibilidad
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al actualizar disponibilidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la disponibilidad."
        )

@router.delete(
    "/{disponibilidad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Elimina una disponibilidad (solo proveedores)."
)
async def eliminar_disponibilidad(
    disponibilidad_id: int,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Elimina una disponibilidad.
    Solo el proveedor del servicio puede eliminar disponibilidades.
    """
    # Obtener la disponibilidad con el servicio
    query = select(DisponibilidadModel).options(
        selectinload(DisponibilidadModel.servicio)
    ).where(DisponibilidadModel.id_disponibilidad == disponibilidad_id)
    
    result = await db.execute(query)
    disponibilidad = result.scalar_one_or_none()
    
    if not disponibilidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disponibilidad no encontrada."
        )
    
    # Verificar que el usuario es el proveedor del servicio
    if disponibilidad.servicio.id_perfil != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta disponibilidad."
        )
    
    try:
        await db.delete(disponibilidad)
        await db.commit()
        logger.info(f"Disponibilidad {disponibilidad_id} eliminada exitosamente.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al eliminar disponibilidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar la disponibilidad."
        )

@router.get(
    "/servicio/{servicio_id}/disponibles",
    response_model=List[DisponibilidadOut],
    summary="Obtener disponibilidades disponibles de un servicio",
    description="Obtiene solo las disponibilidades disponibles (disponible=true) de un servicio específico"
)
async def obtener_disponibilidades_disponibles_servicio(
    servicio_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Obtiene solo las disponibilidades disponibles de un servicio específico.
    """
    try:
        # Verificar que el servicio existe
        servicio_stmt = select(ServicioModel).where(ServicioModel.id_servicio == servicio_id)
        servicio_result = await db.execute(servicio_stmt)
        servicio = servicio_result.scalar_one_or_none()
        
        if not servicio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servicio no encontrado"
            )
        
        # Obtener solo disponibilidades disponibles del servicio
        stmt = select(DisponibilidadModel).where(
            and_(
                DisponibilidadModel.id_servicio == servicio_id,
                DisponibilidadModel.disponible == True
            )
        ).order_by(DisponibilidadModel.fecha_inicio)
        
        result = await db.execute(stmt)
        disponibilidades = result.scalars().all()
        
        logger.info(f"Disponibilidades disponibles obtenidas para servicio {servicio_id}: {len(disponibilidades)}")
        
        return disponibilidades
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener disponibilidades disponibles del servicio {servicio_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )
