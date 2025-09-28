# app/api/v1/routers/services.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.servicio.service import ServicioModel
from app.models.publicar_servicio.category import CategoriaModel
from app.schemas.servicio.service import ServicioOut, ServicioIn, ServicioWithProvider


router = APIRouter(prefix="/services", tags=["services"])


# Schemas para el endpoint de filtros
class FilteredServicesResponse(BaseModel):
    services: List[ServicioWithProvider]
    pagination: dict
    filters_applied: dict


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
            detail=f"No se encontraron servicios disponibles en esta categoría como plantillas."
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
            # Construir la consulta base
            base_query = """
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
                WHERE s.estado = true AND pe.verificado = true
            """
            
            # Construir filtros dinámicamente
            filters = []
            params = []
            param_count = 0
            
            # Filtro por moneda
            if currency:
                param_count += 1
                filters.append(f"TRIM(m.codigo_iso_moneda) = UPPER(${param_count})")
                params.append(currency.strip().upper())
            
            # Filtro por precio mínimo
            if min_price is not None:
                param_count += 1
                filters.append(f"s.precio >= ${param_count}")
                params.append(min_price)
            
            # Filtro por precio máximo
            if max_price is not None:
                param_count += 1
                filters.append(f"s.precio <= ${param_count}")
                params.append(max_price)
            
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
            
            # Aplicar filtros a la consulta
            if filters:
                base_query += " AND " + " AND ".join(filters)
            
            # Agregar ordenamiento y paginación
            base_query += " ORDER BY s.created_at DESC"
            
            # Parámetros para paginación
            param_count += 1
            limit_param = param_count
            param_count += 1
            offset_param = param_count
            
            base_query += f" LIMIT ${limit_param} OFFSET ${offset_param}"
            params.extend([limit, offset])
            
            print(f"🔍 Consulta unificada: {base_query}")
            print(f"📊 Parámetros: {params}")
            
            # Ejecutar consulta principal
            services_data_tuples = await conn.fetch(base_query, *params)
            
            if not services_data_tuples:
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

            # Obtener IDs de servicios para consulta de tarifas
            service_ids = [row['id_servicio'] for row in services_data_tuples]
            
            # Consulta de tarifas (N+1 optimization)
            tarifas_data = []
            if service_ids:
                tarifas_data = await conn.fetch("""
                    SELECT 
                        ts.id_tarifa_servicio, ts.id_servicio, ts.monto, ts.descripcion, 
                        ts.fecha_inicio, ts.fecha_fin, ts.id_tarifa, tt.nombre as nombre_tipo_tarifa
                    FROM tarifa_servicio ts
                    LEFT JOIN tipo_tarifa_servicio tt ON ts.id_tarifa = tt.id_tarifa
                    WHERE ts.id_servicio = ANY($1)
                """, service_ids)

            # Mapear datos a diccionarios
            services_map_by_id = {}
            for row in services_data_tuples:
                service_dict = dict(row)
                service_id = service_dict['id_servicio']
                service_dict['tarifas'] = []
                services_map_by_id[service_id] = service_dict

            # Asignar tarifas
            for tarifa_row in tarifas_data:
                service_id = tarifa_row['id_servicio']
                if service_id in services_map_by_id:
                    tarifa_dict = {
                        "id_tarifa_servicio": tarifa_row['id_tarifa_servicio'],
                        "monto": float(tarifa_row['monto']),
                        "descripcion": tarifa_row['descripcion'],
                        "fecha_inicio": tarifa_row['fecha_inicio'].isoformat(),
                        "fecha_fin": tarifa_row['fecha_fin'].isoformat() if tarifa_row['fecha_fin'] else None,
                        "id_tarifa": tarifa_row['id_tarifa'],
                        "nombre_tipo_tarifa": tarifa_row['nombre_tipo_tarifa'] or "Sin especificar"
                    }
                    services_map_by_id[service_id]['tarifas'].append(tarifa_dict)

            # Crear objetos ServicioWithProvider
            services = [ServicioWithProvider(**data) for data in services_map_by_id.values()]
            
            # Consulta para obtener el total (sin paginación)
            count_query = """
                SELECT COUNT(*) as total
                FROM servicio s
                JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
                JOIN users u ON pe.user_id = u.id
                LEFT JOIN direccion dir ON pe.id_direccion = dir.id_direccion
                LEFT JOIN departamento d ON dir.id_departamento = d.id_departamento
                LEFT JOIN ciudad c ON dir.id_ciudad = c.id_ciudad
                LEFT JOIN barrio b ON dir.id_barrio = b.id_barrio
                LEFT JOIN moneda m ON s.id_moneda = m.id_moneda
                WHERE s.estado = true AND pe.verificado = true
            """
            
            # Aplicar los mismos filtros al count
            if filters:
                count_query += " AND " + " AND ".join(filters)
            
            # Parámetros para count (sin limit/offset)
            count_params = params[:-2]  # Remover limit y offset
            count_result = await conn.fetchrow(count_query, *count_params)
            total = count_result['total'] if count_result else 0
            
            # Calcular paginación
            current_page = (offset // limit) + 1
            total_pages = (total + limit - 1) // limit  # Ceiling division
            
            return FilteredServicesResponse(
                services=services,
                pagination={
                    "total": total,
                    "page": current_page,
                    "total_pages": total_pages,
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
            # Construir la consulta base
            base_query = """
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
                WHERE s.estado = true AND pe.verificado = true
            """
            
            # Construir filtros dinámicamente
            filters = []
            params = []
            param_count = 0
            
            # Filtro por moneda
            if currency:
                param_count += 1
                filters.append(f"TRIM(m.codigo_iso_moneda) = UPPER(${param_count})")
                params.append(currency.strip().upper())
            
            # Filtro por precio mínimo
            if min_price is not None:
                param_count += 1
                filters.append(f"s.precio >= ${param_count}")
                params.append(min_price)
            
            # Filtro por precio máximo
            if max_price is not None:
                param_count += 1
                filters.append(f"s.precio <= ${param_count}")
                params.append(max_price)
            
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
            
            # Aplicar filtros a la consulta
            if filters:
                base_query += " AND " + " AND ".join(filters)
            
            # Agregar ordenamiento y paginación
            base_query += " ORDER BY s.created_at DESC"
            
            # Parámetros para paginación
            param_count += 1
            limit_param = param_count
            param_count += 1
            offset_param = param_count
            
            base_query += f" LIMIT ${limit_param} OFFSET ${offset_param}"
            params.extend([limit, offset])
            
            print(f"🔍 Consulta filtrada: {base_query}")
            print(f"📊 Parámetros: {params}")
            
            # Ejecutar consulta principal
            services_data_tuples = await conn.fetch(base_query, *params)
            
            if not services_data_tuples:
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

            # Obtener IDs de servicios para consulta de tarifas
            service_ids = [row['id_servicio'] for row in services_data_tuples]
            
            # Consulta de tarifas (N+1 optimization)
            tarifas_data = []
            if service_ids:
                tarifas_data = await conn.fetch("""
                    SELECT 
                        ts.id_tarifa_servicio, ts.id_servicio, ts.monto, ts.descripcion, 
                        ts.fecha_inicio, ts.fecha_fin, ts.id_tarifa, tt.nombre as nombre_tipo_tarifa
                    FROM tarifa_servicio ts
                    LEFT JOIN tipo_tarifa_servicio tt ON ts.id_tarifa = tt.id_tarifa
                    WHERE ts.id_servicio = ANY($1)
                """, service_ids)

            # Mapear datos a diccionarios
            services_map_by_id = {}
            for row in services_data_tuples:
                service_dict = dict(row)
                service_id = service_dict['id_servicio']
                service_dict['tarifas'] = []
                services_map_by_id[service_id] = service_dict

            # Asignar tarifas
            for tarifa_row in tarifas_data:
                service_id = tarifa_row['id_servicio']
                if service_id in services_map_by_id:
                    tarifa_dict = {
                        "id_tarifa_servicio": tarifa_row['id_tarifa_servicio'],
                        "monto": float(tarifa_row['monto']),
                        "descripcion": tarifa_row['descripcion'],
                        "fecha_inicio": tarifa_row['fecha_inicio'].isoformat(),
                        "fecha_fin": tarifa_row['fecha_fin'].isoformat() if tarifa_row['fecha_fin'] else None,
                        "id_tarifa": tarifa_row['id_tarifa'],
                        "nombre_tipo_tarifa": tarifa_row['nombre_tipo_tarifa'] or "Sin especificar"
                    }
                    services_map_by_id[service_id]['tarifas'].append(tarifa_dict)

            # Crear objetos ServicioWithProvider
            services = [ServicioWithProvider(**data) for data in services_map_by_id.values()]
            
            # Consulta para obtener el total (sin paginación)
            count_query = """
                SELECT COUNT(*) as total
                FROM servicio s
                JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
                JOIN users u ON pe.user_id = u.id
                LEFT JOIN direccion dir ON pe.id_direccion = dir.id_direccion
                LEFT JOIN departamento d ON dir.id_departamento = d.id_departamento
                LEFT JOIN ciudad c ON dir.id_ciudad = c.id_ciudad
                LEFT JOIN barrio b ON dir.id_barrio = b.id_barrio
                LEFT JOIN moneda m ON s.id_moneda = m.id_moneda
                WHERE s.estado = true AND pe.verificado = true
            """
            
            # Aplicar los mismos filtros al count
            if filters:
                count_query += " AND " + " AND ".join(filters)
            
            # Parámetros para count (sin limit/offset)
            count_params = params[:-2]  # Remover limit y offset
            count_result = await conn.fetchrow(count_query, *count_params)
            total = count_result['total'] if count_result else 0
            
            # Calcular paginación
            current_page = (offset // limit) + 1
            total_pages = (total + limit - 1) // limit  # Ceiling division
            
            return FilteredServicesResponse(
                services=services,
                pagination={
                    "total": total,
                    "page": current_page,
                    "total_pages": total_pages,
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
            detail=f"No se encontraron servicios activos en la categoría {category_id}."
        )
    return list(services)


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

