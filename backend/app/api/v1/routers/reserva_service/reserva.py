# backend/app/api/v1/routers/reserva_service/reserva.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.reserva_servicio.reserva import ReservaIn, ReservaOut, ReservaEstadoUpdate, ReservaCancelacionData
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
import logging
from typing import Optional
from app.services.direct_db_service import direct_db_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reservas", tags=["reservas"])

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
    logger.info(f"🔍 [GET /mis-reservas-test] ========== INICIO TEST ==========")
    logger.info(f"🔍 [GET /mis-reservas-test] User ID: {current_user.id}")
    logger.info(f"🔍 [GET /mis-reservas-test] User Email: {current_user.email}")
    
    try:
        conn = await direct_db_service.get_connection()
        logger.info(f"🔍 [GET /mis-reservas-test] Conexión a BD obtenida exitosamente")
        
        # Query mejorado para obtener datos reales
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
        
        logger.info(f"🔍 [GET /mis-reservas-test] Ejecutando query simple...")
        result = await conn.fetch(simple_query, current_user.id)
        logger.info(f"📊 [GET /mis-reservas-test] Resultados obtenidos: {len(result)}")
        
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
        
        logger.info(f"✅ [GET /mis-reservas-test] Respuesta preparada exitosamente")
        logger.info(f"🔍 [GET /mis-reservas-test] ========== FIN TEST ==========")
        
        return {
            "reservas": reservas_list,
            "total": len(reservas_list),
            "message": "Test exitoso"
        }
        
    except Exception as e:
        logger.error(f"❌ [GET /mis-reservas-test] Error: {str(e)}")
        import traceback
        logger.error(f"❌ [GET /mis-reservas-test] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en test: {str(e)}"
        )
    finally:
        if 'conn' in locals():
            await direct_db_service.pool.release(conn)

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
        #from app.services.direct_db_service import direct_db_service
        
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
            
            # Generar nuevo ID entero para la reserva
            # Nota: Si id_reserva es auto-increment, no necesitamos generar un ID
            # Pero si no es auto-increment, necesitamos obtener el siguiente ID
            reserva_id = None  # Dejar que la base de datos genere el ID
            
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
            
            # Obtener horarios del frontend
            from datetime import time, datetime, timedelta, date
            
            # Usar la hora enviada por el frontend o valores por defecto
            if reserva.hora_inicio:
                hora_inicio_str = reserva.hora_inicio
                logger.info(f"🔍 [POST /reservas] Hora recibida del frontend: {hora_inicio_str}")
            else:
                hora_inicio_str = "09:00"  # 9:00 AM por defecto
                logger.info(f"🔍 [POST /reservas] Usando hora por defecto: {hora_inicio_str}")
            
            # Convertir string a time object
            try:
                hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
            except ValueError:
                hora_inicio = time(9, 0)  # Fallback a 9:00 AM
                logger.warning(f"⚠️ [POST /reservas] Error al parsear hora {hora_inicio_str}, usando 9:00 AM")
            
            # Calcular hora fin (1 hora después)
            hora_fin = (datetime.combine(date.today(), hora_inicio) + timedelta(hours=1)).time()
            
            logger.info(f"🔍 [POST /reservas] Horarios calculados: {hora_inicio} - {hora_fin}")
            
            # Preparar parámetros para la inserción
            user_uuid = current_user.id  # Ya es UUID, no necesita conversión
            logger.info(f"🔍 [POST /reservas] UUID del usuario: {user_uuid}")
            logger.info(f"🔍 [POST /reservas] UUID de reserva generado: {reserva_id}")
            
            insert_query = """
                INSERT INTO reserva (id_servicio, user_id, descripcion, observacion, fecha, hora_inicio, hora_fin, estado)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id_reserva, id_servicio, user_id, descripcion, observacion, fecha, hora_inicio, hora_fin, estado
            """
            logger.info(f"🔍 [POST /reservas] Query de inserción preparado")
            logger.info(f"🔍 [POST /reservas] Parámetros de inserción:")
            logger.info(f"  - id_servicio: {servicio_id}")
            logger.info(f"  - user_id: {user_uuid}")
            logger.info(f"  - descripcion: {reserva.descripcion}")
            logger.info(f"  - observacion: {reserva.observacion}")
            logger.info(f"  - fecha: {reserva.fecha}")
            logger.info(f"  - hora_inicio: {hora_inicio}")
            logger.info(f"  - hora_fin: {hora_fin}")
            logger.info(f"  - estado: pendiente")
            
            logger.info(f"🔍 [POST /reservas] Ejecutando inserción...")
            nueva_reserva = await conn.fetchrow(
                insert_query,
                servicio_id,       # $1 = id_servicio (int)
                user_uuid,         # $2 = user_id (UUID)
                reserva.descripcion,  # $3 = descripcion (string)
                reserva.observacion,  # $4 = observacion (string)
                reserva.fecha,        # $5 = fecha (date)
                hora_inicio,         # $6 = hora_inicio (time)
                hora_fin,            # $7 = hora_fin (time)
                "pendiente"          # $8 = estado (string)
            )
            logger.info(f"🔍 [POST /reservas] Inserción ejecutada")
            logger.info(f"🔍 [POST /reservas] Reserva creada: {nueva_reserva}")
            
            logger.info(f"✅ [POST /reservas] Reserva {nueva_reserva['id_reserva']} creada exitosamente")
            
            # Convertir a formato de respuesta
            logger.info(f"🔍 [POST /reservas] Preparando respuesta...")
            try:
                # Convertir id_reserva a UUID si es necesario
                import uuid
                if isinstance(nueva_reserva['id_reserva'], int):
                    # Si id_reserva es un entero, generar un UUID basado en él
                    reserva_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, str(nueva_reserva['id_reserva']))
                else:
                    reserva_uuid = nueva_reserva['id_reserva']
                
                # Convertir fecha a date puro (sin tiempo)
                from datetime import date
                if hasattr(nueva_reserva['fecha'], 'date'):
                    fecha_pura = nueva_reserva['fecha'].date()
                else:
                    fecha_pura = nueva_reserva['fecha']
                
                respuesta = {
                    "id": reserva_uuid,  # UUID correcto
                    "id_servicio": nueva_reserva['id_servicio'],
                    "user_id": nueva_reserva['user_id'],  # Campo requerido por ReservaOut schema
                    "descripcion": nueva_reserva['descripcion'],
                    "observacion": nueva_reserva['observacion'],
                    "fecha": fecha_pura,  # Fecha sin tiempo
                    "hora_inicio": str(nueva_reserva['hora_inicio']) if nueva_reserva['hora_inicio'] else None,
                    "hora_fin": str(nueva_reserva['hora_fin']) if nueva_reserva['hora_fin'] else None,
                    "estado": nueva_reserva['estado'],
                    "id_disponibilidad": None  # Compatibilidad con schema anterior
                }
                logger.info(f"🔍 [POST /reservas] Respuesta preparada: {respuesta}")
                logger.info(f"🔍 [POST /reservas] ========== FIN CREAR RESERVA EXITOSO ==========")
                return respuesta
            except Exception as response_error:
                logger.error(f"❌ [POST /reservas] Error al construir respuesta: {response_error}")
                logger.error(f"❌ [POST /reservas] Datos de nueva_reserva: {nueva_reserva}")
                logger.error(f"❌ [POST /reservas] Tipo de nueva_reserva: {type(nueva_reserva)}")
                if hasattr(nueva_reserva, 'keys'):
                    logger.error(f"❌ [POST /reservas] Keys disponibles: {list(nueva_reserva.keys())}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error al construir respuesta: {str(response_error)}"
                )
            
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
    logger.info(f"🔍 [GET /mis-reservas] ========== INICIO OBTENER MIS RESERVAS ==========")
    logger.info(f"🔍 [GET /mis-reservas] User ID: {current_user.id}")
    logger.info(f"🔍 [GET /mis-reservas] User Type: {type(current_user.id)}")
    logger.info(f"🔍 [GET /mis-reservas] Filtros: search={search}, servicio={nombre_servicio}, empresa={nombre_empresa}, estado={estado}")
    logger.info(f"🔍 [GET /mis-reservas] Paginación: limit={limit}, offset={offset}")
    logger.info(f"🔍 [GET /mis-reservas] Parámetros recibidos: search={search}, nombre_servicio={nombre_servicio}, nombre_empresa={nombre_empresa}, fecha_desde={fecha_desde}, fecha_hasta={fecha_hasta}, estado={estado}, nombre_contacto={nombre_contacto}")
    
    try:
        # Validaciones básicas de parámetros
        if limit is None or limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
            
        if offset is None or offset < 0:
            offset = 0
            
        logger.info(f"🔍 [GET /mis-reservas] Parámetros validados: limit={limit}, offset={offset}")
        
        conn = await direct_db_service.get_connection()
        logger.info(f"🔍 [GET /mis-reservas] Conexión a BD obtenida exitosamente")
        
        try:
            base_query = """
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
                LEFT JOIN calificacion cal_cliente ON r.id_reserva = cal_cliente.id_reserva AND cal_cliente.rol_emisor = 'cliente'
                LEFT JOIN calificacion cal_proveedor ON r.id_reserva = cal_proveedor.id_reserva AND cal_proveedor.rol_emisor = 'proveedor'
                WHERE r.user_id = $1
            """
            
            where_conditions = []
            params = [current_user.id]
            param_count = 1
            logger.info(f"🔍 [GET /mis-reservas] Parámetros iniciales: {params}")
            logger.info(f"🔍 [GET /mis-reservas] Construyendo condiciones WHERE...")
            
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
                params.append(fecha_desde)
                logger.info(f"🔍 [GET /mis-reservas] Filtro fecha_desde: {fecha_desde}")
            
            if fecha_hasta:
                param_count += 1
                where_conditions.append(f"r.fecha <= ${param_count}")
                params.append(fecha_hasta)
                logger.info(f"🔍 [GET /mis-reservas] Filtro fecha_hasta: {fecha_hasta}")
            
            if estado and estado.strip():
                param_count += 1
                where_conditions.append(f"r.estado = ${param_count}")
                params.append(estado.strip().lower())
                logger.info(f"🔍 [GET /mis-reservas] Filtro estado aplicado: {estado.strip().lower()}")
                logger.info(f"🔍 [GET /mis-reservas] Condición WHERE agregada: r.estado = ${param_count}")
            else:
                logger.info(f"🔍 [GET /mis-reservas] No se aplica filtro de estado (estado={estado})")
            
            if nombre_contacto and nombre_contacto.strip():
                param_count += 1
                where_conditions.append(f"LOWER(u.nombre_persona) LIKE LOWER(${param_count})")
                params.append(f"%{nombre_contacto.strip()}%")
            
            if where_conditions:
                base_query += " AND " + " AND ".join(where_conditions)
                logger.info(f"🔍 [GET /mis-reservas] Condiciones WHERE agregadas: {where_conditions}")
            
            count_query = f"""
                SELECT COUNT(*) as total
                FROM reserva r
                INNER JOIN servicio s ON r.id_servicio = s.id_servicio
                INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
                INNER JOIN users u ON pe.user_id = u.id
                WHERE r.user_id = $1
            """
            
            if where_conditions:
                count_query += " AND " + " AND ".join(where_conditions)
                logger.info(f"🔍 [GET /mis-reservas] Count query con condiciones: {count_query}")
            
            logger.info(f"🔍 [GET /mis-reservas] Ejecutando conteo con query: {count_query}")
            logger.info(f"🔍 [GET /mis-reservas] Parámetros para count: {params}")
            total_result = await conn.fetchrow(count_query, *params)
            total_count = total_result['total'] if total_result else 0
            logger.info(f"📊 [GET /mis-reservas] Total de reservas encontradas: {total_count}")
            
            base_query += f"""
                ORDER BY r.fecha DESC, r.created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            logger.info(f"🔍 [GET /mis-reservas] Query principal final: {base_query}")
            logger.info(f"🔍 [GET /mis-reservas] Parámetros finales: {params}")
            logger.info(f"🔍 [GET /mis-reservas] Ejecutando query principal...")
            
            reservas_result = await conn.fetch(base_query, *params)
            logger.info(f"📊 [GET /mis-reservas] Reservas obtenidas: {len(reservas_result)}")
            
            reservas_list = []
            for row in reservas_result:
                ya_calificado = row['ya_calificado_por_cliente']
                logger.info(f"🔍 [GET /mis-reservas] Reserva {row['id_reserva']} - Estado: {row['estado']}, Ya calificado: {ya_calificado}")
                
                reserva_dict = {
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
                reservas_list.append(reserva_dict)
            
            total_pages = (total_count + limit - 1) // limit
            current_page = (offset // limit) + 1
            
            pagination_info = {
                "total": total_count,
                "page": current_page,
                "limit": limit,
                "offset": offset,
                "total_pages": total_pages,
                "has_next": offset + limit < total_count,
                "has_prev": offset > 0
            }
            
            logger.info(f"✅ [GET /mis-reservas] Respuesta preparada exitosamente")
            logger.info(f"📊 [GET /mis-reservas] Paginación: {pagination_info}")
            logger.info(f"🔍 [GET /mis-reservas] ========== FIN OBTENER MIS RESERVAS ==========")
            
            return {
                "reservas": reservas_list,
                "pagination": pagination_info
            }
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET /mis-reservas] Error crítico: {str(e)}")
        logger.error(f"❌ [GET /mis-reservas] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [GET /mis-reservas] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al obtener reservas: {str(e)}"
        )


@router.get(
    "/reservas-proveedor",
    description="Obtiene las reservas solicitadas por clientes para los servicios del proveedor autenticado."
)
async def obtener_reservas_proveedor(
    current_user: SupabaseUser = Depends(get_current_user),
    search: Optional[str] = Query(None),
    nombre_servicio: Optional[str] = Query(None),
    nombre_cliente: Optional[str] = Query(None),
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
    logger.info(f"🔍 [GET /reservas-proveedor] ========== INICIO RESERVAS PROVEEDOR ==========")
    logger.info(f"🔍 [GET /reservas-proveedor] User ID: {current_user.id}")
    logger.info(f"🔍 [GET /reservas-proveedor] Filtros: search={search}, servicio={nombre_servicio}, cliente={nombre_cliente}, estado={estado}")
    logger.info(f"🔍 [GET /reservas-proveedor] Paginación: limit={limit}, offset={offset}")
    
    try:
        # Validaciones básicas de parámetros
        if limit is None or limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
            
        if offset is None or offset < 0:
            offset = 0
            
        logger.info(f"🔍 [GET /reservas-proveedor] Parámetros validados: limit={limit}, offset={offset}")
        
        conn = await direct_db_service.get_connection()
        logger.info(f"🔍 [GET /reservas-proveedor] Conexión a BD obtenida exitosamente")
        
        try:
            # Primero, obtener el perfil de empresa del proveedor
            perfil_query = """
                SELECT id_perfil, nombre_fantasia, razon_social
                FROM perfil_empresa 
                WHERE user_id = $1 AND verificado = true
            """
            perfil_result = await conn.fetchrow(perfil_query, current_user.id)
            
            if not perfil_result:
                logger.warning(f"❌ [GET /reservas-proveedor] Proveedor no encontrado o no verificado: {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes un perfil de proveedor verificado."
                )
            
            proveedor_id = perfil_result['id_perfil']
            logger.info(f"✅ [GET /reservas-proveedor] Proveedor encontrado: {perfil_result['nombre_fantasia']} (ID: {proveedor_id})")
            
            # Query principal para obtener reservas de los servicios del proveedor
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
                    c.nombre as nombre_categoria,
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
                LEFT JOIN calificacion cal_cliente ON r.id_reserva = cal_cliente.id_reserva AND cal_cliente.rol_emisor = 'cliente'
                LEFT JOIN calificacion cal_proveedor ON r.id_reserva = cal_proveedor.id_reserva AND cal_proveedor.rol_emisor = 'proveedor'
                WHERE s.id_perfil = $1
            """
            
            where_conditions = []
            params = [proveedor_id]
            param_count = 1
            logger.info(f"🔍 [GET /reservas-proveedor] Parámetros iniciales: {params}")
            logger.info(f"🔍 [GET /reservas-proveedor] Construyendo condiciones WHERE...")
            
            if search and search.strip():
                param_count += 1
                where_conditions.append(f"""
                    (LOWER(s.nombre) LIKE LOWER(${param_count}) 
                    OR LOWER(u.nombre_persona) LIKE LOWER(${param_count})
                    OR LOWER(r.descripcion) LIKE LOWER(${param_count}))
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
            
            if fecha_desde:
                param_count += 1
                where_conditions.append(f"r.fecha >= ${param_count}")
                params.append(fecha_desde)
                logger.info(f"🔍 [GET /reservas-proveedor] Filtro fecha_desde: {fecha_desde}")
            
            if fecha_hasta:
                param_count += 1
                where_conditions.append(f"r.fecha <= ${param_count}")
                params.append(fecha_hasta)
                logger.info(f"🔍 [GET /reservas-proveedor] Filtro fecha_hasta: {fecha_hasta}")
            
            if estado and estado.strip():
                param_count += 1
                where_conditions.append(f"r.estado = ${param_count}")
                params.append(estado.strip().lower())
            
            if where_conditions:
                base_query += " AND " + " AND ".join(where_conditions)
                logger.info(f"🔍 [GET /reservas-proveedor] Condiciones WHERE agregadas: {where_conditions}")
            
            # Query para contar total
            count_query = f"""
                SELECT COUNT(*) as total
                FROM reserva r
                INNER JOIN servicio s ON r.id_servicio = s.id_servicio
                INNER JOIN users u ON r.user_id = u.id
                WHERE s.id_perfil = $1
            """
            
            if where_conditions:
                count_query += " AND " + " AND ".join(where_conditions)
                logger.info(f"🔍 [GET /reservas-proveedor] Count query con condiciones: {count_query}")
            
            logger.info(f"🔍 [GET /reservas-proveedor] Ejecutando conteo con query: {count_query}")
            logger.info(f"🔍 [GET /reservas-proveedor] Parámetros para count: {params}")
            total_result = await conn.fetchrow(count_query, *params)
            total_count = total_result['total'] if total_result else 0
            logger.info(f"📊 [GET /reservas-proveedor] Total de reservas encontradas: {total_count}")
            
            # Agregar ORDER BY y LIMIT al query principal
            base_query += f"""
                ORDER BY r.fecha DESC, r.created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            logger.info(f"🔍 [GET /reservas-proveedor] Query principal final: {base_query}")
            logger.info(f"🔍 [GET /reservas-proveedor] Parámetros finales: {params}")
            logger.info(f"🔍 [GET /reservas-proveedor] Ejecutando query principal...")
            
            reservas_result = await conn.fetch(base_query, *params)
            logger.info(f"📊 [GET /reservas-proveedor] Reservas obtenidas: {len(reservas_result)}")
            
            reservas_list = []
            for row in reservas_result:
                ya_calificado = row['ya_calificado_por_proveedor']
                logger.info(f"🔍 [GET /reservas-proveedor] Reserva {row['id_reserva']} - Estado: {row['estado']}, Ya calificado: {ya_calificado}")
                
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
                    "nombre_categoria": row['nombre_categoria'],
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
            
            total_pages = (total_count + limit - 1) // limit
            current_page = (offset // limit) + 1
            
            pagination_info = {
                "total": total_count,
                "page": current_page,
                "limit": limit,
                "offset": offset,
                "total_pages": total_pages,
                "has_next": offset + limit < total_count,
                "has_prev": offset > 0
            }
            
            logger.info(f"✅ [GET /reservas-proveedor] Respuesta preparada exitosamente")
            logger.info(f"📊 [GET /reservas-proveedor] Paginación: {pagination_info}")
            logger.info(f"🔍 [GET /reservas-proveedor] ========== FIN RESERVAS PROVEEDOR ==========")
            
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
        logger.error(f"❌ [GET /reservas-proveedor] Error crítico: {str(e)}")
        logger.error(f"❌ [GET /reservas-proveedor] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [GET /reservas-proveedor] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al obtener reservas del proveedor: {str(e)}"
        )


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
    logger.info(f"🔍 [GET /diagnostico-usuario] ========== INICIO DIAGNÓSTICO ==========")
    logger.info(f"🔍 [GET /diagnostico-usuario] User ID: {current_user.id}")
    logger.info(f"🔍 [GET /diagnostico-usuario] User Email: {current_user.email}")
    
    try:
        conn = await direct_db_service.get_connection()
        logger.info(f"🔍 [GET /diagnostico-usuario] Conexión a BD obtenida exitosamente")
        
        try:
            # 1. Verificar si es proveedor
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
            proveedor_result = await conn.fetchrow(proveedor_query, current_user.id)
            
            # 2. Verificar si es cliente (tiene reservas)
            cliente_query = """
                SELECT COUNT(*) as total_reservas
                FROM reserva r
                WHERE r.user_id = $1
            """
            cliente_result = await conn.fetchrow(cliente_query, current_user.id)
            
            # 3. Si es proveedor, verificar reservas de sus servicios
            reservas_proveedor = 0
            if proveedor_result:
                reservas_proveedor_query = """
                    SELECT COUNT(*) as total_reservas
                    FROM reserva r
                    INNER JOIN servicio s ON r.id_servicio = s.id_servicio
                    WHERE s.id_perfil = $1
                """
                reservas_proveedor_result = await conn.fetchrow(reservas_proveedor_query, proveedor_result['id_perfil'])
                reservas_proveedor = reservas_proveedor_result['total_reservas'] if reservas_proveedor_result else 0
            
            # 4. Obtener información del usuario
            usuario_query = """
                SELECT 
                    u.nombre_persona,
                    u.nombre_empresa,
                    u.ruc,
                    u.estado
                FROM users u
                WHERE u.id = $1
            """
            usuario_result = await conn.fetchrow(usuario_query, current_user.id)
            
            diagnostico = {
                "usuario": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "nombre_persona": usuario_result['nombre_persona'] if usuario_result else None,
                    "nombre_empresa": usuario_result['nombre_empresa'] if usuario_result else None,
                    "ruc": usuario_result['ruc'] if usuario_result else None,
                    "estado": usuario_result['estado'] if usuario_result else None
                },
                "es_proveedor": proveedor_result is not None,
                "es_cliente": cliente_result['total_reservas'] > 0 if cliente_result else False,
                "proveedor": {
                    "id_perfil": proveedor_result['id_perfil'] if proveedor_result else None,
                    "nombre_fantasia": proveedor_result['nombre_fantasia'] if proveedor_result else None,
                    "razon_social": proveedor_result['razon_social'] if proveedor_result else None,
                    "verificado": proveedor_result['verificado'] if proveedor_result else None,
                    "estado": proveedor_result['estado'] if proveedor_result else None
                } if proveedor_result else None,
                "reservas": {
                    "como_cliente": cliente_result['total_reservas'] if cliente_result else 0,
                    "como_proveedor": reservas_proveedor
                },
                "endpoints_recomendados": []
            }
            
            # 5. Recomendar endpoints
            if diagnostico["es_cliente"]:
                diagnostico["endpoints_recomendados"].append("GET /api/v1/reservas/mis-reservas")
            
            if diagnostico["es_proveedor"] and diagnostico["proveedor"]["verificado"]:
                diagnostico["endpoints_recomendados"].append("GET /api/v1/reservas/reservas-proveedor")
            
            if not diagnostico["endpoints_recomendados"]:
                diagnostico["endpoints_recomendados"].append("No hay endpoints disponibles - usuario sin reservas ni perfil de proveedor")
            
            logger.info(f"✅ [GET /diagnostico-usuario] Diagnóstico completado")
            logger.info(f"🔍 [GET /diagnostico-usuario] ========== FIN DIAGNÓSTICO ==========")
            
            return diagnostico
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except Exception as e:
        logger.error(f"❌ [GET /diagnostico-usuario] Error: {str(e)}")
        import traceback
        logger.error(f"❌ [GET /diagnostico-usuario] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en diagnóstico: {str(e)}"
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
            logger.warning(f"⚠️ No se pudo obtener información del cliente para la reserva {reserva_id}")
            return
        
        # Crear mensaje de notificación
        mensajes_estado = {
            'aprobado': 'Tu reserva ha sido aprobada',
            'rechazado': 'Tu reserva ha sido rechazada',
            'concluido': 'Tu servicio ha sido completado'
        }
        
        mensaje_principal = mensajes_estado.get(nuevo_estado, f'El estado de tu reserva ha cambiado a {nuevo_estado}')
        
        # Log de notificación (en producción se enviaría email/push)
        logger.info(f"📧 NOTIFICACIÓN PARA CLIENTE:")
        logger.info(f"   Cliente: {cliente_result['nombre_persona']} (ID: {cliente_result['user_id']})")
        logger.info(f"   Servicio: {cliente_result['servicio_nombre']}")
        logger.info(f"   Empresa: {cliente_result['empresa_nombre']}")
        logger.info(f"   Estado anterior: {estado_anterior}")
        logger.info(f"   Nuevo estado: {nuevo_estado}")
        logger.info(f"   Mensaje: {mensaje_principal}")
        if observacion:
            logger.info(f"   Observación: {observacion}")
        
        # TODO: Aquí se puede agregar:
        # - Envío de email
        # - Push notification
        # - WebSocket notification
        # - SMS
        
        logger.info(f"✅ Notificación registrada para cliente {cliente_result['user_id']}")
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación: {str(e)}")
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
        
        logger.info(f"📝 Historial registrado: Reserva {reserva_id} - {estado_anterior} -> {nuevo_estado}")
        
    except Exception as e:
        logger.error(f"❌ Error al registrar historial: {str(e)}")
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
    logger.info(f"🔍 [GET /reservas/{reserva_id}/historial] ========== INICIO HISTORIAL ==========")
    logger.info(f"🔍 [GET /reservas/{reserva_id}/historial] User ID: {current_user.id}")
    
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
            logger.error(f"❌ [GET /reservas/{reserva_id}/historial] Reserva no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        
        # Verificar permisos (cliente o proveedor)
        es_cliente = str(reserva_result['user_id']) == str(current_user.id)
        es_proveedor = str(reserva_result['proveedor_user_id']) == str(current_user.id)
        
        if not es_cliente and not es_proveedor:
            logger.error(f"❌ [GET /reservas/{reserva_id}/historial] Usuario no tiene permisos")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver el historial de esta reserva"
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
        
        logger.info(f"✅ [GET /reservas/{reserva_id}/historial] Historial obtenido: {len(historial)} registros")
        logger.info(f"🔍 [GET /reservas/{reserva_id}/historial] ========== FIN HISTORIAL ==========")
        
        return {
            "reserva_id": reserva_id,
            "estado_actual": reserva_result['estado'],
            "historial": historial,
            "total_cambios": len(historial)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET /reservas/{reserva_id}/historial] Error crítico: {str(e)}")
        import traceback
        logger.error(f"❌ [GET /reservas/{reserva_id}/historial] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial: {str(e)}"
        )
    finally:
        await direct_db_service.pool.release(conn)


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
    logger.info(f"🔍 [PUT /reservas/{reserva_id}/estado] ========== INICIO ACTUALIZAR ESTADO ==========")
    logger.info(f"🔍 [PUT /reservas/{reserva_id}/estado] User ID: {current_user.id}")
    logger.info(f"🔍 [PUT /reservas/{reserva_id}/estado] Nuevo estado: {estado_update.nuevo_estado}")
    
    try:
        conn = await direct_db_service.pool.acquire()
        
        # 1. Verificar que la reserva existe y obtener información
        reserva_query = """
            SELECT r.id_reserva, r.estado as estado_actual, r.id_servicio, s.id_perfil, pe.user_id as proveedor_user_id
            FROM reserva r
            INNER JOIN servicio s ON r.id_servicio = s.id_servicio
            INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            WHERE r.id_reserva = $1
        """
        
        reserva_result = await conn.fetchrow(reserva_query, reserva_id)
        
        if not reserva_result:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/estado] Reserva no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/estado] Reserva encontrada - Estado actual: {reserva_result['estado_actual']}")
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/estado] Proveedor del servicio: {reserva_result['proveedor_user_id']}")
        
        # 2. Verificar que el usuario es el proveedor del servicio
        if str(reserva_result['proveedor_user_id']) != str(current_user.id):
            logger.error(f"❌ [PUT /reservas/{reserva_id}/estado] Usuario no es el proveedor del servicio")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para cambiar el estado de esta reserva"
            )
        
        # 3. Validar transiciones de estado
        estado_actual = reserva_result['estado_actual']
        nuevo_estado = estado_update.nuevo_estado.lower()
        
        # Validar que el nuevo estado sea válido
        estados_validos = ['pendiente', 'confirmada', 'cancelada', 'completada']
        if nuevo_estado not in estados_validos:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/estado] Estado inválido: {nuevo_estado}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Los estados válidos son: {', '.join(estados_validos)}"
            )
        
        # Validar que no sea el mismo estado
        if estado_actual == nuevo_estado:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/estado] Mismo estado: {estado_actual}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La reserva ya está en estado '{estado_actual}'"
            )
        
        # Validar transiciones permitidas
        transiciones_validas = {
            'pendiente': ['cancelada', 'confirmada'],
            'confirmada': ['completada'],
            'cancelada': [],  # No se puede cambiar
            'completada': []   # No se puede cambiar
        }
        
        if nuevo_estado not in transiciones_validas.get(estado_actual, []):
            logger.error(f"❌ [PUT /reservas/{reserva_id}/estado] Transición inválida: {estado_actual} -> {nuevo_estado}")
            transiciones_permitidas = transiciones_validas.get(estado_actual, [])
            mensaje = f"Transición de estado inválida. Desde '{estado_actual}' solo se puede cambiar a: {', '.join(transiciones_permitidas) if transiciones_permitidas else 'ningún estado'}"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje
            )
        
        # Validaciones adicionales por estado
        if nuevo_estado == 'rechazado' and not estado_update.observacion:
            logger.warning(f"⚠️ [PUT /reservas/{reserva_id}/estado] Rechazo sin observación")
            # No es obligatorio, pero es recomendado
        
        if nuevo_estado == 'concluido':
            # Verificar que la fecha de la reserva no sea futura (opcional)
            fecha_reserva = reserva_result.get('fecha')
            if fecha_reserva:
                from datetime import date
                if fecha_reserva > date.today():
                    logger.warning(f"⚠️ [PUT /reservas/{reserva_id}/estado] Marcando como concluido antes de la fecha: {fecha_reserva}")
                    # No bloqueamos, pero registramos la advertencia
        
        # 4. Actualizar el estado de la reserva
        update_query = """
            UPDATE reserva 
            SET estado = $1
            WHERE id_reserva = $2
            RETURNING id_reserva, estado, fecha, hora_inicio, hora_fin
        """
        
        updated_reserva = await conn.fetchrow(update_query, nuevo_estado, reserva_id)
        
        if not updated_reserva:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/estado] Error al actualizar la reserva")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el estado de la reserva"
            )
        
        # 5. Registrar cambio en historial
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
            logger.warning(f"⚠️ [PUT /reservas/{reserva_id}/estado] Error al registrar historial: {str(e)}")
        
        # 6. Enviar notificación al cliente (opcional)
        try:
            await enviar_notificacion_cliente(
                conn, 
                reserva_id, 
                estado_actual, 
                nuevo_estado, 
                estado_update.observacion
            )
        except Exception as e:
            logger.warning(f"⚠️ [PUT /reservas/{reserva_id}/estado] Error al enviar notificación: {str(e)}")
        
        logger.info(f"✅ [PUT /reservas/{reserva_id}/estado] Estado actualizado exitosamente")
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/estado] Nuevo estado: {updated_reserva['estado']}")
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/estado] ========== FIN ACTUALIZAR ESTADO ==========")
        
        return {
            "message": f"Estado de la reserva actualizado a '{nuevo_estado}' exitosamente",
            "reserva": {
                "id_reserva": updated_reserva['id_reserva'],
                "estado": updated_reserva['estado'],
                "fecha": updated_reserva['fecha'].isoformat() if updated_reserva['fecha'] else None,
                "hora_inicio": str(updated_reserva['hora_inicio']) if updated_reserva['hora_inicio'] else None,
                "hora_fin": str(updated_reserva['hora_fin']) if updated_reserva['hora_fin'] else None
            },
            "observacion": estado_update.observacion,
            "notificacion_enviada": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [PUT /reservas/{reserva_id}/estado] Error crítico: {str(e)}")
        import traceback
        logger.error(f"❌ [PUT /reservas/{reserva_id}/estado] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el estado de la reserva: {str(e)}"
        )
    finally:
        await direct_db_service.pool.release(conn)


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
    logger.info(f"🔍 [PUT /reservas/{reserva_id}/cancelar] ========== INICIO CANCELAR RESERVA ==========")
    logger.info(f"🔍 [PUT /reservas/{reserva_id}/cancelar] User ID: {current_user.id}")
    logger.info(f"🔍 [PUT /reservas/{reserva_id}/cancelar] Motivo: {cancelacion_data.motivo}")
    
    try:
        conn = await direct_db_service.pool.acquire()
        
        # 1. Verificar que la reserva existe y obtener información
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
            logger.error(f"❌ [PUT /reservas/{reserva_id}/cancelar] Reserva no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/cancelar] Cliente: {reserva_result['cliente_user_id']}")
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/cancelar] Proveedor: {reserva_result['proveedor_user_id']}")
        
        # 2. Verificar que el usuario tiene permisos para cancelar
        cliente_user_id = str(reserva_result['cliente_user_id'])
        proveedor_user_id = str(reserva_result['proveedor_user_id'])
        current_user_id = str(current_user.id)
        
        if current_user_id != cliente_user_id and current_user_id != proveedor_user_id:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/cancelar] Usuario no autorizado")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para gestionar esta reserva"
            )
        
        # 3. Verificar que la reserva está en estado pendiente
        estado_actual = reserva_result['estado_actual']
        if estado_actual != 'pendiente':
            logger.error(f"❌ [PUT /reservas/{reserva_id}/cancelar] Estado inválido: {estado_actual}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo se pueden cancelar reservas en estado 'pendiente'. Estado actual: '{estado_actual}'"
            )
        
        # 4. Validar que el motivo no esté vacío
        if not cancelacion_data.motivo or not cancelacion_data.motivo.strip():
            logger.error(f"❌ [PUT /reservas/{reserva_id}/cancelar] Motivo vacío")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debés ingresar un motivo para cancelar la reserva"
            )
        
        # 5. Actualizar el estado de la reserva
        update_query = """
            UPDATE reserva 
            SET estado = 'cancelada'
            WHERE id_reserva = $1
            RETURNING id_reserva, estado, fecha, hora_inicio, hora_fin
        """
        
        updated_reserva = await conn.fetchrow(update_query, reserva_id)
        
        if not updated_reserva:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/cancelar] Error al actualizar reserva")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al cancelar la reserva"
            )
        
        # 6. Registrar en el historial
        try:
            await registrar_cambio_historial(
                conn,
                reserva_id,
                current_user.id,
                estado_actual,
                'cancelada',
                cancelacion_data.motivo
            )
        except Exception as e:
            logger.warning(f"⚠️ [PUT /reservas/{reserva_id}/cancelar] Error al registrar historial: {str(e)}")
        
        # 7. Enviar notificación (opcional)
        try:
            await enviar_notificacion_cliente(
                conn, 
                reserva_id, 
                estado_actual, 
                'cancelada', 
                cancelacion_data.motivo
            )
        except Exception as e:
            logger.warning(f"⚠️ [PUT /reservas/{reserva_id}/cancelar] Error al enviar notificación: {str(e)}")
        
        # 8. Determinar quién canceló
        quien_cancelo = "cliente" if current_user_id == cliente_user_id else "proveedor"
        
        logger.info(f"✅ [PUT /reservas/{reserva_id}/cancelar] Reserva cancelada por {quien_cancelo}")
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/cancelar] ========== FIN CANCELAR RESERVA ==========")
        
        return {
            "message": "✅ Reserva cancelada",
            "reserva": {
                "id_reserva": updated_reserva['id_reserva'],
                "estado": updated_reserva['estado'],
                "fecha": updated_reserva['fecha'].isoformat() if updated_reserva['fecha'] else None,
                "hora_inicio": str(updated_reserva['hora_inicio']) if updated_reserva['hora_inicio'] else None,
                "hora_fin": str(updated_reserva['hora_fin']) if updated_reserva['hora_fin'] else None
            },
            "motivo": cancelacion_data.motivo,
            "cancelado_por": quien_cancelo,
            "notificacion_enviada": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [PUT /reservas/{reserva_id}/cancelar] Error crítico: {str(e)}")
        import traceback
        logger.error(f"❌ [PUT /reservas/{reserva_id}/cancelar] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar la reserva: {str(e)}"
        )
    finally:
        await direct_db_service.pool.release(conn)


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
    logger.info(f"🔍 [PUT /reservas/{reserva_id}/confirmar] ========== INICIO CONFIRMAR RESERVA ==========")
    logger.info(f"🔍 [PUT /reservas/{reserva_id}/confirmar] User ID: {current_user.id}")
    
    try:
        conn = await direct_db_service.pool.acquire()
        
        # 1. Verificar que la reserva existe y obtener información
        reserva_query = """
            SELECT r.id_reserva, r.estado as estado_actual, r.user_id as cliente_user_id
            FROM reserva r
            WHERE r.id_reserva = $1
        """
        
        reserva_result = await conn.fetchrow(reserva_query, reserva_id)
        
        if not reserva_result:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/confirmar] Reserva no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/confirmar] Cliente: {reserva_result['cliente_user_id']}")
        
        # 2. Verificar que el usuario es el cliente dueño de la reserva
        cliente_user_id = str(reserva_result['cliente_user_id'])
        current_user_id = str(current_user.id)
        
        if current_user_id != cliente_user_id:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/confirmar] Usuario no autorizado")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para gestionar esta reserva"
            )
        
        # 3. Verificar que la reserva está en estado pendiente
        estado_actual = reserva_result['estado_actual']
        if estado_actual != 'pendiente':
            logger.error(f"❌ [PUT /reservas/{reserva_id}/confirmar] Estado inválido: {estado_actual}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No es posible realizar esta acción en el estado actual"
            )
        
        # 4. Actualizar el estado de la reserva
        update_query = """
            UPDATE reserva 
            SET estado = 'confirmada'
            WHERE id_reserva = $1
            RETURNING id_reserva, estado, fecha, hora_inicio, hora_fin
        """
        
        updated_reserva = await conn.fetchrow(update_query, reserva_id)
        
        if not updated_reserva:
            logger.error(f"❌ [PUT /reservas/{reserva_id}/confirmar] Error al actualizar reserva")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al confirmar la reserva"
            )
        
        # 5. Registrar en el historial
        try:
            await registrar_cambio_historial(
                conn,
                reserva_id,
                current_user.id,
                estado_actual,
                'confirmada',
                'Reserva confirmada por el cliente'
            )
        except Exception as e:
            logger.warning(f"⚠️ [PUT /reservas/{reserva_id}/confirmar] Error al registrar historial: {str(e)}")
        
        # 6. Enviar notificación (opcional)
        try:
            await enviar_notificacion_cliente(
                conn, 
                reserva_id, 
                estado_actual, 
                'confirmada', 
                'Reserva confirmada por el cliente'
            )
        except Exception as e:
            logger.warning(f"⚠️ [PUT /reservas/{reserva_id}/confirmar] Error al enviar notificación: {str(e)}")
        
        logger.info(f"✅ [PUT /reservas/{reserva_id}/confirmar] Reserva confirmada por cliente")
        logger.info(f"🔍 [PUT /reservas/{reserva_id}/confirmar] ========== FIN CONFIRMAR RESERVA ==========")
        
        return {
            "message": "✅ Reserva confirmada",
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [PUT /reservas/{reserva_id}/confirmar] Error crítico: {str(e)}")
        import traceback
        logger.error(f"❌ [PUT /reservas/{reserva_id}/confirmar] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar la reserva: {str(e)}"
        )
    finally:
        await direct_db_service.pool.release(conn)


