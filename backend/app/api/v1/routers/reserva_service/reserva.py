# backend/app/api/v1/routers/reserva_service/reserva.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.reserva_servicio.reserva import ReservaIn, ReservaOut, ReservaEstadoUpdate, ReservaCancelacionData
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
import logging
import traceback
import uuid
from typing import Optional
from datetime import datetime, time, timedelta, date
from app.services.direct_db_service import direct_db_service
from app.services.reserva_notification_service import reserva_notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reservas", tags=["reservas"])

# Constantes para estados de reserva
ESTADO_PENDIENTE = "pendiente"
ESTADO_CONFIRMADA = "confirmada"
ESTADO_CANCELADA = "cancelada"
ESTADO_COMPLETADA = "completada"

# Constantes para valores por defecto
HORA_INICIO_DEFAULT = "09:00"

# Constantes para formatos
FORMATO_FECHA_DD_MM_YYYY = "%d/%m/%Y"

# Constantes para SQL
SQL_AND = " AND "

# Constantes para mensajes de error
MSG_SERVICIO_NO_ENCONTRADO = "Servicio no encontrado o no disponible."
MSG_ID_SERVICIO_INVALIDO = "ID de servicio inválido"
MSG_RESERVA_NO_ENCONTRADA = "Reserva no encontrada"
MSG_NO_PERMISOS_CAMBIAR_ESTADO = "No tienes permisos para cambiar el estado de esta reserva"
MSG_NO_PERMISOS_VER_HISTORIAL = "No tienes permisos para ver el historial de esta reserva"
MSG_NO_AUTORIZADO_GESTIONAR = "No autorizado para gestionar esta reserva"
MSG_NO_PERFIL_PROVEEDOR = "No tienes un perfil de proveedor verificado."
MSG_ERROR_ACTUALIZAR_ESTADO = "Error al actualizar el estado de la reserva"
MSG_ERROR_CANCELAR_RESERVA = "Error al cancelar la reserva"
MSG_ERROR_CONFIRMAR_RESERVA = "Error al confirmar la reserva"
MSG_ERROR_INTERNO_CREAR_RESERVA = "Error interno del servidor al crear reserva: {error}"
MSG_ERROR_INTERNO_OBTENER_RESERVAS = "Error interno del servidor al obtener reservas: {error}"
MSG_ERROR_INTERNO_OBTENER_RESERVAS_PROVEEDOR = "Error interno del servidor al obtener reservas del proveedor: {error}"
MSG_ERROR_ACTUALIZAR_ESTADO_FORMAT = "Error al actualizar el estado de la reserva: {error}"
MSG_ERROR_CANCELAR_RESERVA_FORMAT = "Error al cancelar la reserva: {error}"
MSG_ERROR_CONFIRMAR_RESERVA_FORMAT = "Error al confirmar la reserva: {error}"
MSG_ERROR_TEST = "Error en test: {error}"
MSG_ERROR_DIAGNOSTICO = "Error en diagnóstico: {error}"
MSG_ERROR_OBTENER_HISTORIAL = "Error al obtener historial: {error}"
MSG_ESTADO_INVALIDO = "Estado inválido. Los estados válidos son: {estados}"
MSG_RESERVA_YA_EN_ESTADO = "La reserva ya está en estado '{estado}'"
MSG_SOLO_CANCELAR_PENDIENTE = "Solo se pueden cancelar reservas en estado 'pendiente'. Estado actual: '{estado}'"
MSG_DEBE_INGRESAR_MOTIVO = "Debés ingresar un motivo para cancelar la reserva"
MSG_NO_POSIBLE_ACCION_ESTADO = "No es posible realizar esta acción en el estado actual"

# Constantes para mensajes de notificación
MSG_NOTIF_APROBADO = "Tu reserva ha sido aprobada"
MSG_NOTIF_RECHAZADO = "Tu reserva ha sido rechazada"
MSG_NOTIF_CONCLUIDO = "Tu servicio ha sido completado"
MSG_NOTIF_ESTADO_CAMBIADO = "El estado de tu reserva ha cambiado a {estado}"

@router.get(
    "/mis-reservas-test",
    description="Endpoint de prueba simplificado para diagnosticar el error 422."
)
async def obtener_mis_reservas_test(
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Endpoint de prueba simplificado para diagnosticar problemas.
    """
    try:
        conn = await direct_db_service.get_connection()
        
        simple_query = """
            SELECT 
                r.id_reserva,
                r.id_servicio,
                r.user_id,
                r.descripcion,
                r.observacion,
                r.fecha,
                r.hora_inicio,
                r.hora_fin,
                r.estado,
                r.created_at,
                s.nombre as nombre_servicio,
                s.descripcion as descripcion_servicio,
                s.precio as precio_servicio,
                s.imagen as imagen_servicio,
                s.id_perfil,
                pe.nombre_fantasia as nombre_empresa,
                pe.razon_social,
                u.nombre_persona as nombre_contacto,
                c.nombre as nombre_categoria
            FROM reserva r
            INNER JOIN servicio s ON r.id_servicio = s.id_servicio
            INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            INNER JOIN users u ON pe.user_id = u.id
            LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
            WHERE r.user_id = $1
            ORDER BY r.fecha DESC
            LIMIT 5
        """
        
        result = await conn.fetch(simple_query, current_user.id)
        
        reservas_list = []
        for row in result:
            reserva_dict = {
                "id_reserva": row['id_reserva'],
                "id_servicio": row['id_servicio'],
                "user_id": row['user_id'],
                "descripcion": row['descripcion'],
                "observacion": row['observacion'],
                "fecha": row['fecha'],
                "hora_inicio": str(row['hora_inicio']) if row['hora_inicio'] else None,
                "hora_fin": str(row['hora_fin']) if row['hora_fin'] else None,
                "estado": row['estado'],
                "created_at": row['created_at'],
                "nombre_servicio": row['nombre_servicio'],
                "descripcion_servicio": row['descripcion_servicio'],
                "precio_servicio": float(row['precio_servicio']) if row['precio_servicio'] else 0,
                "imagen_servicio": row['imagen_servicio'],
                "nombre_empresa": row['nombre_empresa'] or row['razon_social'],
                "razon_social": row['razon_social'],
                "id_perfil": row['id_perfil'],
                "nombre_contacto": row['nombre_contacto'],
                "nombre_categoria": row['nombre_categoria']
            }
            reservas_list.append(reserva_dict)
        
        return {
            "reservas": reservas_list,
            "total": len(reservas_list),
            "message": "Test exitoso"
        }
        
    except Exception as e:
        logger.error(f"[GET /mis-reservas-test] Error: {str(e)}")
        logger.error(f"[GET /mis-reservas-test] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_TEST.format(error=str(e))
        )
    finally:
        if 'conn' in locals():
            await direct_db_service.pool.release(conn)

# Funciones helper para crear_reserva
async def verify_service_exists(conn, servicio_id: int) -> dict:
    """Verifica que el servicio existe y está activo"""
    servicio_query = """
        SELECT s.id_servicio, s.id_perfil, s.estado, s.nombre
        FROM servicio s
        WHERE s.id_servicio = $1 AND s.estado = true
    """
    servicio_result = await conn.fetchrow(servicio_query, servicio_id)
    
    if not servicio_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_SERVICIO_NO_ENCONTRADO
        )
    
    return servicio_result

async def verify_provider_not_own_service(conn, servicio_id: int, user_id: str) -> None:
    """
    Verifica que el usuario no esté intentando reservar su propio servicio.
    Un proveedor no puede reservar servicios que le pertenecen.
    """
    verificacion_query = """
        SELECT s.id_servicio, pe.user_id
        FROM servicio s
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        WHERE s.id_servicio = $1 AND pe.user_id = $2
    """
    
    servicio_propio = await conn.fetchrow(verificacion_query, servicio_id, user_id)
    
    if servicio_propio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes reservar tus propios servicios. Solo los clientes pueden hacer reservas."
        )

async def verify_no_duplicate_reservation(
    conn,
    user_id: str,
    fecha: date,
    hora_inicio: time,
    hora_fin: time
) -> None:
    """
    Verifica que el cliente no tenga otra reserva en el mismo horario.
    Una reserva en el mismo horario es aquella que tiene la misma fecha y horas que se solapan.
    Dos intervalos [a1, b1] y [a2, b2] se solapan si: a1 < b2 AND b1 > a2
    """
    verificacion_query = """
        SELECT id_reserva, fecha, hora_inicio, hora_fin, estado
        FROM reserva
        WHERE user_id = $1
        AND fecha = $2
        AND estado != $3
        AND hora_inicio < $4
        AND hora_fin > $5
    """
    
    reserva_existente = await conn.fetchrow(
        verificacion_query,
        user_id,
        fecha,
        ESTADO_CANCELADA,  # Excluir reservas canceladas
        hora_fin,  # $4: hora_fin de la nueva reserva
        hora_inicio  # $5: hora_inicio de la nueva reserva
    )
    
    if reserva_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya tienes una reserva en el mismo horario (fecha: {fecha.strftime(FORMATO_FECHA_DD_MM_YYYY)}, hora: {hora_inicio.strftime('%H:%M')}). No puedes hacer dos reservas en el mismo horario."
        )


async def verify_no_confirmed_reservation(
    conn,
    servicio_id: int,
    fecha: date,
    hora_inicio: time,
    hora_fin: time
) -> None:
    """
    Verifica que no exista una reserva confirmada en el mismo servicio, fecha y horario.
    Una vez confirmada una reserva en una fecha y horario, no debe aparecer disponible para ningún cliente.
    Dos intervalos [a1, b1] y [a2, b2] se solapan si: a1 < b2 AND b1 > a2
    """
    verificacion_query = """
        SELECT id_reserva, fecha, hora_inicio, hora_fin, estado
        FROM reserva
        WHERE id_servicio = $1
        AND fecha = $2
        AND estado = $3
        AND hora_inicio < $4
        AND hora_fin > $5
    """
    
    reserva_confirmada = await conn.fetchrow(
        verificacion_query,
        servicio_id,
        fecha,
        ESTADO_CONFIRMADA,  # Solo verificar reservas confirmadas
        hora_fin,  # $4: hora_fin de la nueva reserva
        hora_inicio  # $5: hora_inicio de la nueva reserva
    )
    
    if reserva_confirmada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El horario seleccionado (fecha: {fecha.strftime(FORMATO_FECHA_DD_MM_YYYY)}, hora: {hora_inicio.strftime('%H:%M')}) ya está reservado y confirmado por otro cliente. Por favor, selecciona otro horario disponible."
        )

def validate_and_convert_service_id(id_servicio) -> int:
    """Valida y convierte el ID de servicio a entero"""
    try:
        return int(id_servicio)
    except (ValueError, TypeError) as e:
        logger.error(f"[POST /reservas] Error al convertir ID de servicio: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_ID_SERVICIO_INVALIDO
        )

def process_hora_inicio(hora_inicio_str: Optional[str]) -> time:
    """Procesa la hora de inicio con fallback"""
    if not hora_inicio_str:
        hora_inicio_str = HORA_INICIO_DEFAULT
    
    try:
        return datetime.strptime(hora_inicio_str, "%H:%M").time()
    except ValueError:
        return time(9, 0)  # Fallback a 9:00 AM

def calculate_hora_fin(hora_inicio: time) -> time:
    """Calcula la hora fin (1 hora después de la hora de inicio)"""
    return (datetime.combine(date.today(), hora_inicio) + timedelta(hours=1)).time()

async def insert_reserva(
    conn,
    servicio_id: int,
    user_uuid: str,
    reserva: ReservaIn,
    hora_inicio: time,
    hora_fin: time
) -> dict:
    """Inserta una nueva reserva en la base de datos"""
    insert_query = """
        INSERT INTO reserva (id_servicio, user_id, descripcion, observacion, fecha, hora_inicio, hora_fin, estado)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id_reserva, id_servicio, user_id, descripcion, observacion, fecha, hora_inicio, hora_fin, estado
    """
    
    nueva_reserva = await conn.fetchrow(
        insert_query,
        servicio_id,
        user_uuid,
        reserva.descripcion,
        reserva.observacion,
        reserva.fecha,
        hora_inicio,
        hora_fin,
        ESTADO_PENDIENTE
    )
    
    logger.info(f"[POST /reservas] Reserva {nueva_reserva['id_reserva']} creada exitosamente")
    return nueva_reserva

async def send_reservation_notification(conn, reserva_id: int) -> None:
    """Envía notificación por correo cuando se crea una reserva"""
    try:
        notif_query = """
            SELECT
                r.id_reserva,
                s.nombre AS servicio_nombre,
                r.fecha,
                r.hora_inicio,
                u_cliente.nombre_persona AS cliente_nombre,
                au_cliente.email AS cliente_email,
                u_prov.nombre_persona AS proveedor_nombre,
                au_prov.email AS proveedor_email
            FROM reserva r
            JOIN servicio s ON r.id_servicio = s.id_servicio
            JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            JOIN public.users u_cliente ON r.user_id = u_cliente.id
            JOIN auth.users au_cliente ON r.user_id = au_cliente.id
            JOIN public.users u_prov ON pe.user_id = u_prov.id
            JOIN auth.users au_prov ON pe.user_id = au_prov.id
            WHERE r.id_reserva = $1
        """
        notif_data = await conn.fetchrow(notif_query, reserva_id)
        
        if notif_data:
            fecha_formatted = notif_data['fecha'].strftime(FORMATO_FECHA_DD_MM_YYYY) if notif_data['fecha'] else ""
            hora_formatted = str(notif_data['hora_inicio']) if notif_data['hora_inicio'] else ""
            
            reserva_notification_service.notify_reserva_creada(
                reserva_id=notif_data['id_reserva'],
                servicio_nombre=notif_data['servicio_nombre'],
                fecha=fecha_formatted,
                hora=hora_formatted,
                cliente_nombre=notif_data['cliente_nombre'] or "Cliente",
                cliente_email=notif_data['cliente_email'],
                proveedor_nombre=notif_data['proveedor_nombre'] or "Proveedor",
                proveedor_email=notif_data['proveedor_email']
            )
    except Exception as notif_error:
        logger.warning(f"[POST /reservas] Error al enviar notificación: {notif_error}")

def build_reserva_response(nueva_reserva: dict) -> dict:
    """Construye la respuesta de la reserva creada"""
    try:
        if isinstance(nueva_reserva['id_reserva'], int):
            reserva_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, str(nueva_reserva['id_reserva']))
        else:
            reserva_uuid = nueva_reserva['id_reserva']
        
        if hasattr(nueva_reserva['fecha'], 'date'):
            fecha_pura = nueva_reserva['fecha'].date()
        else:
            fecha_pura = nueva_reserva['fecha']
        
        return {
            "id": reserva_uuid,
            "id_servicio": nueva_reserva['id_servicio'],
            "user_id": nueva_reserva['user_id'],
            "descripcion": nueva_reserva['descripcion'],
            "observacion": nueva_reserva['observacion'],
            "fecha": fecha_pura,
            "hora_inicio": str(nueva_reserva['hora_inicio']) if nueva_reserva['hora_inicio'] else None,
            "hora_fin": str(nueva_reserva['hora_fin']) if nueva_reserva['hora_fin'] else None,
            "estado": nueva_reserva['estado'],
            "id_disponibilidad": None
        }
    except Exception as response_error:
        logger.error(f"[POST /reservas] Error al construir respuesta: {response_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al construir respuesta: {str(response_error)}"
        )

@router.post(
    "/crear",
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
    try:
        conn = await direct_db_service.get_connection()
        
        try:
            # Validar y convertir ID de servicio
            servicio_id = validate_and_convert_service_id(reserva.id_servicio)
            
            # Verificar que el servicio existe y está activo
            servicio_info = await verify_service_exists(conn, servicio_id)
            
            # Verificar que el proveedor no esté reservando su propio servicio
            await verify_provider_not_own_service(conn, servicio_id, current_user.id)
            
            # Procesar hora de inicio y calcular hora fin
            hora_inicio = process_hora_inicio(reserva.hora_inicio)
            hora_fin = calculate_hora_fin(hora_inicio)
            
            # Validar que el cliente no tenga otra reserva en el mismo horario
            await verify_no_duplicate_reservation(
                conn, current_user.id, reserva.fecha, hora_inicio, hora_fin
            )
            
            # Validar que no exista una reserva confirmada en el mismo servicio, fecha y horario
            await verify_no_confirmed_reservation(
                conn, servicio_id, reserva.fecha, hora_inicio, hora_fin
            )
            
            # Insertar reserva
            nueva_reserva = await insert_reserva(
                conn, servicio_id, current_user.id, reserva, hora_inicio, hora_fin
            )
            
            # Enviar notificación por correo
            await send_reservation_notification(conn, nueva_reserva['id_reserva'])
            
            # Construir y retornar respuesta
            return build_reserva_response(nueva_reserva)
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[POST /reservas] Error al crear reserva: {str(e)}")
        logger.error(f"[POST /reservas] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_CREAR_RESERVA.format(error=str(e))
        )


# Funciones helper para obtener_mis_reservas_detalladas
def validate_pagination_params(limit: Optional[int], offset: Optional[int]) -> tuple[int, int]:
    """Valida y normaliza los parámetros de paginación"""
    if limit is None or limit < 1:
        limit = 20
    if limit > 100:
        limit = 100
        
    if offset is None or offset < 0:
        offset = 0
    
    return limit, offset

def build_where_conditions(
    search: Optional[str],
    nombre_servicio: Optional[str],
    nombre_empresa: Optional[str],
    fecha_desde: Optional[str],
    fecha_hasta: Optional[str],
    estado: Optional[str],
    nombre_contacto: Optional[str],
    params: list,
    param_count: int
) -> tuple[list[str], list, int]:
    """Construye las condiciones WHERE dinámicas y actualiza los parámetros"""
    where_conditions = []
    
    if search and search.strip():
        param_count += 1
        where_conditions.append(f"""
            (LOWER(s.nombre) LIKE LOWER(${param_count}) 
            OR LOWER(pe.nombre_fantasia) LIKE LOWER(${param_count})
            OR LOWER(pe.razon_social) LIKE LOWER(${param_count}))
        """)
        params.append(f"%{search.strip()}%")
    
    if nombre_servicio and nombre_servicio.strip():
        param_count += 1
        where_conditions.append(f"LOWER(s.nombre) LIKE LOWER(${param_count})")
        params.append(f"%{nombre_servicio.strip()}%")
    
    if nombre_empresa and nombre_empresa.strip():
        param_count += 1
        where_conditions.append(f"""
            (LOWER(pe.nombre_fantasia) LIKE LOWER(${param_count}) 
            OR LOWER(pe.razon_social) LIKE LOWER(${param_count}))
        """)
        params.append(f"%{nombre_empresa.strip()}%")
    
    if fecha_desde:
        param_count += 1
        where_conditions.append(f"r.fecha >= ${param_count}")
        # Convertir string a date si es necesario
        if isinstance(fecha_desde, str):
            fecha_desde_date = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            params.append(fecha_desde_date)
        else:
            params.append(fecha_desde)
    
    if fecha_hasta:
        param_count += 1
        where_conditions.append(f"r.fecha <= ${param_count}")
        # Convertir string a date si es necesario
        if isinstance(fecha_hasta, str):
            fecha_hasta_date = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            params.append(fecha_hasta_date)
        else:
            params.append(fecha_hasta)
    
    if estado and estado.strip():
        param_count += 1
        where_conditions.append(f"r.estado = ${param_count}")
        params.append(estado.strip().lower())
    
    if nombre_contacto and nombre_contacto.strip():
        param_count += 1
        where_conditions.append(f"LOWER(u.nombre_persona) LIKE LOWER(${param_count})")
        params.append(f"%{nombre_contacto.strip()}%")
    
    return where_conditions, params, param_count

def get_base_reservas_query() -> str:
    """Retorna la query base para obtener reservas con información detallada"""
    return """
        SELECT 
            r.id_reserva,
            r.id_servicio,
            r.user_id as id_usuario,
            r.descripcion,
            r.observacion,
            r.fecha,
            r.hora_inicio,
            r.hora_fin,
            r.estado,
            r.created_at,
            s.nombre as nombre_servicio,
            s.descripcion as descripcion_servicio,
            s.precio as precio_servicio,
            s.imagen as imagen_servicio,
            s.id_perfil,
            pe.nombre_fantasia as nombre_empresa,
            pe.razon_social,
            u.nombre_persona as nombre_contacto,
            c.nombre as nombre_categoria,
            m.simbolo as simbolo_moneda,
            m.codigo_iso_moneda,
            CASE WHEN cal_cliente.id_calificacion IS NOT NULL THEN true ELSE false END as ya_calificado_por_cliente,
            cal_cliente.puntaje as calificacion_cliente_puntaje,
            cal_cliente.comentario as calificacion_cliente_comentario,
            cal_cliente.satisfaccion_nps as calificacion_cliente_nps,
            cal_proveedor.puntaje as calificacion_proveedor_puntaje,
            cal_proveedor.comentario as calificacion_proveedor_comentario
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        INNER JOIN users u ON pe.user_id = u.id
        LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
        LEFT JOIN moneda m ON s.id_moneda = m.id_moneda
        LEFT JOIN calificacion cal_cliente ON r.id_reserva = cal_cliente.id_reserva AND cal_cliente.rol_emisor = 'cliente'
        LEFT JOIN calificacion cal_proveedor ON r.id_reserva = cal_proveedor.id_reserva AND cal_proveedor.rol_emisor = 'proveedor'
        WHERE r.user_id = $1
    """

def get_count_reservas_query() -> str:
    """Retorna la query base para contar reservas"""
    return """
        SELECT COUNT(*) as total
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        INNER JOIN users u ON pe.user_id = u.id
        WHERE r.user_id = $1
    """

def process_reserva_row(row: dict) -> dict:
    """Procesa una fila de resultado y la convierte en un diccionario de reserva"""
    ya_calificado = row['ya_calificado_por_cliente']
    
    return {
        "id_reserva": row['id_reserva'],
        "id_servicio": row['id_servicio'],
        "user_id": row['id_usuario'],
        "descripcion": row['descripcion'],
        "observacion": row['observacion'],
        "fecha": row['fecha'],
        "hora_inicio": str(row['hora_inicio']) if row['hora_inicio'] else None,
        "hora_fin": str(row['hora_fin']) if row['hora_fin'] else None,
        "estado": row['estado'],
        "created_at": row['created_at'],
        "nombre_servicio": row['nombre_servicio'],
        "descripcion_servicio": row['descripcion_servicio'],
        "precio_servicio": float(row['precio_servicio']),
        "imagen_servicio": row['imagen_servicio'],
        "nombre_empresa": row['nombre_empresa'] or row['razon_social'],
        "razon_social": row['razon_social'],
        "id_perfil": row['id_perfil'],
        "nombre_contacto": row['nombre_contacto'],
        "email_contacto": None,
        "telefono_contacto": None,
        "nombre_categoria": row['nombre_categoria'],
        "simbolo_moneda": row['simbolo_moneda'] or '₲',
        "codigo_iso_moneda": row['codigo_iso_moneda'] or 'GS',
        "ya_calificado_por_cliente": ya_calificado,
        "calificacion_cliente": {
            "puntaje": row['calificacion_cliente_puntaje'],
            "comentario": row['calificacion_cliente_comentario'],
            "nps": row['calificacion_cliente_nps']
        } if row['calificacion_cliente_puntaje'] else None,
        "calificacion_proveedor": {
            "puntaje": row['calificacion_proveedor_puntaje'],
            "comentario": row['calificacion_proveedor_comentario']
        } if row['calificacion_proveedor_puntaje'] else None
    }

def build_pagination_info(total_count: int, limit: int, offset: int) -> dict:
    """Construye la información de paginación"""
    total_pages = (total_count + limit - 1) // limit
    current_page = (offset // limit) + 1
    
    return {
        "total": total_count,
        "page": current_page,
        "limit": limit,
        "offset": offset,
        "total_pages": total_pages,
        "has_next": offset + limit < total_count,
        "has_prev": offset > 0
    }

@router.get(
    "/mis-reservas",
    description="Obtiene las reservas del cliente autenticado con filtros avanzados y paginación optimizada."
)
async def obtener_mis_reservas_detalladas(
    current_user: SupabaseUser = Depends(get_current_user),
    search: Optional[str] = Query(None),
    nombre_servicio: Optional[str] = Query(None),
    nombre_empresa: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    nombre_contacto: Optional[str] = Query(None),
    limit: Optional[int] = Query(20),
    offset: Optional[int] = Query(0)
):
    """
    Endpoint optimizado para obtener las reservas del cliente autenticado con información detallada.
    """
    try:
        limit, offset = validate_pagination_params(limit, offset)
        
        # Validar fechas (convertir a date si son strings) - Solo validar si ambas están presentes
        if fecha_desde and fecha_hasta:
            fecha_desde_date = datetime.strptime(fecha_desde, "%Y-%m-%d").date() if isinstance(fecha_desde, str) else fecha_desde
            fecha_hasta_date = datetime.strptime(fecha_hasta, "%Y-%m-%d").date() if isinstance(fecha_hasta, str) else fecha_hasta
            if fecha_desde_date > fecha_hasta_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La fecha 'hasta' debe ser mayor o igual a la fecha 'desde'"
                )
            logger.info(f"🔍 [GET /mis-reservas] Rango de fechas válido: {fecha_desde_date} a {fecha_hasta_date}")
        elif fecha_desde:
            logger.info(f"🔍 [GET /mis-reservas] Filtrando solo por fecha desde: {fecha_desde}")
        elif fecha_hasta:
            logger.info(f"🔍 [GET /mis-reservas] Filtrando solo por fecha hasta: {fecha_hasta}")
        
        conn = await direct_db_service.get_connection()
        
        try:
            base_query = get_base_reservas_query()
            params = [current_user.id]
            param_count = 1
            
            where_conditions, params, param_count = build_where_conditions(
                search, nombre_servicio, nombre_empresa, fecha_desde,
                fecha_hasta, estado, nombre_contacto, params, param_count
            )
            
            if where_conditions:
                base_query += SQL_AND + SQL_AND.join(where_conditions)
            
            count_query = get_count_reservas_query()
            if where_conditions:
                count_query += SQL_AND + SQL_AND.join(where_conditions)
            
            total_result = await conn.fetchrow(count_query, *params)
            total_count = total_result['total'] if total_result else 0
            
            base_query += f"""
                ORDER BY r.fecha DESC, r.created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            reservas_result = await conn.fetch(base_query, *params)
            reservas_list = [process_reserva_row(row) for row in reservas_result]
            
            pagination_info = build_pagination_info(total_count, limit, offset)
            
            return {
                "reservas": reservas_list,
                "pagination": pagination_info
            }
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /mis-reservas] Error: {str(e)}")
        logger.error(f"[GET /mis-reservas] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_OBTENER_RESERVAS.format(error=str(e))
        )


# Funciones helper para obtener_reservas_proveedor
def validate_pagination_params(limit: Optional[int], offset: Optional[int]) -> tuple[int, int]:
    """Valida y normaliza los parámetros de paginación"""
    if limit is None or limit < 1:
        limit = 20
    if limit > 100:
        limit = 100
    
    if offset is None or offset < 0:
        offset = 0
    
    return limit, offset

async def get_provider_profile(conn, user_id: str) -> dict:
    """Obtiene el perfil de empresa del proveedor"""
    perfil_query = """
        SELECT id_perfil, nombre_fantasia, razon_social
        FROM perfil_empresa 
        WHERE user_id = $1 AND verificado = true
    """
    perfil_result = await conn.fetchrow(perfil_query, user_id)
    
    if not perfil_result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MSG_NO_PERFIL_PROVEEDOR
        )
    
    return perfil_result

def build_where_conditions_proveedor(
    search: Optional[str],
    nombre_servicio: Optional[str],
    nombre_cliente: Optional[str],
    nombre_empresa: Optional[str],
    nombre_contacto: Optional[str],
    fecha_desde: Optional[str],
    fecha_hasta: Optional[str],
    estado: Optional[str]
) -> tuple[list[str], list, int]:
    """Construye las condiciones WHERE dinámicas y sus parámetros para reservas de proveedores"""
    where_conditions = []
    params = []
    param_count = 1  # Empezamos en 1 porque $1 es para proveedor_id
    
    logger.info(f"🔍 [build_where_conditions_proveedor] Filtros recibidos - fecha_desde: {fecha_desde}, fecha_hasta: {fecha_hasta}")
    
    if search and search.strip():
        param_count += 1
        where_conditions.append(f"""
            (LOWER(s.nombre) LIKE LOWER(${param_count}) 
            OR LOWER(u.nombre_persona) LIKE LOWER(${param_count})
            OR LOWER(r.descripcion) LIKE LOWER(${param_count})
            OR LOWER(pe.nombre_fantasia) LIKE LOWER(${param_count})
            OR LOWER(pe.razon_social) LIKE LOWER(${param_count}))
        """)
        params.append(f"%{search.strip()}%")
    
    if nombre_servicio and nombre_servicio.strip():
        param_count += 1
        where_conditions.append(f"LOWER(s.nombre) LIKE LOWER(${param_count})")
        params.append(f"%{nombre_servicio.strip()}%")
    
    if nombre_cliente and nombre_cliente.strip():
        param_count += 1
        where_conditions.append(f"LOWER(u.nombre_persona) LIKE LOWER(${param_count})")
        params.append(f"%{nombre_cliente.strip()}%")
    
    if nombre_empresa and nombre_empresa.strip():
        param_count += 1
        where_conditions.append(f"""
            (LOWER(pe.nombre_fantasia) LIKE LOWER(${param_count}) 
            OR LOWER(pe.razon_social) LIKE LOWER(${param_count}))
        """)
        params.append(f"%{nombre_empresa.strip()}%")
    
    if nombre_contacto and nombre_contacto.strip():
        param_count += 1
        where_conditions.append(f"LOWER(u.nombre_persona) LIKE LOWER(${param_count})")
        params.append(f"%{nombre_contacto.strip()}%")
    
    if fecha_desde:
        param_count += 1
        where_conditions.append(f"r.fecha >= ${param_count}")
        # Convertir string a date si es necesario
        if isinstance(fecha_desde, str):
            try:
                fecha_desde_date = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                params.append(fecha_desde_date)
                logger.info(f"🔍 [build_where_conditions_proveedor] Fecha desde convertida: '{fecha_desde}' -> {fecha_desde_date} (tipo: {type(fecha_desde_date)})")
            except ValueError as e:
                logger.error(f"❌ [build_where_conditions_proveedor] Error al convertir fecha_desde '{fecha_desde}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Formato de fecha 'desde' inválido: {fecha_desde}. Use formato YYYY-MM-DD"
                )
        else:
            params.append(fecha_desde)
            logger.info(f"🔍 [build_where_conditions_proveedor] Fecha desde (ya es date): {fecha_desde}")
    
    if fecha_hasta:
        param_count += 1
        where_conditions.append(f"r.fecha <= ${param_count}")
        # Convertir string a date si es necesario
        if isinstance(fecha_hasta, str):
            try:
                fecha_hasta_date = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                params.append(fecha_hasta_date)
                logger.info(f"🔍 [build_where_conditions_proveedor] Fecha hasta convertida: '{fecha_hasta}' -> {fecha_hasta_date} (tipo: {type(fecha_hasta_date)})")
            except ValueError as e:
                logger.error(f"❌ [build_where_conditions_proveedor] Error al convertir fecha_hasta '{fecha_hasta}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Formato de fecha 'hasta' inválido: {fecha_hasta}. Use formato YYYY-MM-DD"
                )
        else:
            params.append(fecha_hasta)
            logger.info(f"🔍 [build_where_conditions_proveedor] Fecha hasta (ya es date): {fecha_hasta}")
    
    if estado and estado.strip():
        param_count += 1
        where_conditions.append(f"r.estado = ${param_count}")
        params.append(estado.strip().lower())
    
    logger.info(f"🔍 [build_where_conditions_proveedor] Condiciones WHERE construidas: {where_conditions}")
    logger.info(f"🔍 [build_where_conditions_proveedor] Parámetros: {params}")
    logger.info(f"🔍 [build_where_conditions_proveedor] param_count final: {param_count}")
    
    return where_conditions, params, param_count

def build_count_query(where_conditions: list[str]) -> str:
    """Construye la query para contar el total de reservas"""
    count_query = """
        SELECT COUNT(*) as total
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        INNER JOIN users u ON r.user_id = u.id
        WHERE s.id_perfil = $1
    """
    
    if where_conditions:
        count_query += SQL_AND + SQL_AND.join(where_conditions)
    
    return count_query

def build_base_query(where_conditions: list[str], param_count: int) -> str:
    """Construye la query base con ORDER BY y LIMIT"""
    base_query = """
        SELECT 
            r.id_reserva,
            r.id_servicio,
            r.user_id as id_cliente,
            r.descripcion,
            r.observacion,
            r.fecha,
            r.hora_inicio,
            r.hora_fin,
            r.estado,
            r.created_at,
            s.nombre as nombre_servicio,
            s.descripcion as descripcion_servicio,
            s.precio as precio_servicio,
            s.imagen as imagen_servicio,
            s.id_perfil,
            pe.nombre_fantasia as nombre_empresa,
            pe.razon_social,
            u.nombre_persona as nombre_cliente,
            u.nombre_persona as nombre_contacto,
            c.nombre as nombre_categoria,
            m.simbolo as simbolo_moneda,
            m.codigo_iso_moneda,
            CASE WHEN cal_proveedor.id_calificacion IS NOT NULL THEN true ELSE false END as ya_calificado_por_proveedor,
            cal_cliente.puntaje as calificacion_cliente_puntaje,
            cal_cliente.comentario as calificacion_cliente_comentario,
            cal_cliente.satisfaccion_nps as calificacion_cliente_nps,
            cal_proveedor.puntaje as calificacion_proveedor_puntaje,
            cal_proveedor.comentario as calificacion_proveedor_comentario
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        INNER JOIN users u ON r.user_id = u.id
        LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
        LEFT JOIN moneda m ON s.id_moneda = m.id_moneda
        LEFT JOIN calificacion cal_cliente ON r.id_reserva = cal_cliente.id_reserva AND cal_cliente.rol_emisor = 'cliente'
        LEFT JOIN calificacion cal_proveedor ON r.id_reserva = cal_proveedor.id_reserva AND cal_proveedor.rol_emisor = 'proveedor'
        WHERE s.id_perfil = $1
    """
    
    if where_conditions:
        base_query += SQL_AND + SQL_AND.join(where_conditions)
    
    base_query += f"""
        ORDER BY r.fecha DESC, r.created_at DESC
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
    """
    
    return base_query

def process_reservas_results(reservas_result) -> list[dict]:
    """Procesa los resultados de la query y los convierte a diccionarios"""
    reservas_list = []
    for row in reservas_result:
        ya_calificado = row['ya_calificado_por_proveedor']
        
        reserva_dict = {
            "id_reserva": row['id_reserva'],
            "id_servicio": row['id_servicio'],
            "id_cliente": row['id_cliente'],
            "descripcion": row['descripcion'],
            "observacion": row['observacion'],
            "fecha": row['fecha'],
            "hora_inicio": str(row['hora_inicio']) if row['hora_inicio'] else None,
            "hora_fin": str(row['hora_fin']) if row['hora_fin'] else None,
            "estado": row['estado'],
            "created_at": row['created_at'],
            "nombre_servicio": row['nombre_servicio'],
            "descripcion_servicio": row['descripcion_servicio'],
            "precio_servicio": float(row['precio_servicio']),
            "imagen_servicio": row['imagen_servicio'],
            "nombre_empresa": row['nombre_empresa'] or row['razon_social'],
            "razon_social": row['razon_social'],
            "id_perfil": row['id_perfil'],
            "nombre_cliente": row['nombre_cliente'],
            "nombre_contacto": row['nombre_contacto'],
            "nombre_categoria": row['nombre_categoria'],
            "simbolo_moneda": row['simbolo_moneda'] or '₲',
            "codigo_iso_moneda": row['codigo_iso_moneda'] or 'GS',
            "ya_calificado_por_proveedor": ya_calificado,
            "calificacion_cliente": {
                "puntaje": row['calificacion_cliente_puntaje'],
                "comentario": row['calificacion_cliente_comentario'],
                "nps": row['calificacion_cliente_nps']
            } if row['calificacion_cliente_puntaje'] else None,
            "calificacion_proveedor": {
                "puntaje": row['calificacion_proveedor_puntaje'],
                "comentario": row['calificacion_proveedor_comentario']
            } if row['calificacion_proveedor_puntaje'] else None
        }
        reservas_list.append(reserva_dict)
    
    return reservas_list

def build_pagination_info(total_count: int, limit: int, offset: int) -> dict:
    """Construye la información de paginación"""
    total_pages = (total_count + limit - 1) // limit
    current_page = (offset // limit) + 1
    
    return {
        "total": total_count,
        "page": current_page,
        "limit": limit,
        "offset": offset,
        "total_pages": total_pages,
        "has_next": offset + limit < total_count,
        "has_prev": offset > 0
    }

@router.get(
    "/reservas-proveedor",
    description="Obtiene las reservas solicitadas por clientes para los servicios del proveedor autenticado."
)
async def obtener_reservas_proveedor(
    current_user: SupabaseUser = Depends(get_current_user),
    search: Optional[str] = Query(None),
    nombre_servicio: Optional[str] = Query(None),
    nombre_cliente: Optional[str] = Query(None),
    nombre_empresa: Optional[str] = Query(None),
    nombre_contacto: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    limit: Optional[int] = Query(20),
    offset: Optional[int] = Query(0)
):
    """
    Endpoint para proveedores: Obtiene las reservas solicitadas por clientes para los servicios del proveedor.
    Solo muestra reservas de servicios que pertenecen al proveedor autenticado.
    """
    try:
        # Validar parámetros de paginación
        limit, offset = validate_pagination_params(limit, offset)
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Obtener perfil del proveedor
            perfil_result = await get_provider_profile(conn, current_user.id)
            proveedor_id = perfil_result['id_perfil']
            
            logger.info(f"🔍 [GET /reservas-proveedor] Proveedor ID: {proveedor_id}, User ID: {current_user.id}")
            logger.info(f"🔍 [GET /reservas-proveedor] Filtros de fecha - Desde: {fecha_desde}, Hasta: {fecha_hasta}")
            
            # Validar fechas (convertir a date si son strings) - Solo validar si ambas están presentes
            if fecha_desde and fecha_hasta:
                fecha_desde_date = datetime.strptime(fecha_desde, "%Y-%m-%d").date() if isinstance(fecha_desde, str) else fecha_desde
                fecha_hasta_date = datetime.strptime(fecha_hasta, "%Y-%m-%d").date() if isinstance(fecha_hasta, str) else fecha_hasta
                if fecha_desde_date > fecha_hasta_date:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="La fecha 'hasta' debe ser mayor o igual a la fecha 'desde'"
                    )
                logger.info(f"🔍 [GET /reservas-proveedor] Rango de fechas válido: {fecha_desde_date} a {fecha_hasta_date}")
            elif fecha_desde:
                logger.info(f"🔍 [GET /reservas-proveedor] Filtrando solo por fecha desde: {fecha_desde}")
            elif fecha_hasta:
                logger.info(f"🔍 [GET /reservas-proveedor] Filtrando solo por fecha hasta: {fecha_hasta}")
            
            # Construir condiciones WHERE dinámicas
            where_conditions, where_params, param_count = build_where_conditions_proveedor(
                search, nombre_servicio, nombre_cliente, nombre_empresa, nombre_contacto, fecha_desde, fecha_hasta, estado
            )
            
            # Preparar parámetros completos (proveedor_id + condiciones WHERE)
            params = [proveedor_id] + where_params
            
            # Construir y ejecutar query de conteo
            count_query = build_count_query(where_conditions)
            logger.info(f"🔍 [GET /reservas-proveedor] Count query: {count_query}")
            logger.info(f"🔍 [GET /reservas-proveedor] Count params: {params}")
            logger.info(f"🔍 [GET /reservas-proveedor] Count params tipos: {[type(p).__name__ for p in params]}")
            total_result = await conn.fetchrow(count_query, *params)
            total_count = total_result['total'] if total_result else 0
            logger.info(f"🔍 [GET /reservas-proveedor] Total count: {total_count}")
            
            # Construir y ejecutar query principal
            base_query = build_base_query(where_conditions, param_count)
            params.extend([limit, offset])
            logger.info(f"🔍 [GET /reservas-proveedor] Base query: {base_query}")
            logger.info(f"🔍 [GET /reservas-proveedor] Base params: {params}")
            logger.info(f"🔍 [GET /reservas-proveedor] Base params tipos: {[type(p).__name__ for p in params]}")
            reservas_result = await conn.fetch(base_query, *params)
            logger.info(f"🔍 [GET /reservas-proveedor] Reservas encontradas: {len(reservas_result)}")
            if len(reservas_result) > 0:
                logger.info(f"🔍 [GET /reservas-proveedor] Fechas de las reservas encontradas: {[str(r['fecha']) for r in reservas_result]}")
            
            # Procesar resultados
            reservas_list = process_reservas_results(reservas_result)
            
            # Construir información de paginación
            pagination_info = build_pagination_info(total_count, limit, offset)
            
            return {
                "reservas": reservas_list,
                "pagination": pagination_info,
                "proveedor": {
                    "id_perfil": proveedor_id,
                    "nombre_empresa": perfil_result['nombre_fantasia'],
                    "razon_social": perfil_result['razon_social']
                }
            }
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /reservas-proveedor] Error: {str(e)}")
        logger.error(f"[GET /reservas-proveedor] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_OBTENER_RESERVAS_PROVEEDOR.format(error=str(e))
        )


# Funciones helper para diagnostico_usuario
async def get_provider_info(conn, user_id: str) -> Optional[dict]:
    """Obtiene la información del proveedor si existe"""
    proveedor_query = """
        SELECT 
            pe.id_perfil,
            pe.nombre_fantasia,
            pe.razon_social,
            pe.verificado,
            pe.estado
        FROM perfil_empresa pe
        WHERE pe.user_id = $1
    """
    return await conn.fetchrow(proveedor_query, user_id)

async def get_client_reservations_count(conn, user_id: str) -> int:
    """Obtiene el conteo de reservas como cliente"""
    cliente_query = """
        SELECT COUNT(*) as total_reservas
        FROM reserva r
        WHERE r.user_id = $1
    """
    cliente_result = await conn.fetchrow(cliente_query, user_id)
    return cliente_result['total_reservas'] if cliente_result else 0

async def get_provider_reservations_count(conn, id_perfil: int) -> int:
    """Obtiene el conteo de reservas como proveedor"""
    reservas_proveedor_query = """
        SELECT COUNT(*) as total_reservas
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        WHERE s.id_perfil = $1
    """
    reservas_proveedor_result = await conn.fetchrow(reservas_proveedor_query, id_perfil)
    return reservas_proveedor_result['total_reservas'] if reservas_proveedor_result else 0

async def get_user_info(conn, user_id: str) -> Optional[dict]:
    """Obtiene la información del usuario"""
    usuario_query = """
        SELECT 
            u.nombre_persona,
            u.nombre_empresa,
            u.ruc,
            u.estado
        FROM users u
        WHERE u.id = $1
    """
    return await conn.fetchrow(usuario_query, user_id)

def build_provider_data(proveedor_result: Optional[dict]) -> Optional[dict]:
    """Construye el diccionario de datos del proveedor"""
    if not proveedor_result:
        return None
    
    return {
        "id_perfil": proveedor_result['id_perfil'],
        "nombre_fantasia": proveedor_result['nombre_fantasia'],
        "razon_social": proveedor_result['razon_social'],
        "verificado": proveedor_result['verificado'],
        "estado": proveedor_result['estado']
    }

def extract_user_data(usuario_result: Optional[dict]) -> dict:
    """Extrae los datos del usuario de forma segura"""
    return {
        "nombre_persona": usuario_result['nombre_persona'] if usuario_result else None,
        "nombre_empresa": usuario_result['nombre_empresa'] if usuario_result else None,
        "ruc": usuario_result['ruc'] if usuario_result else None,
        "estado": usuario_result['estado'] if usuario_result else None
    }

def recommend_endpoints(es_cliente: bool, es_proveedor: bool, proveedor_verificado: bool) -> list[str]:
    """Recomienda endpoints basado en el tipo de usuario"""
    endpoints = []
    
    if es_cliente:
        endpoints.append("GET /api/v1/reservas/mis-reservas")
    
    if es_proveedor and proveedor_verificado:
        endpoints.append("GET /api/v1/reservas/reservas-proveedor")
    
    if not endpoints:
        endpoints.append("No hay endpoints disponibles - usuario sin reservas ni perfil de proveedor")
    
    return endpoints

def build_diagnostico(
    current_user: SupabaseUser,
    usuario_data: dict,
    es_proveedor: bool,
    es_cliente: bool,
    proveedor_data: Optional[dict],
    total_reservas_cliente: int,
    reservas_proveedor: int,
    endpoints_recomendados: list[str]
) -> dict:
    """Construye el diccionario de diagnóstico completo"""
    return {
        "usuario": {
            "id": current_user.id,
            "email": current_user.email,
            "nombre_persona": usuario_data["nombre_persona"],
            "nombre_empresa": usuario_data["nombre_empresa"],
            "ruc": usuario_data["ruc"],
            "estado": usuario_data["estado"]
        },
        "es_proveedor": es_proveedor,
        "es_cliente": es_cliente,
        "proveedor": proveedor_data,
        "reservas": {
            "como_cliente": total_reservas_cliente,
            "como_proveedor": reservas_proveedor
        },
        "endpoints_recomendados": endpoints_recomendados
    }

@router.get(
    "/diagnostico-usuario",
    description="Endpoint de diagnóstico para determinar el tipo de usuario y sus datos."
)
async def diagnostico_usuario(
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Endpoint de diagnóstico para verificar el tipo de usuario y sus datos.
    """
    try:
        conn = await direct_db_service.get_connection()
        
        try:
            # Obtener información del proveedor
            proveedor_result = await get_provider_info(conn, current_user.id)
            es_proveedor = proveedor_result is not None
            
            # Obtener conteo de reservas como cliente
            total_reservas_cliente = await get_client_reservations_count(conn, current_user.id)
            es_cliente = total_reservas_cliente > 0
            
            # Obtener conteo de reservas como proveedor (si aplica)
            reservas_proveedor = 0
            if es_proveedor:
                reservas_proveedor = await get_provider_reservations_count(conn, proveedor_result['id_perfil'])
            
            # Obtener información del usuario
            usuario_result = await get_user_info(conn, current_user.id)
            usuario_data = extract_user_data(usuario_result)
            
            # Construir datos del proveedor
            proveedor_data = build_provider_data(proveedor_result)
            
            # Recomendar endpoints
            proveedor_verificado = proveedor_data['verificado'] if proveedor_data else False
            endpoints_recomendados = recommend_endpoints(es_cliente, es_proveedor, proveedor_verificado)
            
            # Construir y retornar diagnóstico
            return build_diagnostico(
                current_user,
                usuario_data,
                es_proveedor,
                es_cliente,
                proveedor_data,
                total_reservas_cliente,
                reservas_proveedor,
                endpoints_recomendados
            )
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except Exception as e:
        logger.error(f"[GET /diagnostico-usuario] Error: {str(e)}")
        logger.error(f"[GET /diagnostico-usuario] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_DIAGNOSTICO.format(error=str(e))
        )


async def enviar_notificacion_cliente(conn, reserva_id: int, estado_anterior: str, nuevo_estado: str, observacion: str = None):
    """
    Envía notificación al cliente cuando cambia el estado de su reserva.
    Por ahora solo registra en logs, pero se puede extender para enviar emails o push notifications.
    """
    try:
        # Obtener información del cliente y la reserva
        cliente_query = """
            SELECT r.id_reserva, r.user_id, u.nombre_persona, s.nombre as servicio_nombre,
                   pe.nombre_fantasia as empresa_nombre
            FROM reserva r
            INNER JOIN users u ON r.user_id = u.id
            INNER JOIN servicio s ON r.id_servicio = s.id_servicio
            INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            WHERE r.id_reserva = $1
        """
        
        cliente_result = await conn.fetchrow(cliente_query, reserva_id)
        
        if not cliente_result:
            logger.warning(f"No se pudo obtener información del cliente para la reserva {reserva_id}")
            return
        
        # Crear mensaje de notificación
        mensajes_estado = {
            'aprobado': MSG_NOTIF_APROBADO,
            'rechazado': MSG_NOTIF_RECHAZADO,
            'concluido': MSG_NOTIF_CONCLUIDO
        }
        
        mensaje_principal = mensajes_estado.get(nuevo_estado, MSG_NOTIF_ESTADO_CAMBIADO.format(estado=nuevo_estado))
        
        # Log de notificación (en producción se enviaría email/push)
        logger.info("NOTIFICACIÓN PARA CLIENTE:")
        logger.info(f"   Cliente: {cliente_result['nombre_persona']} (ID: {cliente_result['user_id']})")
        logger.info(f"   Servicio: {cliente_result['servicio_nombre']}")
        logger.info(f"   Empresa: {cliente_result['empresa_nombre']}")
        logger.info(f"   Estado anterior: {estado_anterior}")
        logger.info(f"   Nuevo estado: {nuevo_estado}")
        logger.info(f"   Mensaje: {mensaje_principal}")
        if observacion:
            logger.info(f"   Observación: {observacion}")
        
        # - Aquí se puede agregar:
        # - Envío de email
        # - Push notification
        # - WebSocket notification
        # - SMS
        
        logger.info(f"Notificación registrada para cliente {cliente_result['user_id']}")
        
    except Exception as e:
        logger.error(f"Error al enviar notificación: {str(e)}")
        raise


async def registrar_cambio_historial(conn, reserva_id: int, usuario_id: str, estado_anterior: str, nuevo_estado: str, observacion: str = None):
    """
    Registra un cambio de estado en el historial de la reserva.
    """
    try:
        # Crear tabla de historial si no existe (esto se haría con migraciones en producción)
        create_table_query = """
            CREATE TABLE IF NOT EXISTS historial_estados (
                id SERIAL PRIMARY KEY,
                reserva_id INTEGER NOT NULL,
                usuario_id VARCHAR(255) NOT NULL,
                estado_anterior VARCHAR(50) NOT NULL,
                nuevo_estado VARCHAR(50) NOT NULL,
                observacion TEXT,
                fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reserva_id) REFERENCES reserva(id_reserva)
            )
        """
        
        await conn.execute(create_table_query)
        
        # Insertar registro en historial
        insert_query = """
            INSERT INTO historial_estados (reserva_id, usuario_id, estado_anterior, nuevo_estado, observacion)
            VALUES ($1, $2, $3, $4, $5)
        """
        
        await conn.execute(insert_query, reserva_id, usuario_id, estado_anterior, nuevo_estado, observacion)
        
        logger.info(f"Historial registrado: Reserva {reserva_id} - {estado_anterior} -> {nuevo_estado}")
        
    except Exception as e:
        logger.error(f"Error al registrar historial: {str(e)}")
        raise


@router.get(
    "/{reserva_id}/historial",
    description="Obtiene el historial de cambios de estado de una reserva."
)
async def obtener_historial_reserva(
    reserva_id: int,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Obtiene el historial de cambios de estado de una reserva.
    """
    
    try:
        conn = await direct_db_service.pool.acquire()
        
        # Verificar que la reserva existe y obtener información
        reserva_query = """
            SELECT r.id_reserva, r.estado, r.id_servicio, s.id_perfil, pe.user_id as proveedor_user_id
            FROM reserva r
            INNER JOIN servicio s ON r.id_servicio = s.id_servicio
            INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            WHERE r.id_reserva = $1
        """
        
        reserva_result = await conn.fetchrow(reserva_query, reserva_id)
        
        if not reserva_result:
            logger.error(f"[GET /reservas/{reserva_id}/historial] Reserva no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_RESERVA_NO_ENCONTRADA
            )
        
        # Verificar permisos (cliente o proveedor)
        es_cliente = str(reserva_result['user_id']) == str(current_user.id)
        es_proveedor = str(reserva_result['proveedor_user_id']) == str(current_user.id)
        
        if not es_cliente and not es_proveedor:
            logger.error(f"[GET /reservas/{reserva_id}/historial] Usuario no tiene permisos")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MSG_NO_PERMISOS_VER_HISTORIAL
            )
        
        # Obtener historial
        historial_query = """
            SELECT h.estado_anterior, h.nuevo_estado, h.observacion, h.fecha_cambio,
                   u.nombre_persona as usuario_nombre
            FROM historial_estados h
            LEFT JOIN users u ON h.usuario_id = u.id
            WHERE h.reserva_id = $1
            ORDER BY h.fecha_cambio DESC
        """
        
        historial_result = await conn.fetch(historial_query, reserva_id)
        
        historial = []
        for row in historial_result:
            historial.append({
                "estado_anterior": row['estado_anterior'],
                "nuevo_estado": row['nuevo_estado'],
                "observacion": row['observacion'],
                "fecha_cambio": row['fecha_cambio'].isoformat() if row['fecha_cambio'] else None,
                "usuario_nombre": row['usuario_nombre']
            })
        
        return {
            "reserva_id": reserva_id,
            "estado_actual": reserva_result['estado'],
            "historial": historial,
            "total_cambios": len(historial)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /reservas/{reserva_id}/historial] Error crítico: {str(e)}")
        logger.error(f"[GET /reservas/{reserva_id}/historial] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_OBTENER_HISTORIAL.format(error=str(e))
        )
    finally:
        await direct_db_service.pool.release(conn)


# Funciones helper para actualizar_estado_reserva
async def get_reserva_with_provider(conn, reserva_id: int) -> dict:
    """Obtiene la información de la reserva con el proveedor asociado"""
    reserva_query = """
        SELECT r.id_reserva, r.estado as estado_actual, r.id_servicio, s.id_perfil, pe.user_id as proveedor_user_id
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        WHERE r.id_reserva = $1
    """
    
    reserva_result = await conn.fetchrow(reserva_query, reserva_id)
    
    if not reserva_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_RESERVA_NO_ENCONTRADA
        )
    
    return reserva_result

def verify_provider_permissions(reserva_result: dict, current_user_id: str) -> None:
    """Verifica que el usuario es el proveedor del servicio"""
    if str(reserva_result['proveedor_user_id']) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MSG_NO_PERMISOS_CAMBIAR_ESTADO
        )

def validate_estado_value(nuevo_estado: str) -> None:
    """Valida que el nuevo estado sea válido"""
    estados_validos = [ESTADO_PENDIENTE, ESTADO_CONFIRMADA, ESTADO_CANCELADA, ESTADO_COMPLETADA]
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_ESTADO_INVALIDO.format(estados=', '.join(estados_validos))
        )

def validate_estado_not_same(estado_actual: str, nuevo_estado: str) -> None:
    """Valida que el nuevo estado no sea el mismo que el actual"""
    if estado_actual == nuevo_estado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_RESERVA_YA_EN_ESTADO.format(estado=estado_actual)
        )

def validate_estado_transition(estado_actual: str, nuevo_estado: str) -> None:
    """Valida que la transición de estado sea permitida"""
    transiciones_validas = {
        ESTADO_PENDIENTE: [ESTADO_CANCELADA, ESTADO_CONFIRMADA],
        ESTADO_CONFIRMADA: [ESTADO_COMPLETADA],
        ESTADO_CANCELADA: [],
        ESTADO_COMPLETADA: []
    }
    
    if nuevo_estado not in transiciones_validas.get(estado_actual, []):
        transiciones_permitidas = transiciones_validas.get(estado_actual, [])
        mensaje = f"Transición de estado inválida. Desde '{estado_actual}' solo se puede cambiar a: {', '.join(transiciones_permitidas) if transiciones_permitidas else 'ningún estado'}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensaje
        )

async def update_reserva_estado(conn, reserva_id: int, nuevo_estado: str) -> dict:
    """Actualiza el estado de la reserva"""
    update_query = """
        UPDATE reserva 
        SET estado = $1
        WHERE id_reserva = $2
        RETURNING id_reserva, estado, fecha, hora_inicio, hora_fin
    """
    
    updated_reserva = await conn.fetchrow(update_query, nuevo_estado, reserva_id)
    
    if not updated_reserva:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_ACTUALIZAR_ESTADO
        )
    
    return updated_reserva

async def get_notification_data(conn, reserva_id: int) -> Optional[dict]:
    """Obtiene los datos necesarios para enviar notificaciones"""
    notif_query = """
        SELECT
            r.id_reserva,
            s.nombre AS servicio_nombre,
            r.fecha,
            r.hora_inicio,
            u_cliente.nombre_persona AS cliente_nombre,
            au_cliente.email AS cliente_email,
            u_prov.nombre_persona AS proveedor_nombre,
            au_prov.email AS proveedor_email
        FROM public.reserva r
        JOIN public.servicio s ON r.id_servicio = s.id_servicio
        JOIN public.perfil_empresa pe ON s.id_perfil = pe.id_perfil
        JOIN public.users u_cliente ON r.user_id = u_cliente.id
        JOIN auth.users au_cliente ON r.user_id = au_cliente.id
        JOIN public.users u_prov ON pe.user_id = u_prov.id
        JOIN auth.users au_prov ON pe.user_id = au_prov.id
        WHERE r.id_reserva = $1
    """
    return await conn.fetchrow(notif_query, reserva_id)

def send_reservation_notification_by_estado(
    nuevo_estado: str,
    notif_data: dict,
    fecha_formatted: str,
    hora_formatted: str
) -> None:
    """Envía la notificación correspondiente según el nuevo estado"""
    if nuevo_estado == ESTADO_CONFIRMADA:
        reserva_notification_service.notify_reserva_confirmada(
            reserva_id=notif_data['id_reserva'],
            servicio_nombre=notif_data['servicio_nombre'],
            fecha=fecha_formatted,
            hora=hora_formatted,
            cliente_nombre=notif_data['cliente_nombre'] or "Cliente",
            cliente_email=notif_data['cliente_email'],
            proveedor_nombre=notif_data['proveedor_nombre'] or "Proveedor",
            proveedor_email=notif_data['proveedor_email']
        )
    elif nuevo_estado == ESTADO_COMPLETADA:
        reserva_notification_service.notify_reserva_completada(
            reserva_id=notif_data['id_reserva'],
            servicio_nombre=notif_data['servicio_nombre'],
            fecha=fecha_formatted,
            hora=hora_formatted,
            cliente_nombre=notif_data['cliente_nombre'] or "Cliente",
            cliente_email=notif_data['cliente_email'],
            proveedor_nombre=notif_data['proveedor_nombre'] or "Proveedor",
            proveedor_email=notif_data['proveedor_email']
        )

async def handle_reservation_notification(
    conn,
    reserva_id: int,
    nuevo_estado: str
) -> None:
    """Maneja el envío de notificaciones cuando cambia el estado"""
    try:
        if nuevo_estado in [ESTADO_CONFIRMADA, ESTADO_COMPLETADA]:
            notif_data = await get_notification_data(conn, reserva_id)
            
            if notif_data:
                fecha_formatted = notif_data['fecha'].strftime(FORMATO_FECHA_DD_MM_YYYY) if notif_data['fecha'] else ""
                hora_formatted = str(notif_data['hora_inicio']) if notif_data['hora_inicio'] else ""
                
                send_reservation_notification_by_estado(
                    nuevo_estado,
                    notif_data,
                    fecha_formatted,
                    hora_formatted
                )
    except Exception as e:
        logger.warning(f"[PUT /reservas/{reserva_id}/estado] Error al enviar notificación: {str(e)}")

def build_reserva_estado_response(updated_reserva: dict, nuevo_estado: str, observacion: Optional[str]) -> dict:
    """Construye la respuesta de la reserva actualizada"""
    return {
        "message": f"Estado de la reserva actualizado a '{nuevo_estado}' exitosamente",
        "reserva": {
            "id_reserva": updated_reserva['id_reserva'],
            "estado": updated_reserva['estado'],
            "fecha": updated_reserva['fecha'].isoformat() if updated_reserva['fecha'] else None,
            "hora_inicio": str(updated_reserva['hora_inicio']) if updated_reserva['hora_inicio'] else None,
            "hora_fin": str(updated_reserva['hora_fin']) if updated_reserva['hora_fin'] else None
        },
        "observacion": observacion,
        "notificacion_enviada": True
    }

@router.put(
    "/{reserva_id}/estado",
    description="Actualiza el estado de una reserva. Solo el proveedor del servicio puede cambiar el estado."
)
async def actualizar_estado_reserva(
    reserva_id: int,
    estado_update: ReservaEstadoUpdate,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Actualiza el estado de una reserva.
    Solo el proveedor del servicio puede cambiar el estado.
    """
    try:
        conn = await direct_db_service.pool.acquire()
        
        try:
            # Obtener información de la reserva
            reserva_result = await get_reserva_with_provider(conn, reserva_id)
            
            # Verificar permisos del proveedor
            verify_provider_permissions(reserva_result, current_user.id)
            
            # Validar nuevo estado
            estado_actual = reserva_result['estado_actual']
            nuevo_estado = estado_update.nuevo_estado.lower()
            
            validate_estado_value(nuevo_estado)
            validate_estado_not_same(estado_actual, nuevo_estado)
            validate_estado_transition(estado_actual, nuevo_estado)
            
            # Actualizar estado de la reserva
            updated_reserva = await update_reserva_estado(conn, reserva_id, nuevo_estado)
            
            # Registrar cambio en historial
            try:
                await registrar_cambio_historial(
                    conn,
                    reserva_id,
                    current_user.id,
                    estado_actual,
                    nuevo_estado,
                    estado_update.observacion
                )
            except Exception as e:
                logger.warning(f"[PUT /reservas/{reserva_id}/estado] Error al registrar historial: {str(e)}")
            
            # Enviar notificación por correo
            await handle_reservation_notification(conn, reserva_id, nuevo_estado)
            
            logger.info(f"[PUT /reservas/{reserva_id}/estado] Estado actualizado a '{nuevo_estado}'")
            
            # Construir y retornar respuesta
            return build_reserva_estado_response(updated_reserva, nuevo_estado, estado_update.observacion)
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUT /reservas/{reserva_id}/estado] Error: {str(e)}")
        logger.error(f"[PUT /reservas/{reserva_id}/estado] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_ACTUALIZAR_ESTADO_FORMAT.format(error=str(e))
        )


# Funciones helper para cancelar_reserva
async def get_reserva_with_cliente_and_proveedor(conn, reserva_id: int) -> dict:
    """Obtiene la información de la reserva con cliente y proveedor"""
    reserva_query = """
        SELECT r.id_reserva, r.estado as estado_actual, r.id_servicio, r.user_id as cliente_user_id,
               s.id_perfil, pe.user_id as proveedor_user_id
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        WHERE r.id_reserva = $1
    """
    
    reserva_result = await conn.fetchrow(reserva_query, reserva_id)
    
    if not reserva_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_RESERVA_NO_ENCONTRADA
        )
    
    return reserva_result

def verify_cancel_permissions(
    reserva_result: dict,
    current_user_id: str
) -> None:
    """Verifica que el usuario tiene permisos para cancelar la reserva"""
    cliente_user_id = str(reserva_result['cliente_user_id'])
    proveedor_user_id = str(reserva_result['proveedor_user_id'])
    current_user_id_str = str(current_user_id)
    
    if current_user_id_str != cliente_user_id and current_user_id_str != proveedor_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MSG_NO_AUTORIZADO_GESTIONAR
        )

def validate_reserva_estado_pendiente(estado_actual: str) -> None:
    """Valida que la reserva esté en estado pendiente"""
    if estado_actual != ESTADO_PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_SOLO_CANCELAR_PENDIENTE.format(estado=estado_actual)
        )

def validate_motivo_cancelacion(motivo: Optional[str]) -> None:
    """Valida que el motivo de cancelación no esté vacío"""
    if not motivo or not motivo.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_DEBE_INGRESAR_MOTIVO
        )

async def cancel_reserva_estado(conn, reserva_id: int) -> dict:
    """Cancela la reserva actualizando su estado"""
    update_query = """
        UPDATE reserva 
        SET estado = $2
        WHERE id_reserva = $1
        RETURNING id_reserva, estado, fecha, hora_inicio, hora_fin
    """
    
    updated_reserva = await conn.fetchrow(update_query, reserva_id, ESTADO_CANCELADA)
    
    if not updated_reserva:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_CANCELAR_RESERVA
        )
    
    return updated_reserva

async def send_cancellation_notification(
    conn,
    reserva_id: int,
    motivo: str
) -> None:
    """Envía notificación por correo cuando se cancela una reserva"""
    try:
        notif_query = """
            SELECT
                r.id_reserva,
                s.nombre AS servicio_nombre,
                r.fecha,
                r.hora_inicio,
                u_cliente.nombre_persona AS cliente_nombre,
                au_cliente.email AS cliente_email,
                u_prov.nombre_persona AS proveedor_nombre,
                au_prov.email AS proveedor_email
            FROM reserva r
            JOIN servicio s ON r.id_servicio = s.id_servicio
            JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            JOIN public.users u_cliente ON r.user_id = u_cliente.id
            JOIN auth.users au_cliente ON r.user_id = au_cliente.id
            JOIN public.users u_prov ON pe.user_id = u_prov.id
            JOIN auth.users au_prov ON pe.user_id = au_prov.id
            WHERE r.id_reserva = $1
        """
        notif_data = await conn.fetchrow(notif_query, reserva_id)
        
        if notif_data:
            fecha_formatted = notif_data['fecha'].strftime(FORMATO_FECHA_DD_MM_YYYY) if notif_data['fecha'] else ""
            hora_formatted = str(notif_data['hora_inicio']) if notif_data['hora_inicio'] else ""
            
            reserva_notification_service.notify_reserva_cancelada(
                reserva_id=notif_data['id_reserva'],
                servicio_nombre=notif_data['servicio_nombre'],
                fecha=fecha_formatted,
                hora=hora_formatted,
                cliente_nombre=notif_data['cliente_nombre'] or "Cliente",
                cliente_email=notif_data['cliente_email'],
                proveedor_nombre=notif_data['proveedor_nombre'] or "Proveedor",
                proveedor_email=notif_data['proveedor_email'],
                motivo=motivo
            )
    except Exception as e:
        logger.warning(f"[PUT /reservas/{reserva_id}/cancelar] Error al enviar notificación: {str(e)}")

def determine_cancelled_by(current_user_id: str, cliente_user_id: str) -> str:
    """Determina quién canceló la reserva"""
    return "cliente" if current_user_id == cliente_user_id else "proveedor"

def build_cancelacion_response(
    updated_reserva: dict,
    motivo: str,
    quien_cancelo: str
) -> dict:
    """Construye la respuesta de cancelación"""
    return {
        "message": "Reserva cancelada",
        "reserva": {
            "id_reserva": updated_reserva['id_reserva'],
            "estado": updated_reserva['estado'],
            "fecha": updated_reserva['fecha'].isoformat() if updated_reserva['fecha'] else None,
            "hora_inicio": str(updated_reserva['hora_inicio']) if updated_reserva['hora_inicio'] else None,
            "hora_fin": str(updated_reserva['hora_fin']) if updated_reserva['hora_fin'] else None
        },
        "motivo": motivo,
        "cancelado_por": quien_cancelo,
        "notificacion_enviada": True
    }

@router.put(
    "/{reserva_id}/cancelar",
    description="Cancela una reserva. Puede ser usado tanto por el cliente como por el proveedor del servicio."
)
async def cancelar_reserva(
    reserva_id: int,
    cancelacion_data: ReservaCancelacionData,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Cancela una reserva.
    Puede ser usado tanto por el cliente como por el proveedor del servicio.
    Solo se puede cancelar si el estado es 'pendiente'.
    El motivo de cancelación es obligatorio.
    """
    try:
        conn = await direct_db_service.pool.acquire()
        
        try:
            # Obtener información de la reserva
            reserva_result = await get_reserva_with_cliente_and_proveedor(conn, reserva_id)
            
            # Verificar permisos para cancelar
            verify_cancel_permissions(reserva_result, current_user.id)
            
            # Validar estado y motivo
            estado_actual = reserva_result['estado_actual']
            validate_reserva_estado_pendiente(estado_actual)
            validate_motivo_cancelacion(cancelacion_data.motivo)
            
            # Cancelar la reserva
            updated_reserva = await cancel_reserva_estado(conn, reserva_id)
            
            # Registrar en el historial
            try:
                await registrar_cambio_historial(
                    conn,
                    reserva_id,
                    current_user.id,
                    estado_actual,
                    ESTADO_CANCELADA,
                    cancelacion_data.motivo
                )
            except Exception as e:
                logger.warning(f"[PUT /reservas/{reserva_id}/cancelar] Error al registrar historial: {str(e)}")
            
            # Enviar notificación por correo
            await send_cancellation_notification(conn, reserva_id, cancelacion_data.motivo)
            
            # Determinar quién canceló
            current_user_id = str(current_user.id)
            cliente_user_id = str(reserva_result['cliente_user_id'])
            quien_cancelo = determine_cancelled_by(current_user_id, cliente_user_id)
            
            logger.info(f"[PUT /reservas/{reserva_id}/cancelar] Reserva cancelada por {quien_cancelo}")
            
            # Construir y retornar respuesta
            return build_cancelacion_response(updated_reserva, cancelacion_data.motivo, quien_cancelo)
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUT /reservas/{reserva_id}/cancelar] Error: {str(e)}")
        logger.error(f"[PUT /reservas/{reserva_id}/cancelar] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_CANCELAR_RESERVA_FORMAT.format(error=str(e))
        )
    finally:
        await direct_db_service.pool.release(conn)


# Funciones helper para confirmar_reserva
async def get_reserva_basic_info(conn, reserva_id: int) -> dict:
    """Obtiene la información básica de la reserva"""
    reserva_query = """
        SELECT 
            r.id_reserva, 
            r.estado as estado_actual, 
            r.user_id as cliente_user_id,
            r.id_servicio,
            r.fecha,
            r.hora_inicio,
            r.hora_fin
        FROM reserva r
        WHERE r.id_reserva = $1
    """
    
    reserva_result = await conn.fetchrow(reserva_query, reserva_id)
    
    if not reserva_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_RESERVA_NO_ENCONTRADA
        )
    
    return reserva_result

def verify_cliente_ownership(reserva_result: dict, current_user_id: str) -> None:
    """Verifica que el usuario es el cliente dueño de la reserva"""
    cliente_user_id = str(reserva_result['cliente_user_id'])
    current_user_id_str = str(current_user_id)
    
    if current_user_id_str != cliente_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MSG_NO_AUTORIZADO_GESTIONAR
        )

def validate_reserva_estado_for_confirmation(estado_actual: str) -> None:
    """Valida que la reserva esté en estado pendiente para confirmar"""
    if estado_actual != ESTADO_PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_NO_POSIBLE_ACCION_ESTADO
        )

async def confirm_reserva_estado(conn, reserva_id: int) -> dict:
    """Confirma la reserva actualizando su estado"""
    update_query = """
        UPDATE reserva 
        SET estado = $2
        WHERE id_reserva = $1
        RETURNING id_reserva, estado, fecha, hora_inicio, hora_fin
    """
    
    updated_reserva = await conn.fetchrow(update_query, reserva_id, ESTADO_CONFIRMADA)
    
    if not updated_reserva:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_CONFIRMAR_RESERVA
        )
    
    return updated_reserva

async def send_confirmation_notification(conn, reserva_id: int) -> None:
    """Envía notificación por correo cuando se confirma una reserva"""
    try:
        notif_query = """
            SELECT
                r.id_reserva,
                s.nombre AS servicio_nombre,
                r.fecha,
                r.hora_inicio,
                u_cliente.nombre_persona AS cliente_nombre,
                au_cliente.email AS cliente_email,
                u_prov.nombre_persona AS proveedor_nombre,
                au_prov.email AS proveedor_email
            FROM public.reserva r
            JOIN public.servicio s ON r.id_servicio = s.id_servicio
            JOIN public.perfil_empresa pe ON s.id_perfil = pe.id_perfil
            JOIN public.users u_cliente ON r.user_id = u_cliente.id
            JOIN auth.users au_cliente ON r.user_id = au_cliente.id
            JOIN public.users u_prov ON pe.user_id = u_prov.id
            JOIN auth.users au_prov ON pe.user_id = au_prov.id
            WHERE r.id_reserva = $1
        """
        notif_data = await conn.fetchrow(notif_query, reserva_id)
        
        if notif_data:
            fecha_formatted = notif_data['fecha'].strftime(FORMATO_FECHA_DD_MM_YYYY) if notif_data['fecha'] else ""
            hora_formatted = str(notif_data['hora_inicio']) if notif_data['hora_inicio'] else ""
            
            reserva_notification_service.notify_reserva_confirmada(
                reserva_id=notif_data['id_reserva'],
                servicio_nombre=notif_data['servicio_nombre'],
                fecha=fecha_formatted,
                hora=hora_formatted,
                cliente_nombre=notif_data['cliente_nombre'] or "Cliente",
                cliente_email=notif_data['cliente_email'],
                proveedor_nombre=notif_data['proveedor_nombre'] or "Proveedor",
                proveedor_email=notif_data['proveedor_email']
            )
    except Exception as e:
        logger.warning(f"[PUT /reservas/{reserva_id}/confirmar] Error al enviar notificación: {str(e)}")

def build_confirmacion_response(updated_reserva: dict) -> dict:
    """Construye la respuesta de confirmación"""
    return {
        "message": "Reserva confirmada",
        "reserva": {
            "id_reserva": updated_reserva['id_reserva'],
            "estado": updated_reserva['estado'],
            "fecha": updated_reserva['fecha'].isoformat() if updated_reserva['fecha'] else None,
            "hora_inicio": str(updated_reserva['hora_inicio']) if updated_reserva['hora_inicio'] else None,
            "hora_fin": str(updated_reserva['hora_fin']) if updated_reserva['hora_fin'] else None
        },
        "confirmado_por": "cliente",
        "notificacion_enviada": True
    }

@router.put(
    "/{reserva_id}/confirmar",
    description="Confirma una reserva. Solo el cliente dueño de la reserva puede confirmarla."
)
async def confirmar_reserva(
    reserva_id: int,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Confirma una reserva.
    Solo el cliente dueño de la reserva puede confirmarla.
    Solo se puede confirmar si el estado es 'pendiente'.
    """
    try:
        conn = await direct_db_service.pool.acquire()
        
        try:
            # Obtener información de la reserva
            reserva_result = await get_reserva_basic_info(conn, reserva_id)
            
            # Verificar que el usuario es el cliente dueño
            verify_cliente_ownership(reserva_result, current_user.id)
            
            # Validar estado para confirmación
            estado_actual = reserva_result['estado_actual']
            validate_reserva_estado_for_confirmation(estado_actual)
            
            # Obtener información de la reserva para validar conflicto
            servicio_id = reserva_result.get('id_servicio')
            fecha_reserva = reserva_result.get('fecha')
            hora_inicio = reserva_result.get('hora_inicio')
            hora_fin = reserva_result.get('hora_fin')
            
            # Validar que no exista otra reserva confirmada en el mismo servicio, fecha y horario
            # (excluyendo la reserva actual que se está confirmando)
            if servicio_id and fecha_reserva and hora_inicio and hora_fin:
                verificacion_query = """
                    SELECT id_reserva, fecha, hora_inicio, hora_fin, estado
                    FROM reserva
                    WHERE id_servicio = $1
                    AND fecha = $2
                    AND estado = $3
                    AND id_reserva != $4
                    AND hora_inicio < $5
                    AND hora_fin > $6
                """
                
                reserva_confirmada = await conn.fetchrow(
                    verificacion_query,
                    servicio_id,
                    fecha_reserva,
                    ESTADO_CONFIRMADA,
                    reserva_id,  # Excluir la reserva actual
                    hora_fin,
                    hora_inicio
                )
                
                if reserva_confirmada:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El horario seleccionado (fecha: {fecha_reserva.strftime(FORMATO_FECHA_DD_MM_YYYY)}, hora: {hora_inicio.strftime('%H:%M')}) ya está reservado y confirmado por otro cliente. No se puede confirmar esta reserva."
                    )
            
            # Confirmar la reserva
            updated_reserva = await confirm_reserva_estado(conn, reserva_id)
            
            # Registrar en el historial
            try:
                await registrar_cambio_historial(
                    conn,
                    reserva_id,
                    current_user.id,
                    estado_actual,
                    ESTADO_CONFIRMADA,
                    'Reserva confirmada por el cliente'
                )
            except Exception as e:
                logger.warning(f"[PUT /reservas/{reserva_id}/confirmar] Error al registrar historial: {str(e)}")
            
            # Enviar notificación por correo
            await send_confirmation_notification(conn, reserva_id)
            
            logger.info(f"[PUT /reservas/{reserva_id}/confirmar] Reserva confirmada")
            
            # Construir y retornar respuesta
            return build_confirmacion_response(updated_reserva)
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUT /reservas/{reserva_id}/confirmar] Error: {str(e)}")
        logger.error(f"[PUT /reservas/{reserva_id}/confirmar] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_CONFIRMAR_RESERVA_FORMAT.format(error=str(e))
        )
    finally:
        await direct_db_service.pool.release(conn)

@router.get(
    "/servicio/{servicio_id}/confirmadas",
    description="Obtiene las reservas confirmadas de un servicio para verificar disponibilidad de horarios"
)
async def obtener_reservas_confirmadas_servicio(
    servicio_id: int
):
    """
    Endpoint público para obtener las reservas confirmadas de un servicio.
    Útil para filtrar horarios no disponibles en el calendario de reservas.
    """
    try:
        conn = await direct_db_service.get_connection()
        
        try:
            # Obtener reservas confirmadas del servicio
            reservas_query = """
                SELECT 
                    fecha,
                    hora_inicio,
                    hora_fin
                FROM reserva
                WHERE id_servicio = $1 
                AND estado = 'confirmada'
                AND fecha >= CURRENT_DATE
                ORDER BY fecha, hora_inicio
            """
            
            reservas_result = await conn.fetch(reservas_query, servicio_id)
            
            # Formatear resultado
            reservas = []
            for reserva in reservas_result:
                reservas.append({
                    "fecha": str(reserva['fecha']),
                    "hora_inicio": str(reserva['hora_inicio']) if reserva['hora_inicio'] else None,
                    "hora_fin": str(reserva['hora_fin']) if reserva['hora_fin'] else None
                })
            
            logger.info(f"🔍 [GET /reservas/servicio/{servicio_id}/confirmadas] {len(reservas)} reservas confirmadas encontradas")
            
            return {"reservas": reservas}
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        logger.error(f"❌ [GET /reservas/servicio/{servicio_id}/confirmadas] Error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener reservas confirmadas: {str(e)}"
        )


