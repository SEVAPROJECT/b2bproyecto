# backend/app/api/v1/routers/reserva_service/reserva.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.schemas.reserva_servicio.reserva import ReservaIn, ReservaOut
from app.models.reserva_servicio.reserva import ReservaModel
from app.models.servicio.service import ServicioModel
from app.models.perfil import UserModel
from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
import logging
from uuid import UUID
from typing import List, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reservas", tags=["reservas"])

@router.post(
    "/",
    response_model=ReservaOut,
    status_code=status.HTTP_201_CREATED,
    description="Permite a un usuario cliente crear una nueva reserva de servicio."
)
async def crear_reserva(
    reserva: ReservaIn,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea una nueva reserva de servicio.
    Requiere autenticación de usuario.
    """
    logger.info(f"Creando reserva para servicio {reserva.id_servicio} por usuario {current_user.id}")
    
    # Verificar que el servicio existe y está activo
    servicio_query = select(ServicioModel).where(
        and_(
            ServicioModel.id_servicio == reserva.id_servicio,
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
    
    # Crea una nueva instancia del modelo de reserva
    nueva_reserva = ReservaModel(
        id_servicio=reserva.id_servicio,
        id_usuario=UUID(current_user.id),
        descripcion=reserva.descripcion,
        observacion=reserva.observacion,
        fecha=reserva.fecha,
        estado="pendiente"
    )
    
    try:
        db.add(nueva_reserva)
        await db.commit()
        await db.refresh(nueva_reserva)
        logger.info(f"Reserva {nueva_reserva.id} creada exitosamente.")
        return nueva_reserva
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al crear la reserva: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar tu reserva."
        )

@router.get(
    "/",
    response_model=List[ReservaOut],
    description="Obtiene las reservas del usuario autenticado."
)
async def obtener_mis_reservas(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    estado: Optional[str] = Query(None, description="Filtrar por estado: pendiente, confirmada, cancelada"),
    limit: int = Query(50, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación")
):
    """
    Obtiene las reservas del usuario autenticado.
    """
    query = select(ReservaModel).where(
        ReservaModel.id_usuario == UUID(current_user.id)
    )
    
    if estado:
        query = query.where(ReservaModel.estado == estado)
    
    query = query.order_by(ReservaModel.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    reservas = result.scalars().all()
    
    return reservas

@router.get(
    "/proveedor",
    response_model=List[ReservaOut],
    description="Obtiene las reservas de los servicios del proveedor autenticado."
)
async def obtener_reservas_proveedor(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Obtiene las reservas de los servicios del proveedor autenticado.
    """
    # Obtener servicios del proveedor
    servicios_query = select(ServicioModel.id_servicio).where(
        ServicioModel.id_perfil == current_user.id
    )
    servicios_result = await db.execute(servicios_query)
    servicio_ids = [row[0] for row in servicios_result.fetchall()]
    
    if not servicio_ids:
        return []
    
    # Obtener reservas de esos servicios
    query = select(ReservaModel).where(
        ReservaModel.id_servicio.in_(servicio_ids)
    )
    
    if estado:
        query = query.where(ReservaModel.estado == estado)
    
    query = query.order_by(ReservaModel.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    reservas = result.scalars().all()
    
    return reservas

@router.put(
    "/{reserva_id}/estado",
    response_model=ReservaOut,
    description="Actualiza el estado de una reserva (solo para proveedores)."
)
async def actualizar_estado_reserva(
    reserva_id: int,
    nuevo_estado: str = Query(..., description="Nuevo estado: confirmada, cancelada"),
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza el estado de una reserva (solo para proveedores del servicio).
    """
    if nuevo_estado not in ["confirmada", "cancelada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido. Use: confirmada o cancelada"
        )
    
    # Obtener la reserva con el servicio
    query = select(ReservaModel).options(
        selectinload(ReservaModel.servicio)
    ).where(ReservaModel.id_reserva == reserva_id)
    
    result = await db.execute(query)
    reserva = result.scalar_one_or_none()
    
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada."
        )
    
    # Verificar que el usuario es el proveedor del servicio
    if reserva.servicio.id_perfil != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta reserva."
        )
    
    # Actualizar estado
    reserva.estado = nuevo_estado
    reserva.updated_at = datetime.utcnow()
    
    try:
        await db.commit()
        await db.refresh(reserva)
        logger.info(f"Estado de reserva {reserva_id} actualizado a {nuevo_estado}")
        return reserva
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al actualizar reserva: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la reserva."
        )

@router.get(
    "/{reserva_id}",
    response_model=ReservaOut,
    description="Obtiene los detalles de una reserva específica."
)
async def obtener_reserva(
    reserva_id: int,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene los detalles de una reserva específica.
    """
    query = select(ReservaModel).where(ReservaModel.id_reserva == reserva_id)
    result = await db.execute(query)
    reserva = result.scalar_one_or_none()
    
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada."
        )
    
    # Verificar permisos: usuario de la reserva o proveedor del servicio
    if reserva.id_usuario != UUID(current_user.id):
        # Verificar si es el proveedor
        servicio_query = select(ServicioModel).where(
            ServicioModel.id_servicio == reserva.id_servicio
        )
        servicio_result = await db.execute(servicio_query)
        servicio = servicio_result.scalar_one_or_none()
        
        if not servicio or servicio.id_perfil != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver esta reserva."
            )
    
    return reserva