from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.calificacion import (
    CalificacionClienteData, 
    CalificacionProveedorData, 
    CalificacionOut,
    CalificacionExistenteOut
)
from app.services.direct_db_service import direct_db_service
from gotrue.types import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/cliente/{reserva_id}", response_model=CalificacionOut)
async def calificar_como_cliente(
    reserva_id: int,
    calificacion_data: CalificacionClienteData,
    current_user: User = Depends(get_current_user)
):
    """
    Calificar servicio como cliente (con NPS)
    """
    try:
        logger.info(f"🔍 [POST /calificacion/cliente/{reserva_id}] Iniciando calificación de cliente")
        logger.info(f"🔍 Usuario: {current_user.id}, Rol: {current_user.role}")
        
        async with direct_db_service.get_connection() as conn:
            # 1. Verificar que la reserva existe y está completada
            reserva_query = """
                SELECT r.id_reserva, r.estado, r.user_id as cliente_id, s.id_proveedor
                FROM public.reserva r
                JOIN public.servicio s ON r.id_servicio = s.id_servicio
                WHERE r.id_reserva = $1
            """
            reserva = await conn.fetchrow(reserva_query, reserva_id)
            
            if not reserva:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reserva no encontrada"
                )
            
            if reserva['estado'] != 'completada':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No es posible calificar en el estado actual."
                )
            
            # 2. Verificar que el usuario es el cliente de la reserva
            if str(reserva['cliente_id']) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No autorizado para calificar esta reserva."
                )
            
            # 3. Verificar que no existe calificación previa del cliente
            calificacion_existente_query = """
                SELECT id_calificacion FROM public.calificacion 
                WHERE id_reserva = $1 AND rol_emisor = 'cliente'
            """
            calificacion_existente = await conn.fetchrow(calificacion_existente_query, reserva_id)
            
            if calificacion_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya enviaste tu calificación para este servicio."
                )
            
            # 4. Insertar calificación
            insert_query = """
                INSERT INTO public.calificacion 
                (id_reserva, puntaje, comentario, satisfaccion_nps, rol_emisor, usuario_id)
                VALUES ($1, $2, $3, $4, 'cliente', $5)
                RETURNING id_calificacion, fecha
            """
            
            result = await conn.fetchrow(
                insert_query,
                reserva_id,
                calificacion_data.puntaje,
                calificacion_data.comentario,
                calificacion_data.satisfaccion_nps,
                current_user.id
            )
            
            logger.info(f"✅ Calificación de cliente creada: {result['id_calificacion']}")
            
            return CalificacionOut(
                id_calificacion=result['id_calificacion'],
                id_reserva=reserva_id,
                puntaje=calificacion_data.puntaje,
                comentario=calificacion_data.comentario,
                fecha=result['fecha'],
                rol_emisor='cliente',
                usuario_id=str(current_user.id),
                satisfaccion_nps=calificacion_data.satisfaccion_nps
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al calificar como cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/proveedor/{reserva_id}", response_model=CalificacionOut)
async def calificar_como_proveedor(
    reserva_id: int,
    calificacion_data: CalificacionProveedorData,
    current_user: User = Depends(get_current_user)
):
    """
    Calificar cliente como proveedor (sin NPS)
    """
    try:
        logger.info(f"🔍 [POST /calificacion/proveedor/{reserva_id}] Iniciando calificación de proveedor")
        logger.info(f"🔍 Usuario: {current_user.id}, Rol: {current_user.role}")
        
        async with direct_db_service.get_connection() as conn:
            # 1. Verificar que la reserva existe y está completada
            reserva_query = """
                SELECT r.id_reserva, r.estado, r.user_id as cliente_id, s.id_proveedor
                FROM public.reserva r
                JOIN public.servicio s ON r.id_servicio = s.id_servicio
                WHERE r.id_reserva = $1
            """
            reserva = await conn.fetchrow(reserva_query, reserva_id)
            
            if not reserva:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reserva no encontrada"
                )
            
            if reserva['estado'] != 'completada':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No es posible calificar en el estado actual."
                )
            
            # 2. Verificar que el usuario es el proveedor del servicio
            if str(reserva['id_proveedor']) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No autorizado para calificar esta reserva."
                )
            
            # 3. Verificar que no existe calificación previa del proveedor
            calificacion_existente_query = """
                SELECT id_calificacion FROM public.calificacion 
                WHERE id_reserva = $1 AND rol_emisor = 'proveedor'
            """
            calificacion_existente = await conn.fetchrow(calificacion_existente_query, reserva_id)
            
            if calificacion_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya enviaste tu calificación para este servicio."
                )
            
            # 4. Insertar calificación
            insert_query = """
                INSERT INTO public.calificacion 
                (id_reserva, puntaje, comentario, satisfaccion_nps, rol_emisor, usuario_id)
                VALUES ($1, $2, $3, NULL, 'proveedor', $4)
                RETURNING id_calificacion, fecha
            """
            
            result = await conn.fetchrow(
                insert_query,
                reserva_id,
                calificacion_data.puntaje,
                calificacion_data.comentario,
                current_user.id
            )
            
            logger.info(f"✅ Calificación de proveedor creada: {result['id_calificacion']}")
            
            return CalificacionOut(
                id_calificacion=result['id_calificacion'],
                id_reserva=reserva_id,
                puntaje=calificacion_data.puntaje,
                comentario=calificacion_data.comentario,
                fecha=result['fecha'],
                rol_emisor='proveedor',
                usuario_id=str(current_user.id),
                satisfaccion_nps=None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al calificar como proveedor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get("/verificar/{reserva_id}", response_model=CalificacionExistenteOut)
async def verificar_calificacion_existente(
    reserva_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Verificar si ya existe calificación para una reserva por el usuario actual
    """
    try:
        logger.info(f"🔍 [GET /calificacion/verificar/{reserva_id}] Verificando calificación existente")
        
        async with direct_db_service.get_connection() as conn:
            # Determinar rol del usuario
            rol_emisor = 'cliente' if current_user.role != 'provider' else 'proveedor'
            
            # Buscar calificación existente
            calificacion_query = """
                SELECT id_calificacion, puntaje, comentario, fecha, satisfaccion_nps
                FROM public.calificacion 
                WHERE id_reserva = $1 AND rol_emisor = $2
            """
            calificacion = await conn.fetchrow(calificacion_query, reserva_id, rol_emisor)
            
            if calificacion:
                return CalificacionExistenteOut(
                    existe=True,
                    calificacion=CalificacionOut(
                        id_calificacion=calificacion['id_calificacion'],
                        id_reserva=reserva_id,
                        puntaje=calificacion['puntaje'],
                        comentario=calificacion['comentario'],
                        fecha=calificacion['fecha'],
                        rol_emisor=rol_emisor,
                        usuario_id=str(current_user.id),
                        satisfaccion_nps=calificacion['satisfaccion_nps']
                    )
                )
            else:
                return CalificacionExistenteOut(existe=False)
                
    except Exception as e:
        logger.error(f"❌ Error al verificar calificación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )
