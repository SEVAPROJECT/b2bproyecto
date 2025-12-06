# app/api/v1/routers/services.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import date as date_type
import logging

logger = logging.getLogger(__name__)

from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.servicio.service import ServicioModel
from app.models.publicar_servicio.category import CategoriaModel
from app.schemas.servicio.service import ServicioOut, ServicioIn, ServicioWithProvider


router = APIRouter(prefix="/services", tags=["services"])

# Constantes para SQL
SQL_AND = " AND "

# Schemas para el endpoint de filtros
class FilteredServicesResponse(BaseModel):
    services: List[ServicioWithProvider]
    pagination: dict
    filters_applied: dict


# Funciones helper para get_filtered_services
def build_currency_filter(currency: str, param_count: int) -> tuple[str, int, str]:
    """Construye el filtro de moneda usando id_moneda (más confiable, no depende del JOIN de moneda)"""
    currency_upper = currency.strip().upper()
    
    # Usar solo id_moneda para evitar problemas con el JOIN de moneda
    # Esto es más confiable porque s.id_moneda siempre está disponible en la consulta base
    if currency_upper == 'GS':
        filter_condition = "s.id_moneda = 1"
    elif currency_upper == 'USD':
        filter_condition = "s.id_moneda = 2"
    elif currency_upper == 'BRL':
        filter_condition = "s.id_moneda = 3"
    elif currency_upper == 'ARS':
        filter_condition = "(s.id_moneda = 4 OR s.id_moneda = 8)"
    else:
        # Si no coincide con ninguna moneda conocida, usar el código ISO si el JOIN está disponible
        # Pero como fallback, intentar buscar por id_moneda = NULL (no debería pasar)
        param_count += 1
        filter_condition = f"(m.codigo_iso_moneda IS NOT NULL AND TRIM(m.codigo_iso_moneda) = UPPER(${param_count}))"
        return filter_condition, param_count, currency_upper
    
    # No necesitamos parámetros para id_moneda, así que no incrementamos param_count
    return filter_condition, param_count, currency_upper

def build_dynamic_filters(
    currency: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    category_id: Optional[int],
    department: Optional[str],
    city: Optional[str],
    search: Optional[str],
    min_rating: Optional[float],
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> tuple[list[str], list]:
    """Construye los filtros dinámicos y sus parámetros"""
    filters = []
    params = []
    param_count = 0
    
    # Filtro por moneda
    if currency:
        filter_condition, param_count, currency_upper = build_currency_filter(currency, param_count)
        filters.append(filter_condition)
        # Solo agregar parámetro si se necesita (cuando no es una moneda conocida)
        if currency_upper not in ['GS', 'USD', 'BRL', 'ARS']:
            params.append(currency_upper)
    
    # Filtro por precio mínimo
    if min_price is not None:
        param_count += 1
        # Asegurar que min_price sea un número válido
        try:
            min_price_float = float(min_price)
            filters.append(f"s.precio >= ${param_count}")
            params.append(min_price_float)
            logger.info(f"💰 Filtro de precio mínimo aplicado: s.precio >= {min_price_float}")
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Error convirtiendo min_price a float: {min_price}, error: {e}")
            # No agregar el filtro si hay error de conversión
    
    # Filtro por precio máximo
    if max_price is not None:
        param_count += 1
        # Asegurar que max_price sea un número válido
        try:
            max_price_float = float(max_price)
            filters.append(f"s.precio <= ${param_count}")
            params.append(max_price_float)
            logger.info(f"💰 Filtro de precio máximo aplicado: s.precio <= {max_price_float} (tipo: {type(max_price_float).__name__})")
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Error convirtiendo max_price a float: {max_price}, error: {e}")
            # No agregar el filtro si hay error de conversión
    
    # Filtro por categoría
    if category_id:
        param_count += 1
        filters.append(f"s.id_categoria = ${param_count}")
        params.append(category_id)
    
    # Filtro por departamento
    if department:
        param_count += 1
        filters.append(f"LOWER(d.nombre) LIKE LOWER(${param_count})")
        params.append(f"%{department}%")
    
    # Filtro por ciudad
    if city:
        param_count += 1
        filters.append(f"LOWER(c.nombre) LIKE LOWER(${param_count})")
        params.append(f"%{city}%")
    
    # Filtro por búsqueda
    if search:
        param_count += 1
        filters.append(f"(LOWER(s.nombre) LIKE LOWER(${param_count}) OR LOWER(s.descripcion) LIKE LOWER(${param_count}))")
        params.append(f"%{search}%")
    
    # Filtro por calificación mínima
    if min_rating is not None and float(min_rating) > 0:
        param_count += 1
        rating_subquery = f"(SELECT r.id_servicio FROM reserva r INNER JOIN calificacion c ON r.id_reserva = c.id_reserva WHERE c.rol_emisor = 'cliente' GROUP BY r.id_servicio HAVING AVG(c.puntaje) >= ${param_count})"
        filters.append(f"s.id_servicio IN {rating_subquery}")
        params.append(float(min_rating))
    
    # Filtro por fechas (date_from y date_to)
    # Filtrar por fecha de publicación del servicio (created_at)
    if date_from or date_to:
        if date_from and date_to:
            # Rango completo: filtrar servicios publicados entre date_from y date_to
            # Convertir strings a date para PostgreSQL
            param_count += 1
            param_count_to = param_count + 1
            filters.append(f"s.created_at::date >= ${param_count} AND s.created_at::date <= ${param_count_to}")
            # Convertir strings a objetos date para asyncpg
            params.append(date_type.fromisoformat(date_from))
            params.append(date_type.fromisoformat(date_to))
        elif date_from:
            # Solo fecha desde: filtrar servicios publicados desde date_from
            param_count += 1
            filters.append(f"s.created_at::date >= ${param_count}")
            # Convertir string a objeto date para asyncpg
            params.append(date_type.fromisoformat(date_from))
        elif date_to:
            # Solo fecha hasta: filtrar servicios publicados hasta date_to
            param_count += 1
            filters.append(f"s.created_at::date <= ${param_count}")
            # Convertir string a objeto date para asyncpg
            params.append(date_type.fromisoformat(date_to))
    
    return filters, params

def get_base_query() -> str:
    """Retorna la consulta base para servicios"""
    return """
        SELECT 
            s.id_servicio, s.id_categoria, s.id_perfil, s.id_moneda, s.nombre, s.descripcion,
            s.precio, s.imagen, s.estado, s.created_at, pe.razon_social, u.nombre_persona as nombre_contacto,
            d.nombre as departamento, c.nombre as ciudad, b.nombre as barrio, m.codigo_iso_moneda,
            m.nombre as nombre_moneda, m.simbolo as simbolo_moneda
        FROM servicio s
        JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        JOIN users u ON pe.user_id = u.id
        LEFT JOIN direccion dir ON pe.id_direccion = dir.id_direccion
        LEFT JOIN departamento d ON dir.id_departamento = d.id_departamento
        LEFT JOIN ciudad c ON dir.id_ciudad = c.id_ciudad
        LEFT JOIN barrio b ON dir.id_barrio = b.id_barrio
        LEFT JOIN moneda m ON s.id_moneda = m.id_moneda
        WHERE s.estado = true AND pe.verificado = true AND s.precio > 0
    """

def get_count_query() -> str:
    """Retorna la consulta base para contar servicios"""
    return """
        SELECT COUNT(*) as total
        FROM servicio s
        JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        LEFT JOIN direccion dir ON pe.id_direccion = dir.id_direccion
        LEFT JOIN departamento d ON dir.id_departamento = d.id_departamento
        LEFT JOIN ciudad c ON dir.id_ciudad = c.id_ciudad
        WHERE s.estado = true AND pe.verificado = true AND s.precio > 0
    """

async def fetch_tarifas_for_services(conn, service_ids: list) -> list:
    """Obtiene las tarifas para una lista de servicios"""
    if not service_ids:
        return []
    
    return await conn.fetch("""
        SELECT 
            ts.id_tarifa_servicio, ts.id_servicio, ts.monto, ts.descripcion, 
            ts.fecha_inicio, ts.fecha_fin, ts.id_tarifa, tt.nombre as nombre_tipo_tarifa
        FROM tarifa_servicio ts
        LEFT JOIN tipo_tarifa_servicio tt ON ts.id_tarifa = tt.id_tarifa
        WHERE ts.id_servicio = ANY($1)
    """, service_ids)

def format_tarifa_dict(tarifa_row: dict) -> dict:
    """Formatea una tarifa en diccionario"""
    return {
        "id_tarifa_servicio": tarifa_row['id_tarifa_servicio'],
        "monto": float(tarifa_row['monto']),
        "descripcion": tarifa_row['descripcion'],
        "fecha_inicio": tarifa_row['fecha_inicio'].isoformat(),
        "fecha_fin": tarifa_row['fecha_fin'].isoformat() if tarifa_row['fecha_fin'] else None,
        "id_tarifa": tarifa_row['id_tarifa'],
        "nombre_tipo_tarifa": tarifa_row['nombre_tipo_tarifa'] or "Sin especificar"
    }

def map_services_with_tarifas(services_data_tuples: list, tarifas_data: list) -> list:
    """Mapea servicios con sus tarifas"""
    services_map_by_id = {}
    
    # Crear mapa de servicios
    for row in services_data_tuples:
        service_dict = dict(row)
        service_id = service_dict['id_servicio']
        service_dict['tarifas'] = []
        services_map_by_id[service_id] = service_dict
    
    # Asignar tarifas
    for tarifa_row in tarifas_data:
        service_id = tarifa_row['id_servicio']
        if service_id in services_map_by_id:
            tarifa_dict = format_tarifa_dict(tarifa_row)
            services_map_by_id[service_id]['tarifas'].append(tarifa_dict)
    
    return [ServicioWithProvider(**data) for data in services_map_by_id.values()]

def build_empty_response(offset: int, limit: int, currency: Optional[str], min_price: Optional[float], 
                        max_price: Optional[float], category_id: Optional[int], department: Optional[str], 
                        city: Optional[str], search: Optional[str]) -> FilteredServicesResponse:
    """Construye una respuesta vacía cuando no hay servicios"""
    return FilteredServicesResponse(
        services=[],
        pagination={
            "total": 0,
            "page": (offset // limit) + 1,
            "total_pages": 0,
            "limit": limit,
            "offset": offset
        },
        filters_applied={
            "currency": currency,
            "min_price": min_price,
            "max_price": max_price,
            "category_id": category_id,
            "department": department,
            "city": city,
            "search": search
        }
    )

def build_pagination_info(total: int, offset: int, limit: int) -> dict:
    """Construye la información de paginación"""
    current_page = (offset // limit) + 1
    total_pages = (total + limit - 1) // limit
    return {
        "total": total,
        "page": current_page,
        "total_pages": total_pages,
        "limit": limit,
        "offset": offset
    }

def build_filters_applied(currency: Optional[str], min_price: Optional[float], max_price: Optional[float],
                         category_id: Optional[int], department: Optional[str], city: Optional[str],
                         search: Optional[str]) -> dict:
    """Construye el diccionario de filtros aplicados"""
    return {
        "currency": currency,
        "min_price": min_price,
        "max_price": max_price,
        "category_id": category_id,
        "department": department,
        "city": city,
        "search": search
    }

def build_filters_applied_response(
    services: list,
    total: int,
    offset: int,
    limit: int,
    currency: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    category_id: Optional[int],
    department: Optional[str],
    city: Optional[str],
    search: Optional[str]
) -> FilteredServicesResponse:
    """Construye la respuesta completa con servicios, paginación y filtros aplicados"""
    pagination = build_pagination_info(total, offset, limit)
    filters_applied = build_filters_applied(
        currency, min_price, max_price, category_id, department, city, search
    )
    return FilteredServicesResponse(
        services=services,
        pagination=pagination,
        filters_applied=filters_applied
    )

class ServiceFilters(BaseModel):
    currency: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    category_id: Optional[int] = None
    department: Optional[str] = None
    city: Optional[str] = None
    search: Optional[str] = None


@router.get(
    "/list",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de todos los servicios activos disponibles en la plataforma."
)
async def get_all_services_list(db: AsyncSession = Depends(get_async_db)):
    """
    Este endpoint devuelve una lista de todos los servicios activos.
    """
    result = await db.execute(
        select(ServicioModel).where(ServicioModel.estado == True)
    )
    
    services = result.scalars().all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron servicios activos."
        )
    return list(services)


@router.get(
    "/templates",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de todos los servicios activos para usar como plantillas."
)
async def get_service_templates(db: AsyncSession = Depends(get_async_db)):
    """
    Este endpoint devuelve una lista de todos los servicios activos que pueden ser usados como plantillas.
    """
    result = await db.execute(
        select(ServicioModel).where(ServicioModel.estado == True)
    )
    
    services = result.scalars().all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron servicios disponibles como plantillas."
        )
    return list(services)


@router.get(
    "/templates/category/{category_id}",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de servicios activos de una categoría específica para usar como plantillas."
)
async def get_service_templates_by_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Este endpoint devuelve una lista de servicios activos de una categoría específica que pueden ser usados como plantillas.
    """
    result = await db.execute(
        select(ServicioModel).where(
            ServicioModel.estado == True,
            ServicioModel.id_categoria == category_id
        )
    )
    
    services = result.scalars().all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron servicios disponibles en esta categoría como plantillas."
        )
    return list(services)


@router.get(
    "/all/category/{category_id}",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de TODOS los servicios (activos e inactivos) de una categoría específica."
)
async def get_all_services_by_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Este endpoint devuelve una lista de TODOS los servicios (activos e inactivos) de una categoría específica.
    Permite a los proveedores ver todos los servicios disponibles antes de decidir si reutilizar o solicitar uno nuevo.
    """
    result = await db.execute(
        select(ServicioModel).where(
            ServicioModel.id_categoria == category_id
        )
    )
    
    services = result.scalars().all()

    # Devolver lista vacía en lugar de error 404
    return list(services)


@router.get(
    "/test-connection",
    status_code=status.HTTP_200_OK,
    description="Endpoint de prueba para verificar conexión a base de datos."
)
async def test_connection(db: AsyncSession = Depends(get_async_db)):
    """
    Endpoint simple para verificar que la conexión a la base de datos funciona.
    """
    try:
        # Query simple para contar servicios
        query = select(ServicioModel).where(ServicioModel.estado == True)
        result = await db.execute(query)
        services = result.scalars().all()
        return {
            "status": "success", 
            "message": f"Conexión exitosa. ServicioModels activos: {len(services)}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Error de conexión: {str(e)}"
        }

@router.get(
    "/services",
    response_model=FilteredServicesResponse,
    status_code=status.HTTP_200_OK,
    description="Endpoint unificado para obtener servicios con información del proveedor. Soporta paginación y filtros opcionales."
)
async def get_services_unified(
    # Parámetros de paginación (siempre presentes)
    limit: int = Query(10, ge=1, le=100, description="Número de servicios por página"),
    offset: int = Query(0, ge=0, description="Número de servicios a omitir"),
    
    # Filtros opcionales
    currency: Optional[str] = Query(None, description="Código de moneda (ej: GS, USD)"),
    min_price: Optional[float] = Query(None, ge=0, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Precio máximo"),
    category_id: Optional[int] = Query(None, ge=1, description="ID de categoría"),
    department: Optional[str] = Query(None, description="Nombre del departamento"),
    city: Optional[str] = Query(None, description="Nombre de la ciudad"),
    search: Optional[str] = Query(None, description="Búsqueda por nombre o descripción"),
    # Nuevos filtros
    date_from: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Calificación mínima (0-5)")
):
    """
    Endpoint unificado que maneja tanto servicios sin filtros como con filtros.
    - Sin parámetros de filtro: Comportamiento igual a /with-providers original
    - Con parámetros de filtro: Comportamiento igual a /filtered original
    """
    try:
        from app.services.direct_db_service import direct_db_service
        
        # Usar direct_db_service para evitar problemas con PgBouncer
        conn = await direct_db_service.get_connection()
        try:
            # Construir filtros dinámicos usando función helper
            filters, params = build_dynamic_filters(
                currency, min_price, max_price, category_id, 
                department, city, search, min_rating, date_from, date_to
            )
            
            # Log de filtros recibidos
            logger.info(f"🔍 Filtros recibidos: currency={currency}, min_price={min_price}, max_price={max_price}, category_id={category_id}")
            logger.info(f"📊 Filtros construidos: {filters}")
            logger.info(f"📊 Parámetros construidos: {params}")
            
            # Construir query base usando función helper
            base_query = get_base_query()
            
            # Aplicar filtros a la consulta
            if filters:
                base_query += SQL_AND + SQL_AND.join(filters)
            
            # Log de la consulta completa para debugging (especialmente si hay filtro de precio)
            if max_price is not None or min_price is not None:
                logger.info(f"📝 Consulta SQL completa (con filtros de precio): {base_query}")
                logger.info(f"📊 Parámetros: {params}")
                logger.info(f"💰 Filtros de precio: min_price={min_price}, max_price={max_price}")
            else:
                logger.debug(f"📝 Consulta SQL completa: {base_query}")
                logger.debug(f"📊 Parámetros: {params}")
            
            # Agregar ordenamiento y paginación
            base_query += " ORDER BY s.created_at DESC"
            
            # Agregar paginación
            param_count = len(params)
            param_count += 1
            limit_param = param_count
            param_count += 1
            offset_param = param_count
            
            base_query += f" LIMIT ${limit_param} OFFSET ${offset_param}"
            params.extend([limit, offset])
            
            logger.info(f"🔍 Consulta unificada - Límite: {limit}, Offset: {offset}")
            logger.info(f"📊 Parámetros totales: {len(params)}")
            
            # Log de la consulta completa para debugging (solo si hay filtro de moneda)
            if currency:
                logger.debug(f"📝 Consulta SQL completa: {base_query}")
                logger.debug(f"📊 Parámetros: {params}")
                # Verificar que la consulta incluya el JOIN de moneda
                if "moneda m" not in base_query and "LEFT JOIN moneda" not in base_query:
                    logger.error("❌ ERROR: La consulta no incluye el JOIN de moneda pero se está usando el filtro de moneda")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error en la construcción de la consulta: falta JOIN de moneda"
                    )
            
            # Verificación de seguridad: asegurar que el límite no exceda 100
            if limit > 100:
                logger.warning(f"⚠️ Límite solicitado ({limit}) excede el máximo (100), limitando a 100")
                limit = 100
                params[-2] = 100  # Actualizar el parámetro limit en la lista
            
            # Ejecutar consulta principal
            try:
                # Log de la consulta final antes de ejecutar
                logger.info(f"📝 Ejecutando consulta SQL final: {base_query}")
                logger.info(f"📊 Parámetros finales: {params}")
                
                services_data_tuples = await conn.fetch(base_query, *params)
                
                # Log de resultados
                logger.info(f"✅ Consulta ejecutada exitosamente. Resultados: {len(services_data_tuples)} servicios")
                if max_price is not None and len(services_data_tuples) > 0:
                    # Verificar que los precios de los servicios devueltos sean <= max_price
                    precios = [row['precio'] for row in services_data_tuples if row.get('precio')]
                    if precios:
                        max_precio_encontrado = max(precios)
                        logger.info(f"💰 Precio máximo en resultados: {max_precio_encontrado}, Filtro aplicado: <= {max_price}")
                        if max_precio_encontrado > max_price:
                            logger.warning(f"⚠️ ADVERTENCIA: Se encontró un servicio con precio {max_precio_encontrado} que excede el filtro máximo de {max_price}")
            except Exception as e:
                logger.error(f"❌ Error en get_services_unified: {str(e)}")
                logger.error(f"📝 Consulta que falló: {base_query}")
                logger.error(f"📊 Parámetros: {params}")
                raise
            
            # Verificación de seguridad: asegurar que no se devuelvan más servicios de los solicitados
            if len(services_data_tuples) > limit:
                logger.warning(f"⚠️ La consulta devolvió {len(services_data_tuples)} servicios, pero el límite es {limit}. Limitando...")
                services_data_tuples = services_data_tuples[:limit]
            
            if not services_data_tuples:
                return build_empty_response(
                    offset, limit, currency, min_price, max_price,
                    category_id, department, city, search
                )

            # Obtener IDs de servicios para consulta de tarifas
            service_ids = [row['id_servicio'] for row in services_data_tuples]
            
            # Obtener tarifas usando función helper
            tarifas_data = await fetch_tarifas_for_services(conn, service_ids)

            # Mapear servicios con tarifas usando función helper
            services = map_services_with_tarifas(services_data_tuples, tarifas_data)
            
            # Filtro adicional de seguridad: asegurar que los servicios devueltos respeten el filtro de precio máximo
            if max_price is not None:
                services_antes_filtro = len(services)
                services = [s for s in services if s.precio <= max_price]
                servicios_filtrados = services_antes_filtro - len(services)
                if servicios_filtrados > 0:
                    logger.warning(f"⚠️ Filtro de seguridad: Se eliminaron {servicios_filtrados} servicios que excedían el precio máximo de {max_price}")
                    logger.warning(f"   Esto indica que el filtro SQL no se aplicó correctamente")
            
            # Filtro adicional de seguridad: asegurar que los servicios devueltos respeten el filtro de precio mínimo
            if min_price is not None:
                services_antes_filtro = len(services)
                services = [s for s in services if s.precio >= min_price]
                servicios_filtrados = services_antes_filtro - len(services)
                if servicios_filtrados > 0:
                    logger.warning(f"⚠️ Filtro de seguridad: Se eliminaron {servicios_filtrados} servicios que estaban por debajo del precio mínimo de {min_price}")
                    logger.warning(f"   Esto indica que el filtro SQL no se aplicó correctamente")
            
            # Construir query de conteo usando función helper
            count_query = get_count_query()
            
            # Aplicar los mismos filtros al count
            if filters:
                count_query += SQL_AND + SQL_AND.join(filters)
            
            # Parámetros para count (sin limit/offset)
            count_params = params[:-2]  # Remover limit y offset
            count_result = await conn.fetchrow(count_query, *count_params)
            total = count_result['total'] if count_result else 0
            
            # Construir respuesta usando función helper
            return build_filters_applied_response(
                services, total, offset, limit, currency, min_price,
                max_price, category_id, department, city, search
            )
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except Exception as e:
        print(f"❌ Error en get_services_unified: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/filtered",
    response_model=FilteredServicesResponse,
    status_code=status.HTTP_200_OK,
    description="Obtiene servicios filtrados con paginación. Soporta filtros por precio, moneda, categoría, ubicación y búsqueda."
)
async def get_filtered_services(
    # Filtros básicos
    currency: Optional[str] = Query(None, description="Código de moneda (ej: GS, USD)"),
    min_price: Optional[float] = Query(None, ge=0, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Precio máximo"),
    
    # Filtros de categoría
    category_id: Optional[int] = Query(None, ge=1, description="ID de categoría"),
    
    # Filtros de ubicación
    department: Optional[str] = Query(None, description="Nombre del departamento"),
    city: Optional[str] = Query(None, description="Nombre de la ciudad"),
    
    # Búsqueda
    search: Optional[str] = Query(None, description="Búsqueda por nombre o descripción"),
    
    # Nuevos filtros
    date_from: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Calificación mínima (0-5)"),
    
    # Paginación
    limit: int = Query(10, ge=1, le=100, description="Número de servicios por página"),
    offset: int = Query(0, ge=0, description="Número de servicios a omitir")
):
    """
    Endpoint para obtener servicios con filtros avanzados.
    Mantiene compatibilidad con el endpoint /with-providers original.
    """
    try:
        from app.services.direct_db_service import direct_db_service
        
        # Usar direct_db_service para evitar problemas con PgBouncer
        conn = await direct_db_service.get_connection()
        try:
            # Construir filtros dinámicamente
            filters, params = build_dynamic_filters(
                currency, min_price, max_price, category_id, department, city, search, min_rating, date_from, date_to
            )
            
            # Construir la consulta base
            base_query = get_base_query()
            
            # Aplicar filtros a la consulta
            if filters:
                base_query += SQL_AND + SQL_AND.join(filters)
            
            # Agregar ordenamiento y paginación
            base_query += " ORDER BY s.created_at DESC"
            
            # Parámetros para paginación
            limit_param = len(params) + 1
            offset_param = len(params) + 2
            base_query += f" LIMIT ${limit_param} OFFSET ${offset_param}"
            params.extend([limit, offset])
            
            print(f"🔍 Consulta filtrada: {base_query}")
            print(f"📊 Parámetros: {params}")
            
            # Ejecutar consulta principal
            services_data_tuples = await conn.fetch(base_query, *params)
            
            # Verificación de seguridad: asegurar que no se devuelvan más servicios de los solicitados
            if len(services_data_tuples) > limit:
                logger.warning(f"⚠️ La consulta devolvió {len(services_data_tuples)} servicios, pero el límite es {limit}. Limitando...")
                services_data_tuples = services_data_tuples[:limit]
            
            if not services_data_tuples:
                return build_empty_response(
                    offset, limit, currency, min_price, max_price, category_id, department, city, search
                )

            # Obtener IDs de servicios para consulta de tarifas
            service_ids = [row['id_servicio'] for row in services_data_tuples]
            
            # Consulta de tarifas (N+1 optimization)
            tarifas_data = await fetch_tarifas_for_services(conn, service_ids)

            # Mapear servicios con tarifas
            services = map_services_with_tarifas(services_data_tuples, tarifas_data)
            
            # Consulta para obtener el total (sin paginación)
            count_query = get_count_query()
            
            # Aplicar los mismos filtros al count
            if filters:
                count_query += SQL_AND + SQL_AND.join(filters)
            
            # Parámetros para count (sin limit/offset)
            count_params = params[:-2]  # Remover limit y offset
            count_result = await conn.fetchrow(count_query, *count_params)
            total = count_result['total'] if count_result else 0
            
            # Construir respuesta
            return FilteredServicesResponse(
                services=services,
                pagination=build_pagination_info(total, offset, limit),
                filters_applied=build_filters_applied(
                    currency, min_price, max_price, category_id, department, city, search
                )
            )
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except Exception as e:
        print(f"❌ Error en get_filtered_services: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/category/{category_id}",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de servicios activos de una categoría específica."
)
async def get_services_by_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene todos los servicios activos de una categoría específica.
    Usa direct_db_service para evitar problemas con PgBouncer y prepared statements.
    """
    try:
        from app.services.direct_db_service import direct_db_service
        
        conn = await direct_db_service.get_connection()
        try:
            # Query SQL directa para evitar prepared statements
            query = """
                SELECT 
                    s.id_servicio, s.id_categoria, s.id_perfil, s.id_moneda, 
                    s.nombre, s.descripcion, s.precio, s.imagen, s.estado, s.created_at
                FROM servicio s
                WHERE s.estado = true AND s.id_categoria = $1 AND s.precio > 0
                ORDER BY s.created_at DESC
            """
            
            rows = await conn.fetch(query, category_id)
            
            # Convertir rows a objetos ServicioModel para mantener compatibilidad
            services = []
            for row in rows:
                service = ServicioModel(
                    id_servicio=row['id_servicio'],
                    id_categoria=row['id_categoria'],
                    id_perfil=row['id_perfil'],
                    id_moneda=row['id_moneda'],
                    nombre=row['nombre'],
                    descripcion=row['descripcion'],
                    precio=row['precio'],
                    imagen=row['imagen'],
                    estado=row['estado'],
                    created_at=row['created_at']
                )
                services.append(service)
            
            # Retornar lista vacía si no hay servicios (comportamiento RESTful normal)
            return services
        finally:
            await direct_db_service.pool.release(conn)
    except Exception as e:
        print(f"Error obteniendo servicios por categoría: {e}")
        # Retornar lista vacía en caso de error en lugar de lanzar excepción
        return []


@router.post(
    "/",
    response_model=ServicioOut,
    status_code=status.HTTP_201_CREATED,
    description="Crea un nuevo servicio."
)
async def create_service(
    service_in: ServicioIn,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea un nuevo servicio.
    """
    try:
        # Verificar que la categoría existe
        category_result = await db.execute(
            select(CategoriaModel).where(CategoriaModel.id_categoria == service_in.id_categoria)
        )
        category = category_result.scalars().first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada."
            )

        nuevo_servicio = ServicioModel(
            nombre=service_in.nombre,
            descripcion=service_in.descripcion,
            precio=service_in.precio,
            id_categoria=service_in.id_categoria,
            id_moneda=service_in.id_moneda,
            estado=True
        )
        db.add(nuevo_servicio)
        await db.commit()
        await db.refresh(nuevo_servicio)

        return nuevo_servicio
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el servicio: {str(e)}"
        )


@router.put(
    "/{service_id}",
    response_model=ServicioOut,
    status_code=status.HTTP_200_OK,
    description="Actualiza un servicio existente."
)
async def update_service(
    service_id: int,
    service_data: dict,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza un servicio existente.
    """
    try:
        # Verificar que el servicio existe
        service_result = await db.execute(
            select(ServicioModel).where(ServicioModel.id_servicio == service_id)
        )
        service = service_result.scalars().first()

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ServicioModel no encontrado."
            )

        # Actualizar campos del servicio
        if "nombre" in service_data:
            service.nombre = service_data["nombre"]
        if "descripcion" in service_data:
            service.descripcion = service_data["descripcion"]
        if "precio" in service_data:
            service.precio = service_data["precio"]
        if "estado" in service_data:
            service.estado = service_data["estado"]
        if "imagen" in service_data:
            service.imagen = service_data["imagen"]

        await db.commit()
        await db.refresh(service)

        return service
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el servicio: {str(e)}"
        )


# Modelo para actualizar estado del servicio
class ServicioModelStatusUpdate(BaseModel):
    estado: bool

@router.patch(
    "/{service_id}/status",
    status_code=status.HTTP_200_OK,
    description="Actualiza el estado (activo/inactivo) de un servicio."
)
async def update_service_status(
    service_id: int,
    status_data: ServicioModelStatusUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza el estado (activo/inactivo) de un servicio.
    """
    try:
        # Verificar que el servicio existe
        service_result = await db.execute(
            select(ServicioModel).where(ServicioModel.id_servicio == service_id)
        )
        service = service_result.scalars().first()

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ServicioModel no encontrado."
            )

        # Actualizar el estado del servicio
        service.estado = status_data.estado
        await db.commit()
        await db.refresh(service)

        return {
            "message": f"ServicioModel {'activado' if status_data.estado else 'desactivado'} exitosamente",
            "servicio": {
                "id_servicio": service.id_servicio,
                "nombre": service.nombre,
                "estado": service.estado
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el estado del servicio: {str(e)}"
        )

