from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.dependencies.auth_user import get_current_user, get_admin_user
from app.schemas.calificacion import (
    CalificacionClienteData, 
    CalificacionProveedorData, 
    CalificacionOut,
    CalificacionExistenteOut
)
from app.services.direct_db_service import direct_db_service
from app.services.calificacion_notification_service import calificacion_notification_service
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
                SELECT r.id_reserva, r.estado, r.user_id as cliente_id, pe.user_id as proveedor_user_id
                FROM public.reserva r
                JOIN public.servicio s ON r.id_servicio = s.id_servicio
                JOIN public.perfil_empresa pe ON s.id_perfil = pe.id_perfil
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
            
            # 5. Enviar notificación al proveedor
            try:
                # Obtener datos completos para la notificación
                notif_query = """
                    SELECT 
                        s.nombre as servicio_nombre,
                        pe.nombre_fantasia as proveedor_empresa,
                        u_prov.nombre_persona as proveedor_nombre,
                        au_prov.email as proveedor_email,
                        u_cli.nombre_persona as cliente_nombre,
                        r.fecha_reserva::date as fecha,
                        r.hora_inicio as hora
                    FROM public.reserva r
                    JOIN public.servicio s ON r.id_servicio = s.id_servicio
                    JOIN public.perfil_empresa pe ON s.id_perfil = pe.id_perfil
                    JOIN public.users u_prov ON u_prov.id = pe.user_id
                    JOIN auth.users au_prov ON au_prov.id = pe.user_id
                    JOIN public.users u_cli ON u_cli.id = r.user_id
                    WHERE r.id_reserva = $1
                """
                notif_data = await conn.fetchrow(notif_query, reserva_id)
                
                if notif_data:
                    # Formatear fecha y hora
                    fecha_formateada = notif_data['fecha'].strftime("%d/%m/%Y") if notif_data['fecha'] else "N/A"
                    hora_formateada = notif_data['hora'].strftime("%H:%M") if notif_data['hora'] else "N/A"
                    
                    calificacion_notification_service.notify_calificacion_a_proveedor(
                        reserva_id=reserva_id,
                        servicio_nombre=notif_data['servicio_nombre'],
                        proveedor_nombre=notif_data['proveedor_nombre'] or "Proveedor",
                        proveedor_email=notif_data['proveedor_email'],
                        cliente_nombre=notif_data['cliente_nombre'] or "Cliente",
                        puntaje=calificacion_data.puntaje,
                        comentario=calificacion_data.comentario,
                        nps=calificacion_data.satisfaccion_nps,
                        fecha=fecha_formateada,
                        hora=hora_formateada
                    )
                    logger.info(f"📧 Notificación de calificación enviada al proveedor")
            except Exception as e:
                logger.error(f"⚠️ Error enviando notificación al proveedor: {e}")
                # No fallar si la notificación falla
            
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
                SELECT r.id_reserva, r.estado, r.user_id as cliente_id, pe.user_id as proveedor_user_id
                FROM public.reserva r
                JOIN public.servicio s ON r.id_servicio = s.id_servicio
                JOIN public.perfil_empresa pe ON s.id_perfil = pe.id_perfil
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
            if str(reserva['proveedor_user_id']) != str(user_info['id']):
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
            
            # 5. Enviar notificación al cliente
            try:
                # Obtener datos completos para la notificación
                notif_query = """
                    SELECT 
                        s.nombre as servicio_nombre,
                        pe.nombre_fantasia as proveedor_empresa,
                        u_prov.nombre_persona as proveedor_nombre,
                        u_cli.nombre_persona as cliente_nombre,
                        au_cli.email as cliente_email,
                        r.fecha_reserva::date as fecha,
                        r.hora_inicio as hora
                    FROM public.reserva r
                    JOIN public.servicio s ON r.id_servicio = s.id_servicio
                    JOIN public.perfil_empresa pe ON s.id_perfil = pe.id_perfil
                    JOIN public.users u_prov ON u_prov.id = pe.user_id
                    JOIN public.users u_cli ON u_cli.id = r.user_id
                    JOIN auth.users au_cli ON au_cli.id = r.user_id
                    WHERE r.id_reserva = $1
                """
                notif_data = await conn.fetchrow(notif_query, reserva_id)
                
                if notif_data:
                    # Formatear fecha y hora
                    fecha_formateada = notif_data['fecha'].strftime("%d/%m/%Y") if notif_data['fecha'] else "N/A"
                    hora_formateada = notif_data['hora'].strftime("%H:%M") if notif_data['hora'] else "N/A"
                    
                    calificacion_notification_service.notify_calificacion_a_cliente(
                        reserva_id=reserva_id,
                        servicio_nombre=notif_data['servicio_nombre'],
                        cliente_nombre=notif_data['cliente_nombre'] or "Cliente",
                        cliente_email=notif_data['cliente_email'],
                        proveedor_nombre=notif_data['proveedor_nombre'] or "Proveedor",
                        proveedor_empresa=notif_data['proveedor_empresa'] or "Empresa",
                        puntaje=calificacion_data.puntaje,
                        comentario=calificacion_data.comentario,
                        fecha=fecha_formateada,
                        hora=hora_formateada
                    )
                    logger.info(f"📧 Notificación de calificación enviada al cliente")
            except Exception as e:
                logger.error(f"⚠️ Error enviando notificación al cliente: {e}")
                # No fallar si la notificación falla
            
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

# ========================================
# REPORTES DE CALIFICACIONES
# ========================================

@router.get(
    "/mis-calificaciones-recibidas-cliente",
    description="Obtiene el reporte de calificaciones recibidas por el cliente actual de proveedores"
)
async def get_mis_calificaciones_recibidas_cliente(
    user_info = Depends(get_user_with_roles)
):
    """Reporte de calificaciones recibidas por un cliente de proveedores"""
    try:
        from datetime import datetime
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Query para obtener calificaciones que el CLIENTE RECIBIÓ de PROVEEDORES
            # El cliente es quien hizo la reserva (r.user_id), y el proveedor lo calificó (rol_emisor = 'proveedor')
            calificaciones_query = """
                SELECT
                    c.fecha::date AS fecha,
                    s.nombre AS servicio,
                    pe.nombre_fantasia AS proveedor_empresa,
                    u_prov.nombre_persona AS proveedor_persona,
                    c.puntaje AS puntaje,
                    LEFT(COALESCE(c.comentario, ''), 120) AS comentario
                FROM public.calificacion c
                JOIN public.reserva r ON r.id_reserva = c.id_reserva
                JOIN public.servicio s ON s.id_servicio = r.id_servicio
                JOIN public.perfil_empresa pe ON pe.id_perfil = s.id_perfil
                JOIN public.users u_prov ON u_prov.id = pe.user_id
                WHERE c.rol_emisor = 'proveedor' AND r.user_id = $1
                ORDER BY c.fecha DESC
            """
            
            calificaciones_data = await conn.fetch(calificaciones_query, user_info['id'])
            
            calificaciones_detalladas = []
            for row in calificaciones_data:
                # Formatear fecha a DD/MM/YYYY
                fecha_formateada = None
                if row['fecha']:
                    fecha_formateada = row['fecha'].strftime("%d/%m/%Y")
                
                calificaciones_detalladas.append({
                    "fecha": fecha_formateada,
                    "servicio": row['servicio'],
                    "proveedor_empresa": row['proveedor_empresa'],
                    "proveedor_persona": row['proveedor_persona'],
                    "puntaje": row['puntaje'],
                    "comentario": row['comentario'] if row['comentario'] else "Sin comentario"
                })
        
        finally:
            await direct_db_service.pool.release(conn)

        return {
            "total_calificaciones": len(calificaciones_detalladas),
            "calificaciones": calificaciones_detalladas,
            "fecha_generacion": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Error generando reporte de calificaciones recibidas del cliente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando reporte de calificaciones"
        )

@router.get(
    "/mis-calificaciones-recibidas-proveedor",
    description="Obtiene el reporte de calificaciones recibidas por el proveedor actual de clientes"
)
async def get_mis_calificaciones_recibidas_proveedor(
    user_info = Depends(get_user_with_roles)
):
    """Reporte de calificaciones recibidas por un proveedor de clientes"""
    try:
        from datetime import datetime
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Query para obtener calificaciones que el PROVEEDOR RECIBIÓ de CLIENTES
            # El proveedor es dueño del servicio (pe.user_id), y el cliente lo calificó (rol_emisor = 'cliente')
            calificaciones_query = """
                SELECT
                    c.fecha::date AS fecha,
                    s.nombre AS servicio,
                    u_cli.nombre_persona AS cliente_persona,
                    u_cli.nombre_empresa AS cliente_empresa,
                    c.puntaje AS puntaje,
                    c.satisfaccion_nps AS nps,
                    LEFT(COALESCE(c.comentario, ''), 120) AS comentario
                FROM public.calificacion c
                JOIN public.reserva r ON r.id_reserva = c.id_reserva
                JOIN public.servicio s ON s.id_servicio = r.id_servicio
                JOIN public.perfil_empresa pe ON pe.id_perfil = s.id_perfil
                JOIN public.users u_cli ON u_cli.id = r.user_id
                WHERE c.rol_emisor = 'cliente' AND pe.user_id = $1
                ORDER BY c.fecha DESC
            """
            
            calificaciones_data = await conn.fetch(calificaciones_query, user_info['id'])
            
            calificaciones_detalladas = []
            for row in calificaciones_data:
                # Formatear fecha a DD/MM/YYYY
                fecha_formateada = None
                if row['fecha']:
                    fecha_formateada = row['fecha'].strftime("%d/%m/%Y")
                
                calificaciones_detalladas.append({
                    "fecha": fecha_formateada,
                    "servicio": row['servicio'],
                    "cliente_persona": row['cliente_persona'],
                    "cliente_empresa": row['cliente_empresa'] if row['cliente_empresa'] else "N/A",
                    "puntaje": row['puntaje'],
                    "nps": row['nps'] if row['nps'] else "N/A",
                    "comentario": row['comentario'] if row['comentario'] else "Sin comentario"
                })
        
        finally:
            await direct_db_service.pool.release(conn)

        return {
            "total_calificaciones": len(calificaciones_detalladas),
            "calificaciones": calificaciones_detalladas,
            "fecha_generacion": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Error generando reporte de calificaciones recibidas del proveedor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando reporte de calificaciones"
        )
