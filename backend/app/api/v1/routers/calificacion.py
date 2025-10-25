from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.dependencies.auth_user import get_current_user, get_admin_user
from app.schemas.calificacion import (
    CalificacionClienteData, 
    CalificacionProveedorData, 
    CalificacionOut,
    CalificacionExistenteOut
)
from app.services.direct_db_service import direct_db_service
from gotrue.types import User
from app.schemas.auth_user import SupabaseUser
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_user_with_roles(current_user: SupabaseUser = Depends(get_current_user)):
    """
    Obtiene el perfil del usuario con sus roles para determinar si es cliente o proveedor.
    """
    try:
        logger.info(f"🔍 [get_user_with_roles] Iniciando para usuario: {current_user.id}")
        user_uuid = str(current_user.id)
        logger.info(f"🔍 [get_user_with_roles] UUID convertido: {user_uuid}")
        
        user_data = await direct_db_service.get_user_profile_with_roles(user_uuid)
        logger.info(f"🔍 [get_user_with_roles] Datos obtenidos: {user_data is not None}")
        
        if not user_data:
            logger.error(f"❌ [get_user_with_roles] Perfil no encontrado para: {user_uuid}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Perfil de usuario no encontrado"
            )
        
        # Extraer los nombres de los roles
        roles_data = user_data.get('roles', [])
        logger.info(f"🔍 [get_user_with_roles] Roles data: {roles_data}")
        roles_nombres = [rol.get('nombre') for rol in roles_data if rol.get('nombre')]
        logger.info(f"🔍 [get_user_with_roles] Roles nombres: {roles_nombres}")
        roles_lower = [rol.lower() for rol in roles_nombres]
        logger.info(f"🔍 [get_user_with_roles] Roles lower: {roles_lower}")
        
        # Determinar si es proveedor
        is_provider = any(rol in ['provider', 'proveedor', 'proveedores'] for rol in roles_lower)
        logger.info(f"🔍 [get_user_with_roles] Es proveedor: {is_provider}")
        
        result = {
            'id': user_data['id'],
            'email': current_user.email,
            'roles': roles_nombres,
            'is_provider': is_provider
        }
        logger.info(f"🔍 [get_user_with_roles] Resultado: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [get_user_with_roles] Error al obtener perfil del usuario: {e}")
        logger.error(f"❌ [get_user_with_roles] Tipo de error: {type(e)}")
        import traceback
        logger.error(f"❌ [get_user_with_roles] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener información del usuario"
        )

@router.post("/cliente/{reserva_id}", response_model=CalificacionOut)
async def calificar_como_cliente(
    reserva_id: int,
    calificacion_data: CalificacionClienteData,
    user_info = Depends(get_user_with_roles)
):
    """
    Calificar servicio como cliente (con NPS)
    """
    try:
        logger.info(f"🔍 [POST /calificacion/cliente/{reserva_id}] Iniciando calificación de cliente")
        logger.info(f"🔍 Usuario: {user_info['id']}, Es proveedor: {user_info['is_provider']}")
        logger.info(f"🔍 Datos de calificación: {calificacion_data}")
        
        conn = await direct_db_service.get_connection()
        try:
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
            if str(reserva['cliente_id']) != str(user_info['id']):
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
                user_info['id']
            )
            
            logger.info(f"✅ Calificación de cliente creada: {result['id_calificacion']}")
            
            return CalificacionOut(
                id_calificacion=result['id_calificacion'],
                id_reserva=reserva_id,
                puntaje=calificacion_data.puntaje,
                comentario=calificacion_data.comentario,
                fecha=result['fecha'],
                rol_emisor='cliente',
                usuario_id=str(user_info['id']),
                satisfaccion_nps=calificacion_data.satisfaccion_nps
            )
        finally:
            await direct_db_service.pool.release(conn)
            
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
    user_info = Depends(get_user_with_roles)
):
    """
    Calificar cliente como proveedor (sin NPS)
    """
    try:
        logger.info(f"🔍 [POST /calificacion/proveedor/{reserva_id}] Iniciando calificación de proveedor")
        logger.info(f"🔍 Usuario: {user_info['id']}, Es proveedor: {user_info['is_provider']}")
        
        conn = await direct_db_service.get_connection()
        try:
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
            if str(reserva['id_proveedor']) != str(user_info['id']):
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
                user_info['id']
            )
            
            logger.info(f"✅ Calificación de proveedor creada: {result['id_calificacion']}")
            
            return CalificacionOut(
                id_calificacion=result['id_calificacion'],
                id_reserva=reserva_id,
                puntaje=calificacion_data.puntaje,
                comentario=calificacion_data.comentario,
                fecha=result['fecha'],
                rol_emisor='proveedor',
                usuario_id=str(user_info['id']),
                satisfaccion_nps=None
            )
        finally:
            await direct_db_service.pool.release(conn)
            
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
    user_info = Depends(get_user_with_roles)
):
    """
    Verificar si ya existe calificación para una reserva por el usuario actual
    """
    try:
        logger.info(f"🔍 [GET /calificacion/verificar/{reserva_id}] Verificando calificación existente")
        
        conn = await direct_db_service.get_connection()
        try:
            # Determinar rol del usuario
            rol_emisor = 'proveedor' if user_info['is_provider'] else 'cliente'
            
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
                        usuario_id=str(user_info['id']),
                        satisfaccion_nps=calificacion['satisfaccion_nps']
                    )
                )
            else:
                return CalificacionExistenteOut(existe=False)
        finally:
            await direct_db_service.pool.release(conn)
                
    except Exception as e:
        logger.error(f"❌ Error al verificar calificación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )
