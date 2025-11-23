# app/api/v1/routers/service_requests.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.models.publicar_servicio.solicitud_servicio import SolicitudServicio
from app.models.servicio.service import ServicioModel
from app.models.publicar_servicio.category import CategoriaModel
from app.models.publicar_servicio.moneda import Moneda
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.perfil import UserModel
from app.services.direct_db_service import direct_db_service

router = APIRouter(prefix="/service-requests", tags=["service-requests"])

# Constantes para estados de aprobación
ESTADO_PENDIENTE = "pendiente"
ESTADO_APROBADA = "aprobada"
ESTADO_RECHAZADA = "rechazada"

# Constantes para valores por defecto
VALOR_DEFAULT_NO_ESPECIFICADO = "No especificado"

# Constantes para mensajes de error
MSG_SOLICITUD_NO_ENCONTRADA = "Solicitud no encontrada."
MSG_SOLICITUD_YA_PROCESADA = "La solicitud ya ha sido procesada."
MSG_PERFIL_EMPRESA_NO_ENCONTRADO = "Perfil de empresa no encontrado."
MSG_NO_MONEDAS_ENCONTRADAS = "No se encontraron monedas en la base de datos. Agregue al menos una moneda."
MSG_ERROR_OBTENER_SOLICITUDES = "Error al obtener todas las solicitudes: {error}"
MSG_ERROR_APROBAR_SOLICITUD = "Error al aprobar la solicitud: {error}"
MSG_ERROR_RECHAZAR_SOLICITUD = "Error al rechazar la solicitud: {error}"

# Constantes para mensajes de éxito
MSG_SOLICITUD_APROBADA = "Solicitud aprobada y servicio creado exitosamente."
MSG_SOLICITUD_RECHAZADA = "Solicitud rechazada exitosamente."

from pydantic import BaseModel

class ServiceRequestWithDetails(BaseModel):
    id_solicitud: int
    nombre_servicio: str
    descripcion: str
    estado_aprobacion: str
    comentario_admin: str | None
    created_at: str
    id_categoria: int | None
    id_perfil: int

    # Información adicional
    nombre_categoria: str | None
    nombre_empresa: str | None
    nombre_contacto: str | None
    email_contacto: str | None

    class Config:
        from_attributes = True

class RejectRequestData(BaseModel):
    comentario_admin: str | None = None

@router.get(
    "/",
    response_model=List[ServiceRequestWithDetails],
    status_code=status.HTTP_200_OK,
    description="Obtiene solicitudes de servicios. Con all=true trae todas las solicitudes, sin parámetros solo las pendientes."
)
async def get_service_requests(
    all: bool = Query(False, description="Si es True, trae todas las solicitudes independiente del estado"),
    admin: bool = Query(False, description="Si es True, indica que es un administrador"),
    limit: int = Query(100, description="Límite de solicitudes a retornar"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene solicitudes de servicios.
    - Si all=True: trae todas las solicitudes independiente del estado
    - Si all=False: trae solo las solicitudes pendientes
    Incluye información adicional de la empresa, contacto y categoría.
    """
    # Obtener solicitudes con información completa
    try:
        # Construir la consulta base
        query = select(
            SolicitudServicio.id_solicitud,
            SolicitudServicio.nombre_servicio,
            SolicitudServicio.descripcion,
            SolicitudServicio.estado_aprobacion,
            SolicitudServicio.comentario_admin,
            SolicitudServicio.created_at,
            SolicitudServicio.id_categoria,
            SolicitudServicio.id_perfil,
            CategoriaModel.nombre.label('nombre_categoria'),
            PerfilEmpresa.razon_social.label('nombre_empresa'),
            UserModel.nombre_persona.label('nombre_contacto')
        ).select_from(SolicitudServicio)\
         .join(CategoriaModel, SolicitudServicio.id_categoria == CategoriaModel.id_categoria, isouter=True)\
         .join(PerfilEmpresa, SolicitudServicio.id_perfil == PerfilEmpresa.id_perfil, isouter=True)\
         .join(UserModel, PerfilEmpresa.user_id == UserModel.id, isouter=True)

        # Aplicar filtro según el parámetro 'all'
        if not all:
            # Solo solicitudes pendientes (comportamiento original)
            query = query.where(SolicitudServicio.estado_aprobacion == ESTADO_PENDIENTE)
        
        # Ordenar por fecha de creación (más recientes primero)
        query = query.order_by(SolicitudServicio.created_at.desc())
        
        # Aplicar límite
        if limit > 0:
            query = query.limit(limit)

        # Ejecutar la consulta
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Log para debugging
        print(f"🔍 Parámetros recibidos: all={all}, admin={admin}, limit={limit}")
        print(f"📊 Total de solicitudes encontradas: {len(rows)}")
        if rows:
            estados = [row.estado_aprobacion for row in rows]
            print(f"🔍 Estados encontrados: {set(estados)}")

        # Formatear respuesta con información completa
        formatted_requests = []
        for row in rows:
            formatted_request = {
                "id_solicitud": row.id_solicitud,
                "nombre_servicio": row.nombre_servicio,
                "descripcion": row.descripcion,
                "estado_aprobacion": row.estado_aprobacion,
                "comentario_admin": row.comentario_admin,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "id_categoria": row.id_categoria,
                "id_perfil": row.id_perfil,
                "nombre_categoria": row.nombre_categoria or VALOR_DEFAULT_NO_ESPECIFICADO,
                "nombre_empresa": row.nombre_empresa or VALOR_DEFAULT_NO_ESPECIFICADO,
                "nombre_contacto": row.nombre_contacto or VALOR_DEFAULT_NO_ESPECIFICADO,
                "email_contacto": None  # Email no disponible en el modelo actual
            }
            formatted_requests.append(formatted_request)

        return formatted_requests

    except Exception as e:
        # Si hay algún error, devolver al menos las solicitudes básicas
        print(f"Error en get_pending_service_requests: {e}")
        print("Intentando consulta básica...")

        # Consulta básica como fallback
        result = await db.execute(
            select(SolicitudServicio)
            .where(SolicitudServicio.estado_aprobacion == 'pendiente')
        )
        requests = result.scalars().all()

        formatted_requests = []
        for request in requests:
            formatted_request = {
                "id_solicitud": request.id_solicitud,
                "nombre_servicio": request.nombre_servicio,
                "descripcion": request.descripcion,
                "estado_aprobacion": request.estado_aprobacion,
                "comentario_admin": request.comentario_admin,
                "created_at": request.created_at.isoformat() if request.created_at else None,
                "id_categoria": request.id_categoria,
                "id_perfil": request.id_perfil,
                "nombre_categoria": VALOR_DEFAULT_NO_ESPECIFICADO,
                "nombre_empresa": VALOR_DEFAULT_NO_ESPECIFICADO,
                "nombre_contacto": VALOR_DEFAULT_NO_ESPECIFICADO,
                "email_contacto": VALOR_DEFAULT_NO_ESPECIFICADO
            }
            formatted_requests.append(formatted_request)

        return formatted_requests


# Endpoint específico para administradores - Todas las solicitudes
@router.get(
    "/admin/todas",
    response_model=List[ServiceRequestWithDetails],
    status_code=status.HTTP_200_OK,
    description="Obtiene TODAS las solicitudes de servicios para administradores (pendientes, aprobadas, rechazadas)."
)
async def get_all_service_requests_for_admin(
    limit: int = Query(100, description="Límite de solicitudes a retornar"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene TODAS las solicitudes de servicios para administradores.
    Incluye solicitudes pendientes, aprobadas y rechazadas.
    Usa direct_db_service para evitar problemas con PgBouncer y prepared statements.
    """
    try:
        conn = await direct_db_service.get_connection()
        try:
            # Query SQL directa para evitar prepared statements
            query = """
                SELECT 
                    ss.id_solicitud,
                    ss.nombre_servicio,
                    ss.descripcion,
                    ss.estado_aprobacion,
                    ss.comentario_admin,
                    ss.created_at,
                    ss.id_categoria,
                    ss.id_perfil,
                    c.nombre AS nombre_categoria,
                    pe.razon_social AS nombre_empresa,
                    u.nombre_persona AS nombre_contacto
                FROM solicitud_servicio ss
                LEFT JOIN categoria c ON ss.id_categoria = c.id_categoria
                LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
                LEFT JOIN users u ON pe.user_id = u.id
                ORDER BY ss.created_at DESC
                LIMIT $1
            """
            
            rows = await conn.fetch(query, limit)
            
            # Log para debugging
            print(f"🔍 Endpoint /admin/todas - Total de solicitudes encontradas: {len(rows)}")
            if rows:
                estados = [row['estado_aprobacion'] for row in rows]
                print(f"🔍 Estados encontrados: {set(estados)}")

            # Formatear respuesta con información completa
            formatted_requests = []
            for row in rows:
                formatted_request = {
                    "id_solicitud": row['id_solicitud'],
                    "nombre_servicio": row['nombre_servicio'],
                    "descripcion": row['descripcion'],
                    "estado_aprobacion": row['estado_aprobacion'],
                    "comentario_admin": row['comentario_admin'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "id_categoria": row['id_categoria'],
                    "id_perfil": row['id_perfil'],
                    "nombre_categoria": row['nombre_categoria'] or VALOR_DEFAULT_NO_ESPECIFICADO,
                    "nombre_empresa": row['nombre_empresa'] or VALOR_DEFAULT_NO_ESPECIFICADO,
                    "nombre_contacto": row['nombre_contacto'] or VALOR_DEFAULT_NO_ESPECIFICADO,
                    "email_contacto": None  # Se obtendrá por separado
                }
                formatted_requests.append(formatted_request)

            return formatted_requests
        finally:
            await direct_db_service.pool.release(conn)

    except Exception as e:
        print(f"❌ Error en get_all_service_requests_for_admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_OBTENER_SOLICITUDES.format(error=str(e))
        )


@router.put(
    "/{request_id}/approve",
    status_code=status.HTTP_200_OK,
    description="Aprueba una solicitud de servicio y crea automáticamente el servicio."
)
async def approve_service_request(
    request_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Aprueba una solicitud de servicio y crea automáticamente el servicio correspondiente.
    """
    try:
        async with db.begin():
            # Obtener la solicitud
            request_result = await db.execute(
                select(SolicitudServicio).where(SolicitudServicio.id_solicitud == request_id)
            )
            request = request_result.scalars().first()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=MSG_SOLICITUD_NO_ENCONTRADA
                )

            if request.estado_aprobacion != ESTADO_PENDIENTE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=MSG_SOLICITUD_YA_PROCESADA
                )

            # Obtener la primera moneda disponible (simplificado)
            from sqlalchemy import text

            # Intentar primero con PYG, luego con cualquier moneda disponible
            moneda_result = await db.execute(
                text("SELECT id_moneda, codigo_iso_moneda FROM moneda ORDER BY codigo_iso_moneda LIMIT 1")
            )
            moneda_row = moneda_result.first()

            if not moneda_row:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=MSG_NO_MONEDAS_ENCONTRADAS
                )

            id_moneda_default = moneda_row[0]
            codigo_moneda = moneda_row[1]
            print(f"✅ Usando moneda: {codigo_moneda} (ID: {id_moneda_default})")

            # Crear el servicio
            nuevo_servicio = ServicioModel(
                nombre=request.nombre_servicio,
                descripcion=request.descripcion,
                precio=0.0,  # Precio por defecto, el proveedor lo configurará después
                id_categoria=request.id_categoria,
                id_perfil=request.id_perfil,
                id_moneda=id_moneda_default,
                estado=True
            )
            db.add(nuevo_servicio)

            # Actualizar el estado de la solicitud
            request.estado_aprobacion = ESTADO_APROBADA

            await db.flush()

        return {"message": MSG_SOLICITUD_APROBADA}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_APROBAR_SOLICITUD.format(error=str(e))
        )


@router.put(
    "/{request_id}/reject",
    status_code=status.HTTP_200_OK,
    description="Rechaza una solicitud de servicio."
)
async def reject_service_request(
    request_id: int,
    request_data: RejectRequestData,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Rechaza una solicitud de servicio.
    """
    try:
        # Obtener la solicitud
        request_result = await db.execute(
            select(SolicitudServicio).where(SolicitudServicio.id_solicitud == request_id)
        )
        request = request_result.scalars().first()

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada."
            )

        if request.estado_aprobacion != 'pendiente':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La solicitud ya ha sido procesada."
            )

        # Actualizar el estado de la solicitud
        request.estado_aprobacion = ESTADO_RECHAZADA

        # Guardar el comentario si existe (incluso si es vacío)
        comentario_admin = request_data.comentario_admin
        if comentario_admin is not None:
            request.comentario_admin = comentario_admin

        await db.commit()

        print(f"✅ Solicitud {request_id} rechazada")
        if comentario_admin:
            print(f"   Comentario guardado: {comentario_admin}")
        else:
            print("   Sin comentario")

        return {"message": MSG_SOLICITUD_RECHAZADA}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_RECHAZAR_SOLICITUD.format(error=str(e))
        )


# Endpoint para proveedores - Mis Solicitudes de Servicios
@router.get(
    "/my-requests",
    response_model=List[ServiceRequestWithDetails],
    status_code=status.HTTP_200_OK,
    description="Obtiene las solicitudes de servicios del proveedor actual."
)
async def get_my_service_requests(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene todas las solicitudes de servicios realizadas por el proveedor actual.
    Incluye información adicional de la empresa, contacto y categoría.
    Usa direct_db_service para evitar problemas con PgBouncer y prepared statements.
    """
    try:
        conn = await direct_db_service.get_connection()
        try:
            # Obtener el perfil de empresa del usuario actual
            perfil_query = "SELECT id_perfil, razon_social FROM perfil_empresa WHERE user_id = $1"
            perfil_row = await conn.fetchrow(perfil_query, current_user.id)
            
            if not perfil_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
                )
            
            perfil_id = perfil_row['id_perfil']
            razon_social = perfil_row['razon_social']
            
            # Consulta SQL directa con joins para obtener toda la información
            query = """
                SELECT 
                    ss.id_solicitud,
                    ss.nombre_servicio,
                    ss.descripcion,
                    ss.estado_aprobacion,
                    ss.comentario_admin,
                    ss.created_at,
                    ss.id_categoria,
                    ss.id_perfil,
                    c.nombre AS nombre_categoria,
                    pe.razon_social AS nombre_empresa,
                    u.nombre_persona AS nombre_contacto
                FROM solicitud_servicio ss
                LEFT JOIN categoria c ON ss.id_categoria = c.id_categoria
                LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
                LEFT JOIN users u ON pe.user_id = u.id
                WHERE ss.id_perfil = $1
                ORDER BY ss.created_at DESC
            """
            
            rows = await conn.fetch(query, perfil_id)
            
            # Formatear respuesta con información completa
            formatted_requests = []
            for row in rows:
                formatted_request = {
                    "id_solicitud": row['id_solicitud'],
                    "nombre_servicio": row['nombre_servicio'],
                    "descripcion": row['descripcion'],
                    "estado_aprobacion": row['estado_aprobacion'],
                    "comentario_admin": row['comentario_admin'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "id_categoria": row['id_categoria'],
                    "id_perfil": row['id_perfil'],
                    "nombre_categoria": row['nombre_categoria'] or VALOR_DEFAULT_NO_ESPECIFICADO,
                    "nombre_empresa": row['nombre_empresa'] or razon_social or VALOR_DEFAULT_NO_ESPECIFICADO,
                    "nombre_contacto": row['nombre_contacto'] or VALOR_DEFAULT_NO_ESPECIFICADO,
                    "email_contacto": None
                }
                formatted_requests.append(formatted_request)

            return formatted_requests
        finally:
            await direct_db_service.pool.release(conn)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en get_my_service_requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo solicitudes de servicios: {e}"
        )
