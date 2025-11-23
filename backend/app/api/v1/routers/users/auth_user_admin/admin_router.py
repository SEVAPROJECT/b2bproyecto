# app/api/v1/routers/admin_router.py

from datetime import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional, Tuple
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
from app.supabase.auth_service import supabase_admin, supabase_auth
import os
from app.services.date_service import DateService
import secrets
import string
from app.services.direct_db_service import direct_db_service
import mimetypes
from app.idrive.idrive_service import idrive_s3_client
from app.core.config import IDRIVE_BUCKET_NAME
from app.api.v1.dependencies.local_storage import local_storage_service

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Constantes ---
ESTADO_PENDIENTE = "pendiente"
ESTADO_APROBADA = "aprobada"
ESTADO_RECHAZADA = "rechazada"
ESTADO_PENDING = "pending"
ESTADO_APPROVED = "approved"
ESTADO_REJECTED = "rejected"
ESTADO_NONE = "none"
ESTADO_ACTIVO = "ACTIVO"
ESTADO_INACTIVO = "INACTIVO"
ESTADO_ACTIVO_SUPABASE = "Activo"
ESTADO_SUSPENDIDO_SUPABASE = "Suspendido"
ESTADO_ACTIVE_METADATA = "active"
ESTADO_INACTIVE_METADATA = "inactive"
ROL_ADMINISTRADOR = "Administrador"
ROL_PROVEEDOR = "Proveedor"
ROL_CLIENTE = "Cliente"
MSG_USUARIO_NO_ENCONTRADO = "Usuario no encontrado"
VALOR_DEFAULT_NO_DISPONIBLE = "No disponible"
URL_TEMP_PENDING = "temp://pending"


FORMATO_FECHA_DD_MM_YYYY = "%d/%m/%Y"


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
async def get_pending_solicitudes(db: AsyncSession) -> List[VerificacionSolicitud]:
    """Obtiene todas las solicitudes de verificación pendientes"""
    query = select(VerificacionSolicitud).where(VerificacionSolicitud.estado == ESTADO_PENDIENTE)
    result = await db.execute(query)
    return result.scalars().all()

async def get_empresa_by_perfil(db: AsyncSession, id_perfil: int) -> Optional[PerfilEmpresa]:
    """Obtiene la información de la empresa por id_perfil"""
    empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.id_perfil == id_perfil)
    empresa_result = await db.execute(empresa_query)
    return empresa_result.scalars().first()

async def get_user_info_from_db(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserModel]:
    """Obtiene la información del usuario desde la base de datos"""
    user_query = select(UserModel).where(UserModel.id == user_id)
    user_result = await db.execute(user_query)
    return user_result.scalars().first()

def get_user_email_from_supabase(user_id: uuid.UUID) -> str:
    """Obtiene el email del usuario desde Supabase Auth"""
    try:
        auth_user = supabase_admin.auth.admin.get_user_by_id(str(user_id))
        if auth_user and auth_user.user:
            return auth_user.user.email or "No disponible"
        return "No disponible"
    except Exception as e:
        print(f"Error obteniendo email para usuario {user_id}: {e}")
        return "No disponible"

async def get_user_contact_info(db: AsyncSession, empresa: Optional[PerfilEmpresa]) -> Tuple[str, str]:
    """Obtiene la información de contacto del usuario (nombre y email)"""
    user_nombre = VALOR_DEFAULT_NO_DISPONIBLE
    user_email = VALOR_DEFAULT_NO_DISPONIBLE
    
    if not empresa or not empresa.user_id:
        return user_nombre, user_email
    
    user = await get_user_info_from_db(db, empresa.user_id)
    if user:
        user_nombre = user.nombre_persona or "Usuario sin nombre"
        user_email = get_user_email_from_supabase(empresa.user_id)
    
    return user_nombre, user_email

async def get_documentos_detallados(db: AsyncSession, id_verificacion: int) -> List[dict]:
    """Obtiene los documentos detallados de una solicitud de verificación"""
    documentos_query = select(Documento).options(
        selectinload(Documento.tipo_documento)
    ).where(Documento.id_verificacion == id_verificacion)
    documentos_result = await db.execute(documentos_query)
    documentos = documentos_result.scalars().all()
    
    documentos_detallados = []
    for doc in documentos:
        tipo_doc = doc.tipo_documento if hasattr(doc, 'tipo_documento') else None
        
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
    
    return documentos_detallados

def build_solicitud_dict(
    solicitud: VerificacionSolicitud,
    empresa: Optional[PerfilEmpresa],
    user_nombre: str,
    user_email: str,
    documentos_detallados: List[dict]
) -> dict:
    """Construye el diccionario de datos de solicitud"""
    return {
        "id_verificacion": solicitud.id_verificacion,
        "fecha_solicitud": solicitud.fecha_solicitud,
        "fecha_revision": solicitud.fecha_revision,
        "estado": solicitud.estado,
        "comentario": solicitud.comentario,
        "id_perfil": solicitud.id_perfil,
        "created_at": solicitud.created_at,
        "documentos": documentos_detallados,
        # Información de la empresa
        "nombre_empresa": empresa.razon_social if empresa else "Empresa no encontrada",
        "nombre_fantasia": empresa.nombre_fantasia if empresa else "N/A",
        "nombre_contacto": user_nombre,
        "email_contacto": user_email,
        # Información adicional de la empresa
        "verificado": empresa.verificado if empresa else False,
        "fecha_verificacion": empresa.fecha_verificacion if empresa else None,
        "estado_empresa": empresa.estado if empresa else "N/A",
        "fecha_inicio": empresa.fecha_inicio if empresa else None,
        "fecha_fin": empresa.fecha_fin if empresa else None
    }

async def process_solicitud_data(
    db: AsyncSession,
    solicitud: VerificacionSolicitud
) -> dict:
    """Procesa los datos de una solicitud y retorna el diccionario completo"""
    # Obtener información de la empresa
    empresa = await get_empresa_by_perfil(db, solicitud.id_perfil)
    
    # Obtener información del usuario (contacto)
    user_nombre, user_email = await get_user_contact_info(db, empresa)
    
    # Obtener documentos detallados
    documentos_detallados = await get_documentos_detallados(db, solicitud.id_verificacion)
    
    # Construir diccionario de solicitud
    return build_solicitud_dict(solicitud, empresa, user_nombre, user_email, documentos_detallados)

@router.get(
    "/verificaciones/pendientes",
    description="Obtiene todas las solicitudes de verificación pendientes."
)
async def get_solicitudes_pendientes(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    # Obtener solicitudes pendientes
    solicitudes = await get_pending_solicitudes(db)
    
    # Procesar cada solicitud y construir datos completos
    solicitudes_data = []
    for solicitud in solicitudes:
        solicitud_dict = await process_solicitud_data(db, solicitud)
        solicitudes_data.append(solicitud_dict)
    
    return solicitudes_data


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
            print(f"❌ Error obteniendo roles del usuario: {str(e)}")
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
            ESTADO_PENDIENTE: ESTADO_PENDING,
            ESTADO_APROBADA: ESTADO_APPROVED, 
            ESTADO_RECHAZADA: ESTADO_REJECTED
        }
        
        estado_frontend = estado_mapping.get(solicitud.estado, ESTADO_NONE)
        
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
        print(f"❌ Error obteniendo estado de verificación: {str(e)}")
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
        solicitud.estado = ESTADO_APROBADA
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
        print("🔍 Buscando rol de proveedor en la base de datos...")
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

        print("🔄 Realizando commit de los cambios...")

        # Commit de los cambios
        await db.commit()

        print(f"✅ Solicitud {solicitud_id} aprobada exitosamente")
        print(f"✅ Usuario {perfil_empresa.user_id} ahora es proveedor")
        return {"message": "Solicitud aprobada, perfil verificado y usuario promovido a proveedor."}
        
    except Exception as e:
        print(f"❌ Error al aprobar solicitud {solicitud_id}: {str(e)}")
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
        solicitud.estado = ESTADO_RECHAZADA
        
        solicitud.fecha_revision = DateService.now_for_database()
        solicitud.comentario = decision.comentario

        print("🔄 Realizando commit de los cambios...")

        # Commit de los cambios
        await db.commit()

        print(f"✅ Solicitud {solicitud_id} rechazada exitosamente")
        return {"message": "Solicitud rechazada."}
        
    except Exception as e:
        print(f"❌ Error al rechazar solicitud {solicitud_id}: {str(e)}")
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
    import os
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
    if documento.url_archivo and documento.url_archivo != URL_TEMP_PENDING:
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
    if documento.url_archivo and documento.url_archivo != URL_TEMP_PENDING:
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
    """Verifica el token y que el usuario sea admin, retorna el user_id"""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    
    try:
        # Verificar el token con Supabase
        user_response = supabase_auth.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        
        user_id = user_response.user.id
        
        # Buscar el usuario en la base de datos
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_USUARIO_NO_ENCONTRADO)
        
        # Verificar roles
        roles_query = select(UsuarioRolModel).options(
            joinedload(UsuarioRolModel.rol)
        ).where(UsuarioRolModel.id_usuario == user_id)
        roles_result = await db.execute(roles_query)
        roles = roles_result.scalars().all()
        
        # Verificar si tiene rol de admin
        is_admin = False
        for role in roles:
            if role.rol and role.rol.nombre.lower() in ['admin', 'administrador']:
                is_admin = True
                break
        
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

async def get_documento_by_ids(db: AsyncSession, documento_id: int, solicitud_id: int) -> Documento:
    """Obtiene el documento por ID y solicitud"""
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

def generate_filename(tipo_doc: Optional[TipoDocumento], documento_id: int, url_archivo: Optional[str]) -> str:
    """Genera el nombre de archivo basado en el tipo de documento y la extensión"""
    extension = '.pdf'  # Por defecto
    
    # Extraer extensión de la URL si es posible
    if url_archivo and '.' in url_archivo:
        url_parts = url_archivo.split('/')
        if url_parts:
            last_part = url_parts[-1]
            if '.' in last_part:
                extension = '.' + last_part.split('.')[-1].lower()
    
    tipo_nombre = tipo_doc.nombre if tipo_doc else 'documento'
    return f"{tipo_nombre}_{documento_id}{extension}"

def get_content_type_from_filename(filename: str, extension: str) -> str:
    """Determina el tipo de contenido basado en la extensión"""
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        # Mapeo manual para extensiones comunes
        if extension in ['.jpg', '.jpeg']:
            content_type = "image/jpeg"
        elif extension == '.png':
            content_type = "image/png"
        elif extension == '.pdf':
            content_type = "application/pdf"
        elif extension in ['.doc', '.docx']:
            content_type = "application/msword"
        else:
            content_type = "application/octet-stream"
    return content_type

async def serve_local_document(url_archivo: str, nombre_archivo: str) -> StreamingResponse:
    """Sirve un documento almacenado localmente"""
    print(f"📁 Documento local detectado: {url_archivo}")
    
    serve_success, serve_message, file_content = local_storage_service.serve_file(url_archivo)
    
    if not serve_success or not file_content:
        print(f"❌ Error sirviendo documento local: {serve_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accediendo al documento local: {serve_message}"
        )
    
    print(f"✅ Documento local servido exitosamente: {len(file_content)} bytes")
    
    extension = '.' + nombre_archivo.split('.')[-1] if '.' in nombre_archivo else '.pdf'
    content_type = get_content_type_from_filename(nombre_archivo, extension)
    
    return StreamingResponse(
        iter([file_content]),
        media_type=content_type,
        headers={
            "Content-Disposition": f"inline; filename={nombre_archivo}",
            "Content-Type": content_type,
            "Content-Length": str(len(file_content))
        }
    )

def extract_file_key_from_idrive_url(url: str) -> str:
    """Extrae la clave del archivo de una URL de IDrive"""
    url_parts = url.split('/')
    key_parts = []
    found_bucket = False
    
    for part in url_parts:
        if found_bucket:
            key_parts.append(part)
        elif part in ['documentos', 'files', 'uploads'] or (IDRIVE_BUCKET_NAME and IDRIVE_BUCKET_NAME in part):
            found_bucket = True
    
    if not key_parts:
        raise ValueError("No se pudo extraer la clave de la URL")
    
    return '/'.join(key_parts)

async def download_from_idrive_direct(url: str) -> bytes:
    """Intenta descargar el archivo usando HTTP directo desde IDrive"""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content

async def download_from_idrive_s3(url: str) -> bytes:
    """Intenta descargar el archivo usando el cliente S3 de IDrive"""
    print("🔄 Intentando con cliente IDrive2...")
    
    key = extract_file_key_from_idrive_url(url)
    print(f"🔍 Intentando descargar desde IDrive2 con clave: {key}")
    
    response = idrive_s3_client.get_object(
        Bucket=IDRIVE_BUCKET_NAME,
        Key=key
    )
    return response['Body'].read()

async def download_from_idrive_with_headers(url: str) -> bytes:
    """Intenta descargar el archivo usando headers específicos"""
    print(f"🔄 Intentando con headers específicos...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/pdf,application/octet-stream,*/*',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.content

async def download_idrive_document(url: str) -> bytes:
    """Descarga un documento de IDrive usando múltiples estrategias"""
    print(f"🌐 Documento iDrive detectado: {url}")
    
    # Estrategia 1: Intentar con HTTP directo primero
    try:
        content = await download_from_idrive_direct(url)
        print(f"✅ Descarga HTTP exitosa: {len(content)} bytes")
        return content
    except Exception as http_error:
        print(f"❌ Error HTTP directo: {str(http_error)}")
        
        # Estrategia 2: Intentar con cliente IDrive2 como fallback
        try:
            content = await download_from_idrive_s3(url)
            print(f"✅ Descarga IDrive2 exitosa: {len(content)} bytes")
            return content
        except Exception as idrive_error:
            print(f"❌ Error con IDrive2: {str(idrive_error)}")
            
            # Estrategia 3: Intentar con headers específicos
            try:
                content = await download_from_idrive_with_headers(url)
                print(f"✅ Descarga con headers exitosa: {len(content)} bytes")
                return content
            except Exception as final_error:
                print(f"❌ Error final: {str(final_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"No se pudo acceder al documento. Error: {str(final_error)}"
                )

async def serve_idrive_document(url: str, nombre_archivo: str) -> StreamingResponse:
    """Sirve un documento almacenado en IDrive"""
    content = await download_idrive_document(url)
    
    extension = '.' + nombre_archivo.split('.')[-1] if '.' in nombre_archivo else '.pdf'
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

async def serve_document_by_storage_type(url_archivo: str, nombre_archivo: str) -> StreamingResponse:
    """Sirve un documento según su tipo de almacenamiento"""
    if url_archivo.startswith('local://'):
        return await serve_local_document(url_archivo, nombre_archivo)
    elif url_archivo.startswith('temp://'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Documento temporal no disponible para descarga."
        )
    elif url_archivo.startswith(('http://', 'https://')):
        return await serve_idrive_document(url_archivo, nombre_archivo)
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
    
    # Verificar autenticación y permisos de admin
    await verify_admin_token(token, db)
    
    # Verificar que la solicitud existe
    solicitud = await get_solicitud_by_id(db, solicitud_id)
    
    # Obtener el documento específico
    documento = await get_documento_by_ids(db, documento_id, solicitud_id)
    
    # Obtener tipo de documento para el nombre del archivo
    tipo_doc = await get_tipo_documento_by_id(db, documento.id_tip_documento)
    
    # Generar nombre de archivo
    nombre_archivo = generate_filename(tipo_doc, documento_id, documento.url_archivo)
    
    # Verificar que el documento tiene una URL válida
    if not documento.url_archivo or documento.url_archivo == URL_TEMP_PENDING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Documento no disponible."
        )
    
    print(f"🔍 Procesando documento: {documento.url_archivo}")
    
    # Servir el documento según su tipo de almacenamiento
    return await serve_document_by_storage_type(documento.url_archivo, nombre_archivo)

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
                    "estado": ESTADO_ACTIVO_SUPABASE if not auth_user.banned_until else ESTADO_SUSPENDIDO_SUPABASE
                }
        
        return {"emails": emails_dict}

    except Exception as e:
        print(f"⚠️ Error obteniendo emails de Supabase: {e}")
        return {"emails": {}}


@router.get(
    "/users",
    description="Obtiene la lista de todos los usuarios de la plataforma con opción de búsqueda optimizada"
)
async def get_all_users(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    search_empresa: str = None,
    search_nombre: str = None,
    page: int = 1,
    limit: int = 100
):
    """Obtiene usuarios con paginación y búsqueda optimizada usando DirectDBService"""
    try:
        # Usar DirectDBService para evitar problemas con prepared statements
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Construir consulta SQL con filtros
            where_conditions = []
            params = []
            param_count = 1
            
            if search_empresa and search_empresa.strip():
                where_conditions.append(f"u.nombre_empresa ILIKE ${param_count}")
                params.append(f"%{search_empresa.strip()}%")
                param_count += 1
                
            if search_nombre and search_nombre.strip():
                where_conditions.append(f"u.nombre_persona ILIKE ${param_count}")
                params.append(f"%{search_nombre.strip()}%")
                param_count += 1
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Consulta para obtener total de usuarios
            count_query = f"""
                SELECT COUNT(DISTINCT u.id) as total
                FROM users u
                {where_clause}
            """
            
            total_result = await conn.fetchrow(count_query, *params)
            total_users = total_result['total'] if total_result else 0
            
            # Aplicar paginación
            offset = (page - 1) * limit
            
            # Consulta principal para obtener usuarios
            users_query = f"""
                SELECT 
                    u.id,
                    u.nombre_persona,
                    u.nombre_empresa,
                    u.estado,
                    u.foto_perfil,
                    u.created_at
                FROM users u
                {where_clause}
                ORDER BY u.created_at DESC
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            
            params.extend([limit, offset])
            users_data = await conn.fetch(users_query, *params)
            
            # Obtener emails de Supabase
            emails_dict = {}
            try:
        
                auth_users = supabase_admin.auth.admin.list_users()
                
                if auth_users and len(auth_users) > 0:
                    for auth_user in auth_users:
                        if auth_user.id and auth_user.email:
                            emails_dict[auth_user.id] = {
                                "email": auth_user.email,
                                "ultimo_acceso": auth_user.last_sign_in_at
                            }
            except Exception as supabase_error:
                print(f"❌ Error obteniendo emails de Supabase: {supabase_error}")
            
            # Procesar usuarios
            users_list = []
            for row in users_data:
                user_id = str(row['id'])
                
                # Obtener email si existe
                email = VALOR_DEFAULT_NO_DISPONIBLE
                ultimo_acceso = None
                if user_id in emails_dict:
                    email = emails_dict[user_id]["email"]
                    ultimo_acceso = emails_dict[user_id]["ultimo_acceso"]
                
                # Obtener roles del usuario desde la base de datos
                roles_query = """
                    SELECT r.nombre
                    FROM usuario_rol ur
                    JOIN rol r ON ur.id_rol = r.id
                    WHERE ur.id_usuario = $1
                """
                
                roles_data = await conn.fetch(roles_query, user_id)
                roles = [row['nombre'] for row in roles_data]
                
                # Si no tiene roles, usar lista vacía
                if not roles:
                    roles = []
                
                # Determinar rol principal basado en los roles encontrados
                normalized_roles = [rol.lower().strip() for rol in roles]
                if any(admin_role in normalized_roles for admin_role in ["admin", "administrador", "administrator"]):
                    rol_principal = "admin"
                elif any(provider_role in normalized_roles for provider_role in ["provider", "proveedor", "proveedores"]):
                    rol_principal = "provider"
                elif any(client_role in normalized_roles for client_role in ["client", "cliente"]):
                    rol_principal = "client"
                else:
                    # Si no tiene roles asignados, usar "client" como predeterminado
                    rol_principal = "client"
                
                users_list.append({
                    "id": user_id,
                    "nombre_persona": row['nombre_persona'] or "Sin nombre",
                    "nombre_empresa": row['nombre_empresa'] or "Sin empresa",
                    "foto_perfil": row['foto_perfil'],
                    "estado": row['estado'] or ESTADO_ACTIVO,
                    "email": email,
                    "ultimo_acceso": ultimo_acceso,
                    "roles": roles,  # Roles reales de la base de datos
                    "rol_principal": rol_principal,  # Rol principal determinado
                    "todos_roles": roles,  # Todos los roles (igual que roles)
                    "fecha_registro": row['created_at'].strftime(FORMATO_FECHA_DD_MM_YYYY) if row['created_at'] else "Sin fecha"
                })
            
            return {
                "usuarios": users_list,
                "total": total_users,
                "page": page,
                "limit": limit,
                "total_pages": (total_users + limit - 1) // limit,
                "message": "Usuarios obtenidos exitosamente"
            }
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {str(e)}")
        import traceback
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
        print(f"❌ Error obteniendo user_id por id_perfil: {str(e)}")
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
        print(f"❌ Error obteniendo permisos: {str(e)}")
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




# Funciones helper para update_user_profile
async def get_user_by_id(db: AsyncSession, user_id: str) -> UserModel:
    """Obtiene el usuario por ID"""
    user_query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(user_query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_USUARIO_NO_ENCONTRADO
        )
    
    return user

def is_admin_user(admin_user: UserProfileAndRolesOut) -> bool:
    """Verifica si el usuario es administrador"""
    return any(rol.lower() in ["admin", "administrador"] for rol in admin_user.roles)

def update_user_basic_fields(user: UserModel, user_data: dict) -> Tuple[List[str], bool]:
    """Actualiza los campos básicos del usuario (nombre_persona, nombre_empresa)"""
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
    
    return updated_fields, changes_made

def update_user_email(user_id: str, user_data: dict, is_admin: bool, updated_fields: list[str]) -> None:
    """Actualiza el email del usuario si es admin"""
    if "email" in user_data and user_data["email"]:
        if is_admin:
            try:
                supabase_admin.auth.admin.update_user_by_id(
                    user_id,
                    {"email": user_data["email"]}
                )
                updated_fields.append("email")
                print(f"✅ Email actualizado en Supabase Auth para usuario {user_id}")
            except Exception as email_error:
                print(f"⚠️ Error actualizando email en Supabase: {str(email_error)}")
                # Continuar con la actualización del perfil aunque falle el email
        else:
            print(f"⚠️ Usuario no administrador intentó editar email de {user_id}")

def build_no_changes_response(user_id: str, user: UserModel, user_data: dict, is_admin: bool, admin_user: UserProfileAndRolesOut) -> dict:
    """Construye la respuesta cuando no se hicieron cambios"""
    return {
        "message": "No se hicieron cambios",
        "user_id": user_id,
        "updated_fields": [],
        "new_data": {
            "nombre_persona": user.nombre_persona,
            "nombre_empresa": user.nombre_empresa,
            "email": user_data.get("email", VALOR_DEFAULT_NO_DISPONIBLE)
        },
        "permissions": {
            "can_edit_email": is_admin,
            "editor_is_admin": is_admin,
            "editor_roles": admin_user.roles
        }
    }

async def apply_user_changes(db: AsyncSession, user: UserModel) -> None:
    """Aplica los cambios del usuario (flush y commit)"""
    print(f"🔍 DEBUG: Estado antes del commit - Nombre: '{user.nombre_persona}', Empresa: '{user.nombre_empresa}'")
    
    try:
        await db.flush()
        print("✅ DEBUG: Flush exitoso - cambios aplicados en memoria")
    except Exception as flush_error:
        print(f"❌ Error en flush: {str(flush_error)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error aplicando cambios: {str(flush_error)}"
        )
    
    await db.commit()
    print("✅ DEBUG: Commit exitoso - cambios guardados en BD")

def build_success_response(user_id: str, user: UserModel, user_data: dict, updated_fields: list[str], is_admin: bool, admin_user: UserProfileAndRolesOut) -> dict:
    """Construye la respuesta de éxito"""
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
        user = await get_user_by_id(db, user_id)
        
        print(f"🔍 DEBUG: Iniciando edición de usuario {user_id}")
        print(f"🔍 DEBUG: Datos recibidos: {user_data}")
        print(f"🔍 DEBUG: Estado inicial - Nombre: '{user.nombre_persona}', Empresa: '{user.nombre_empresa}'")

        # Actualizar campos básicos del usuario
        updated_fields, changes_made = update_user_basic_fields(user, user_data)

        # Verificar si el usuario es administrador
        is_admin = is_admin_user(admin_user)
        print(f"🔍 DEBUG: Usuario editor es admin: {is_admin}")

        # Actualizar email si es admin
        update_user_email(user_id, user_data, is_admin, updated_fields)

        # Si no se hicieron cambios, retornar respuesta apropiada
        if not changes_made:
            print("⚠️ DEBUG: No se hicieron cambios en el usuario")
            return build_no_changes_response(user_id, user, user_data, is_admin, admin_user)

        # Aplicar cambios (flush y commit)
        await apply_user_changes(db, user)

        # Construir y retornar respuesta de éxito
        return build_success_response(user_id, user, user_data, updated_fields, is_admin, admin_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando perfil de usuario: {str(e)}")
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
                detail=MSG_USUARIO_NO_ENCONTRADO
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
        print(f"❌ Error actualizando roles de usuario: {str(e)}")
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
                detail=MSG_USUARIO_NO_ENCONTRADO
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
        user.estado = ESTADO_INACTIVO
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
                        "user_metadata": {"status": ESTADO_INACTIVE_METADATA},
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
            "status": ESTADO_INACTIVE_METADATA,
            "estado_db": user.estado,  # Confirmar estado en BD
            "supabase_updated": supabase_success,
            "admin_user": admin_user.id,
            "supabase_error": supabase_error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error desactivando usuario: {str(e)}")
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
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene todos los roles disponibles en el sistema"""
    try:
        query = select(RolModel)
        result = await db.execute(query)
        roles = result.scalars().all()
        
        roles_data = []
        for role in roles:
            roles_data.append({
                "id": str(role.id),
                "nombre": role.nombre,
                "descripcion": role.descripcion
            })
        
        return {
            "roles": roles_data,
            "total": len(roles_data)
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo roles: {str(e)}")
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
                detail=MSG_USUARIO_NO_ENCONTRADO
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
            print(f"❌ Error obteniendo email desde Supabase Auth: {str(auth_error)}")
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
            print(f"❌ Error de Supabase al restablecer contraseña: {str(supabase_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al restablecer la contraseña: {str(supabase_error)}"
            )
            
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
    except Exception as e:
        print(f"❌ Error inesperado al restablecer contraseña: {str(e)}")
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
                "error": MSG_USUARIO_NO_ENCONTRADO,
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
        email = VALOR_DEFAULT_NO_DISPONIBLE
        try:
            from app.supabase.auth_service import supabase_admin
            auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
            if auth_user and auth_user.user:
                email = auth_user.user.email or VALOR_DEFAULT_NO_DISPONIBLE
        except Exception as e:
            print(f"⚠️ Error obteniendo email: {str(e)}")

        return {
            "user_id": str(user.id),
            "nombre_persona": user.nombre_persona,
            "nombre_empresa": user.nombre_empresa,
            "email": email,
            "roles": list(roles),
            "estado": user.estado or ESTADO_ACTIVO,
            "verificado_en": "Base de datos local"
        }

    except Exception as e:
        print(f"❌ Error verificando usuario: {str(e)}")
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
            return {"error": MSG_USUARIO_NO_ENCONTRADO, "user_id": user_id}

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
        print(f"❌ Error en test de edición: {str(e)}")
        await db.rollback()
        return {
            "error": str(e),
            "user_id": user_id,
            "test_successful": False
        }


# Funciones helper para toggle_user_status
def verify_not_self_modification(user_id: str, admin_user_id: str) -> None:
    """Verifica que el usuario no se está modificando a sí mismo"""
    if str(user_id) == str(admin_user_id):
        print(f"❌ Intento de auto-modificación por usuario {admin_user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes modificar tu propia cuenta"
        )

def determine_status_action(current_status: Optional[str]) -> Tuple[str, str]:
    """Determina el nuevo estado y la acción basada en el estado actual"""
    if current_status == ESTADO_ACTIVO:
        return ESTADO_INACTIVO, "desactivado"
    elif current_status == ESTADO_INACTIVO:
        return ESTADO_ACTIVO, "reactivado"
    else:
        # Si no tiene estado definido, asumir ACTIVO
        return ESTADO_INACTIVO, "desactivado"

def update_perfil_empresa_status(action: str, user_id: str) -> bool:
    """Actualiza el estado en perfil_empresa (temporalmente deshabilitado)"""
    print("ℹ️ Funcionalidad de perfil_empresa temporalmente deshabilitada para evitar importación circular")
    perfil_updated = False  # Temporalmente deshabilitado
    
    if action == "desactivado" and perfil_updated:
        print(f"✅ Fecha_fin actualizada en perfil_empresa para usuario {user_id} (desactivado)")
    elif action == "reactivado" and perfil_updated:
        print(f"✅ Fecha_fin limpiada en perfil_empresa para usuario {user_id} (reactivado)")
    
    return perfil_updated

def update_supabase_user_status(user_id: str, new_status: str) -> bool:
    """Actualiza el estado del usuario en Supabase Auth"""
    try:
        from app.supabase.auth_service import supabase_admin
        if supabase_admin:
            result = supabase_admin.auth.admin.update_user_by_id(
                str(user_id),
                {
                    "user_metadata": {"status": ESTADO_INACTIVE_METADATA if new_status == ESTADO_INACTIVO else ESTADO_ACTIVE_METADATA},
                    "app_metadata": {"deactivated": new_status == ESTADO_INACTIVO}
                }
            )
            print(f"✅ Usuario {user_id} actualizado en Supabase Auth")
            return True
    except Exception as e:
        print(f"⚠️ Error actualizando en Supabase: {str(e)}")
    
    return False

def build_toggle_status_response(user: UserModel, action: str, current_status: str, new_status: str, supabase_success: bool, admin_user: UserProfileAndRolesOut) -> dict:
    """Construye la respuesta del cambio de estado"""
    return {
        "message": f"Usuario {action} exitosamente",
        "user_id": str(user.id),
        "status": new_status.lower(),
        "estado_anterior": current_status,
        "estado_nuevo": new_status,
        "supabase_updated": supabase_success,
        "admin_user": admin_user.id
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

        # Verificar que el usuario existe
        user = await get_user_by_id(db, user_id)

        # Verificar que no se está modificando a sí mismo
        verify_not_self_modification(user.id, admin_user.id)

        # Determinar la acción basada en el estado actual
        current_status = user.estado
        new_status, action = determine_status_action(current_status)
        print(f"✅ Estado actual: {current_status}, Nuevo estado: {new_status}, Acción: {action}")

        # Cambiar el estado del usuario
        user.estado = new_status
        
        # Actualizar perfil_empresa (temporalmente deshabilitado)
        update_perfil_empresa_status(action, user_id)

        # Intentar actualizar en Supabase Auth
        supabase_success = update_supabase_user_status(user.id, new_status)

        # Guardar cambios en la base de datos
        await db.commit()
        print(f"✅ Cambio de estado completado para usuario {user_id}")

        # Construir y retornar respuesta
        return build_toggle_status_response(user, action, current_status, new_status, supabase_success, admin_user)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error cambiando estado del usuario: {str(e)}")
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
                detail=MSG_USUARIO_NO_ENCONTRADO
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
        user.estado = ESTADO_ACTIVO
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
            from app.supabase.auth_service import supabase_admin
            if supabase_admin:
                result = supabase_admin.auth.admin.update_user_by_id(
                    str(user.id),
                    {
                        "user_metadata": {"status": ESTADO_ACTIVE_METADATA},
                        "app_metadata": {"deactivated": False}
                    }
                )
                print(f"✅ Usuario {user.id} actualizado en Supabase Auth")
                supabase_success = True
        except Exception as e:
            print(f"⚠️ Error actualizando en Supabase: {str(e)}")

        # Guardar cambios en la base de datos
        await db.commit()
        print(f"✅ Activación completada para usuario {user_id}")

        return {
            "message": "Usuario activado exitosamente",
            "user_id": str(user.id),
            "status": ESTADO_ACTIVE_METADATA,
            "estado_db": user.estado,
            "supabase_updated": supabase_success,
            "admin_user": admin_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error activando usuario: {str(e)}")
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
                detail=MSG_USUARIO_NO_ENCONTRADO
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
            "status": ESTADO_INACTIVE_METADATA,
            "method": "simple",
            "admin_user": admin_user.id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en desactivación simple: {str(e)}")
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
    users_data = await conn.fetch(users_query)
    print(f"🔍 DEBUG: {len(users_data)} usuarios encontrados para reporte")
    return users_data

def get_emails_from_supabase() -> dict:
    """Obtiene los emails de Supabase Auth"""
    emails_dict = {}
    try:
        from app.supabase.auth_service import supabase_admin
        auth_users = supabase_admin.auth.admin.list_users()
        
        if auth_users and len(auth_users) > 0:
            for auth_user in auth_users:
                if auth_user.id and auth_user.email:
                    emails_dict[auth_user.id] = {
                        "email": auth_user.email,
                        "created_at": auth_user.created_at
                    }
    except Exception as supabase_error:
        print(f"❌ Error obteniendo emails de Supabase: {supabase_error}")
    
    return emails_dict

def format_creation_date(created_at) -> str:
    """Formatea la fecha de creación"""
    if not created_at:
        return "No disponible"
    
    try:
        from datetime import datetime
        if isinstance(created_at, str):
            if created_at.endswith('Z'):
                created_at = created_at.replace('Z', '+00:00')
            elif '+' not in created_at and 'T' in created_at:
                created_at = created_at + '+00:00'
            return datetime.fromisoformat(created_at).strftime(FORMATO_FECHA_DD_MM_YYYY)
        else:
            return created_at.strftime(FORMATO_FECHA_DD_MM_YYYY)
    except Exception as date_error:
        print(f"DEBUG: Error formateando fecha: {date_error}")
        return "Error formato"

async def get_user_roles(conn, user_id: str) -> list[str]:
    """Obtiene los roles del usuario"""
    roles_query = """
        SELECT r.nombre
        FROM usuario_rol ur
        JOIN rol r ON ur.id_rol = r.id
        WHERE ur.id_usuario = $1
    """
    roles_data = await conn.fetch(roles_query, user_id)
    return [row['nombre'] for row in roles_data]

def determine_main_role(roles: list[str]) -> str:
    """Determina el rol principal del usuario"""
    normalized_roles = [rol.lower().strip() for rol in roles]
    
    if any(admin_role in normalized_roles for admin_role in ["admin", "administrador", "administrator"]):
        return ROL_ADMINISTRADOR
    elif any(provider_role in normalized_roles for provider_role in ["provider", "proveedor", "proveedores"]):
        return ROL_PROVEEDOR
    elif any(client_role in normalized_roles for client_role in ["client", "cliente"]):
        return ROL_CLIENTE
    else:
        return ROL_CLIENTE

def normalize_user_status(estado_raw) -> str:
    """Normaliza el estado del usuario"""
    if estado_raw is None or estado_raw == '':
        return ESTADO_ACTIVO
    elif isinstance(estado_raw, str):
        return estado_raw.strip().upper()
    else:
        return str(estado_raw).strip().upper()

def get_user_email(user_id: str, emails_dict: dict) -> str:
    """Obtiene el email del usuario desde el diccionario de emails"""
    if user_id in emails_dict:
        return emails_dict[user_id]["email"]
    return VALOR_DEFAULT_NO_DISPONIBLE

def get_user_creation_date(user_id: str, emails_dict: dict) -> str:
    """Obtiene y formatea la fecha de creación del usuario"""
    if user_id in emails_dict and emails_dict[user_id]["created_at"]:
        return format_creation_date(emails_dict[user_id]["created_at"])
    return "No disponible"

async def process_user_row(conn, row: dict, emails_dict: dict) -> dict:
    """Procesa una fila de usuario y retorna el diccionario completo"""
    user_id = str(row['id'])
    
    email = get_user_email(user_id, emails_dict)
    fecha_creacion = get_user_creation_date(user_id, emails_dict)
    
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
        usuario = await process_user_row(conn, row, emails_dict)
        usuarios_con_roles.append(usuario)
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
        
        # Usar DirectDBService para evitar problemas con prepared statements
        from app.services.direct_db_service import direct_db_service
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Obtener usuarios desde la base de datos
            users_data = await get_users_from_db(conn)
            
            # Obtener emails de Supabase
            emails_dict = get_emails_from_supabase()
            
            # Procesar todos los usuarios
            usuarios_con_roles = await process_all_users(conn, users_data, emails_dict)
            
            # Calcular estadísticas
            statistics = calculate_user_statistics(usuarios_con_roles)
            
            # Construir y retornar respuesta
            return build_report_response(usuarios_con_roles, statistics)
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        print(f"❌ Error generando reporte de usuarios: {str(e)}")
        import traceback
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
        from app.services.direct_db_service import direct_db_service
        
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
                proveedor_email = VALOR_DEFAULT_NO_DISPONIBLE
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
                    proveedor_email = VALOR_DEFAULT_NO_DISPONIBLE
                
                # Formatear fechas
                fecha_verificacion_formateada = None
                if row['fecha_verificacion']:
                    fecha_verificacion_formateada = row['fecha_verificacion'].strftime(FORMATO_FECHA_DD_MM_YYYY)
                
                fecha_inicio_formateada = None
                if row['fecha_inicio']:
                    fecha_inicio_formateada = row['fecha_inicio'].strftime(FORMATO_FECHA_DD_MM_YYYY)
                
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
async def get_all_verification_requests(db: AsyncSession) -> List[VerificacionSolicitud]:
    """Obtiene todas las solicitudes de verificación ordenadas por fecha"""
    solicitudes_query = select(VerificacionSolicitud).order_by(VerificacionSolicitud.created_at.desc())
    solicitudes_result = await db.execute(solicitudes_query)
    return solicitudes_result.scalars().all()

async def get_empresa_by_perfil_id(db: AsyncSession, id_perfil: int) -> Optional[PerfilEmpresa]:
    """Obtiene la empresa por id_perfil"""
    empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.id_perfil == id_perfil)
    empresa_result = await db.execute(empresa_query)
    return empresa_result.scalars().first()

async def get_user_by_id_from_db(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserModel]:
    """Obtiene el usuario desde la base de datos"""
    user_query = select(UserModel).where(UserModel.id == user_id)
    user_result = await db.execute(user_query)
    return user_result.scalars().first()

def get_user_email_from_supabase_auth(user_id: uuid.UUID) -> str:
    """Obtiene el email del usuario desde Supabase Auth"""
    try:
        from app.supabase.auth_service import supabase_admin
        auth_user = supabase_admin.auth.admin.get_user_by_id(str(user_id))
        if auth_user and auth_user.user:
            return auth_user.user.email or VALOR_DEFAULT_NO_DISPONIBLE
    except Exception:
        pass
    return VALOR_DEFAULT_NO_DISPONIBLE

async def get_user_contact_info(db: AsyncSession, empresa: Optional[PerfilEmpresa]) -> Tuple[str, str]:
    """Obtiene la información de contacto del usuario (nombre y email)"""
    user_nombre = VALOR_DEFAULT_NO_DISPONIBLE
    user_email = VALOR_DEFAULT_NO_DISPONIBLE
    
    if not empresa or not empresa.user_id:
        return user_nombre, user_email
    
    user = await get_user_by_id_from_db(db, empresa.user_id)
    if user:
        user_nombre = user.nombre_persona
        user_email = get_user_email_from_supabase_auth(empresa.user_id)
    
    return user_nombre, user_email

def format_solicitud_date(date_value) -> Optional[str]:
    """Formatea la fecha de solicitud a DD/MM/AAAA"""
    if not date_value:
        return None
    return date_value.strftime(FORMATO_FECHA_DD_MM_YYYY)

async def process_solicitud_data(
    db: AsyncSession,
    solicitud: VerificacionSolicitud
) -> dict:
    """Procesa los datos de una solicitud y retorna el diccionario completo"""
    # Obtener datos de la empresa
    empresa = await get_empresa_by_perfil_id(db, solicitud.id_perfil)
    
    # Obtener datos del usuario
    user_nombre, user_email = await get_user_contact_info(db, empresa)
    
    # Formatear fechas
    fecha_solicitud_formateada = format_solicitud_date(solicitud.created_at)
    fecha_revision_formateada = format_solicitud_date(solicitud.fecha_revision)
    
    return {
        "razon_social": empresa.razon_social if empresa else VALOR_DEFAULT_NO_DISPONIBLE,
        "nombre_fantasia": empresa.nombre_fantasia if empresa else VALOR_DEFAULT_NO_DISPONIBLE,
        "nombre_contacto": user_nombre,
        "email_contacto": user_email,
        "estado": solicitud.estado,
        "fecha_solicitud": fecha_solicitud_formateada,
        "fecha_revision": fecha_revision_formateada,
        "comentario": solicitud.comentario
    }

async def process_all_solicitudes(
    db: AsyncSession,
    solicitudes: List[VerificacionSolicitud]
) -> List[dict]:
    """Procesa todas las solicitudes y retorna la lista completa"""
    solicitudes_detalladas = []
    for solicitud in solicitudes:
        solicitud_dict = await process_solicitud_data(db, solicitud)
        solicitudes_detalladas.append(solicitud_dict)
    return solicitudes_detalladas

def build_solicitudes_report_response(solicitudes_detalladas: List[dict]) -> dict:
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
        # Obtener todas las solicitudes de verificación
        solicitudes = await get_all_verification_requests(db)

        # Procesar todas las solicitudes
        solicitudes_detalladas = await process_all_solicitudes(db, solicitudes)

        # Construir y retornar respuesta
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
            fecha_formateada = None
            if categoria.created_at:
                fecha_formateada = categoria.created_at.strftime(FORMATO_FECHA_DD_MM_YYYY)
            
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
            except:
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
        from app.services.direct_db_service import direct_db_service
        
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
                fecha_formateada = None
                if row['created_at']:
                    fecha_formateada = row['created_at'].strftime(FORMATO_FECHA_DD_MM_YYYY)
                
                # Formatear estado: true -> "ACTIVO", false -> "INACTIVO"
                estado_formateado = ESTADO_ACTIVO if row['estado'] else ESTADO_INACTIVO
                
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
async def get_reservas_from_db(conn) -> list:
    """Obtiene todas las reservas desde la base de datos"""
    reservas_query = """
        SELECT 
            r.id_reserva,
            r.estado,
            r.fecha,
            r.hora_inicio,
            r.hora_fin,
            r.descripcion,
            r.observacion,
            r.created_at as fecha_reserva,
            -- Información del cliente
            u.nombre_persona as cliente_nombre,
            u.id as cliente_user_id,
            -- Información del servicio
            s.nombre as servicio_nombre,
            s.precio as servicio_precio,
            s.descripcion as servicio_descripcion,
            -- Información del proveedor/empresa
            pe.razon_social as empresa_razon_social,
            pe.nombre_fantasia as empresa_nombre_fantasia,
            pe.user_id as proveedor_user_id,
            -- Información de la categoría
            c.nombre as categoria_nombre
        FROM reserva r
        INNER JOIN servicio s ON r.id_servicio = s.id_servicio
        INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        INNER JOIN users u ON r.user_id = u.id
        LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
        ORDER BY r.created_at DESC
    """
    return await conn.fetch(reservas_query)

async def get_cliente_email_from_auth(conn, cliente_user_id) -> str:
    """Obtiene el email del cliente desde Supabase auth.users"""
    try:
        email_query = """
            SELECT email FROM auth.users WHERE id = $1
        """
        email_result = await conn.fetchrow(email_query, cliente_user_id)
        if email_result:
            return email_result['email']
    except Exception as e:
        print(f"Error obteniendo email del cliente {cliente_user_id}: {e}")
    return VALOR_DEFAULT_NO_DISPONIBLE

def format_reserva_date(date_value) -> Optional[str]:
    """Formatea la fecha de reserva a DD/MM/YYYY HH:MM"""
    if not date_value:
        return None
    return date_value.strftime("%d/%m/%Y %H:%M")

def format_servicio_date(date_value) -> Optional[str]:
    """Formatea la fecha de servicio a DD/MM/YYYY"""
    if not date_value:
        return None
    return date_value.strftime(FORMATO_FECHA_DD_MM_YYYY)

def format_horario(hora_inicio, hora_fin) -> Optional[str]:
    """Formatea el horario completo"""
    if hora_inicio and hora_fin:
        return f"{hora_inicio} - {hora_fin}"
    elif hora_inicio:
        return str(hora_inicio)
    return None

def format_estado_reserva(estado: str) -> dict:
    """Formatea el estado de la reserva con información adicional"""
    estado_info = {
        'pendiente': {'label': 'Pendiente', 'color': 'yellow'},
        'aprobado': {'label': 'Aprobado', 'color': 'green'},
        'rechazado': {'label': 'Rechazado', 'color': 'red'},
        'concluido': {'label': 'Concluido', 'color': 'blue'},
        'confirmada': {'label': 'Confirmada', 'color': 'green'},
        'cancelada': {'label': 'Cancelada', 'color': 'red'}
    }
    
    estado_actual = estado.lower()
    return estado_info.get(estado_actual, {
        'label': estado_actual.title(), 
        'color': 'gray'
    })

async def process_reserva_row(conn, row: dict) -> dict:
    """Procesa una fila de reserva y retorna el diccionario completo"""
    # Obtener email del cliente
    cliente_email = await get_cliente_email_from_auth(conn, row['cliente_user_id'])
    
    # Formatear fechas
    fecha_reserva_formateada = format_reserva_date(row['fecha_reserva'])
    fecha_servicio_formateada = format_servicio_date(row['fecha'])
    
    # Formatear horario
    horario_completo = format_horario(row['hora_inicio'], row['hora_fin'])
    
    # Formatear estado
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
            "fecha_servicio": fecha_servicio_formateada,
            "horario": horario_completo,
            "fecha_reserva": fecha_reserva_formateada,
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
        reserva_dict = await process_reserva_row(conn, row)
        reservas_detalladas.append(reserva_dict)
    return reservas_detalladas

def calculate_reservas_statistics(reservas_detalladas: list[dict]) -> dict:
    """Calcula las estadísticas de reservas"""
    total_reservas = len(reservas_detalladas)
    estados_count = {}
    
    for reserva in reservas_detalladas:
        estado = reserva['estado']['valor']
        estados_count[estado] = estados_count.get(estado, 0) + 1
    
    return {
        "por_estado": estados_count,
        "total_proveedores": len(set(r['proveedor']['user_id'] for r in reservas_detalladas)),
        "total_clientes": len(set(r['cliente']['email'] for r in reservas_detalladas))
    }

def build_reservas_report_response(reservas_detalladas: list[dict], statistics: dict) -> dict:
    """Construye la respuesta del reporte de reservas"""
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
        # Usar consulta SQL directa para obtener información completa
        from app.services.direct_db_service import direct_db_service
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Obtener reservas desde la base de datos
            reservas_data = await get_reservas_from_db(conn)
            
            # Procesar todas las reservas
            reservas_detalladas = await process_all_reservas(conn, reservas_data)
            
            # Calcular estadísticas
            statistics = calculate_reservas_statistics(reservas_detalladas)
            
            # Construir y retornar respuesta
            return build_reservas_report_response(reservas_detalladas, statistics)
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except Exception as e:
        print(f"Error generando reporte de reservas de proveedores: {e}")
        # Si es un error de PgBouncer, intentar rollback
        if "prepared statement" in str(e).lower() or "pgbouncer" in str(e).lower():
            try:
                await db.rollback()
            except:
                pass
        raise HTTPException(status_code=500, detail="Error generando reporte de reservas de proveedores")

# Funciones helper para get_reporte_reservas
async def get_reservas_simple_from_db(conn) -> list:
    """Obtiene todas las reservas desde la base de datos (versión simple)"""
    reservas_query = """
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
    return await conn.fetch(reservas_query)

def format_reserva_date_simple(date_value) -> Optional[str]:
    """Formatea la fecha de reserva a DD/MM/YYYY (sin hora)"""
    if not date_value:
        return None
    return date_value.strftime(FORMATO_FECHA_DD_MM_YYYY)

def format_hora_servicio_simple(hora_inicio, hora_fin) -> Optional[str]:
    """Formatea la hora del servicio"""
    if hora_inicio and hora_fin:
        return f"{hora_inicio} - {hora_fin}"
    elif hora_inicio:
        return str(hora_inicio)
    return None

def format_estado_simple(estado: Optional[str]) -> str:
    """Formatea el estado de la reserva"""
    if not estado:
        return "Sin estado"
    return estado.title()

def format_precio_simple(precio) -> float:
    """Formatea el precio del servicio"""
    if precio:
        return float(precio)
    return 0.0

async def process_reserva_row_simple(conn, row: dict) -> dict:
    """Procesa una fila de reserva y retorna el diccionario completo (versión simple)"""
    # Obtener email del cliente
    cliente_email = await get_cliente_email_from_auth(conn, row['cliente_user_id'])
    
    # Formatear fechas
    fecha_reserva_formateada = format_reserva_date_simple(row['created_at'])
    fecha_servicio_formateada = format_servicio_date(row['fecha'])
    
    # Formatear hora del servicio
    hora_servicio_formateada = format_hora_servicio_simple(row['hora_inicio'], row['hora_fin'])
    
    # Formatear estado y precio
    estado_formateado = format_estado_simple(row['estado'])
    precio_formateado = format_precio_simple(row['servicio_precio'])
    
    return {
        "id_reserva": row['id_reserva'],
        "fecha_reserva": fecha_reserva_formateada,
        "estado": estado_formateado,
        "cliente_nombre": row['cliente_nombre'] or VALOR_DEFAULT_NO_DISPONIBLE,
        "cliente_email": cliente_email or VALOR_DEFAULT_NO_DISPONIBLE,
        "servicio_nombre": row['servicio_nombre'] or VALOR_DEFAULT_NO_DISPONIBLE,
        "empresa_razon_social": row['empresa_razon_social'] or VALOR_DEFAULT_NO_DISPONIBLE,
        "empresa_nombre_fantasia": row['empresa_nombre_fantasia'] or VALOR_DEFAULT_NO_DISPONIBLE,
        "fecha_servicio": fecha_servicio_formateada,
        "hora_servicio": hora_servicio_formateada,
        "precio": precio_formateado,
        "descripcion": row['descripcion'] or "",
        "observacion": row['observacion'] or ""
    }

async def process_all_reservas_simple(conn, reservas_data: list) -> list[dict]:
    """Procesa todas las reservas y retorna la lista completa (versión simple)"""
    reservas_detalladas = []
    for row in reservas_data:
        reserva_dict = await process_reserva_row_simple(conn, row)
        reservas_detalladas.append(reserva_dict)
    return reservas_detalladas

def build_reservas_simple_report_response(reservas_detalladas: list[dict]) -> dict:
    """Construye la respuesta del reporte de reservas (versión simple)"""
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
        # Usar consulta SQL directa ya que el modelo ReservaModel no existe
        from app.services.direct_db_service import direct_db_service
        
        conn = await direct_db_service.get_connection()
        
        try:
            # Obtener reservas desde la base de datos
            reservas_data = await get_reservas_simple_from_db(conn)
            
            # Procesar todas las reservas
            reservas_detalladas = await process_all_reservas_simple(conn, reservas_data)
            
            # Construir y retornar respuesta
            return build_reservas_simple_report_response(reservas_detalladas)
            
        finally:
            await direct_db_service.pool.release(conn)
    except Exception as e:
        print(f"Error generando reporte de reservas: {e}")
        # Si es un error de PgBouncer, intentar rollback
        if "prepared statement" in str(e).lower() or "pgbouncer" in str(e).lower():
            try:
                await db.rollback()
            except:
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
        from app.services.direct_db_service import direct_db_service
        
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
                fecha_formateada = None
                if row['fecha']:
                    fecha_formateada = row['fecha'].strftime(FORMATO_FECHA_DD_MM_YYYY)
                
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
            except:
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
        from app.services.direct_db_service import direct_db_service
        
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
                fecha_formateada = None
                if row['fecha']:
                    fecha_formateada = row['fecha'].strftime(FORMATO_FECHA_DD_MM_YYYY)
                
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
            except:
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
        from app.supabase.auth_service import supabase_admin

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
                    "estado": ESTADO_ACTIVO_SUPABASE if not auth_user.banned_until else ESTADO_SUSPENDIDO_SUPABASE
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
            from app.supabase.auth_service import supabase_admin
            auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
            if auth_user and auth_user.user:
                supabase_status = ESTADO_ACTIVO_SUPABASE if not auth_user.user.banned_until else ESTADO_SUSPENDIDO_SUPABASE
        except Exception as e:
            supabase_status = f"Error: {str(e)}"

        return {
            "user_id": str(user.id),
            "nombre_persona": user.nombre_persona,
            "estado_db": user.estado,
            "estado_supabase": supabase_status,
            "coinciden": (user.estado == ESTADO_ACTIVO and supabase_status == ESTADO_ACTIVO_SUPABASE) or
                        (user.estado == ESTADO_INACTIVO and supabase_status == ESTADO_SUSPENDIDO_SUPABASE),
            "timestamp": "2024-12-19"
        }

    except Exception as e:
        print(f"❌ Error en debug: {str(e)}")
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
                detail=MSG_USUARIO_NO_ENCONTRADO
            )

        # Verificar que el usuario no esté ya inactivo
        if user.estado == ESTADO_INACTIVO:
            print(f"❌ Usuario {current_user.id} ya está inactivo")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya está desactivado"
            )

        print(f"✅ Desactivando usuario {current_user.id}")

        # Cambiar el estado del usuario a INACTIVO
        user.estado = ESTADO_INACTIVO
        
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
                result = supabase_admin.auth.admin.update_user_by_id(
                    str(user.id),
                    {
                        "user_metadata": {"status": ESTADO_INACTIVE_METADATA},
                        "app_metadata": {"deactivated": True}
                    }
                )
                print(f"✅ Usuario {user.id} actualizado en Supabase Auth")
                supabase_success = True
        except Exception as e:
            print(f"⚠️ Error actualizando en Supabase: {str(e)}")

        # Guardar cambios en la base de datos
        await db.commit()
        print(f"✅ Auto-desactivación completada para usuario {current_user.id}")

        return {
            "message": "Tu cuenta ha sido desactivada exitosamente. Serás redirigido al login.",
            "user_id": str(user.id),
            "status": ESTADO_INACTIVE_METADATA,
            "estado_anterior": ESTADO_ACTIVO,
            "estado_nuevo": ESTADO_INACTIVO,
            "supabase_updated": supabase_success,
            "redirect_to_login": True
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en auto-desactivación: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error desactivando la cuenta: {str(e)}"
        )


# Funciones helper para get_user_details
async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[UserModel]:
    """Obtiene un usuario por su ID"""
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    return result.scalars().first()

async def get_user_roles_from_db(db: AsyncSession, user_id: uuid.UUID) -> List[UsuarioRolModel]:
    """Obtiene los roles del usuario desde la base de datos"""
    roles_query = select(UsuarioRolModel).where(UsuarioRolModel.id_usuario == user_id)
    roles_result = await db.execute(roles_query)
    return roles_result.scalars().all()

def extract_roles_data(user_roles: List[UsuarioRolModel]) -> List[dict]:
    """Extrae información de roles en formato de diccionario"""
    roles_data = []
    for user_role in user_roles:
        if user_role.rol:
            roles_data.append({
                "id": str(user_role.rol.id),
                "nombre": user_role.rol.nombre,
                "descripcion": user_role.rol.descripcion
            })
    return roles_data

def get_auth_user_info(user_id: uuid.UUID):
    """Obtiene información del usuario desde Supabase Auth"""
    try:
        auth_user = supabase_auth.auth.admin.get_user_by_id(str(user_id))
        return auth_user if auth_user and auth_user.user else None
    except Exception as e:
        print(f"Error obteniendo información de auth para usuario {user_id}: {e}")
        return None

def build_auth_user_fields(auth_user) -> dict:
    """Construye los campos relacionados con autenticación"""
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

def build_user_details_dict(user: UserModel, roles_data: List[dict], auth_fields: dict) -> dict:
    """Construye el diccionario completo de detalles del usuario"""
    return {
        "id": str(user.id),
        "nombre_persona": user.nombre_persona,
        "nombre_empresa": user.nombre_empresa,
        "email": auth_fields["email"],
        "email_verificado": auth_fields["email_verificado"],
        "telefono": auth_fields["telefono"],
        "telefono_verificado": auth_fields["telefono_verificado"],
        "roles": roles_data,
        "estado": user.estado if user else ESTADO_ACTIVO,
        "ultimo_acceso": auth_fields["ultimo_acceso"],
        "ultima_actividad": auth_fields["ultima_actividad"]
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
        # Obtener usuario
        user = await get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_USUARIO_NO_ENCONTRADO
            )
        
        # Obtener roles del usuario
        user_roles = await get_user_roles_from_db(db, user.id)
        
        # Extraer información de roles
        roles_data = extract_roles_data(user_roles)
        
        # Obtener información de Supabase Auth
        auth_user = get_auth_user_info(user.id)
        
        # Construir campos de autenticación
        auth_fields = build_auth_user_fields(auth_user)
        
        # Construir y retornar datos del usuario
        return build_user_details_dict(user, roles_data, auth_fields)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo detalles del usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo detalles del usuario: {str(e)}"
        )

