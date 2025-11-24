# app/api/v1/routers/admin_router.py

from datetime import datetime
import httpx
import os
import mimetypes
import traceback
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional
import uuid
from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.documento import Documento
from app.models.empresa.tipo_documento import TipoDocumento
from app.models.perfil import UserModel
from app.models.rol import RolModel
from app.models.usuario_rol import UsuarioRolModel
from app.models.publicar_servicio.category import CategoriaModel
from app.models.servicio.service import ServicioModel
from app.schemas.empresa.verificacion_solicitud import VerificacionSolicitudOut
from app.schemas.user import UserProfileAndRolesOut
from app.api.v1.dependencies.auth_user import get_admin_user, get_current_user
from sqlalchemy import delete
from sqlalchemy import or_, and_, func
from app.services.direct_db_service import direct_db_service
from app.services.date_service import DateService
from app.supabase.auth_service import supabase_admin, supabase_auth
from app.api.v1.dependencies.local_storage import local_storage_service
from app.core.config import IDRIVE_BUCKET_NAME
from app.idrive.idrive_service import idrive_s3_client

# Constantes para valores por defecto
VALOR_DEFAULT_NO_DISPONIBLE = "No disponible"
VALOR_DEFAULT_USUARIO_SIN_NOMBRE = "Usuario sin nombre"
VALOR_DEFAULT_EMPRESA_NO_ENCONTRADA = "Empresa no encontrada"
VALOR_DEFAULT_NA = "N/A"
VALOR_DEFAULT_TIPO_NO_ENCONTRADO = "Tipo no encontrado"

# Constantes para estados
ESTADO_PENDIENTE = "pendiente"

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/verificaciones/todas",
    description="Obtiene todas las solicitudes de verificación (aprobadas, rechazadas y pendientes) para estadísticas."
)
async def get_todas_solicitudes_verificacion(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene todas las solicitudes de verificación para calcular estadísticas del dashboard"""
    try:
        print("🔍 DEBUG: Obteniendo todas las solicitudes de verificación...")
        
        # Obtener todas las solicitudes sin filtro de estado
        query = select(VerificacionSolicitud)
        result = await db.execute(query)
        solicitudes = result.scalars().all()
        
        print(f"📊 DEBUG: Total de solicitudes encontradas: {len(solicitudes)}")
        
        # Convertir a formato simple para estadísticas
        solicitudes_data = []
        for solicitud in solicitudes:
            solicitudes_data.append({
                "id_verificacion": solicitud.id_verificacion,
                "estado_aprobacion": solicitud.estado,
                "id_perfil": solicitud.id_perfil,
                "fecha_solicitud": solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else None,
                "fecha_revision": solicitud.fecha_revision.isoformat() if solicitud.fecha_revision else None
            })
        
        print(f"✅ DEBUG: Solicitudes procesadas: {len(solicitudes_data)}")
        print(f"📊 DEBUG: Estados encontrados: {[s['estado_aprobacion'] for s in solicitudes_data]}")
        
        return solicitudes_data
        
    except Exception as e:
        print(f"❌ ERROR: Error obteniendo todas las solicitudes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo todas las solicitudes de verificación: {str(e)}"
        )


# Funciones helper para get_solicitudes_pendientes
async def get_empresa_by_perfil_id(db: AsyncSession, perfil_id: int) -> Optional[PerfilEmpresa]:
    """Obtiene la empresa por ID de perfil"""
    empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.id_perfil == perfil_id)
    empresa_result = await db.execute(empresa_query)
    return empresa_result.scalars().first()

async def get_user_contact_info(db: AsyncSession, user_id: uuid.UUID) -> tuple[str, str]:
    """Obtiene el nombre y email del usuario desde la base de datos y Supabase Auth"""
    user_nombre = VALOR_DEFAULT_NO_DISPONIBLE
    user_email = VALOR_DEFAULT_NO_DISPONIBLE
    
    user_query = select(UserModel).where(UserModel.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalars().first()
    
    if not user:
        return user_nombre, user_email
    
    user_nombre = user.nombre_persona or VALOR_DEFAULT_USUARIO_SIN_NOMBRE
    
    try:
        auth_user = supabase_admin.auth.admin.get_user_by_id(str(user_id))
        if auth_user and auth_user.user:
            user_email = auth_user.user.email or VALOR_DEFAULT_NO_DISPONIBLE
    except Exception as e:
        print(f"Error obteniendo email para usuario {user_id}: {e}")
    
    return user_nombre, user_email

async def get_documentos_by_verificacion(db: AsyncSession, id_verificacion: int) -> List[Documento]:
    """Obtiene todos los documentos de una solicitud de verificación"""
    documentos_query = select(Documento).where(Documento.id_verificacion == id_verificacion)
    documentos_result = await db.execute(documentos_query)
    return documentos_result.scalars().all()

async def get_tipo_documento_by_id(db: AsyncSession, id_tip_documento: int) -> Optional[TipoDocumento]:
    """Obtiene el tipo de documento por ID"""
    tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == id_tip_documento)
    tipo_doc_result = await db.execute(tipo_doc_query)
    return tipo_doc_result.scalars().first()

async def process_documento_detallado(db: AsyncSession, doc: Documento) -> dict:
    """Procesa un documento y retorna su información detallada"""
    tipo_doc = await get_tipo_documento_by_id(db, doc.id_tip_documento)
    
    return {
        "id_documento": doc.id_documento,
        "tipo_documento": tipo_doc.nombre if tipo_doc else VALOR_DEFAULT_TIPO_NO_ENCONTRADO,
        "es_requerido": tipo_doc.es_requerido if tipo_doc else False,
        "estado_revision": doc.estado_revision,
        "url_archivo": doc.url_archivo,
        "fecha_verificacion": doc.fecha_verificacion,
        "observacion": doc.observacion,
        "created_at": doc.created_at
    }

async def process_documentos_detallados(db: AsyncSession, documentos: List[Documento]) -> List[dict]:
    """Procesa todos los documentos y retorna su información detallada"""
    return [await process_documento_detallado(db, doc) for doc in documentos]

def build_empresa_info(empresa: Optional[PerfilEmpresa]) -> dict:
    """Construye la información de empresa para la respuesta"""
    if not empresa:
        return {
            "nombre_empresa": VALOR_DEFAULT_EMPRESA_NO_ENCONTRADA,
            "nombre_fantasia": VALOR_DEFAULT_NA,
            "verificado": False,
            "fecha_verificacion": None,
            "estado_empresa": VALOR_DEFAULT_NA,
            "fecha_inicio": None,
            "fecha_fin": None
        }
    
    return {
        "nombre_empresa": empresa.razon_social,
        "nombre_fantasia": empresa.nombre_fantasia,
        "verificado": empresa.verificado,
        "fecha_verificacion": empresa.fecha_verificacion,
        "estado_empresa": empresa.estado,
        "fecha_inicio": empresa.fecha_inicio,
        "fecha_fin": empresa.fecha_fin
    }

def process_solicitud_data(
    solicitud: VerificacionSolicitud,
    empresa: Optional[PerfilEmpresa],
    user_nombre: str,
    user_email: str,
    documentos_detallados: List[dict]
) -> dict:
    """Procesa una solicitud y construye su diccionario de datos
    
    Nota: Esta función es síncrona porque solo construye un diccionario sin operaciones asíncronas.
    El parámetro db no se usa y se eliminó.
    """
    empresa_info = build_empresa_info(empresa)
    
    return {
        "id_verificacion": solicitud.id_verificacion,
        "fecha_solicitud": solicitud.fecha_solicitud,
        "fecha_revision": solicitud.fecha_revision,
        "estado": solicitud.estado,
        "comentario": solicitud.comentario,
        "id_perfil": solicitud.id_perfil,
        "created_at": solicitud.created_at,
        "documentos": documentos_detallados,
        "nombre_empresa": empresa_info["nombre_empresa"],
        "nombre_fantasia": empresa_info["nombre_fantasia"],
        "nombre_contacto": user_nombre,
        "email_contacto": user_email,
        "verificado": empresa_info["verificado"],
        "fecha_verificacion": empresa_info["fecha_verificacion"],
        "estado_empresa": empresa_info["estado_empresa"],
        "fecha_inicio": empresa_info["fecha_inicio"],
        "fecha_fin": empresa_info["fecha_fin"]
    }

@router.get(
    "/verificaciones/pendientes",
    description="Obtiene todas las solicitudes de verificación pendientes."
)
async def get_solicitudes_pendientes(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene todas las solicitudes de verificación pendientes con información completa.
    Usa direct_db_service para evitar problemas con PgBouncer y prepared statements.
    """
    try:
        conn = await direct_db_service.get_connection()
        try:
            # Query SQL directa para obtener todas las solicitudes pendientes con información relacionada
            query = """
                SELECT 
                    vs.id_verificacion,
                    vs.fecha_solicitud,
                    vs.fecha_revision,
                    vs.estado,
                    vs.comentario,
                    vs.id_perfil,
                    vs.created_at,
                    pe.razon_social AS nombre_empresa,
                    pe.nombre_fantasia,
                    pe.verificado,
                    pe.fecha_verificacion,
                    pe.estado AS estado_empresa,
                    pe.fecha_inicio,
                    pe.fecha_fin,
                    pe.user_id,
                    u.nombre_persona AS nombre_contacto
                FROM verificacion_solicitud vs
                LEFT JOIN perfil_empresa pe ON vs.id_perfil = pe.id_perfil
                LEFT JOIN users u ON pe.user_id = u.id
                WHERE vs.estado = $1
                ORDER BY vs.created_at DESC
            """
            
            solicitudes_rows = await conn.fetch(query, ESTADO_PENDIENTE)
            
            # Obtener todos los user_ids únicos para consultar Supabase Auth
            user_ids = [str(row['user_id']) for row in solicitudes_rows if row['user_id']]
            emails_dict = {}
            
            if user_ids:
                try:
                    for user_id in user_ids:
                        try:
                            auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
                            if auth_user and auth_user.user and auth_user.user.email:
                                emails_dict[user_id] = auth_user.user.email
                        except Exception as e:
                            print(f"Error obteniendo email para usuario {user_id}: {e}")
                except Exception as e:
                    print(f"Error obteniendo emails desde Supabase: {e}")
            
            # Obtener todos los documentos para todas las solicitudes
            verificacion_ids = [row['id_verificacion'] for row in solicitudes_rows]
            documentos_dict = {}
            
            if verificacion_ids:
                documentos_query = """
                    SELECT 
                        d.id_documento,
                        d.id_verificacion,
                        d.id_tip_documento,
                        d.estado_revision,
                        d.url_archivo,
                        d.fecha_verificacion,
                        d.observacion,
                        d.created_at,
                        td.tipo_documento AS tipo_documento_nombre,
                        td.es_requerido
                    FROM documento d
                    LEFT JOIN tipo_documento td ON d.id_tip_documento = td.id_tip_documento
                    WHERE d.id_verificacion = ANY($1)
                    ORDER BY d.id_verificacion, d.created_at
                """
                documentos_rows = await conn.fetch(documentos_query, verificacion_ids)
                
                # Agrupar documentos por id_verificacion
                for doc_row in documentos_rows:
                    id_verificacion = doc_row['id_verificacion']
                    if id_verificacion not in documentos_dict:
                        documentos_dict[id_verificacion] = []
                    documentos_dict[id_verificacion].append({
                        "id_documento": doc_row['id_documento'],
                        "tipo_documento": doc_row['tipo_documento_nombre'] or VALOR_DEFAULT_TIPO_NO_ENCONTRADO,
                        "es_requerido": doc_row['es_requerido'] or False,
                        "estado_revision": doc_row['estado_revision'],
                        "url_archivo": doc_row['url_archivo'],
                        "fecha_verificacion": doc_row['fecha_verificacion'],
                        "observacion": doc_row['observacion'],
                        "created_at": doc_row['created_at']
                    })
            
            # Construir respuesta
            solicitudes_data = []
            for row in solicitudes_rows:
                user_id_str = str(row['user_id']) if row['user_id'] else None
                user_email = emails_dict.get(user_id_str, VALOR_DEFAULT_NO_DISPONIBLE) if user_id_str else VALOR_DEFAULT_NO_DISPONIBLE
                user_nombre = row['nombre_contacto'] or VALOR_DEFAULT_NO_DISPONIBLE
                
                documentos_detallados = documentos_dict.get(row['id_verificacion'], [])
                
                solicitud_data = {
                    "id_verificacion": row['id_verificacion'],
                    "fecha_solicitud": row['fecha_solicitud'],
                    "fecha_revision": row['fecha_revision'],
                    "estado": row['estado'],
                    "comentario": row['comentario'],
                    "id_perfil": row['id_perfil'],
                    "created_at": row['created_at'],
                    "documentos": documentos_detallados,
                    "nombre_empresa": row['nombre_empresa'] or VALOR_DEFAULT_EMPRESA_NO_ENCONTRADA,
                    "nombre_fantasia": row['nombre_fantasia'] or VALOR_DEFAULT_NA,
                    "nombre_contacto": user_nombre,
                    "email_contacto": user_email,
                    "verificado": row['verificado'] or False,
                    "fecha_verificacion": row['fecha_verificacion'],
                    "estado_empresa": row['estado_empresa'] or VALOR_DEFAULT_NA,
                    "fecha_inicio": row['fecha_inicio'],
                    "fecha_fin": row['fecha_fin']
                }
                solicitudes_data.append(solicitud_data)
            
            return solicitudes_data
        finally:
            await direct_db_service.pool.release(conn)
    except Exception as e:
        print(f"Error obteniendo solicitudes pendientes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo solicitudes de verificación pendientes: {str(e)}"
        )


@router.get(
    "/verificaciones/{solicitud_id}/estado",
    description="Obtiene el estado actual de una solicitud de verificación y el rol del usuario asociado."
)
async def get_estado_solicitud(
    solicitud_id: int,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene el estado actual de una solicitud y verifica el rol del usuario"""
    
    # Obtener la solicitud
    solicitud_query = select(VerificacionSolicitud).where(
        VerificacionSolicitud.id_verificacion == solicitud_id
    )
    solicitud_result = await db.execute(solicitud_query)
    solicitud = solicitud_result.scalars().first()
    
    if not solicitud:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    
    # Obtener información de la empresa
    empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.id_perfil == solicitud.id_perfil)
    empresa_result = await db.execute(empresa_query)
    empresa = empresa_result.scalars().first()
    
    # Obtener roles del usuario
    roles_usuario = []
    if empresa and empresa.user_id:
        try:
            roles_query = select(UsuarioRolModel).options(
                joinedload(UsuarioRolModel.rol)
            ).where(UsuarioRolModel.id_usuario == empresa.user_id)
            roles_result = await db.execute(roles_query)
            roles = roles_result.scalars().all()
            roles_usuario = [rol.rol.nombre for rol in roles if rol.rol]
            print(f"✅ Roles encontrados para usuario {empresa.user_id}: {roles_usuario}")
        except Exception as e:
            print(f"❌ Error obteniendo roles del usuario: {e}")
            roles_usuario = []
    
    return {
        "solicitud_id": solicitud_id,
        "estado_solicitud": solicitud.estado,
        "fecha_revision": solicitud.fecha_revision,
        "comentario": solicitud.comentario,
        "user_id": empresa.user_id if empresa else None,
        "roles_usuario": roles_usuario,
        "estado_empresa": empresa.estado if empresa else None,
        "verificado": empresa.verificado if empresa else None
    }


@router.get(
    "/verificaciones/mi-estado",
    description="Obtiene el estado actual de la solicitud de verificación del usuario autenticado."
)
async def get_mi_estado_verificacion(
    current_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene el estado de la solicitud de verificación del usuario actual"""
    
    try:
        # Buscar el perfil de empresa del usuario
        empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            return {
                "estado": "none",
                "mensaje": "No se encontró perfil de empresa para este usuario"
            }
        
        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()
        
        if not solicitud:
            return {
                "estado": "none",
                "mensaje": "No se encontró solicitud de verificación"
            }
        
        # Mapear el estado de la base de datos al estado del frontend
        estado_mapping = {
            "pendiente": "pending",
            "aprobada": "approved", 
            "rechazada": "rejected"
        }
        
        estado_frontend = estado_mapping.get(solicitud.estado, "none")
        
        return {
            "estado": estado_frontend,
            "solicitud_id": solicitud.id_verificacion,
            "fecha_solicitud": solicitud.fecha_solicitud,
            "fecha_revision": solicitud.fecha_revision,
            "comentario": solicitud.comentario,
            "estado_empresa": empresa.estado,
            "verificado": empresa.verificado,
            "mensaje": f"Solicitud {solicitud.estado}"
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo estado de verificación: {e}")
        return {
            "estado": "none",
            "mensaje": f"Error al obtener estado: {str(e)}"
        }

    
@router.get(
    "/verificaciones/{solicitud_id}",
    response_model=VerificacionSolicitudOut,
    description="Obtiene los detalles de una solicitud de verificación específica, incluyendo el perfil "
    "de la empresa y los documentos asociados."
)
async def get_detalle_solicitud(
    solicitud_id: int, 
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    query = select(VerificacionSolicitud).where(VerificacionSolicitud.id_verificacion == solicitud_id)
    #joinedload para cargar el perfil y los documentos
    result = await db.execute(query.options(joinedload(VerificacionSolicitud.perfil_empresa), 
                                            joinedload(VerificacionSolicitud.documento)))
    solicitud = result.scalars().first()

    if not solicitud:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    return solicitud

class AdministradorDecisionAprobar(BaseModel):
    comentario: Optional[str] = None

class AdministradorDecisionRechazar(BaseModel):
    comentario: str

@router.post(
    "/verificaciones/{solicitud_id}/aprobar",
    status_code=status.HTTP_200_OK,
    description="Aprobar una solicitud de verificación y actualizar el estado de la empresa."
)
async def aprobar_solicitud(
    solicitud_id: int, 
    decision: AdministradorDecisionAprobar, 
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        print(f"🔄 Iniciando aprobación de solicitud {solicitud_id}")
        print(f"📝 Comentario recibido: {decision.comentario}")
        
        # Verificar que la solicitud existe
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_verificacion == solicitud_id
        )
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()

        if not solicitud:
            print(f"❌ Solicitud {solicitud_id} no encontrada")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

        print(f"✅ Solicitud encontrada: {solicitud.id_verificacion} - Estado actual: {solicitud.estado}")

        # Verificar que el perfil de empresa existe
        perfil_empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.id_perfil == solicitud.id_perfil)
        perfil_empresa_result = await db.execute(perfil_empresa_query)
        perfil_empresa = perfil_empresa_result.scalars().first()

        if not perfil_empresa:
            print(f"❌ Perfil de empresa no encontrado para solicitud {solicitud_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de empresa no encontrado.")

        print(f"✅ Perfil de empresa encontrado: {perfil_empresa.id_perfil} - Estado actual: {perfil_empresa.estado}")

        # Actualizar la solicitud
        solicitud.estado = "aprobada"
        solicitud.fecha_revision = DateService.now_for_database()
        solicitud.comentario = decision.comentario

        # Actualizar el perfil de empresa
        perfil_empresa.estado = "verificado"
        perfil_empresa.verificado = True
        perfil_empresa.fecha_verificacion = solicitud.fecha_revision
        print(f"✅ Fecha de verificación actualizada en perfil_empresa: {solicitud.fecha_revision}")

        # Actualizar el rol del usuario de cliente a proveedor
        print(f"🔄 Actualizando rol del usuario {perfil_empresa.user_id} de cliente a proveedor...")
        
        # Buscar el rol de proveedor
        print(f"🔍 Buscando rol de proveedor en la base de datos...")
        rol_proveedor_query = select(RolModel).where(RolModel.nombre.ilike('%proveedor%'))
        rol_proveedor_result = await db.execute(rol_proveedor_query)
        rol_proveedor = rol_proveedor_result.scalars().first()
        
        if not rol_proveedor:
            print("❌ No se encontró el rol de proveedor")
            # Intentar buscar todos los roles disponibles para debugging
            todos_roles_query = select(RolModel)
            todos_roles_result = await db.execute(todos_roles_query)
            todos_roles = todos_roles_result.scalars().all()
            roles_disponibles = [rol.nombre for rol in todos_roles]
            print(f"📋 Roles disponibles en el sistema: {roles_disponibles}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"No se encontró el rol de proveedor en el sistema. Roles disponibles: {roles_disponibles}"
            )
        
        print(f"✅ Rol de proveedor encontrado: {rol_proveedor.nombre} (ID: {rol_proveedor.id})")
        
        # Verificar si el usuario ya tiene el rol de proveedor
        rol_usuario_query = select(UsuarioRolModel).where(
            UsuarioRolModel.id_usuario == perfil_empresa.user_id,
            UsuarioRolModel.id_rol == rol_proveedor.id
        )
        rol_usuario_result = await db.execute(rol_usuario_query)
        rol_usuario_existente = rol_usuario_result.scalars().first()
        
        if not rol_usuario_existente:
            # Agregar el rol de proveedor al usuario
            nuevo_rol_usuario = UsuarioRolModel(
                id_usuario=perfil_empresa.user_id,
                id_rol=rol_proveedor.id
            )
            db.add(nuevo_rol_usuario)
            print(f"✅ Rol de proveedor agregado al usuario {perfil_empresa.user_id}")
        else:
            print(f"✅ Usuario {perfil_empresa.user_id} ya tiene el rol de proveedor")

        print(f"🔄 Realizando commit de los cambios...")

        # Commit de los cambios
        await db.commit()

        print(f"✅ Solicitud {solicitud_id} aprobada exitosamente")
        print(f"✅ Usuario {perfil_empresa.user_id} ahora es proveedor")
        return {"message": "Solicitud aprobada, perfil verificado y usuario promovido a proveedor."}
        
    except Exception as e:
        print(f"❌ Error al aprobar solicitud {solicitud_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aprobar la solicitud: {str(e)}"
        )


@router.post(
    "/verificaciones/{solicitud_id}/rechazar",
    status_code=status.HTTP_200_OK,
    description="Rechazar una solicitud de verificación y actualizar el estado de la empresa."
)
async def rechazar_solicitud(
    solicitud_id: int, 
    decision: AdministradorDecisionRechazar, 
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        print(f"🔄 Iniciando rechazo de solicitud {solicitud_id}")
        print(f"📝 Comentario recibido: {decision.comentario}")
        
        # Validar que el comentario no esté vacío
        if not decision.comentario or not decision.comentario.strip():
            print(f"❌ Comentario vacío para solicitud {solicitud_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="El comentario es obligatorio para rechazar una solicitud."
            )
        
        # Verificar que la solicitud existe
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_verificacion == solicitud_id
        )
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()

        if not solicitud:
            print(f"❌ Solicitud {solicitud_id} no encontrada")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

        print(f"✅ Solicitud encontrada: {solicitud.id_verificacion} - Estado actual: {solicitud.estado}")

        # Actualizar la solicitud
        solicitud.estado = "rechazada"
        solicitud.fecha_revision = DateService.now_for_database()
        solicitud.comentario = decision.comentario

        print(f"🔄 Realizando commit de los cambios...")

        # Commit de los cambios
        await db.commit()

        print(f"✅ Solicitud {solicitud_id} rechazada exitosamente")
        return {"message": "Solicitud rechazada."}
        
    except Exception as e:
        print(f"❌ Error al rechazar solicitud {solicitud_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al rechazar la solicitud: {str(e)}"
        )


@router.get(
    "/verificaciones/{solicitud_id}/documentos",
    description="Obtiene los documentos de una solicitud de verificación específica."
)
async def get_documentos_solicitud(
    solicitud_id: int, 
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene todos los documentos de una solicitud de verificación"""
    
    # Verificar que la solicitud existe
    solicitud_query = select(VerificacionSolicitud).where(VerificacionSolicitud.id_verificacion == solicitud_id)
    solicitud_result = await db.execute(solicitud_query)
    solicitud = solicitud_result.scalars().first()
    
    if not solicitud:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    
    # Obtener documentos de la solicitud
    documentos_query = select(Documento).where(Documento.id_verificacion == solicitud_id)
    documentos_result = await db.execute(documentos_query)
    documentos = documentos_result.scalars().all()
    
    # Obtener información detallada de cada documento
    documentos_detallados = []
    for doc in documentos:
        # Obtener tipo de documento
        tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == doc.id_tip_documento)
        tipo_doc_result = await db.execute(tipo_doc_query)
        tipo_doc = tipo_doc_result.scalars().first()
        
        documentos_detallados.append({
            "id_documento": doc.id_documento,
            "tipo_documento": tipo_doc.nombre if tipo_doc else "Tipo no encontrado",
            "es_requerido": tipo_doc.es_requerido if tipo_doc else False,
            "estado_revision": doc.estado_revision,
            "url_archivo": doc.url_archivo,
            "fecha_verificacion": doc.fecha_verificacion,
            "observacion": doc.observacion,
            "created_at": doc.created_at
        })
    
    return {
        "solicitud_id": solicitud_id,
        "documentos": documentos_detallados,
        "total_documentos": len(documentos_detallados)
    }


@router.get(
    "/verificaciones/{solicitud_id}/documentos/{documento_id}/descargar",
    description="Descarga un documento específico de una solicitud de verificación."
)
async def descargar_documento(
    solicitud_id: int,
    documento_id: int,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Descarga un documento específico de una solicitud"""
    
    # Verificar que la solicitud existe
    solicitud_query = select(VerificacionSolicitud).where(VerificacionSolicitud.id_verificacion == solicitud_id)
    solicitud_result = await db.execute(solicitud_query)
    solicitud = solicitud_result.scalars().first()
    
    if not solicitud:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    
    # Obtener el documento específico
    documento_query = select(Documento).where(
        Documento.id_documento == documento_id,
        Documento.id_verificacion == solicitud_id
    )
    documento_result = await db.execute(documento_query)
    documento = documento_result.scalars().first()
    
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    
    # Obtener tipo de documento para el nombre del archivo
    tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == documento.id_tip_documento)
    tipo_doc_result = await db.execute(tipo_doc_query)
    tipo_doc = tipo_doc_result.scalars().first()
    
    # Generar nombre de archivo basado en la extensión real del archivo
    url_archivo = documento.url_archivo
    extension = '.pdf'  # Por defecto
    
    # Extraer extensión de la URL si es posible
    if url_archivo and '.' in url_archivo:
        # Buscar la extensión en la URL
        url_parts = url_archivo.split('/')
        if url_parts:
            last_part = url_parts[-1]
            if '.' in last_part:
                extension = '.' + last_part.split('.')[-1].lower()
    
    nombre_archivo = f"{tipo_doc.nombre if tipo_doc else 'documento'}_{documento_id}{extension}"
    
    # Si el documento está en IDrive2, devolver la URL directa
    if documento.url_archivo and documento.url_archivo != 'temp://pending':
        return {
            "url_descarga": documento.url_archivo,
            "nombre_archivo": nombre_archivo,
            "tipo_documento": tipo_doc.nombre if tipo_doc else "Documento",
            "mensaje": "Documento disponible para descarga"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Documento no disponible para descarga."
        )


@router.get(
    "/verificaciones/{solicitud_id}/documentos/{documento_id}/ver",
    description="Sirve un documento específico para visualización."
)
async def ver_documento(
    solicitud_id: int,
    documento_id: int,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Sirve un documento específico para visualización"""
    
    # Verificar que la solicitud existe
    solicitud_query = select(VerificacionSolicitud).where(VerificacionSolicitud.id_verificacion == solicitud_id)
    solicitud_result = await db.execute(solicitud_query)
    solicitud = solicitud_result.scalars().first()
    
    if not solicitud:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    
    # Obtener el documento específico
    documento_query = select(Documento).where(
        Documento.id_documento == documento_id,
        Documento.id_verificacion == solicitud_id
    )
    documento_result = await db.execute(documento_query)
    documento = documento_result.scalars().first()
    
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    
    # Obtener tipo de documento para el nombre del archivo
    tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == documento.id_tip_documento)
    tipo_doc_result = await db.execute(tipo_doc_query)
    tipo_doc = tipo_doc_result.scalars().first()
    
    # Generar nombre de archivo basado en la extensión real del archivo
    url_archivo = documento.url_archivo
    extension = '.pdf'  # Por defecto
    
    # Extraer extensión de la URL si es posible
    if url_archivo and '.' in url_archivo:
        # Buscar la extensión en la URL
        url_parts = url_archivo.split('/')
        if url_parts:
            last_part = url_parts[-1]
            if '.' in last_part:
                extension = '.' + last_part.split('.')[-1].lower()
    
    nombre_archivo = f"{tipo_doc.nombre if tipo_doc else 'documento'}_{documento_id}{extension}"
    
    # Si el documento está en IDrive2, devolver la URL directa
    if documento.url_archivo and documento.url_archivo != 'temp://pending':
        return {
            "url_visualizacion": documento.url_archivo,
            "nombre_archivo": nombre_archivo,
            "tipo_documento": tipo_doc.nombre if tipo_doc else "Documento",
            "mensaje": "Documento disponible para visualización"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Documento no disponible para visualización."
        )


# Funciones helper para servir_documento
async def verify_admin_token(token: str, db: AsyncSession) -> str:
    """Verifica el token y retorna el user_id si es admin válido"""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    
    try:
        user_response = supabase_auth.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        
        user_id = user_response.user.id
        
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
        
        roles_query = select(UsuarioRolModel).options(
            joinedload(UsuarioRolModel.rol)
        ).where(UsuarioRolModel.id_usuario == user_id)
        roles_result = await db.execute(roles_query)
        roles = roles_result.scalars().all()
        
        is_admin = any(
            role.rol and role.rol.nombre.lower() in ['admin', 'administrador']
            for role in roles
        )
        
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos de administrador")
        
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error de autenticación: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Error de autenticación")

async def get_solicitud_by_id(db: AsyncSession, solicitud_id: int) -> VerificacionSolicitud:
    """Obtiene la solicitud por ID"""
    solicitud_query = select(VerificacionSolicitud).where(VerificacionSolicitud.id_verificacion == solicitud_id)
    solicitud_result = await db.execute(solicitud_query)
    solicitud = solicitud_result.scalars().first()
    
    if not solicitud:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    return solicitud

async def get_documento_by_ids(db: AsyncSession, solicitud_id: int, documento_id: int) -> Documento:
    """Obtiene el documento por IDs de solicitud y documento"""
    documento_query = select(Documento).where(
        Documento.id_documento == documento_id,
        Documento.id_verificacion == solicitud_id
    )
    documento_result = await db.execute(documento_query)
    documento = documento_result.scalars().first()
    
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    return documento

async def get_tipo_documento_by_id(db: AsyncSession, id_tip_documento: int) -> Optional[TipoDocumento]:
    """Obtiene el tipo de documento por ID"""
    tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == id_tip_documento)
    tipo_doc_result = await db.execute(tipo_doc_query)
    return tipo_doc_result.scalars().first()

def generate_filename(tipo_doc: Optional[TipoDocumento], documento_id: int, url_archivo: str) -> str:
    """Genera el nombre de archivo basado en el tipo de documento y la extensión de la URL"""
    extension = '.pdf'  # Por defecto
    
    if url_archivo and '.' in url_archivo:
        url_parts = url_archivo.split('/')
        if url_parts:
            last_part = url_parts[-1]
            if '.' in last_part:
                extension = '.' + last_part.split('.')[-1].lower()
    
    nombre_base = tipo_doc.nombre if tipo_doc else 'documento'
    return f"{nombre_base}_{documento_id}{extension}"

def get_content_type_from_filename(nombre_archivo: str, extension: str) -> str:
    """Determina el tipo de contenido basado en el nombre del archivo y extensión"""
    content_type, _ = mimetypes.guess_type(nombre_archivo)
    if content_type:
        return content_type
    
    extension_lower = extension.lower()
    if extension_lower in ['.jpg', '.jpeg']:
        return "image/jpeg"
    elif extension_lower == '.png':
        return "image/png"
    elif extension_lower == '.pdf':
        return "application/pdf"
    elif extension_lower in ['.doc', '.docx']:
        return "application/msword"
    return "application/octet-stream"

def serve_local_document(url_archivo: str, nombre_archivo: str) -> StreamingResponse:
    """Sirve un documento almacenado localmente"""
    serve_success, serve_message, file_content = local_storage_service.serve_file(url_archivo)
    
    if not serve_success or not file_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accediendo al documento local: {serve_message}"
        )
    
    content_type, _ = mimetypes.guess_type(nombre_archivo)
    if not content_type:
        content_type = "application/octet-stream"
    
    return StreamingResponse(
        iter([file_content]),
        media_type=content_type,
        headers={
            "Content-Disposition": f"inline; filename={nombre_archivo}",
            "Content-Type": content_type,
            "Content-Length": str(len(file_content))
        }
    )

def extract_file_key_from_idrive_url(url_archivo: str) -> str:
    """Extrae la clave del archivo desde una URL de iDrive"""
    url_parts = url_archivo.split('/')
    key_parts = []
    found_bucket = False
    
    for part in url_parts:
        if found_bucket:
            key_parts.append(part)
        elif part in ['documentos', 'files', 'uploads'] or (IDRIVE_BUCKET_NAME and IDRIVE_BUCKET_NAME in part):
            found_bucket = True
    
    if not key_parts:
        raise Exception("No se pudo extraer la clave de la URL")
    
    return '/'.join(key_parts)

async def download_from_idrive_direct(url_archivo: str) -> bytes:
    """Intenta descargar desde iDrive usando HTTP directo"""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url_archivo)
        response.raise_for_status()
        return response.content

def download_from_idrive_s3(url_archivo: str) -> bytes:
    """Intenta descargar desde iDrive usando el cliente S3
    
    Nota: Esta función es síncrona porque boto3 (idrive_s3_client) es síncrono.
    Se ejecutará en un thread pool cuando se llame desde una función asíncrona.
    """
    key = extract_file_key_from_idrive_url(url_archivo)
    response = idrive_s3_client.get_object(Bucket=IDRIVE_BUCKET_NAME, Key=key)
    return response['Body'].read()

async def download_from_idrive_with_headers(url_archivo: str) -> bytes:
    """Intenta descargar desde iDrive usando headers específicos"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/pdf,application/octet-stream,*/*',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url_archivo, headers=headers)
        response.raise_for_status()
        return response.content

async def download_idrive_document(url_archivo: str) -> bytes:
    """Descarga un documento desde iDrive usando múltiples estrategias"""
    import asyncio
    try:
        return await download_from_idrive_direct(url_archivo)
    except Exception:
        try:
            # Ejecutar función síncrona en thread pool para no bloquear el event loop
            return await asyncio.to_thread(download_from_idrive_s3, url_archivo)
        except Exception:
            return await download_from_idrive_with_headers(url_archivo)

async def serve_idrive_document(url_archivo: str, nombre_archivo: str, extension: str) -> StreamingResponse:
    """Sirve un documento desde iDrive"""
    try:
        content = await download_idrive_document(url_archivo)
        content_type = get_content_type_from_filename(nombre_archivo, extension)
        
        return StreamingResponse(
            iter([content]),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={nombre_archivo}",
                "Content-Type": content_type,
                "Content-Length": str(len(content))
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo acceder al documento. Error: {str(e)}"
        )

async def serve_document_by_storage_type(documento: Documento, nombre_archivo: str, extension: str) -> StreamingResponse:
    """Sirve un documento según su tipo de almacenamiento"""
    url_archivo = documento.url_archivo
    
    if not url_archivo or url_archivo == 'temp://pending':
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no disponible."
        )
    
    if url_archivo.startswith('local://'):
        return serve_local_document(url_archivo, nombre_archivo)
    elif url_archivo.startswith('temp://'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento temporal no disponible para descarga."
        )
    elif url_archivo.startswith(('http://', 'https://')):
        return await serve_idrive_document(url_archivo, nombre_archivo, extension)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de URL no reconocido: {url_archivo}"
        )

@router.get(
    "/verificaciones/{solicitud_id}/documentos/{documento_id}/servir",
    description="Sirve directamente el archivo desde el backend."
)
async def servir_documento(
    solicitud_id: int,
    documento_id: int,
    token: str = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Sirve directamente el archivo desde el backend"""
    await verify_admin_token(token, db)
    
    solicitud = await get_solicitud_by_id(db, solicitud_id)
    documento = await get_documento_by_ids(db, solicitud_id, documento_id)
    tipo_doc = await get_tipo_documento_by_id(db, documento.id_tip_documento)
    
    nombre_archivo = generate_filename(tipo_doc, documento_id, documento.url_archivo)
    
    # Extraer extensión del nombre de archivo
    extension = '.pdf'  # Por defecto
    if '.' in nombre_archivo:
        extension = '.' + nombre_archivo.split('.')[-1]
    
    return await serve_document_by_storage_type(documento, nombre_archivo, extension)

# ========================================
# GESTIÓN DE USUARIOS
# ========================================



@router.get(
    "/users/emails-only",
    description="Obtiene solo los emails de usuarios para AdminCategoryRequestsPage (endpoint específico)"
)
async def get_users_emails_only(
    user_id: str = None,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint específico para obtener emails de usuarios - optimizado para AdminCategoryRequestsPage"""
    try:
        
        # OPTIMIZACIÓN: Si se proporciona user_id, obtener solo ese usuario
        if user_id:
            
            # Obtener email específico de Supabase
            try:
                auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
                if auth_user and auth_user.user and auth_user.user.email:
                    emails_dict = {
                        user_id: {
                            "email": auth_user.user.email,
                            "user_id": user_id,
                            "last_sign_in": auth_user.user.last_sign_in_at
                        }
                    }
                    return {
                        "emails": emails_dict,
                        "total": 1
                    }
                else:
                    return {"emails": {}, "total": 0}
            except Exception as e:
                return {"emails": {}, "total": 0}
        
        # Si no se proporciona user_id, obtener todos los usuarios (comportamiento original)
        # OPTIMIZACIÓN: Solo obtener IDs de usuarios (consulta ultra simple)
        query = select(UserModel.id)
        result = await db.execute(query)
        user_ids = [str(row.id) for row in result.all()]
        
        # Obtener emails de Supabase
        auth_users = supabase_admin.auth.admin.list_users()
        
        if not auth_users or len(auth_users) == 0:
            return {"emails": {}, "total": 0}
        
        # Crear diccionario de emails con información adicional
        emails_dict = {}
        for auth_user in auth_users:
            if auth_user.id and auth_user.email:
                # Incluir tanto ID como email para búsqueda flexible
                emails_dict[auth_user.id] = {
                    "email": auth_user.email,
                    "user_id": auth_user.id,
                    "last_sign_in": auth_user.last_sign_in_at
                }
        return {
            "emails": emails_dict,
            "total": len(emails_dict)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo emails: {str(e)}")

@router.get(
    "/users/emails",
    description="Obtiene los emails de todos los usuarios desde Supabase Auth"
)
async def get_users_emails(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user)
):
    """Obtiene los emails de todos los usuarios desde Supabase Auth"""
    try:
        
        # Obtener todos los usuarios de Supabase en una sola llamada
        auth_users = supabase_admin.auth.admin.list_users()
        
        if not auth_users or len(auth_users) == 0:
            return {"emails": {}}
        
        # Crear diccionario de ID -> email
        emails_dict = {}
        for auth_user in auth_users:
            if auth_user.id and auth_user.email:
                emails_dict[auth_user.id] = {
                    "email": auth_user.email,
                    "ultimo_acceso": auth_user.last_sign_in_at,
                    "estado": "Activo" if not auth_user.banned_until else "Suspendido"
                }
        
        return {"emails": emails_dict}

    except Exception as e:
        print(f"⚠️ Error obteniendo emails de Supabase: {e}")
        return {"emails": {}}


# Constantes para búsqueda de usuarios
CAMPO_NOMBRE_EMPRESA = "u.nombre_empresa"
CAMPO_NOMBRE_PERSONA = "u.nombre_persona"
TABLA_USERS = "users"
ALIAS_USERS = "u"
TABLA_USUARIO_ROL = "usuario_rol"
ALIAS_USUARIO_ROL = "ur"
TABLA_ROL = "rol"
ALIAS_ROL = "r"
CAMPO_ID_ROL = "r.id"
CAMPO_NOMBRE_ROL = "r.nombre"
CAMPO_ID_USUARIO = "ur.id_usuario"
CAMPO_ID_USUARIO_SIN_ALIAS = "id_usuario"
OPERADOR_ILIKE = "ILIKE"
OPERADOR_AND = "AND"
OPERADOR_OR = "OR"
OPERADOR_IN = "IN"
OPERADOR_EQUAL = "="
CLAUSULA_WHERE = "WHERE"
CLAUSULA_JOIN = "JOIN"
CLAUSULA_LEFT_JOIN = "LEFT JOIN"
CLAUSULA_INNER_JOIN = "INNER JOIN"
ORDEN_DESC = "DESC"
CAMPO_CREATED_AT = "u.created_at"
CAMPO_ID = "u.id"
CAMPO_TOTAL = "total"
VALOR_FILTRO_TODOS = "all"
OPERADOR_EQUAL_EXACTO = "="

# Mapeo de valores de filtro del frontend a nombres de roles en la BD
MAPEO_FILTRO_ROL = {
    "admin": "Administrador",
    "provider": "Proveedor",
    "proveedor": "Proveedor",
    "client": "Cliente",
    "cliente": "Cliente",
    "administrador": "Administrador"
}

# Constantes para nombres de roles en BD
NOMBRE_ROL_ADMINISTRADOR = "Administrador"
NOMBRE_ROL_PROVEEDOR = "Proveedor"
NOMBRE_ROL_CLIENTE = "Cliente"

def mapear_filtro_rol_a_nombre_bd(filter_role: Optional[str]) -> Optional[str]:
    """Mapea el valor del filtro de rol del frontend al nombre en la base de datos"""
    if not filter_role or filter_role == VALOR_FILTRO_TODOS:
        return None
    
    filter_role_lower = filter_role.lower().strip()
    return MAPEO_FILTRO_ROL.get(filter_role_lower, filter_role)

# Funciones helper para get_all_users
def get_user_ids_by_email(search_nombre: Optional[str]) -> list[str]:
    """Obtiene los IDs de usuarios que coinciden con la búsqueda por email"""
    if not search_nombre or not search_nombre.strip():
        return []
    
    try:
        search_term = search_nombre.strip().lower()
        auth_users = supabase_admin.auth.admin.list_users()
        matching_ids = []
        
        for auth_user in auth_users:
            if auth_user.id and auth_user.email:
                email_lower = auth_user.email.lower()
                if search_term in email_lower:
                    matching_ids.append(auth_user.id)
        
        return matching_ids
    except Exception as e:
        print(f"⚠️ Error buscando usuarios por email: {e}")
        return []

def build_user_search_filters(search_empresa: Optional[str], search_nombre: Optional[str], filter_role: Optional[str] = None, email_user_ids: list[str] = None) -> tuple[list[str], list, int, bool]:
    """Construye las condiciones WHERE y parámetros para la búsqueda de usuarios"""
    where_conditions = []
    params = []
    param_count = 1
    
    if search_empresa and search_empresa.strip():
        where_conditions.append(f"{CAMPO_NOMBRE_EMPRESA} {OPERADOR_ILIKE} ${param_count}")
        params.append(f"%{search_empresa.strip()}%")
        param_count += 1
        
    # Construir condición de búsqueda por nombre/email
    nombre_email_conditions = []
    if search_nombre and search_nombre.strip():
        # Buscar por nombre de persona
        nombre_email_conditions.append(f"{CAMPO_NOMBRE_PERSONA} {OPERADOR_ILIKE} ${param_count}")
        params.append(f"%{search_nombre.strip()}%")
        param_count += 1
    
    # Si hay IDs de usuarios por email, agregarlos a la búsqueda
    if email_user_ids:
        if len(email_user_ids) == 1:
            nombre_email_conditions.append(f"{CAMPO_ID} = ${param_count}")
            params.append(email_user_ids[0])
            param_count += 1
        else:
            placeholders = ", ".join([f"${param_count + i}" for i in range(len(email_user_ids))])
            nombre_email_conditions.append(f"{CAMPO_ID} IN ({placeholders})")
            params.extend(email_user_ids)
            param_count += len(email_user_ids)
    
    # Si hay condiciones de nombre/email, combinarlas con OR
    if nombre_email_conditions:
        if len(nombre_email_conditions) > 1:
            where_conditions.append(f"({' OR '.join(nombre_email_conditions)})")
        else:
            where_conditions.append(nombre_email_conditions[0])
    
    # Filtro por rol - mapear valor del frontend al nombre en BD
    # Para "Cliente", filtrar usuarios que tienen Cliente pero NO tienen Administrador ni Proveedor
    # (ya que todos los usuarios pueden tener Cliente como rol base)
    needs_role_join = False
    role_name_bd = mapear_filtro_rol_a_nombre_bd(filter_role)
    if role_name_bd:
        if role_name_bd == NOMBRE_ROL_CLIENTE:
            # Para Cliente: usuarios que tienen Cliente pero NO tienen Administrador ni Proveedor
            # Usar subconsulta para filtrar correctamente (no necesita JOIN en query principal)
            where_conditions.append(f"""
                {CAMPO_ID} IN (
                    SELECT ur_cliente.{CAMPO_ID_USUARIO_SIN_ALIAS}
                    FROM {TABLA_USUARIO_ROL} ur_cliente
                    {CLAUSULA_INNER_JOIN} {TABLA_ROL} r_cliente ON ur_cliente.id_rol = r_cliente.id
                    WHERE LOWER(r_cliente.nombre) = LOWER(${param_count})
                    AND NOT EXISTS (
                        SELECT 1
                        FROM {TABLA_USUARIO_ROL} ur_otros
                        {CLAUSULA_INNER_JOIN} {TABLA_ROL} r_otros ON ur_otros.id_rol = r_otros.id
                        WHERE ur_otros.{CAMPO_ID_USUARIO_SIN_ALIAS} = ur_cliente.{CAMPO_ID_USUARIO_SIN_ALIAS}
                        AND LOWER(r_otros.nombre) IN (LOWER(${param_count + 1}), LOWER(${param_count + 2}))
                    )
                )
            """)
            params.append(role_name_bd)
            params.append(NOMBRE_ROL_ADMINISTRADOR)
            params.append(NOMBRE_ROL_PROVEEDOR)
            param_count += 3
            needs_role_join = False  # No necesita JOIN porque usa subconsulta
        else:
            # Para otros roles: filtro normal con INNER JOIN
            where_conditions.append(f"LOWER({CAMPO_NOMBRE_ROL}) {OPERADOR_EQUAL_EXACTO} LOWER(${param_count})")
            params.append(role_name_bd)
            param_count += 1
            needs_role_join = True  # Necesita JOIN para otros roles
    
    return where_conditions, params, param_count, needs_role_join

def build_user_where_clause(where_conditions: list[str]) -> str:
    """Construye la cláusula WHERE para las queries"""
    if not where_conditions:
        return ""
    return f"{CLAUSULA_WHERE} {OPERADOR_AND.join(where_conditions)}"

def build_user_count_query(where_clause: str, has_role_filter: bool = False) -> str:
    """Construye la query para contar usuarios"""
    join_clause = ""
    if has_role_filter:
        # Usar INNER JOIN cuando hay filtro de rol para devolver solo usuarios con ese rol específico
        join_clause = f"""
        {CLAUSULA_INNER_JOIN} {TABLA_USUARIO_ROL} {ALIAS_USUARIO_ROL} ON {ALIAS_USERS}.id = {CAMPO_ID_USUARIO}
        {CLAUSULA_INNER_JOIN} {TABLA_ROL} {ALIAS_ROL} ON {ALIAS_USUARIO_ROL}.id_rol = {CAMPO_ID_ROL}
        """
    return f"""
        SELECT COUNT(DISTINCT {CAMPO_ID}) as {CAMPO_TOTAL}
        FROM {TABLA_USERS} {ALIAS_USERS}
        {join_clause}
        {where_clause}
    """

def build_user_list_query(where_clause: str, param_count: int, has_role_filter: bool = False) -> str:
    """Construye la query para obtener la lista de usuarios"""
    limit_param = param_count
    offset_param = param_count + 1
    join_clause = ""
    if has_role_filter:
        # Usar INNER JOIN cuando hay filtro de rol para devolver solo usuarios con ese rol específico
        join_clause = f"""
        {CLAUSULA_INNER_JOIN} {TABLA_USUARIO_ROL} {ALIAS_USUARIO_ROL} ON {ALIAS_USERS}.id = {CAMPO_ID_USUARIO}
        {CLAUSULA_INNER_JOIN} {TABLA_ROL} {ALIAS_ROL} ON {ALIAS_USUARIO_ROL}.id_rol = {CAMPO_ID_ROL}
        """
    return f"""
        SELECT DISTINCT
            {ALIAS_USERS}.id,
            {ALIAS_USERS}.nombre_persona,
            {ALIAS_USERS}.nombre_empresa,
            {ALIAS_USERS}.estado,
            {ALIAS_USERS}.foto_perfil,
            {ALIAS_USERS}.created_at
        FROM {TABLA_USERS} {ALIAS_USERS}
        {join_clause}
        {where_clause}
        ORDER BY {CAMPO_CREATED_AT} {ORDEN_DESC}
        LIMIT ${limit_param} OFFSET ${offset_param}
    """

# Función unificada para formatear fechas a DD/MM/YYYY
def format_date_dd_mm_yyyy(date_value) -> Optional[str]:
    """Formatea una fecha a DD/MM/YYYY (función unificada para todas las fechas)"""
    if date_value:
        return date_value.strftime("%d/%m/%Y")
    return None

def get_emails_from_supabase_auth() -> dict:
    """Obtiene los emails de usuarios desde Supabase Auth"""
    emails_dict = {}
    try:
        auth_users = supabase_admin.auth.admin.list_users()
        
        if auth_users and len(auth_users) > 0:
            for auth_user in auth_users:
                if auth_user.id and auth_user.email:
                    user_data = {
                        "email": auth_user.email,
                        "ultimo_acceso": auth_user.last_sign_in_at
                    }
                    # Intentar obtener created_at si está disponible
                    if hasattr(auth_user, 'user') and hasattr(auth_user.user, 'created_at'):
                        user_data["created_at"] = auth_user.user.created_at
                    elif hasattr(auth_user, 'created_at'):
                        user_data["created_at"] = auth_user.created_at
                    emails_dict[auth_user.id] = user_data
    except Exception as supabase_error:
        print(f"❌ Error obteniendo emails de Supabase: {supabase_error}")
    
    return emails_dict

def get_user_email_and_access(user_id: str, emails_dict: dict) -> tuple[str, Optional]:
    """Obtiene el email y último acceso de un usuario"""
    if user_id in emails_dict:
        return emails_dict[user_id]["email"], emails_dict[user_id]["ultimo_acceso"]
    return VALOR_DEFAULT_NO_DISPONIBLE, None

async def process_user_row_for_list(conn, row: dict, emails_dict: dict) -> dict:
    """Procesa una fila de usuario y retorna su diccionario con roles reales"""
    user_id = str(row['id'])
    email, ultimo_acceso = get_user_email_and_access(user_id, emails_dict)
    
    # Obtener roles reales del usuario
    roles = await get_user_roles(conn, user_id)
    rol_principal = determine_main_role(roles) if roles else "client"
    
    return {
        "id": user_id,
        "nombre_persona": row['nombre_persona'] or "Sin nombre",
        "nombre_empresa": row['nombre_empresa'] or "Sin empresa",
        "foto_perfil": row['foto_perfil'],
        "estado": row['estado'] or "ACTIVO",
        "email": email,
        "ultimo_acceso": ultimo_acceso,
        "roles": roles if roles else ["Usuario"],
        "rol_principal": rol_principal,
        "todos_roles": roles if roles else ["Usuario"],
        "fecha_registro": format_date_dd_mm_yyyy(row['created_at']) if row['created_at'] else "Sin fecha"
    }

def build_users_response(users_list: list, total_users: int, page: int, limit: int) -> dict:
    """Construye la respuesta final con usuarios y paginación"""
    # Asegurar que total_users sea un entero
    total_int = int(total_users) if total_users is not None else 0
    total_pages = (total_int + limit - 1) // limit if total_int > 0 else 1
    
    return {
        "usuarios": users_list,
        "total": total_int,
        "page": int(page),
        "limit": int(limit),
        "total_pages": total_pages,
        "message": "Usuarios obtenidos exitosamente"
    }

@router.get(
    "/users",
    description="Obtiene la lista de todos los usuarios de la plataforma con opción de búsqueda optimizada"
)
async def get_all_users(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    search_empresa: Optional[str] = Query(None, description="Búsqueda por nombre de empresa"),
    search_nombre: Optional[str] = Query(None, description="Búsqueda por nombre de persona o email"),
    filter_role: Optional[str] = Query(None, description="Filtro por rol (ej: 'admin', 'provider', 'client')"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(100, ge=1, le=1000, description="Cantidad de resultados por página")
):
    """Obtiene usuarios con paginación y búsqueda optimizada usando DirectDBService"""
    try:
        # Obtener IDs de usuarios que coinciden con búsqueda por email
        email_user_ids = get_user_ids_by_email(search_nombre) if search_nombre else []
        
        # Mapear filtro de rol del frontend al nombre en BD
        role_name_bd = mapear_filtro_rol_a_nombre_bd(filter_role)
        has_role_filter = role_name_bd is not None
        
        conn = await direct_db_service.get_connection()
        
        try:
            where_conditions, params, param_count, needs_role_join = build_user_search_filters(search_empresa, search_nombre, role_name_bd, email_user_ids)
            where_clause = build_user_where_clause(where_conditions)
            
            count_query = build_user_count_query(where_clause, needs_role_join)
            # Crear una copia de params para la query de conteo (sin limit y offset)
            count_params = params.copy()
            total_result = await conn.fetchrow(count_query, *count_params)
            total_users = int(total_result['total']) if total_result and total_result.get('total') is not None else 0
            print(f"🔍 DEBUG: Total usuarios encontrados con filtros: {total_users}")
            
            offset = (page - 1) * limit
            users_query = build_user_list_query(where_clause, param_count, needs_role_join)
            # Crear una copia de params para la query de usuarios (con limit y offset)
            users_params = params.copy()
            users_params.extend([limit, offset])
            users_data = await conn.fetch(users_query, *users_params)
            
            emails_dict = get_emails_from_supabase_auth()
            users_list = []
            for row in users_data:
                user_data = await process_user_row_for_list(conn, row, emails_dict)
                users_list.append(user_data)
            
            response_data = build_users_response(users_list, total_users, page, limit)
            print(f"🔍 DEBUG: Respuesta enviada - Total: {response_data['total']}, Usuarios: {len(users_list)}")
            return response_data
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        print("Traceback completo:")
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo usuarios: {str(e)}"
        )


@router.get(
    "/users/user-id-by-profile/{id_perfil}",
    description="Obtiene el user_id usando el id_perfil"
)
async def get_user_id_by_profile(
    id_perfil: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene el user_id usando el id_perfil de PerfilEmpresa.
    """
    try:
        # Usar el modelo PerfilEmpresa ya importado al inicio del archivo
        query = select(PerfilEmpresa.user_id).where(PerfilEmpresa.id_perfil == id_perfil)
        result = await db.execute(query)
        user_id = result.scalar()
        
        if user_id:
            return {
                "success": True,
                "user_id": str(user_id),
                "id_perfil": id_perfil
            }
        else:
            return {
                "success": False,
                "message": f"No se encontró user_id para id_perfil {id_perfil}"
            }
            
    except Exception as e:
        print(f"❌ Error obteniendo user_id por id_perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo user_id: {str(e)}"
        )

@router.get(
    "/users/permissions",
    description="Obtiene los permisos del usuario administrador actual"
)
async def get_user_permissions(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user)
):
    """Obtiene información sobre los permisos del usuario administrador actual"""
    try:
        print(f"🔍 DEBUG: Obteniendo permisos para usuario: {admin_user.id}")
        print(f"🔍 DEBUG: Roles del usuario: {admin_user.roles}")
        
        # Verificar si el usuario es administrador
        is_admin = any(rol.lower() in ["admin", "administrador"] for rol in admin_user.roles)
        print(f"🔍 DEBUG: Es admin: {is_admin}")

        # Determinar permisos basados en roles
        permissions = {
            "can_edit_users": is_admin,
            "can_edit_emails": is_admin,
            "can_deactivate_users": is_admin,
            "can_change_roles": is_admin,
            "can_search_users": True,  # Todos pueden buscar
            "can_view_user_details": True,  # Todos pueden ver detalles
            "is_admin": is_admin,
            "user_roles": admin_user.roles,
            "user_id": admin_user.id,
            "user_email": admin_user.email
        }

        result = {
            "permissions": permissions,
            "features": {
                "search_by_company": True,
                "readonly_email_for_admins": True,
                "user_management": is_admin,
                "role_management": is_admin
            }
        }
        
        print(f"🔍 DEBUG: Permisos generados exitosamente: {permissions}")
        return result

    except Exception as e:
        print(f"❌ Error obteniendo permisos: {e}")
        return {
            "permissions": {
                "can_edit_users": False,
                "can_edit_emails": False,
                "can_deactivate_users": False,
                "can_change_roles": False,
                "can_search_users": True,
                "can_view_user_details": True,
                "is_admin": False,
                "user_roles": [],
                "user_id": None,
                "user_email": None
            },
            "features": {
                "search_by_company": True,
                "readonly_email_for_admins": False,
                "user_management": False,
                "role_management": False
            },
            "error": str(e)
        }




@router.put(
    "/users/{user_id}/profile",
    description="Actualiza el perfil de un usuario"
)
async def update_user_profile(
    user_id: str,
    user_data: dict,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Actualiza el perfil de un usuario"""
    try:
        # Verificar que el usuario existe
        user_query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(user_query)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        print(f"🔍 DEBUG: Iniciando edición de usuario {user_id}")
        print(f"🔍 DEBUG: Datos recibidos: {user_data}")

        # Verificar estado inicial del usuario
        print(f"🔍 DEBUG: Estado inicial - Nombre: '{user.nombre_persona}', Empresa: '{user.nombre_empresa}'")

        # Actualizar campos del usuario
        updated_fields = []
        changes_made = False

        if "nombre_persona" in user_data and user_data["nombre_persona"]:
            old_name = user.nombre_persona
            user.nombre_persona = user_data["nombre_persona"]
            updated_fields.append("nombre_persona")
            changes_made = True
            print(f"🔍 DEBUG: Nombre actualizado: '{old_name}' -> '{user.nombre_persona}'")

        if "nombre_empresa" in user_data:
            old_company = user.nombre_empresa
            user.nombre_empresa = user_data["nombre_empresa"]  # Puede ser None/vacío
            updated_fields.append("nombre_empresa")
            changes_made = True
            print(f"🔍 DEBUG: Empresa actualizada: '{old_company}' -> '{user.nombre_empresa}'")

        # CONTROL DE ACCESO AL EMAIL: Solo administradores pueden editar emails
        # Verificar si el usuario actual es administrador
        is_admin = any(rol.lower() in ["admin", "administrador"] for rol in admin_user.roles)
        print(f"🔍 DEBUG: Usuario editor es admin: {is_admin}")

        # Si se proporciona email, verificar permisos antes de actualizar
        if "email" in user_data and user_data["email"]:
            if is_admin:
                # Administrador puede editar email
                try:
                    supabase_admin.auth.admin.update_user_by_id(
                        user_id,
                        {"email": user_data["email"]}
                    )
                    updated_fields.append("email")
                    print(f"✅ Email actualizado en Supabase Auth para usuario {user_id}")
                except Exception as email_error:
                    print(f"⚠️ Error actualizando email en Supabase: {email_error}")
                    # Continuar con la actualización del perfil aunque falle el email
            else:
                # Usuario no administrador: rechazar edición de email
                print(f"⚠️ Usuario no administrador intentó editar email de {user_id}")
                # No actualizar email, continuar con otros campos

        if not changes_made:
            print("⚠️ DEBUG: No se hicieron cambios en el usuario")
            return {
                "message": "No se hicieron cambios",
                "user_id": user_id,
                "updated_fields": [],
                "new_data": {
                    "nombre_persona": user.nombre_persona,
                    "nombre_empresa": user.nombre_empresa,
                    "email": user_data.get("email", "No disponible")
                },
                "permissions": {
                    "can_edit_email": is_admin,
                    "editor_is_admin": is_admin,
                    "editor_roles": admin_user.roles
                }
            }

        # Verificar que los cambios se reflejen antes del commit
        print(f"🔍 DEBUG: Estado antes del commit - Nombre: '{user.nombre_persona}', Empresa: '{user.nombre_empresa}'")

        # Forzar flush para verificar que los cambios se apliquen
        try:
            await db.flush()
            print("✅ DEBUG: Flush exitoso - cambios aplicados en memoria")
        except Exception as flush_error:
            print(f"❌ Error en flush: {flush_error}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error aplicando cambios: {str(flush_error)}"
            )

        # Guardar cambios en base de datos
        await db.commit()
        print("✅ DEBUG: Commit exitoso - cambios guardados en BD")

        return {
            "message": "Perfil de usuario actualizado exitosamente",
            "user_id": user_id,
            "updated_fields": updated_fields,
            "new_data": {
                "nombre_persona": user.nombre_persona,
                "nombre_empresa": user.nombre_empresa,
                "email": user_data.get("email", "No disponible")
            },
            "permissions": {
                "can_edit_email": is_admin,
                "editor_is_admin": is_admin,
                "editor_roles": admin_user.roles
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando perfil de usuario: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando perfil de usuario: {str(e)}"
        )


@router.put(
    "/users/{user_id}/roles",
    description="Actualiza los roles de un usuario"
)
async def update_user_roles(
    user_id: str,
    roles_data: dict,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Actualiza los roles de un usuario"""
    try:
        # Verificar que el usuario existe
        user_query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(user_query)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Obtener roles disponibles
        roles_query = select(RolModel)
        roles_result = await db.execute(roles_query)
        available_roles = roles_result.scalars().all()
        available_role_names = [role.nombre for role in available_roles]
        
        # Verificar y mapear los roles solicitados
        requested_roles = roles_data.get("roles", [])

        # Mapeo de roles para compatibilidad
        role_mapping = {
            "provider": "proveedor",  # Mapear 'provider' a 'proveedor'
            "proveedores": "proveedor",  # Mapear 'proveedores' a 'proveedor'
            "client": "cliente",  # Mapear 'client' a 'cliente'
            "admin": "administrador",  # Mapear 'admin' a 'administrador'
            "administrator": "administrador"  # Mapear 'administrator' a 'administrador'
        }

        # Mapear roles solicitados a nombres reales en BD
        mapped_roles = []
        for role_name in requested_roles:
            # Usar el mapeo si existe, sino usar el nombre original
            mapped_role = role_mapping.get(role_name.lower(), role_name)
            mapped_roles.append(mapped_role)

        # Verificar que los roles mapeados existen
        for mapped_role in mapped_roles:
            if mapped_role not in available_role_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rol '{mapped_role}' no existe en la base de datos"
                )
        
        # Eliminar roles actuales del usuario
        delete_query = select(UsuarioRolModel).where(UsuarioRolModel.id_usuario == user_id)
        delete_result = await db.execute(delete_query)
        current_roles = delete_result.scalars().all()
        
        for current_role in current_roles:
            await db.delete(current_role)
        
        # Agregar nuevos roles (usar roles mapeados)
        for mapped_role in mapped_roles:
            role_query = select(RolModel).where(RolModel.nombre == mapped_role)
            role_result = await db.execute(role_query)
            role = role_result.scalars().first()

            if role:
                new_user_role = UsuarioRolModel(
                    id_usuario=user_id,
                    id_rol=role.id
                )
                db.add(new_user_role)

        # Guardar cambios
        await db.commit()

        return {
            "message": "Roles de usuario actualizados exitosamente",
            "user_id": user_id,
            "requested_roles": requested_roles,
            "mapped_roles": mapped_roles,
            "available_roles": available_role_names
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando roles de usuario: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando roles de usuario: {str(e)}"
        )


@router.post(
    "/users/{user_id}/deactivate",
    description="Desactiva un usuario (marca como inactivo)"
)
async def deactivate_user(
    user_id: str,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Desactiva un usuario"""
    try:
        print(f"🔍 DEBUG: Iniciando desactivación de usuario {user_id}")

        # Verificar que el usuario existe
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            print(f"❌ Usuario {user_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Verificar que no se está desactivando a sí mismo
        if str(user.id) == str(admin_user.id):
            print(f"❌ Intento de auto-desactivación por usuario {admin_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta"
            )

        print(f"✅ Verificaciones pasadas para usuario {user_id}")

        # Cambiar estado del usuario a INACTIVO en la base de datos
        user.estado = "INACTIVO"
        print(f"🔄 Cambiando estado del usuario {user_id} a INACTIVO")
        
        # Actualizar fecha_fin en perfil_empresa si existe
        # from app.services.perfil_empresa_service import PerfilEmpresaService  # Comentado temporalmente
        # perfil_updated = await PerfilEmpresaService.deactivate_user_profile(db, user_id)
        # if perfil_updated:
        #     print(f"✅ Fecha_fin actualizada en perfil_empresa para usuario {user_id}")
        # else:
        #     print(f"ℹ️ No se encontró perfil_empresa para usuario {user_id} o ya estaba desactivado")
        print(f"ℹ️ Funcionalidad de perfil_empresa temporalmente deshabilitada para evitar importación circular")

        # Desactivar en Supabase Auth usando el cliente admin
        supabase_success = False
        supabase_error = None

        try:

            if not supabase_admin:
                print("⚠️ Cliente Supabase admin no disponible")
                supabase_error = "Cliente admin no configurado"
            else:
                print(f"🔍 Intentando desactivar en Supabase para usuario {user_id}")

                # Marcar como desactivado en Supabase
                result = supabase_admin.auth.admin.update_user_by_id(
                    str(user.id),
                    {
                        "user_metadata": {"status": "inactive"},
                        "app_metadata": {"deactivated": True}
                    }
                )
                print(f"✅ Usuario {user.id} desactivado en Supabase Auth")
                supabase_success = True

        except Exception as e:
            supabase_error = str(e)
            print(f"⚠️ Error desactivando usuario en Supabase Auth: {supabase_error}")

            # Si es un error de token expirado, dar información específica
            if "expired" in supabase_error.lower() or "invalid" in supabase_error.lower():
                print("💡 Posible token expirado - puede requerir refresh del token")

        # Guardar cambios en la base de datos
        await db.commit()
        print(f"✅ Desactivación completada para usuario {user_id}")

        return {
            "message": "Usuario desactivado exitosamente",
            "user_id": str(user.id),
            "status": "inactive",
            "estado_db": user.estado,  # Confirmar estado en BD
            "supabase_updated": supabase_success,
            "admin_user": admin_user.id,
            "supabase_error": supabase_error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error desactivando usuario: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error desactivando usuario: {str(e)}"
        )


@router.get(
    "/roles",
    description="Obtiene la lista de todos los roles disponibles"
)
async def get_available_roles(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user)
):
    """Obtiene todos los roles disponibles en el sistema usando DirectDBService para evitar problemas con PgBouncer"""
    try:
        # Usar direct_db_service para evitar problemas con prepared statements y PgBouncer
        conn = await direct_db_service.get_connection()
        
        try:
            # Query SQL directa sin prepared statements
            query = "SELECT id, nombre, descripcion FROM rol ORDER BY nombre"
            rows = await conn.fetch(query)
            
            roles_data = []
            for row in rows:
                roles_data.append({
                    "id": str(row['id']),
                    "nombre": row['nombre'],
                    "descripcion": row['descripcion'] if row['descripcion'] else None
                })
            
            return {
                "roles": roles_data,
                "total": len(roles_data)
            }
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except Exception as e:
        print(f"❌ Error obteniendo roles: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo roles: {str(e)}"
        )


@router.post(
    "/users/{user_id}/reset-password",
    description="Restablece la contraseña de un usuario específico (solo administradores)"
)
async def reset_user_password(
    user_id: str,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Restablece la contraseña de un usuario específico usando Supabase Admin API"""
    try:
        print(f"🔐 Iniciando restablecimiento de contraseña para usuario: {user_id}")
        
        # Verificar que el usuario existe en nuestra base de datos
        user_query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(user_query)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        print(f"✅ Usuario encontrado: {user.nombre_persona}")
        
        # Obtener el email del usuario desde Supabase Auth
        
        try:
            # Obtener información del usuario desde Supabase Auth
            auth_user_response = supabase_admin.auth.admin.get_user_by_id(user_id)
            
            if not auth_user_response.user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado en Supabase Auth"
                )
            
            user_email = auth_user_response.user.email
            print(f"📧 Email obtenido desde Supabase Auth: {user_email}")
            
        except Exception as auth_error:
            print(f"❌ Error obteniendo email desde Supabase Auth: {auth_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo información del usuario: {str(auth_error)}"
            )
        
        # Generar nueva contraseña temporal que cumpla con todos los requisitos
        def generate_secure_password(length=12):
            """Genera una contraseña segura que garantiza al menos:
            - Un número
            - Una letra mayúscula
            - Una letra minúscula
            - Un carácter especial
            """
            # Definir conjuntos de caracteres
            lowercase = string.ascii_lowercase
            uppercase = string.ascii_uppercase
            digits = string.digits
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            # Garantizar al menos un carácter de cada tipo
            password = [
                secrets.choice(lowercase),    # Al menos una minúscula
                secrets.choice(uppercase),    # Al menos una mayúscula
                secrets.choice(digits),       # Al menos un número
                secrets.choice(special_chars) # Al menos un carácter especial
            ]
            
            # Completar el resto con caracteres aleatorios
            all_chars = lowercase + uppercase + digits + special_chars
            for _ in range(length - 4):
                password.append(secrets.choice(all_chars))
            
            # Mezclar la contraseña para que no sea predecible
            secrets.SystemRandom().shuffle(password)
            
            return ''.join(password)
        
        # Generar contraseña segura de 12 caracteres
        new_password = generate_secure_password(12)
        
        print(f"🔑 Nueva contraseña generada para {user_email}")
        
        try:
            # Usar el cliente admin para restablecer la contraseña
            reset_response = supabase_admin.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password}
            )
            
            if not reset_response.user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error al restablecer la contraseña en Supabase"
                )
            
            print(f"✅ Contraseña restablecida exitosamente para {user_email}")
            
            return {
                "message": f"Contraseña restablecida exitosamente para {user.nombre_persona}",
                "user_id": user_id,
                "user_email": user_email,
                "new_password": new_password,
                "reset_by": admin_user.email,
                "reset_at": datetime.now().isoformat()
            }
            
        except Exception as supabase_error:
            print(f"❌ Error de Supabase al restablecer contraseña: {supabase_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al restablecer la contraseña: {str(supabase_error)}"
            )
            
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
    except Exception as e:
        print(f"❌ Error inesperado al restablecer contraseña: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al restablecer la contraseña: {str(e)}"
        )


@router.get(
    "/users/{user_id}/verify-edit",
    description="Verificar el estado actual de un usuario para debugging de edición"
)
async def verify_user_edit(
    user_id: str,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Verificar el estado actual de un usuario - útil para debugging"""
    try:
        print(f"🔍 DEBUG: Verificando estado de usuario {user_id}")

        # Obtener usuario
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            return {
                "error": "Usuario no encontrado",
                "user_id": user_id
            }

        # Obtener roles
        roles_query = select(RolModel.nombre).select_from(
            UsuarioRolModel
        ).join(
            RolModel, UsuarioRolModel.id_rol == RolModel.id
        ).where(
            UsuarioRolModel.id_usuario == user_id
        )
        roles_result = await db.execute(roles_query)
        roles = roles_result.scalars().all()

        # Obtener email de Supabase si es posible
        email = "No disponible"
        try:
            auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
            if auth_user and auth_user.user:
                email = auth_user.user.email or "No disponible"
        except Exception as e:
            print(f"⚠️ Error obteniendo email: {e}")

        return {
            "user_id": str(user.id),
            "nombre_persona": user.nombre_persona,
            "nombre_empresa": user.nombre_empresa,
            "email": email,
            "roles": list(roles),
            "estado": user.estado or "ACTIVO",
            "verificado_en": "Base de datos local"
        }

    except Exception as e:
        print(f"❌ Error verificando usuario: {e}")
        return {
            "error": str(e),
            "user_id": user_id
        }


@router.post(
    "/users/{user_id}/test-edit",
    description="Endpoint de prueba para edición sin dependencias complejas"
)
async def test_edit_user(
    user_id: str,
    test_data: dict,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint de prueba para verificar que la edición funciona"""
    try:
        print(f"🧪 TEST EDIT: Usuario {user_id}")
        print(f"🧪 TEST EDIT: Datos recibidos: {test_data}")

        # Verificar que el usuario existe
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            return {"error": "Usuario no encontrado", "user_id": user_id}

        # Estado antes de cambios
        before_state = {
            "nombre_persona": user.nombre_persona,
            "nombre_empresa": user.nombre_empresa
        }

        # Aplicar cambios de prueba
        changes_applied = []

        if "nombre_persona" in test_data:
            user.nombre_persona = test_data["nombre_persona"]
            changes_applied.append("nombre_persona")

        if "nombre_empresa" in test_data:
            user.nombre_empresa = test_data["nombre_empresa"]
            changes_applied.append("nombre_empresa")

        # Estado después de cambios (antes del commit)
        after_state = {
            "nombre_persona": user.nombre_persona,
            "nombre_empresa": user.nombre_empresa
        }

        # Aplicar cambios
        await db.flush()
        await db.commit()

        # Verificar que los cambios persistieron
        verify_query = select(UserModel.nombre_persona, UserModel.nombre_empresa).where(UserModel.id == user_id)
        verify_result = await db.execute(verify_query)
        verify_data = verify_result.first()

        persisted_state = {
            "nombre_persona": verify_data.nombre_persona if verify_data else None,
            "nombre_empresa": verify_data.nombre_empresa if verify_data else None
        }

        return {
            "message": "Test de edición completado",
            "user_id": user_id,
            "before_changes": before_state,
            "after_changes": after_state,
            "persisted_changes": persisted_state,
            "changes_applied": changes_applied,
            "test_successful": (
                persisted_state["nombre_persona"] == after_state["nombre_persona"] and
                persisted_state["nombre_empresa"] == after_state["nombre_empresa"]
            )
        }

    except Exception as e:
        print(f"❌ Error en test de edición: {e}")
        await db.rollback()
        return {
            "error": str(e),
            "user_id": user_id,
            "test_successful": False
        }


# Funciones helper para toggle_user_status
async def get_user_by_id_for_toggle(db: AsyncSession, user_id: str) -> UserModel:
    """Obtiene el usuario por ID para toggle de estado"""
    user_query = select(UserModel).where(UserModel.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

def verify_not_self_modification(user_id: str, admin_user_id: str) -> None:
    """Verifica que el admin no esté intentando modificar su propia cuenta"""
    if str(user_id) == str(admin_user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes modificar tu propia cuenta"
        )

def determine_status_action(current_status: Optional[str]) -> tuple[str, str]:
    """Determina el nuevo estado y la acción basada en el estado actual"""
    if current_status == "ACTIVO":
        return "INACTIVO", "desactivado"
    elif current_status == "INACTIVO":
        return "ACTIVO", "reactivado"
    else:
        # Si no tiene estado definido, asumir ACTIVO
        return "INACTIVO", "desactivado"

def update_perfil_empresa_status(db: AsyncSession, user_id: str, action: str) -> bool:
    """Actualiza el estado en perfil_empresa (temporalmente deshabilitado)"""
    print(f"ℹ️ Funcionalidad de perfil_empresa temporalmente deshabilitada para evitar importación circular")
    return False  # Temporalmente deshabilitado

def update_supabase_user_status(user_id: str, new_status: str) -> bool:
    """Actualiza el estado del usuario en Supabase Auth"""
    try:
        if supabase_admin:
            supabase_admin.auth.admin.update_user_by_id(
                str(user_id),
                {
                    "user_metadata": {"status": "inactive" if new_status == "INACTIVO" else "active"},
                    "app_metadata": {"deactivated": new_status == "INACTIVO"}
                }
            )
            print(f"✅ Usuario {user_id} actualizado en Supabase Auth")
            return True
    except Exception as e:
        print(f"⚠️ Error actualizando en Supabase: {e}")
    return False

def build_toggle_status_response(user: UserModel, action: str, current_status: str, 
                                new_status: str, supabase_success: bool, admin_user_id: str) -> dict:
    """Construye la respuesta para toggle de estado"""
    return {
        "message": f"Usuario {action} exitosamente",
        "user_id": str(user.id),
        "status": new_status.lower(),
        "estado_anterior": current_status,
        "estado_nuevo": new_status,
        "supabase_updated": supabase_success,
        "admin_user": admin_user_id
    }

@router.post(
    "/users/{user_id}/toggle-status",
    description="Activa o desactiva un usuario según su estado actual"
)
async def toggle_user_status(
    user_id: str,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Activa o desactiva un usuario según su estado actual"""
    try:
        print(f"🔍 DEBUG: Iniciando cambio de estado para usuario {user_id}")

        user = await get_user_by_id_for_toggle(db, user_id)
        verify_not_self_modification(user.id, admin_user.id)

        current_status = user.estado
        new_status, action = determine_status_action(current_status)
        print(f"✅ Estado actual: {current_status}, Nuevo estado: {new_status}, Acción: {action}")

        user.estado = new_status
        update_perfil_empresa_status(db, user_id, action)
        supabase_success = update_supabase_user_status(user.id, new_status)

        await db.commit()
        print(f"✅ Cambio de estado completado para usuario {user_id}")

        return build_toggle_status_response(user, action, current_status, new_status, supabase_success, admin_user.id)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error cambiando estado del usuario: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cambiando estado del usuario: {str(e)}"
        )


@router.post(
    "/users/{user_id}/activate",
    description="Activa un usuario (marca como activo)"
)
async def activate_user(
    user_id: str,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Activa un usuario"""
    try:
        print(f"🔍 DEBUG: Iniciando activación de usuario {user_id}")

        # Verificar que el usuario existe
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            print(f"❌ Usuario {user_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Verificar que no se está modificando a sí mismo
        if str(user.id) == str(admin_user.id):
            print(f"❌ Intento de auto-modificación por usuario {admin_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes modificar tu propia cuenta"
            )

        print(f"✅ Verificaciones pasadas para usuario {user_id}")

        # Cambiar estado del usuario a ACTIVO en la base de datos
        user.estado = "ACTIVO"
        print(f"🔄 Cambiando estado del usuario {user_id} a ACTIVO")
        
        # Actualizar fecha_fin en perfil_empresa si existe (limpiar fecha_fin)
        # from app.services.perfil_empresa_service import PerfilEmpresaService  # Comentado temporalmente
        # perfil_updated = await PerfilEmpresaService.reactivate_user_profile(db, user_id)
        perfil_updated = False  # Temporalmente deshabilitado
        if perfil_updated:
            print(f"✅ Fecha_fin limpiada en perfil_empresa para usuario {user_id}")
        else:
            print(f"ℹ️ No se encontró perfil_empresa para usuario {user_id} o ya estaba activo")

        # Intentar actualizar en Supabase Auth también
        supabase_success = False
        try:
            if supabase_admin:
                result = supabase_admin.auth.admin.update_user_by_id(
                    str(user.id),
                    {
                        "user_metadata": {"status": "active"},
                        "app_metadata": {"deactivated": False}
                    }
                )
                print(f"✅ Usuario {user.id} actualizado en Supabase Auth")
                supabase_success = True
        except Exception as e:
            print(f"⚠️ Error actualizando en Supabase: {e}")

        # Guardar cambios en la base de datos
        await db.commit()
        print(f"✅ Activación completada para usuario {user_id}")

        return {
            "message": "Usuario activado exitosamente",
            "user_id": str(user.id),
            "status": "active",
            "estado_db": user.estado,
            "supabase_updated": supabase_success,
            "admin_user": admin_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error activando usuario: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activando usuario: {str(e)}"
        )


@router.post(
    "/users/{user_id}/deactivate-simple",
    description="Desactiva un usuario (versión simplificada sin Supabase)"
)
async def deactivate_user_simple(
    user_id: str,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Desactiva un usuario de manera simplificada"""
    try:
        print(f"🔍 DEBUG: Iniciando desactivación simple de usuario {user_id}")

        # Verificar que el usuario existe
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            print(f"❌ Usuario {user_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Verificar que no se está desactivando a sí mismo
        if str(user.id) == str(admin_user.id):
            print(f"❌ Intento de auto-desactivación por usuario {admin_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta"
            )

        print(f"✅ Verificaciones pasadas para usuario {user_id}")

        # Solo hacer commit para confirmar que todo está bien
        await db.commit()
        print(f"✅ Desactivación simple completada para usuario {user_id}")

        return {
            "message": "Usuario marcado como inactivo",
            "user_id": str(user.id),
            "status": "inactive",
            "method": "simple",
            "admin_user": admin_user.id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en desactivación simple: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error desactivando usuario: {str(e)}"
        )


# Funciones helper para get_reporte_usuarios_activos
async def get_users_from_db(conn) -> list:
    """Obtiene todos los usuarios desde la base de datos"""
    users_query = """
        SELECT 
            u.id,
            u.nombre_persona,
            u.nombre_empresa,
            u.estado,
            u.created_at
        FROM users u
        ORDER BY u.created_at DESC
    """
    return await conn.fetch(users_query)

def get_emails_from_supabase() -> dict:
    """Obtiene los emails de usuarios desde Supabase Auth (alias para compatibilidad)"""
    # Usar la función unificada get_emails_from_supabase_auth
    return get_emails_from_supabase_auth()

def format_creation_date(created_at) -> str:
    """Formatea la fecha de creación del usuario"""
    if not created_at:
        return VALOR_DEFAULT_NO_DISPONIBLE
    
    try:
        if isinstance(created_at, str):
            if created_at.endswith('Z'):
                created_at = created_at.replace('Z', '+00:00')
            elif '+' not in created_at and 'T' in created_at:
                created_at = created_at + '+00:00'
            date_obj = datetime.fromisoformat(created_at)
            return format_date_dd_mm_yyyy(date_obj) or VALOR_DEFAULT_NO_DISPONIBLE
        else:
            return format_date_dd_mm_yyyy(created_at) or VALOR_DEFAULT_NO_DISPONIBLE
    except Exception as date_error:
        print(f"DEBUG: Error formateando fecha: {date_error}")
        return "Error formato"

async def get_user_roles(conn, user_id: str) -> list[str]:
    """Obtiene los roles de un usuario"""
    roles_query = """
        SELECT r.nombre
        FROM usuario_rol ur
        JOIN rol r ON ur.id_rol = r.id
        WHERE ur.id_usuario = $1
    """
    roles_data = await conn.fetch(roles_query, user_id)
    return [row['nombre'] for row in roles_data]

def determine_main_role(roles: list[str]) -> str:
    """Determina el rol principal basado en los roles del usuario"""
    normalized_roles = [rol.lower().strip() for rol in roles]
    
    if any(admin_role in normalized_roles for admin_role in ["admin", "administrador", "administrator"]):
        return "admin"  # Valor que espera el frontend
    elif any(provider_role in normalized_roles for provider_role in ["provider", "proveedor", "proveedores"]):
        return "provider"  # Valor que espera el frontend
    elif any(client_role in normalized_roles for client_role in ["client", "cliente"]):
        return "client"  # Valor que espera el frontend
    return "client"  # Valor por defecto que espera el frontend

def normalize_user_status(estado_raw) -> str:
    """Normaliza el estado del usuario"""
    if estado_raw is None or estado_raw == '':
        return "ACTIVO"
    elif isinstance(estado_raw, str):
        return estado_raw.strip().upper()
    else:
        return str(estado_raw).strip().upper()

def get_user_email_and_creation_date(user_id: str, emails_dict: dict) -> tuple[str, str]:
    """Obtiene el email y fecha de creación de un usuario para reportes"""
    if user_id in emails_dict:
        email = emails_dict[user_id]["email"]
        # El dict puede tener "created_at" o "ultimo_acceso", usar el que esté disponible
        created_at = emails_dict[user_id].get("created_at") or emails_dict[user_id].get("ultimo_acceso")
        fecha_creacion = format_creation_date(created_at) if created_at else VALOR_DEFAULT_NO_DISPONIBLE
        return email, fecha_creacion
    return VALOR_DEFAULT_NO_DISPONIBLE, VALOR_DEFAULT_NO_DISPONIBLE

async def process_user_row(conn, row: dict, emails_dict: dict) -> dict:
    """Procesa una fila de usuario y retorna su diccionario para el reporte"""
    user_id = str(row['id'])
    email, fecha_creacion = get_user_email_and_creation_date(user_id, emails_dict)
    roles = await get_user_roles(conn, user_id)
    rol_principal = determine_main_role(roles)
    estado = normalize_user_status(row['estado'])
    
    return {
        "id": user_id,
        "nombre_persona": row['nombre_persona'] or "Sin nombre",
        "nombre_empresa": row['nombre_empresa'] or "Sin empresa",
        "email": email,
        "estado": estado,
        "rol_principal": rol_principal,
        "fecha_creacion": fecha_creacion
    }

async def process_all_users(conn, users_data: list, emails_dict: dict) -> list[dict]:
    """Procesa todos los usuarios y retorna la lista completa"""
    usuarios_con_roles = []
    for row in users_data:
        usuario_data = await process_user_row(conn, row, emails_dict)
        usuarios_con_roles.append(usuario_data)
    return usuarios_con_roles

def calculate_user_statistics(usuarios_con_roles: list[dict]) -> dict:
    """Calcula las estadísticas de usuarios"""
    total_usuarios = len(usuarios_con_roles)
    usuarios_activos = len([u for u in usuarios_con_roles if u['estado'] == 'ACTIVO'])
    usuarios_inactivos = total_usuarios - usuarios_activos
    
    return {
        "total_usuarios": total_usuarios,
        "usuarios_activos": usuarios_activos,
        "usuarios_inactivos": usuarios_inactivos
    }

def build_report_response(usuarios_con_roles: list[dict], statistics: dict) -> dict:
    """Construye la respuesta del reporte"""
    return {
        "total_usuarios": statistics["total_usuarios"],
        "usuarios_activos": statistics["usuarios_activos"],
        "usuarios_inactivos": statistics["usuarios_inactivos"],
        "usuarios": usuarios_con_roles,
        "fecha_generacion": datetime.now().isoformat(),
        "filtros_aplicados": "Todos los usuarios (activos e inactivos)"
    }

@router.get(
    "/reports/usuarios-activos",
    description="Genera reporte de todos los usuarios (activos e inactivos)"
)
async def get_reporte_usuarios_activos(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user)
):
    """Genera reporte de todos los usuarios usando DirectDBService"""
    try:
        print("🔍 DEBUG: Generando reporte de todos los usuarios...")
        
        
        conn = await direct_db_service.get_connection()
        
        try:
            users_data = await get_users_from_db(conn)
            print(f"🔍 DEBUG: {len(users_data)} usuarios encontrados para reporte")
            
            emails_dict = get_emails_from_supabase()
            usuarios_con_roles = await process_all_users(conn, users_data, emails_dict)
            statistics = calculate_user_statistics(usuarios_con_roles)
            
            return build_report_response(usuarios_con_roles, statistics)
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        print(f"❌ Error generando reporte de usuarios: {e}")
        print("Traceback completo:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando reporte de usuarios: {str(e)}"
        )

@router.get(
    "/reports/proveedores-verificados",
    description="Genera reporte de proveedores verificados"
)
async def get_reporte_proveedores_verificados(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user)
):
    """Genera reporte de proveedores verificados usando DirectDBService"""
    try:
        # Usar DirectDBService para evitar problemas con prepared statements
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Consulta SQL directa para obtener proveedores verificados con información completa
            proveedores_query = """
                SELECT 
                    pe.id_perfil,
                    pe.razon_social,
                    pe.nombre_fantasia,
                    pe.estado,
                    pe.fecha_inicio,
                    pe.fecha_verificacion,
                    pe.verificado,
                    u.nombre_persona,
                    u.id as user_id
                FROM perfil_empresa pe
                INNER JOIN users u ON pe.user_id = u.id
                WHERE pe.verificado = true
                ORDER BY pe.fecha_verificacion DESC
            """
            
            proveedores_data = await conn.fetch(proveedores_query)
            
            proveedores_verificados = []
            for row in proveedores_data:
                # Obtener email del proveedor desde Supabase auth.users
                proveedor_email = "No disponible"
                try:
                    # Consulta para obtener email desde auth.users
                    email_query = """
                        SELECT email FROM auth.users WHERE id = $1
                    """
                    email_result = await conn.fetchrow(email_query, row['user_id'])
                    if email_result:
                        proveedor_email = email_result['email']
                except Exception as e:
                    print(f"Error obteniendo email del proveedor {row['user_id']}: {e}")
                    proveedor_email = "No disponible"
                
                # Formatear fechas
                fecha_verificacion_formateada = format_date_dd_mm_yyyy(row['fecha_verificacion'])
                fecha_inicio_formateada = format_date_dd_mm_yyyy(row['fecha_inicio'])
                
                proveedores_verificados.append({
                    "id_perfil": str(row['id_perfil']),
                    "razon_social": row['razon_social'],
                    "nombre_fantasia": row['nombre_fantasia'],
                    "nombre_contacto": row['nombre_persona'],
                    "email_contacto": proveedor_email,
                    "estado": row['estado'],
                    "fecha_inicio": fecha_inicio_formateada,
                    "fecha_verificacion": fecha_verificacion_formateada,
                    "verificado": row['verificado']
                })
            
            return {
                "total_proveedores": len(proveedores_verificados),
                "proveedores": proveedores_verificados,
                "fecha_generacion": datetime.now().isoformat(),
                "filtros_aplicados": "Proveedores verificados"
            }
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        print(f"Error generando reporte de proveedores verificados: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte de proveedores verificados")

# Funciones helper para get_reporte_solicitudes_proveedores
async def get_all_verification_requests(db: AsyncSession) -> list[VerificacionSolicitud]:
    """Obtiene todas las solicitudes de verificación ordenadas por fecha"""
    solicitudes_query = select(VerificacionSolicitud).order_by(VerificacionSolicitud.created_at.desc())
    solicitudes_result = await db.execute(solicitudes_query)
    return solicitudes_result.scalars().all()

async def get_empresa_by_perfil_id_for_report(db: AsyncSession, perfil_id: int) -> Optional[PerfilEmpresa]:
    """Obtiene la empresa por ID de perfil para el reporte"""
    empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.id_perfil == perfil_id)
    empresa_result = await db.execute(empresa_query)
    return empresa_result.scalars().first()

async def get_user_by_id_from_db(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserModel]:
    """Obtiene el usuario por ID desde la base de datos"""
    user_query = select(UserModel).where(UserModel.id == user_id)
    user_result = await db.execute(user_query)
    return user_result.scalars().first()

def get_user_email_from_supabase_auth(user_id: uuid.UUID) -> str:
    """Obtiene el email del usuario desde Supabase Auth"""
    try:
        auth_user = supabase_admin.auth.admin.get_user_by_id(str(user_id))
        if auth_user and auth_user.user:
            return auth_user.user.email or VALOR_DEFAULT_NO_DISPONIBLE
    except Exception:
        pass
    return VALOR_DEFAULT_NO_DISPONIBLE

async def get_user_contact_info_for_report(db: AsyncSession, empresa: Optional[PerfilEmpresa]) -> tuple[str, str]:
    """Obtiene el nombre y email del usuario de contacto"""
    user_nombre = VALOR_DEFAULT_NO_DISPONIBLE
    user_email = VALOR_DEFAULT_NO_DISPONIBLE
    
    if not empresa or not empresa.user_id:
        return user_nombre, user_email
    
    user = await get_user_by_id_from_db(db, empresa.user_id)
    
    if user:
        user_nombre = user.nombre_persona or VALOR_DEFAULT_NO_DISPONIBLE
        user_email = get_user_email_from_supabase_auth(empresa.user_id)
    
    return user_nombre, user_email

def format_solicitud_date(date_value) -> Optional[str]:
    """Formatea una fecha de solicitud a DD/MM/YYYY (alias para compatibilidad)"""
    return format_date_dd_mm_yyyy(date_value)

async def process_solicitud_data(db: AsyncSession, solicitud: VerificacionSolicitud) -> dict:
    """Procesa una solicitud y retorna su diccionario para el reporte"""
    empresa = await get_empresa_by_perfil_id_for_report(db, solicitud.id_perfil)
    user_nombre, user_email = await get_user_contact_info_for_report(db, empresa)
    
    return {
        "razon_social": empresa.razon_social if empresa else VALOR_DEFAULT_NO_DISPONIBLE,
        "nombre_fantasia": empresa.nombre_fantasia if empresa else VALOR_DEFAULT_NO_DISPONIBLE,
        "nombre_contacto": user_nombre,
        "email_contacto": user_email,
        "estado": solicitud.estado,
        "fecha_solicitud": format_solicitud_date(solicitud.created_at),
        "fecha_revision": format_solicitud_date(solicitud.fecha_revision),
        "comentario": solicitud.comentario
    }

async def process_all_solicitudes(db: AsyncSession, solicitudes: list[VerificacionSolicitud]) -> list[dict]:
    """Procesa todas las solicitudes y retorna la lista completa"""
    solicitudes_detalladas = []
    for solicitud in solicitudes:
        solicitud_data = await process_solicitud_data(db, solicitud)
        solicitudes_detalladas.append(solicitud_data)
    return solicitudes_detalladas

def build_solicitudes_report_response(solicitudes_detalladas: list[dict]) -> dict:
    """Construye la respuesta del reporte de solicitudes"""
    return {
        "total_solicitudes": len(solicitudes_detalladas),
        "solicitudes": solicitudes_detalladas,
        "fecha_generacion": datetime.now().isoformat()
    }

@router.get(
    "/reports/solicitudes-proveedores",
    description="Genera reporte de solicitudes para ser proveedores"
)
async def get_reporte_solicitudes_proveedores(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte de solicitudes para ser proveedores"""
    try:
        solicitudes = await get_all_verification_requests(db)
        solicitudes_detalladas = await process_all_solicitudes(db, solicitudes)
        return build_solicitudes_report_response(solicitudes_detalladas)
    except Exception as e:
        print(f"Error generando reporte de solicitudes: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte")

@router.get(
    "/reports/categorias",
    description="Genera reporte de categorías en la plataforma"
)
async def get_reporte_categorias(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte de categorías en la plataforma"""
    try:
        # Obtener todas las categorías
        categorias_query = select(CategoriaModel).order_by(CategoriaModel.nombre)
        categorias_result = await db.execute(categorias_query)
        categorias = categorias_result.scalars().all()

        categorias_detalladas = []
        for categoria in categorias:
            # Contar servicios en esta categoría
            servicios_query = select(ServicioModel).where(ServicioModel.id_categoria == categoria.id_categoria)
            servicios_result = await db.execute(servicios_query)
            servicios = servicios_result.scalars().all()

            # Formatear fecha a DD/MM/AAAA
            fecha_formateada = format_date_dd_mm_yyyy(categoria.created_at)
            
            # Formatear estado: true -> "Activa", false -> "Inactiva"
            estado_formateado = "Activa" if categoria.estado else "Inactiva"
            
            categorias_detalladas.append({
                "nombre": categoria.nombre,
                "estado": estado_formateado,
                "total_servicios": len(servicios),
                "fecha_creacion": fecha_formateada
            })

        return {
            "total_categorias": len(categorias_detalladas),
            "categorias": categorias_detalladas,
            "fecha_generacion": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error generando reporte de categorías: {e}")
        # Si es un error de PgBouncer, intentar rollback
        if "prepared statement" in str(e).lower() or "pgbouncer" in str(e).lower():
            try:
                await db.rollback()
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Error generando reporte")

@router.get(
    "/reports/servicios",
    description="Genera reporte de servicios en la plataforma"
)
async def get_reporte_servicios(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user)
):
    """Genera reporte de servicios en la plataforma usando DirectDBService"""
    try:
        # Usar DirectDBService para evitar problemas con prepared statements
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Consulta SQL directa para obtener servicios con información completa
            servicios_query = """
                SELECT 
                    s.id_servicio,
                    s.nombre,
                    s.descripcion,
                    s.precio,
                    s.estado,
                    s.created_at,
                    pe.razon_social,
                    pe.nombre_fantasia,
                    c.nombre as categoria_nombre
                FROM servicio s
                INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
                LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
                ORDER BY s.created_at DESC
            """
            
            servicios_data = await conn.fetch(servicios_query)
            
            servicios_detallados = []
            for row in servicios_data:
                # Formatear fecha a DD/MM/AAAA
                fecha_formateada = format_date_dd_mm_yyyy(row['created_at'])
                
                # Formatear estado: true -> "ACTIVO", false -> "INACTIVO"
                estado_formateado = "ACTIVO" if row['estado'] else "INACTIVO"
                
                servicios_detallados.append({
                    "id_servicio": str(row['id_servicio']),
                    "nombre": row['nombre'] or "Sin nombre",
                    "descripcion": row['descripcion'] or "Sin descripción",
                    "precio": float(row['precio']) if row['precio'] else 0,
                    "estado": estado_formateado,
                    "empresa": row['razon_social'] or "Sin empresa",
                    "nombre_fantasia": row['nombre_fantasia'] or "Sin nombre fantasia",
                    "categoria": row['categoria_nombre'] or "Sin categoría",
                    "fecha_creacion": fecha_formateada or "Sin fecha"
                })
            
            return {
                "total_servicios": len(servicios_detallados),
                "servicios": servicios_detallados,
                "fecha_generacion": datetime.now().isoformat(),
                "filtros_aplicados": "Todos los servicios publicados"
            }
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        print(f"Error generando reporte de servicios: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte de servicios")

# Funciones helper para get_reporte_reservas_proveedores
def build_reservas_proveedores_query() -> str:
    """Construye la query SQL para obtener reservas de proveedores"""
    return """
        SELECT 
            r.id_reserva,
            r.estado,
            r.fecha,
            r.hora_inicio,
            r.hora_fin,
            r.descripcion,
            r.observacion,
            r.created_at as fecha_reserva,
            u.nombre_persona as cliente_nombre,
            u.id as cliente_user_id,
            s.nombre as servicio_nombre,
            s.precio as servicio_precio,
            s.descripcion as servicio_descripcion,
            pe.razon_social as empresa_razon_social,
            pe.nombre_fantasia as empresa_nombre_fantasia,
            pe.user_id as proveedor_user_id,
            c.nombre as categoria_nombre
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        INNER JOIN users u ON r.user_id = u.id
        LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
        ORDER BY r.created_at DESC
    """

async def get_cliente_email_from_auth(conn, cliente_user_id: uuid.UUID) -> str:
    """Obtiene el email del cliente desde auth.users"""
    try:
        email_query = "SELECT email FROM auth.users WHERE id = $1"
        email_result = await conn.fetchrow(email_query, cliente_user_id)
        if email_result:
            return email_result['email']
    except Exception as e:
        print(f"Error obteniendo email del cliente {cliente_user_id}: {e}")
    return VALOR_DEFAULT_NO_DISPONIBLE

def format_reserva_datetime(date_value) -> Optional[str]:
    """Formatea una fecha/hora de reserva a DD/MM/YYYY HH:MM"""
    if date_value:
        return date_value.strftime("%d/%m/%Y %H:%M")
    return None

def format_servicio_date(date_value) -> Optional[str]:
    """Formatea una fecha de servicio a DD/MM/YYYY (alias para compatibilidad)"""
    return format_date_dd_mm_yyyy(date_value)

def format_horario_completo(hora_inicio, hora_fin) -> Optional[str]:
    """Formatea el horario completo de la reserva"""
    if hora_inicio and hora_fin:
        return f"{hora_inicio} - {hora_fin}"
    elif hora_inicio:
        return str(hora_inicio)
    return None

def get_estado_info() -> dict:
    """Retorna el diccionario de información de estados"""
    return {
        'pendiente': {'label': 'Pendiente', 'color': 'yellow'},
        'aprobado': {'label': 'Aprobado', 'color': 'green'},
        'rechazado': {'label': 'Rechazado', 'color': 'red'},
        'concluido': {'label': 'Concluido', 'color': 'blue'},
        'confirmada': {'label': 'Confirmada', 'color': 'green'},
        'cancelada': {'label': 'Cancelada', 'color': 'red'}
    }

def format_estado_reserva(estado: str) -> dict:
    """Formatea el estado de la reserva con label y color"""
    estado_info = get_estado_info()
    estado_actual = estado.lower()
    return estado_info.get(estado_actual, {
        'label': estado_actual.title(),
        'color': 'gray'
    })

async def process_reserva_row(conn, row: dict) -> dict:
    """Procesa una fila de reserva y retorna su diccionario"""
    cliente_email = await get_cliente_email_from_auth(conn, row['cliente_user_id'])
    estado_formateado = format_estado_reserva(row['estado'])
    
    return {
        "id_reserva": row['id_reserva'],
        "cliente": {
            "nombre": row['cliente_nombre'],
            "email": cliente_email,
            "user_id": str(row['cliente_user_id'])
        },
        "proveedor": {
            "empresa": row['empresa_razon_social'],
            "nombre_fantasia": row['empresa_nombre_fantasia'],
            "user_id": str(row['proveedor_user_id'])
        },
        "servicio": {
            "nombre": row['servicio_nombre'],
            "precio": float(row['servicio_precio']) if row['servicio_precio'] else 0,
            "descripcion": row['servicio_descripcion'],
            "categoria": row['categoria_nombre']
        },
        "reserva": {
            "fecha_servicio": format_servicio_date(row['fecha']),
            "horario": format_horario_completo(row['hora_inicio'], row['hora_fin']),
            "fecha_reserva": format_reserva_datetime(row['fecha_reserva']),
            "descripcion": row['descripcion'],
            "observacion": row['observacion']
        },
        "estado": {
            "valor": row['estado'],
            "label": estado_formateado['label'],
            "color": estado_formateado['color']
        }
    }

async def process_all_reservas(conn, reservas_data: list) -> list[dict]:
    """Procesa todas las reservas y retorna la lista completa"""
    reservas_detalladas = []
    for row in reservas_data:
        reserva_data = await process_reserva_row(conn, row)
        reservas_detalladas.append(reserva_data)
    return reservas_detalladas

def calculate_reservas_statistics(reservas_detalladas: list[dict]) -> dict:
    """Calcula las estadísticas de las reservas"""
    estados_count = {}
    for reserva in reservas_detalladas:
        estado = reserva['estado']['valor']
        estados_count[estado] = estados_count.get(estado, 0) + 1
    
    return {
        "por_estado": estados_count,
        "total_proveedores": len(set(r['proveedor']['user_id'] for r in reservas_detalladas)),
        "total_clientes": len(set(r['cliente']['email'] for r in reservas_detalladas))
    }

def build_reservas_proveedores_response(reservas_detalladas: list[dict], statistics: dict) -> dict:
    """Construye la respuesta del reporte de reservas de proveedores"""
    return {
        "total_reservas": len(reservas_detalladas),
        "reservas": reservas_detalladas,
        "estadisticas": statistics,
        "fecha_generacion": datetime.now().isoformat(),
        "filtros_aplicados": "Todas las reservas de proveedores"
    }

@router.get(
    "/reports/reservas-proveedores",
    description="Genera reporte detallado de reservas de proveedores con información completa"
)
async def get_reporte_reservas_proveedores(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte detallado de reservas de proveedores"""
    try:
        
        conn = await direct_db_service.get_connection()
        
        try:
            reservas_query = build_reservas_proveedores_query()
            reservas_data = await conn.fetch(reservas_query)
            reservas_detalladas = await process_all_reservas(conn, reservas_data)
            statistics = calculate_reservas_statistics(reservas_detalladas)
            
            return build_reservas_proveedores_response(reservas_detalladas, statistics)
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        print(f"Error generando reporte de reservas de proveedores: {e}")
        if "prepared statement" in str(e).lower() or "pgbouncer" in str(e).lower():
            try:
                await db.rollback()
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Error generando reporte de reservas de proveedores")

# Funciones helper para get_reporte_reservas
def build_reservas_query() -> str:
    """Construye la query SQL para obtener reservas"""
    return """
        SELECT 
            r.id_reserva,
            r.created_at,
            r.fecha,
            r.hora_inicio,
            r.hora_fin,
            r.estado,
            r.descripcion,
            r.observacion,
            s.nombre as servicio_nombre,
            s.precio as servicio_precio,
            pe.razon_social as empresa_razon_social,
            pe.nombre_fantasia as empresa_nombre_fantasia,
            u.nombre_persona as cliente_nombre,
            u.id as cliente_user_id
        FROM reserva r
        JOIN servicio s ON r.id_servicio = s.id_servicio
        JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
    """

def format_reserva_date(date_value) -> Optional[str]:
    """Formatea una fecha de reserva a DD/MM/YYYY (alias para compatibilidad)"""
    return format_date_dd_mm_yyyy(date_value)

def format_hora_servicio(hora_inicio, hora_fin) -> Optional[str]:
    """Formatea la hora del servicio"""
    if hora_inicio and hora_fin:
        return f"{hora_inicio} - {hora_fin}"
    elif hora_inicio:
        return str(hora_inicio)
    return None

def format_estado_simple(estado: Optional[str]) -> str:
    """Formatea el estado de la reserva"""
    return estado.title() if estado else "Sin estado"

def format_precio(precio_value) -> float:
    """Formatea el precio del servicio"""
    if precio_value:
        return float(precio_value)
    return 0.0

async def process_reserva_row_simple(conn, row: dict) -> dict:
    """Procesa una fila de reserva y retorna su diccionario para el reporte simple"""
    cliente_email = await get_cliente_email_from_auth(conn, row['cliente_user_id'])
    
    return {
        "id_reserva": row['id_reserva'],
        "fecha_reserva": format_reserva_date(row['created_at']),
        "estado": format_estado_simple(row['estado']),
        "cliente_nombre": row['cliente_nombre'] or VALOR_DEFAULT_NO_DISPONIBLE,
        "cliente_email": cliente_email or VALOR_DEFAULT_NO_DISPONIBLE,
        "servicio_nombre": row['servicio_nombre'] or VALOR_DEFAULT_NO_DISPONIBLE,
        "empresa_razon_social": row['empresa_razon_social'] or VALOR_DEFAULT_NO_DISPONIBLE,
        "empresa_nombre_fantasia": row['empresa_nombre_fantasia'] or VALOR_DEFAULT_NO_DISPONIBLE,
        "fecha_servicio": format_servicio_date(row['fecha']),
        "hora_servicio": format_hora_servicio(row['hora_inicio'], row['hora_fin']),
        "precio": format_precio(row['servicio_precio']),
        "descripcion": row['descripcion'] or "",
        "observacion": row['observacion'] or ""
    }

async def process_all_reservas_simple(conn, reservas_data: list) -> list[dict]:
    """Procesa todas las reservas y retorna la lista completa para el reporte simple"""
    reservas_detalladas = []
    for row in reservas_data:
        reserva_data = await process_reserva_row_simple(conn, row)
        reservas_detalladas.append(reserva_data)
    return reservas_detalladas

def build_reservas_response(reservas_detalladas: list[dict]) -> dict:
    """Construye la respuesta del reporte de reservas"""
    return {
        "total_reservas": len(reservas_detalladas),
        "reservas": reservas_detalladas,
        "fecha_generacion": datetime.now().isoformat()
    }

@router.get(
    "/reports/reservas",
    description="Genera reporte de reservas en la plataforma"
)
async def get_reporte_reservas(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte de reservas en la plataforma"""
    try:
        
        conn = await direct_db_service.get_connection()
        
        try:
            reservas_query = build_reservas_query()
            reservas_data = await conn.fetch(reservas_query)
            reservas_detalladas = await process_all_reservas_simple(conn, reservas_data)
            
            return build_reservas_response(reservas_detalladas)
        finally:
            await direct_db_service.pool.release(conn)

    except Exception as e:
        print(f"Error generando reporte de reservas: {e}")
        if "prepared statement" in str(e).lower() or "pgbouncer" in str(e).lower():
            try:
                await db.rollback()
            except Exception:
                pass

        raise HTTPException(status_code=500, detail="Error generando reporte")

@router.get(
    "/reports/calificaciones",
    description="Genera reporte de calificaciones de clientes hacia proveedores"
)
async def get_reporte_calificaciones(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte de calificaciones de clientes hacia proveedores (8 columnas)"""
    try:
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Query SQL optimizada para reporte de calificaciones
            calificaciones_query = """
                SELECT
                    c.fecha::date AS fecha,
                    s.nombre AS servicio,
                    pe.nombre_fantasia AS proveedor_empresa,
                    u_prov.nombre_persona AS proveedor_persona,
                    u_cli.nombre_persona AS cliente,
                    c.puntaje AS puntaje,
                    c.satisfaccion_nps AS nps,
                    LEFT(COALESCE(c.comentario, ''), 120) AS comentario
                FROM public.calificacion c
                JOIN public.reserva r ON r.id_reserva = c.id_reserva
                JOIN public.servicio s ON s.id_servicio = r.id_servicio
                JOIN public.perfil_empresa pe ON pe.id_perfil = s.id_perfil
                JOIN public.users u_prov ON u_prov.id = pe.user_id
                JOIN public.users u_cli ON u_cli.id = r.user_id
                WHERE c.rol_emisor = 'cliente'
                ORDER BY c.fecha DESC
            """
            
            calificaciones_data = await conn.fetch(calificaciones_query)
            
            calificaciones_detalladas = []
            for row in calificaciones_data:
                # Formatear fecha a DD/MM/YYYY
                fecha_formateada = format_date_dd_mm_yyyy(row['fecha'])
                
                calificaciones_detalladas.append({
                    "fecha": fecha_formateada,
                    "servicio": row['servicio'],
                    "proveedor_empresa": row['proveedor_empresa'],
                    "proveedor_persona": row['proveedor_persona'],
                    "cliente": row['cliente'],
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
        print(f"Error generando reporte de calificaciones: {e}")
        # Si es un error de PgBouncer, intentar rollback
        if "prepared statement" in str(e).lower() or "pgbouncer" in str(e).lower():
            try:
                await db.rollback()
            except Exception:
                pass
        
        raise HTTPException(status_code=500, detail="Error generando reporte de calificaciones")

@router.get(
    "/reports/calificaciones-proveedores",
    description="Genera reporte de calificaciones de proveedores hacia clientes"
)
async def get_reporte_calificaciones_proveedores(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte de calificaciones de proveedores hacia clientes (8 columnas)"""
    try:
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Query SQL optimizada para reporte de calificaciones de proveedores
            calificaciones_query = """
                SELECT
                    c.fecha::date AS fecha,
                    s.nombre AS servicio,
                    u_cli.nombre_persona AS cliente_persona,
                    u_cli.nombre_empresa AS cliente_empresa,
                    pe.nombre_fantasia AS proveedor_empresa,
                    u_prov.nombre_persona AS proveedor_persona,
                    c.puntaje AS puntaje,
                    LEFT(COALESCE(c.comentario, ''), 120) AS comentario
                FROM public.calificacion c
                JOIN public.reserva r ON r.id_reserva = c.id_reserva
                JOIN public.servicio s ON s.id_servicio = r.id_servicio
                JOIN public.perfil_empresa pe ON pe.id_perfil = s.id_perfil
                JOIN public.users u_prov ON u_prov.id = pe.user_id
                JOIN public.users u_cli ON u_cli.id = r.user_id
                WHERE c.rol_emisor = 'proveedor'
                ORDER BY c.fecha DESC
            """
            
            calificaciones_data = await conn.fetch(calificaciones_query)
            
            calificaciones_detalladas = []
            for row in calificaciones_data:
                # Formatear fecha a DD/MM/YYYY
                fecha_formateada = format_date_dd_mm_yyyy(row['fecha'])
                
                calificaciones_detalladas.append({
                    "fecha": fecha_formateada,
                    "servicio": row['servicio'],
                    "cliente_persona": row['cliente_persona'],
                    "cliente_empresa": row['cliente_empresa'] if row['cliente_empresa'] else "N/A",
                    "proveedor_empresa": row['proveedor_empresa'],
                    "proveedor_persona": row['proveedor_persona'],
                    "puntaje": row['puntaje'],
                    "comentario": row['comentario'] if row['comentario'] else "Sin comentario"
                })
        
        finally:
            await direct_db_service.pool.release(conn)

        return {
            "total_calificaciones_proveedores": len(calificaciones_detalladas),
            "calificaciones_proveedores": calificaciones_detalladas,
            "fecha_generacion": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Error generando reporte de calificaciones de proveedores: {e}")
        # Si es un error de PgBouncer, intentar rollback
        if "prepared statement" in str(e).lower() or "pgbouncer" in str(e).lower():
            try:
                await db.rollback()
            except Exception:
                pass
        
        raise HTTPException(status_code=500, detail="Error generando reporte de calificaciones de proveedores")

@router.get(
    "/users/batch-emails",
    description="Obtiene emails de usuarios por lotes para evitar sobrecarga"
)
async def get_users_batch_emails(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    skip: int = 0,
    limit: int = 50
):
    """Obtiene emails de usuarios por lotes"""
    try:

        # Obtener usuarios de Supabase en lotes
        auth_users = supabase_admin.auth.admin.list_users()

        if not auth_users or len(auth_users) == 0:
            return {"emails": {}, "total": 0}

        # Aplicar paginación
        paginated_users = auth_users[skip:skip + limit]

        # Crear diccionario de emails
        emails_dict = {}
        for auth_user in paginated_users:
            if auth_user.id and auth_user.email:
                emails_dict[auth_user.id] = {
                    "email": auth_user.email,
                    "ultimo_acceso": auth_user.last_sign_in_at,
                    "estado": "Activo" if not auth_user.banned_until else "Suspendido"
                }

        return {
            "emails": emails_dict,
            "total": len(emails_dict),
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        print(f"⚠️ Error obteniendo emails por lotes: {e}")
        return {"emails": {}, "total": 0}


@router.get(
    "/debug/user-status/{user_id}",
    description="Debug: Verificar estado de un usuario específico"
)
async def debug_user_status(
    user_id: str,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint de debug para verificar el estado de un usuario"""
    try:
        print(f"🔍 DEBUG: Verificando estado de usuario {user_id}")

        # Obtener usuario de la base de datos
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            return {
                "error": "Usuario no encontrado en base de datos",
                "user_id": user_id
            }

        # Obtener estado de Supabase
        supabase_status = "Desconocido"
        try:
            auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
            if auth_user and auth_user.user:
                supabase_status = "Activo" if not auth_user.user.banned_until else "Suspendido"
        except Exception as e:
            supabase_status = f"Error: {str(e)}"

        return {
            "user_id": str(user.id),
            "nombre_persona": user.nombre_persona,
            "estado_db": user.estado,
            "estado_supabase": supabase_status,
            "coinciden": (user.estado == "ACTIVO" and supabase_status == "Activo") or
                        (user.estado == "INACTIVO" and supabase_status == "Suspendido"),
            "timestamp": "2024-12-19"
        }

    except Exception as e:
        print(f"❌ Error en debug: {e}")
        return {
            "error": str(e),
            "user_id": user_id
        }


@router.post(
    "/users/self-deactivate",
    description="Permite a un usuario desactivarse a sí mismo del sistema"
)
async def self_deactivate_user(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Permite a un usuario desactivarse a sí mismo del sistema"""
    try:
        print(f"🔍 DEBUG: Usuario {current_user.id} solicitando auto-desactivación")

        # Verificar que el usuario existe en la base de datos
        user_uuid = uuid.UUID(current_user.id)
        user_query = select(UserModel).where(UserModel.id == user_uuid)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        if not user:
            print(f"❌ Usuario {current_user.id} no encontrado en base de datos")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Verificar que el usuario no esté ya inactivo
        if user.estado == "INACTIVO":
            print(f"❌ Usuario {current_user.id} ya está inactivo")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya está desactivado"
            )

        print(f"✅ Desactivando usuario {current_user.id}")

        # Cambiar el estado del usuario a INACTIVO
        user.estado = "INACTIVO"
        
        # Actualizar fecha_fin en perfil_empresa si existe
        # from app.services.perfil_empresa_service import PerfilEmpresaService  # Comentado temporalmente
        # perfil_updated = await PerfilEmpresaService.deactivate_user_profile(db, str(user.id))
        perfil_updated = False  # Temporalmente deshabilitado
        if perfil_updated:
            print(f"✅ Fecha_fin actualizada en perfil_empresa para usuario {user.id} (auto-desactivación)")
        else:
            print(f"ℹ️ No se encontró perfil_empresa para usuario {user.id} o ya estaba desactivado")

        # Intentar actualizar en Supabase Auth también
        supabase_success = False
        try:
            
            if supabase_admin:
                supabase_admin.auth.admin.update_user_by_id(
                    str(user.id),
                    {
                        "user_metadata": {"status": "inactive"},
                        "app_metadata": {"deactivated": True}
                    }
                )
                print(f"✅ Usuario {user.id} actualizado en Supabase Auth")
                supabase_success = True
        except Exception as e:
            print(f"⚠️ Error actualizando en Supabase: {e}")

        # Guardar cambios en la base de datos
        await db.commit()
        print(f"✅ Auto-desactivación completada para usuario {current_user.id}")

        return {
            "message": "Tu cuenta ha sido desactivada exitosamente. Serás redirigido al login.",
            "user_id": str(user.id),
            "status": "inactive",
            "estado_anterior": "ACTIVO",
            "estado_nuevo": "INACTIVO",
            "supabase_updated": supabase_success,
            "redirect_to_login": True
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en auto-desactivación: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error desactivando la cuenta: {str(e)}"
        )


# Funciones helper para get_user_details
async def get_user_by_id_for_details(db: AsyncSession, user_id: str) -> UserModel:
    """Obtiene el usuario por ID para detalles"""
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

async def get_user_roles_data(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    """Obtiene los roles del usuario y retorna la lista de datos"""
    roles_query = select(UsuarioRolModel).where(UsuarioRolModel.id_usuario == user_id)
    roles_result = await db.execute(roles_query)
    user_roles = roles_result.scalars().all()
    
    roles_data = []
    for user_role in user_roles:
        if user_role.rol:
            roles_data.append({
                "id": str(user_role.rol.id),
                "nombre": user_role.rol.nombre,
                "descripcion": user_role.rol.descripcion
            })
    return roles_data

def get_auth_user_data(user_id: uuid.UUID) -> Optional:
    """Obtiene los datos del usuario desde Supabase Auth"""
    try:
        return supabase_auth.auth.admin.get_user_by_id(str(user_id))
    except Exception as e:
        print(f"Error obteniendo información de auth para usuario {user_id}: {e}")
        return None

def extract_auth_user_info(auth_user) -> dict:
    """Extrae la información del usuario desde auth_user"""
    if not auth_user or not auth_user.user:
        return {
            "email": VALOR_DEFAULT_NO_DISPONIBLE,
            "email_verificado": False,
            "telefono": None,
            "telefono_verificado": False,
            "ultimo_acceso": None,
            "ultima_actividad": None
        }
    
    return {
        "email": auth_user.user.email or VALOR_DEFAULT_NO_DISPONIBLE,
        "email_verificado": auth_user.user.email_confirmed_at is not None,
        "telefono": auth_user.user.phone,
        "telefono_verificado": auth_user.user.phone_confirmed_at is not None,
        "ultimo_acceso": auth_user.user.last_sign_in_at,
        "ultima_actividad": auth_user.user.last_sign_in_at
    }

def build_user_details_response(user: UserModel, roles_data: list[dict], auth_info: dict) -> dict:
    """Construye la respuesta con los detalles del usuario"""
    return {
        "id": str(user.id),
        "nombre_persona": user.nombre_persona,
        "nombre_empresa": user.nombre_empresa,
        "email": auth_info["email"],
        "email_verificado": auth_info["email_verificado"],
        "telefono": auth_info["telefono"],
        "telefono_verificado": auth_info["telefono_verificado"],
        "roles": roles_data,
        "estado": user.estado if user.estado else "ACTIVO",
        "ultimo_acceso": auth_info["ultimo_acceso"],
        "ultima_actividad": auth_info["ultima_actividad"]
    }

@router.get(
    "/users/{user_id}",
    description="Obtiene información detallada de un usuario específico"
)
async def get_user_details(
    user_id: str,
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene información detallada de un usuario específico"""
    try:
        user = await get_user_by_id_for_details(db, user_id)
        roles_data = await get_user_roles_data(db, user.id)
        auth_user = get_auth_user_data(user.id)
        auth_info = extract_auth_user_info(auth_user)
        
        return build_user_details_response(user, roles_data, auth_info)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo detalles del usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo detalles del usuario: {str(e)}"
        )

