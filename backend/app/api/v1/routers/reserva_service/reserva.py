# backend/app/api/v1/routers/reserva_service/reserva.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.schemas.reserva_servicio.reserva import ReservaIn, ReservaOut
from app.schemas.reserva_servicio.reserva_detallada import ReservaDetalladaOut, ReservasPaginadasOut
from app.models.reserva_servicio.reserva import ReservaModel
from app.models.servicio.service import ServicioModel
from app.models.perfil import UserModel
from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
import logging
import re
from uuid import UUID
from typing import List, Optional
from datetime import datetime, date
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
                    "id_usuario": nueva_reserva['user_id'],  # Mapear user_id a id_usuario en la respuesta
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
                    c.nombre as nombre_categoria
                FROM reserva r
                INNER JOIN servicio s ON r.id_servicio = s.id_servicio
                INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
                INNER JOIN users u ON pe.user_id = u.id
                LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
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
                    "nombre_categoria": row['nombre_categoria']
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


