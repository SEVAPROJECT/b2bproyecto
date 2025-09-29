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
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Crea una nueva reserva de servicio usando direct_db_service.
    Requiere autenticación de usuario.
    """
    logger.info(f"🔍 [POST /reservas] ========== INICIO CREAR RESERVA ==========")
    logger.info(f"🔍 [POST /reservas] User ID: {current_user.id}")
    logger.info(f"🔍 [POST /reservas] User email: {getattr(current_user, 'email', 'N/A')}")
    logger.info(f"🔍 [POST /reservas] Datos completos de reserva: {reserva.dict()}")
    logger.info(f"🔍 [POST /reservas] Tipo de id_servicio: {type(reserva.id_servicio)}")
    logger.info(f"🔍 [POST /reservas] Valor de id_servicio: {reserva.id_servicio}")
    logger.info(f"🔍 [POST /reservas] Fecha de reserva: {reserva.fecha}")
    logger.info(f"🔍 [POST /reservas] Descripción: {reserva.descripcion}")
    logger.info(f"🔍 [POST /reservas] Observación: {reserva.observacion}")
    
    try:
        from app.services.direct_db_service import direct_db_service
        
        # Helper para obtener conexión
        logger.info("🔍 [POST /reservas] Obteniendo conexión de direct_db_service...")
        conn = await direct_db_service.get_connection()
        logger.info("✅ [POST /reservas] Conexión obtenida exitosamente")
        
        try:
            # 1. Verificar que el servicio existe y está activo
            logger.info(f"🔍 [POST /reservas] Verificando servicio {reserva.id_servicio}...")
            logger.info(f"🔍 [POST /reservas] Query de verificación preparado")
            servicio_query = """
                SELECT s.id_servicio, s.id_perfil, s.estado, s.nombre
                FROM servicio s
                WHERE s.id_servicio = $1 AND s.estado = true
            """
            logger.info(f"🔍 [POST /reservas] Ejecutando query con parámetro: {reserva.id_servicio}")
            servicio_result = await conn.fetchrow(servicio_query, reserva.id_servicio)
            logger.info(f"🔍 [POST /reservas] Query ejecutado exitosamente")
            logger.info(f"🔍 [POST /reservas] Servicio encontrado: {servicio_result}")
            logger.info(f"🔍 [POST /reservas] Tipo de resultado: {type(servicio_result)}")
            
            if not servicio_result:
                logger.warning(f"❌ [POST /reservas] Servicio {reserva.id_servicio} no encontrado")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Servicio no encontrado o no disponible."
                )
            # 2. Crear nueva reserva usando direct_db_service
            logger.info("🔍 [POST /reservas] Creando nueva reserva en base de datos...")
            
            # Generar nuevo UUID para la reserva
            import uuid
            reserva_id = uuid.uuid4()
            
            # Convertir id_servicio si viene como string
            logger.info(f"🔍 [POST /reservas] Convirtiendo id_servicio: {reserva.id_servicio} (tipo: {type(reserva.id_servicio)})")
            try:
                servicio_id = int(reserva.id_servicio)
                logger.info(f"✅ [POST /reservas] ID convertido exitosamente: {servicio_id}")
            except (ValueError, TypeError) as e:
                logger.error(f"❌ [POST /reservas] Error al convertir ID de servicio: {e}")
                logger.error(f"❌ [POST /reservas] ID de servicio inválido: {reserva.id_servicio}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID de servicio inválido"
                )
            
            # Para la nueva arquitectura, necesitamos hora_inicio y hora_fin
            # Como el frontend no las envía aún, usaremos valores por defecto
            from datetime import time
            hora_inicio_default = time(9, 0)  # 9:00 AM
            hora_fin_default = time(10, 0)    # 10:00 AM (1 hora de duración)
            logger.info(f"🔍 [POST /reservas] Horarios por defecto: {hora_inicio_default} - {hora_fin_default}")
            
            # Preparar parámetros para la inserción
            user_uuid = UUID(current_user.id)
            logger.info(f"🔍 [POST /reservas] UUID del usuario: {user_uuid}")
            logger.info(f"🔍 [POST /reservas] UUID de reserva generado: {reserva_id}")
            
            insert_query = """
                INSERT INTO reserva (id, id_servicio, id_usuario, descripcion, observacion, fecha, hora_inicio, hora_fin, estado)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, id_servicio, id_usuario, descripcion, observacion, fecha, hora_inicio, hora_fin, estado
            """
            logger.info(f"🔍 [POST /reservas] Query de inserción preparado")
            logger.info(f"🔍 [POST /reservas] Parámetros de inserción:")
            logger.info(f"  - id: {reserva_id}")
            logger.info(f"  - id_servicio: {servicio_id}")
            logger.info(f"  - id_usuario: {user_uuid}")
            logger.info(f"  - descripcion: {reserva.descripcion}")
            logger.info(f"  - observacion: {reserva.observacion}")
            logger.info(f"  - fecha: {reserva.fecha}")
            logger.info(f"  - hora_inicio: {hora_inicio_default}")
            logger.info(f"  - hora_fin: {hora_fin_default}")
            logger.info(f"  - estado: pendiente")
            
            logger.info(f"🔍 [POST /reservas] Ejecutando inserción...")
            nueva_reserva = await conn.fetchrow(
                insert_query,
                reserva_id,
                servicio_id,
                user_uuid,
                reserva.descripcion,
                reserva.observacion,
                reserva.fecha,
                hora_inicio_default,
                hora_fin_default,
                "pendiente"
            )
            logger.info(f"🔍 [POST /reservas] Inserción ejecutada")
            logger.info(f"🔍 [POST /reservas] Reserva creada: {nueva_reserva}")
            
            logger.info(f"✅ [POST /reservas] Reserva {nueva_reserva['id']} creada exitosamente")
            
            # Convertir a formato de respuesta
            logger.info(f"🔍 [POST /reservas] Preparando respuesta...")
            respuesta = {
                "id": nueva_reserva['id'],
                "id_servicio": nueva_reserva['id_servicio'],
                "id_usuario": nueva_reserva['id_usuario'],
                "descripcion": nueva_reserva['descripcion'],
                "observacion": nueva_reserva['observacion'],
                "fecha": nueva_reserva['fecha'],
                "estado": nueva_reserva['estado'],
                "id_disponibilidad": None  # Compatibilidad con schema anterior
            }
            logger.info(f"🔍 [POST /reservas] Respuesta preparada: {respuesta}")
            logger.info(f"🔍 [POST /reservas] ========== FIN CREAR RESERVA EXITOSO ==========")
            return respuesta
            
        finally:
            logger.info(f"🔍 [POST /reservas] Liberando conexión...")
            await direct_db_service.pool.release(conn)
            logger.info(f"🔍 [POST /reservas] Conexión liberada")
        
    except HTTPException as he:
        logger.error(f"❌ [POST /reservas] HTTPException capturada: {he.status_code} - {he.detail}")
        logger.error(f"❌ [POST /reservas] ========== FIN CREAR RESERVA CON ERROR HTTP ==========")
        raise
    except Exception as e:
        logger.error(f"❌ [POST /reservas] ========== ERROR CRÍTICO EN CREAR RESERVA ==========")
        logger.error(f"❌ [POST /reservas] Error crítico: {str(e)}")
        logger.error(f"❌ [POST /reservas] Tipo de error: {type(e).__name__}")
        logger.error(f"❌ [POST /reservas] Módulo del error: {getattr(e, '__module__', 'N/A')}")
        import traceback
        logger.error(f"❌ [POST /reservas] Traceback completo: {traceback.format_exc()}")
        logger.error(f"❌ [POST /reservas] ========== FIN CREAR RESERVA CON ERROR ==========")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al crear reserva: {str(e)}"
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