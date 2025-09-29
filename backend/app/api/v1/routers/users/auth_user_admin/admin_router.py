# app/api/v1/routers/admin_router.py

from datetime import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
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


@router.get(
    "/verificaciones/pendientes",
    description="Obtiene todas las solicitudes de verificación pendientes."
)
async def get_solicitudes_pendientes(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    # SOLUCIÓN DIRECTA: Obtener solicitudes con información completa
    query = select(VerificacionSolicitud).where(VerificacionSolicitud.estado == "pendiente")
    result = await db.execute(query)
    solicitudes = result.scalars().all()
    
    # Convertir a diccionarios con información completa
    solicitudes_data = []
    for solicitud in solicitudes:
        # Obtener información de la empresa
        empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.id_perfil == solicitud.id_perfil)
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        # Obtener información del usuario (contacto)
        user_nombre = "No disponible"
        user_email = "No disponible"
        if empresa and empresa.user_id:
            user_query = select(UserModel).where(UserModel.id == empresa.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalars().first()
            if user:
                user_nombre = user.nombre_persona or "Usuario sin nombre"
                # Obtener email desde Supabase Auth (igual que en /admin/users)
                try:
                    from app.supabase_client.auth_service import supabase_admin
                    auth_user = supabase_admin.auth.admin.get_user_by_id(str(empresa.user_id))
                    if auth_user and auth_user.user:
                        user_email = auth_user.user.email or "No disponible"
                    else:
                        user_email = "No disponible"
                except Exception as e:
                    print(f"Error obteniendo email para usuario {empresa.user_id}: {e}")
                    user_email = "No disponible"
            
        # Categoría eliminada del detalle de solicitud
        
        # Obtener documentos de la solicitud
        documentos_query = select(Documento).where(Documento.id_verificacion == solicitud.id_verificacion)
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
        
        solicitudes_data.append({
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
        })
    
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
        solicitud.estado = "aprobada"
        from app.services.date_service import DateService
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
            print(f"❌ No se encontró el rol de proveedor")
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
        solicitud.estado = "rechazada"
        from app.services.date_service import DateService
        solicitud.fecha_revision = DateService.now_for_database()
        solicitud.comentario = decision.comentario

        print(f"🔄 Realizando commit de los cambios...")

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
    
    # Verificar autenticación usando el token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    
    try:
        # Verificar que el token es válido usando Supabase directamente
        from app.supabase_client.auth_service import supabase_auth
        
        # Verificar el token con Supabase
        user_response = supabase_auth.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        
        # Verificar que el usuario es admin
        user_id = user_response.user.id
        
        # Buscar el usuario en la base de datos y verificar roles
        from app.models.perfil import UserModel
        from app.models.usuario_rol import UsuarioRolModel
        from app.models.rol import RolModel
        
        user_query = select(UserModel).where(UserModel.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
        
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
            
    except Exception as e:
        print(f"Error de autenticación: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Error de autenticación")
    
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
    
    # Manejar diferentes tipos de almacenamiento
    if documento.url_archivo and documento.url_archivo != 'temp://pending':
        print(f"🔍 Procesando documento: {documento.url_archivo}")
        
        # Caso 1: Documento local (almacenamiento local)
        if documento.url_archivo.startswith('local://'):
            try:
                print(f"📁 Documento local detectado: {documento.url_archivo}")
                
                # Usar el servicio de almacenamiento local
                from app.api.v1.dependencies.local_storage import local_storage_service
                
                # Servir el archivo local
                serve_success, serve_message, file_content = local_storage_service.serve_file(documento.url_archivo)
                
                if serve_success and file_content:
                    print(f"✅ Documento local servido exitosamente: {len(file_content)} bytes")
                    
                    # Determinar el tipo de contenido
                    import mimetypes
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
                else:
                    print(f"❌ Error sirviendo documento local: {serve_message}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error accediendo al documento local: {serve_message}"
                    )
                    
            except Exception as local_error:
                print(f"❌ Error con documento local: {str(local_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error accediendo al documento local: {str(local_error)}"
                )
        
        # Caso 2: Documento temporal
        elif documento.url_archivo.startswith('temp://'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Documento temporal no disponible para descarga."
            )
        
        # Caso 3: Documento en iDrive2 (URL externa)
        elif documento.url_archivo.startswith(('http://', 'https://')):
            try:
                print(f"🌐 Documento iDrive detectado: {documento.url_archivo}")
                
                # Estrategia 1: Intentar con HTTP directo primero
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    response = await client.get(documento.url_archivo)
                    response.raise_for_status()
                    content = response.content
                    print(f"✅ Descarga HTTP exitosa: {len(content)} bytes")
                    
            except Exception as http_error:
                print(f"❌ Error HTTP directo: {str(http_error)}")
                
                # Estrategia 2: Intentar con cliente IDrive2 como fallback
                try:
                    from app.idrive.idrive_service import idrive_s3_client
                    from app.core.config import IDRIVE_BUCKET_NAME
                    
                    print(f"🔄 Intentando con cliente IDrive2...")
                    
                    # Extraer la clave del archivo de la URL
                    url_parts = documento.url_archivo.split('/')
                    
                    # Buscar la clave del archivo (después del dominio)
                    key_parts = []
                    found_bucket = False
                    for part in url_parts:
                        if found_bucket:
                            key_parts.append(part)
                        elif part in ['documentos', 'files', 'uploads'] or (IDRIVE_BUCKET_NAME and IDRIVE_BUCKET_NAME in part):
                            found_bucket = True
                    
                    if not key_parts:
                        raise Exception("No se pudo extraer la clave de la URL")
                    
                    # Usar el cliente de IDrive2
                    key = '/'.join(key_parts)
                    print(f"🔍 Intentando descargar desde IDrive2 con clave: {key}")
                    
                    # Descargar el archivo usando el cliente S3 de IDrive2
                    response = idrive_s3_client.get_object(
                        Bucket=IDRIVE_BUCKET_NAME,
                        Key=key
                    )
                    content = response['Body'].read()
                    print(f"✅ Descarga IDrive2 exitosa: {len(content)} bytes")
                    
                except Exception as idrive_error:
                    print(f"❌ Error con IDrive2: {str(idrive_error)}")
                    
                    # Estrategia 3: Intentar con headers específicos
                    try:
                        print(f"🔄 Intentando con headers específicos...")
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept': 'application/pdf,application/octet-stream,*/*',
                            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'
                        }
                        
                        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                            response = await client.get(documento.url_archivo, headers=headers)
                            response.raise_for_status()
                            content = response.content
                            print(f"✅ Descarga con headers exitosa: {len(content)} bytes")
                            
                    except Exception as final_error:
                        print(f"❌ Error final: {str(final_error)}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"No se pudo acceder al documento. Error: {str(final_error)}"
                        )
            
            # Determinar el tipo de contenido basado en la extensión del archivo
            import mimetypes
            content_type, _ = mimetypes.guess_type(nombre_archivo)
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
            
            # Devolver el archivo como streaming response
            return StreamingResponse(
                iter([content]),
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename={nombre_archivo}",
                    "Content-Type": content_type,
                    "Content-Length": str(len(content))
                }
            )
        
        # Caso 4: URL no reconocida
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Tipo de URL no reconocido: {documento.url_archivo}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Documento no disponible."
        )

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
            from app.supabase_client.auth_service import supabase_admin
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
        from sqlalchemy.future import select
        from app.models.perfil import UserModel
        
        query = select(UserModel.id)
        result = await db.execute(query)
        user_ids = [str(row.id) for row in result.all()]
        
        # Obtener emails de Supabase
        from app.supabase_client.auth_service import supabase_admin
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
        from app.supabase_client.auth_service import supabase_admin
        
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


@router.get(
    "/users",
    description="Obtiene la lista de todos los usuarios de la plataforma con opción de búsqueda optimizada"
)
async def get_all_users(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db),
    search_empresa: str = None,
    search_nombre: str = None,
    page: int = 1,
    limit: int = 100
):
    """Obtiene usuarios con paginación y búsqueda optimizada"""
    try:
        '''print(f"🔍 DEBUG: Endpoint optimizado - Página: {page}, Límite: {limit}")
        print(f"🔍 DEBUG: Búsqueda empresa: {search_empresa}, nombre: {search_nombre}")
        print(f"🔍 DEBUG: Iniciando consulta de base de datos...")'''

        # OPTIMIZACIÓN 1: Consulta completa para funcionalidad completa
        base_query = select(
            UserModel.id,
            UserModel.nombre_persona,
            UserModel.nombre_empresa,
            UserModel.estado,
            UserModel.foto_perfil
        ).select_from(
            UserModel
        )

        # Aplicar filtros de búsqueda
        if search_empresa and search_empresa.strip():
            search_term = f"%{search_empresa.strip()}%"
            base_query = base_query.where(UserModel.nombre_empresa.ilike(search_term))
            print(f"🔍 DEBUG: Filtro empresa aplicado: {search_term}")

        if search_nombre and search_nombre.strip():
            search_term = f"%{search_nombre.strip()}%"
            base_query = base_query.where(UserModel.nombre_persona.ilike(search_term))
            print(f"🔍 DEBUG: Filtro nombre aplicado: {search_term}")

        # OPTIMIZACIÓN 2: Obtener total de registros para paginación
        count_query = select(func.count(func.distinct(UserModel.id)))
        if search_empresa and search_empresa.strip():
            count_query = count_query.where(UserModel.nombre_empresa.ilike(f"%{search_empresa.strip()}%"))
        if search_nombre and search_nombre.strip():
            count_query = count_query.where(UserModel.nombre_persona.ilike(f"%{search_nombre.strip()}%"))

        try:
            total_result = await db.execute(count_query)
            total_users = total_result.scalar()
        except Exception as db_error:
            # Manejar errores de PgBouncer en conteo
            if "DuplicatePreparedStatementError" in str(db_error):
                print(f"🔄 Error de PgBouncer detectado en count_query, reintentando...")
                await db.rollback()
                # Reintentar la consulta de conteo
                total_result = await db.execute(count_query)
                total_users = total_result.scalar()
            else:
                raise db_error

        # OPTIMIZACIÓN 3: Aplicar paginación
        offset = (page - 1) * limit
        base_query = base_query.offset(offset).limit(limit)

        # Ejecutar consulta optimizada
        print("🔍 DEBUG: Ejecutando consulta de base de datos...")
        try:
            result = await db.execute(base_query)
            users_with_roles = result.all()
            print("🔍 DEBUG: Consulta de base de datos completada")
        except Exception as db_error:
            # Manejar errores de PgBouncer
            if "DuplicatePreparedStatementError" in str(db_error):
                print(f"🔄 Error de PgBouncer detectado en get_all_users, reintentando...")
                await db.rollback()
                # Reintentar la consulta
                result = await db.execute(base_query)
                users_with_roles = result.all()
                print("🔍 DEBUG: Consulta de base de datos completada después del reintento")
            else:
                raise db_error

        print(f"🔍 DEBUG: {len(users_with_roles)} registros obtenidos de {total_users} totales")

        # OPTIMIZACIÓN 4: Obtener todos los emails de Supabase de una vez
        print("🔍 DEBUG: Obteniendo usuarios de Supabase...")
        try:
            from app.supabase_client.auth_service import supabase_admin
            auth_users = supabase_admin.auth.admin.list_users()
            print(f"🔍 DEBUG: Supabase devolvió {len(auth_users) if auth_users else 0} usuarios")
            
            emails_dict = {}
            if auth_users and len(auth_users) > 0:
                for auth_user in auth_users:
                    if auth_user.id and auth_user.email:
                        emails_dict[auth_user.id] = {
                            "email": auth_user.email,
                            "ultimo_acceso": auth_user.last_sign_in_at
                        }
                print(f"🔍 DEBUG: {len(emails_dict)} emails obtenidos de Supabase")
            else:
                print("⚠️ DEBUG: No se obtuvieron usuarios de Supabase")
        except Exception as supabase_error:
            print(f"❌ DEBUG: Error en Supabase: {str(supabase_error)}")
            emails_dict = {}

        # OPTIMIZACIÓN 5: Procesar resultados agrupados por usuario
        users_dict = {}
        for row in users_with_roles:
            user_id = str(row.id)
            
            if user_id not in users_dict:
                # Crear usuario base
                users_dict[user_id] = {
                    "id": user_id,
                    "nombre_persona": row.nombre_persona,
                    "nombre_empresa": row.nombre_empresa,
                    "foto_perfil": row.foto_perfil,
                    "estado": row.estado or "ACTIVO",
                    "roles": [],
                    "rol_principal": "client",
                    "email": "No disponible",
                    "ultimo_acceso": None
                }

                # Agregar email si existe
                if user_id in emails_dict:
                    users_dict[user_id]["email"] = emails_dict[user_id]["email"]
                    users_dict[user_id]["ultimo_acceso"] = emails_dict[user_id]["ultimo_acceso"]

            # Agregar rol por defecto (consulta simplificada)
            if not users_dict[user_id]["roles"]:
                users_dict[user_id]["roles"] = ["Usuario"]

        # OPTIMIZACIÓN 6: Determinar rol principal para cada usuario
        users_data = []
        for user_id, user_data in users_dict.items():
            roles = user_data["roles"]
            user_data["todos_roles"] = roles.copy()

            # Determinar rol principal
            normalized_roles = [rol.lower().strip() for rol in roles]
            if any(admin_role in normalized_roles for admin_role in ["admin", "administrador", "administrator"]):
                user_data["rol_principal"] = "admin"
            elif any(provider_role in normalized_roles for provider_role in ["provider", "proveedor", "proveedores"]):
                user_data["rol_principal"] = "provider"
            elif any(client_role in normalized_roles for client_role in ["client", "cliente"]):
                user_data["rol_principal"] = "client"
            else:
                user_data["rol_principal"] = "client"

            users_data.append(user_data)

        print(f"🔍 DEBUG: Procesamiento completado, {len(users_data)} usuarios listos")

        return {
            "usuarios": users_data,
            "total": total_users,
            "page": page,
            "limit": limit,
            "total_pages": (total_users + limit - 1) // limit,
            "message": "Usuarios obtenidos exitosamente"
        }

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
        from app.models.perfil_empresa import PerfilEmpresaModel
        
        # Consulta simple para obtener user_id por id_perfil
        query = select(PerfilEmpresaModel.user_id).where(PerfilEmpresaModel.id_perfil == id_perfil)
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
                    from app.supabase_client.auth_service import supabase_admin
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
            print(f"❌ Error en flush: {str(flush_error)}")
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
            from app.supabase_client.auth_service import supabase_admin

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
                detail="Usuario no encontrado"
            )
        
        print(f"✅ Usuario encontrado: {user.nombre_persona}")
        
        # Obtener el email del usuario desde Supabase Auth
        from app.supabase_client.auth_service import supabase_admin
        
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
        import secrets
        import string
        
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
            from app.supabase_client.auth_service import supabase_admin
            auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
            if auth_user and auth_user.user:
                email = auth_user.user.email or "No disponible"
        except Exception as e:
            print(f"⚠️ Error obteniendo email: {str(e)}")

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
        print(f"❌ Error en test de edición: {str(e)}")
        await db.rollback()
        return {
            "error": str(e),
            "user_id": user_id,
            "test_successful": False
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

        # Determinar la acción basada en el estado actual
        current_status = user.estado
        if current_status == "ACTIVO":
            new_status = "INACTIVO"
            action = "desactivado"
        elif current_status == "INACTIVO":
            new_status = "ACTIVO"
            action = "reactivado"
        else:
            # Si no tiene estado definido, asumir ACTIVO
            new_status = "INACTIVO"
            action = "desactivado"

        print(f"✅ Estado actual: {current_status}, Nuevo estado: {new_status}, Acción: {action}")

        # Cambiar el estado del usuario
        user.estado = new_status
        
        # Actualizar fecha_fin en perfil_empresa según la acción
        # from app.services.perfil_empresa_service import PerfilEmpresaService  # Comentado temporalmente
        # if action == "desactivado":
        #     perfil_updated = await PerfilEmpresaService.deactivate_user_profile(db, user_id)
        #     if perfil_updated:
        print(f"ℹ️ Funcionalidad de perfil_empresa temporalmente deshabilitada para evitar importación circular")
        if action == "desactivado":
            perfil_updated = False  # Temporalmente deshabilitado
            if perfil_updated:
                print(f"✅ Fecha_fin actualizada en perfil_empresa para usuario {user_id} (desactivado)")
        elif action == "reactivado":
            # perfil_updated = await PerfilEmpresaService.reactivate_user_profile(db, user_id)  # Comentado temporalmente
            perfil_updated = False  # Temporalmente deshabilitado
            if perfil_updated:
                print(f"✅ Fecha_fin limpiada en perfil_empresa para usuario {user_id} (reactivado)")

        # Intentar actualizar en Supabase Auth también
        supabase_success = False
        try:
            from app.supabase_client.auth_service import supabase_admin
            if supabase_admin:
                result = supabase_admin.auth.admin.update_user_by_id(
                    str(user.id),
                    {
                        "user_metadata": {"status": "inactive" if new_status == "INACTIVO" else "active"},
                        "app_metadata": {"deactivated": new_status == "INACTIVO"}
                    }
                )
                print(f"✅ Usuario {user.id} actualizado en Supabase Auth")
                supabase_success = True
        except Exception as e:
            print(f"⚠️ Error actualizando en Supabase: {str(e)}")

        # Guardar cambios en la base de datos
        await db.commit()
        print(f"✅ Cambio de estado completado para usuario {user_id}")

        return {
            "message": f"Usuario {action} exitosamente",
            "user_id": str(user.id),
            "status": new_status.lower(),
            "estado_anterior": current_status,
            "estado_nuevo": new_status,
            "supabase_updated": supabase_success,
            "admin_user": admin_user.id
        }

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
            from app.supabase_client.auth_service import supabase_admin
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
            print(f"⚠️ Error actualizando en Supabase: {str(e)}")

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
        print(f"❌ Error en desactivación simple: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error desactivando usuario: {str(e)}"
        )


@router.get(
    "/reports/usuarios-activos",
    description="Genera reporte de todos los usuarios (activos e inactivos)"
)
async def get_reporte_usuarios_activos(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte de todos los usuarios (activos e inactivos) con rol principal"""
    try:
        print("🔍 DEBUG: Generando reporte de todos los usuarios...")
        
        # Obtener TODOS los usuarios (activos e inactivos) - mismo enfoque que /users
        from sqlalchemy.future import select
        user_query = select(UserModel.id, UserModel.nombre_persona, UserModel.nombre_empresa, UserModel.estado)
        user_result = await db.execute(user_query)
        users = user_result.all()

        print(f"🔍 DEBUG: {len(users)} usuarios encontrados para reporte")

        # Procesar usuarios uno por uno
        usuarios_con_roles = []
        for user_row in users:
            user_id = str(user_row.id)
            print(f"🔍 DEBUG: Procesando usuario {user_id} para reporte")

            # Crear objeto usuario básico
            user_data = {
                "id": user_id,
                "nombre_persona": user_row.nombre_persona,
                "nombre_empresa": user_row.nombre_empresa,
                "email": "No disponible",
                "estado": user_row.estado or "ACTIVO",
                "rol_principal": "Cliente",  # Valor por defecto
                "fecha_creacion": None
            }

            # Obtener email y fecha de creación desde Supabase Auth
            try:
                from app.supabase_client.auth_service import supabase_admin
                auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)

                if auth_user and auth_user.user:
                    user_data["email"] = auth_user.user.email or "No disponible"
                    
                    # Formatear fecha de creación a DD/MM/AAAA
                    if auth_user.user.created_at:
                        from datetime import datetime
                        try:
                            created_at_str = str(auth_user.user.created_at)
                            print(f"DEBUG: Fecha original para {user_row.nombre_persona}: {created_at_str}")
                            
                            # Limpiar y formatear la fecha
                            if created_at_str.endswith('Z'):
                                created_at_str = created_at_str.replace('Z', '+00:00')
                            elif '+' not in created_at_str and 'T' in created_at_str:
                                created_at_str = created_at_str + '+00:00'
                            
                            fecha_creacion = datetime.fromisoformat(created_at_str)
                            user_data["fecha_creacion"] = fecha_creacion.strftime("%d/%m/%Y")
                            print(f"DEBUG: Usuario {user_row.nombre_persona} - Fecha formateada: {user_data['fecha_creacion']}")
                        except Exception as date_error:
                            print(f"DEBUG: Error formateando fecha para {user_row.nombre_persona}: {date_error}")
                            user_data["fecha_creacion"] = "Error formato"
                    else:
                        print(f"DEBUG: Usuario {user_row.nombre_persona} - No tiene created_at")
                        user_data["fecha_creacion"] = "No disponible"

            except Exception as e:
                print(f"DEBUG: Error obteniendo datos de Supabase para usuario {user_row.nombre_persona}: {e}")
                user_data["fecha_creacion"] = "No disponible"

            # Obtener rol principal (misma lógica que /users)
            try:
                roles_query = select(RolModel.nombre).select_from(
                    UsuarioRolModel
                ).join(
                    RolModel, UsuarioRolModel.id_rol == RolModel.id
                ).where(
                    UsuarioRolModel.id_usuario == user_row.id
                )

                roles_result = await db.execute(roles_query)
                roles = roles_result.scalars().all()

                # Determinar rol principal (usar lógica de mapeo consistente)
                normalized_roles = [rol.lower().strip() for rol in roles]
                if any(admin_role in normalized_roles for admin_role in ["admin", "administrador", "administrator"]):
                    user_data["rol_principal"] = "Administrador"
                elif any(provider_role in normalized_roles for provider_role in ["provider", "proveedor", "proveedores"]):
                    user_data["rol_principal"] = "Proveedor"
                elif any(client_role in normalized_roles for client_role in ["client", "cliente"]):
                    user_data["rol_principal"] = "Cliente"
                else:
                    user_data["rol_principal"] = "Cliente"

                print(f"🔍 DEBUG: Usuario {user_id} - Rol principal: {user_data['rol_principal']}")

            except Exception as role_error:
                print(f"⚠️ Error obteniendo roles para usuario {user_id}: {str(role_error)}")
                user_data["rol_principal"] = "Cliente"

            usuarios_con_roles.append(user_data)

        print(f"🔍 DEBUG: Reporte generado con {len(usuarios_con_roles)} usuarios")

        return {
            "total_usuarios": len(usuarios_con_roles),
            "usuarios": usuarios_con_roles,
            "fecha_generacion": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error generando reporte de usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte")

@router.get(
    "/reports/proveedores-verificados",
    description="Genera reporte de proveedores verificados"
)
async def get_reporte_proveedores_verificados(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte de proveedores verificados"""
    try:
        # Obtener empresas verificadas
        empresas_query = select(PerfilEmpresa).where(PerfilEmpresa.verificado == True)
        empresas_result = await db.execute(empresas_query)
        empresas = empresas_result.scalars().all()

        proveedores_verificados = []
        for empresa in empresas:
            # Obtener datos del usuario
            user_query = select(UserModel).where(UserModel.id == empresa.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalars().first()

            # Obtener email desde Supabase
            user_email = "No disponible"
            try:
                from app.supabase_client.auth_service import supabase_admin
                auth_user = supabase_admin.auth.admin.get_user_by_id(str(empresa.user_id))
                if auth_user and auth_user.user:
                    user_email = auth_user.user.email or "No disponible"
            except:
                pass

            # Formatear fecha de verificación a DD/MM/AAAA
            fecha_verificacion_formateada = None
            if empresa.fecha_verificacion:
                fecha_verificacion_formateada = empresa.fecha_verificacion.strftime("%d/%m/%Y")
            
            # Formatear fecha de inicio a DD/MM/AAAA
            fecha_inicio_formateada = None
            if empresa.fecha_inicio:
                fecha_inicio_formateada = empresa.fecha_inicio.strftime("%d/%m/%Y")

            proveedores_verificados.append({
                "razon_social": empresa.razon_social,
                "nombre_fantasia": empresa.nombre_fantasia,
                "nombre_contacto": user.nombre_persona if user else "No disponible",
                "email_contacto": user_email,
                "estado": empresa.estado,
                "fecha_inicio": fecha_inicio_formateada
            })

        return {
            "total_proveedores": len(proveedores_verificados),
            "proveedores": proveedores_verificados,
            "fecha_generacion": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error generando reporte de proveedores verificados: {e}")
        # Si es un error de PgBouncer, intentar rollback
        if "prepared statement" in str(e).lower() or "pgbouncer" in str(e).lower():
            try:
                await db.rollback()
            except:
                pass
        raise HTTPException(status_code=500, detail="Error generando reporte")

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
        solicitudes_query = select(VerificacionSolicitud).order_by(VerificacionSolicitud.created_at.desc())
        solicitudes_result = await db.execute(solicitudes_query)
        solicitudes = solicitudes_result.scalars().all()

        solicitudes_detalladas = []
        for solicitud in solicitudes:
            # Obtener datos de la empresa
            empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.id_perfil == solicitud.id_perfil)
            empresa_result = await db.execute(empresa_query)
            empresa = empresa_result.scalars().first()

            # Obtener datos del usuario
            user_nombre = "No disponible"
            user_email = "No disponible"
            if empresa and empresa.user_id:
                user_query = select(UserModel).where(UserModel.id == empresa.user_id)
                user_result = await db.execute(user_query)
                user = user_result.scalars().first()
                
                if user:
                    user_nombre = user.nombre_persona
                    # Obtener email desde Supabase
                    try:
                        from app.supabase_client.auth_service import supabase_admin
                        auth_user = supabase_admin.auth.admin.get_user_by_id(str(empresa.user_id))
                        if auth_user and auth_user.user:
                            user_email = auth_user.user.email or "No disponible"
                    except:
                        pass

            # Formatear fecha de solicitud a DD/MM/AAAA
            fecha_solicitud_formateada = None
            if solicitud.created_at:
                fecha_solicitud_formateada = solicitud.created_at.strftime("%d/%m/%Y")
            
            # Formatear fecha de revisión a DD/MM/AAAA
            fecha_revision_formateada = None
            if solicitud.fecha_revision:
                fecha_revision_formateada = solicitud.fecha_revision.strftime("%d/%m/%Y")

            solicitudes_detalladas.append({
                "razon_social": empresa.razon_social if empresa else "No disponible",
                "nombre_fantasia": empresa.nombre_fantasia if empresa else "No disponible",
                "nombre_contacto": user_nombre,
                "email_contacto": user_email,
                "estado": solicitud.estado,
                "fecha_solicitud": fecha_solicitud_formateada,
                "fecha_revision": fecha_revision_formateada,
                "comentario": solicitud.comentario
            })

        return {
            "total_solicitudes": len(solicitudes_detalladas),
            "solicitudes": solicitudes_detalladas,
            "fecha_generacion": datetime.now().isoformat()
        }
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
                fecha_formateada = categoria.created_at.strftime("%d/%m/%Y")
            
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
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Genera reporte de servicios en la plataforma"""
    try:
        # Obtener todos los servicios con información de empresa y categoría
        servicios_query = select(
            ServicioModel,
            PerfilEmpresa.razon_social,
            PerfilEmpresa.nombre_fantasia,
            CategoriaModel.nombre.label('categoria_nombre')
        ).join(
            PerfilEmpresa, ServicioModel.id_perfil == PerfilEmpresa.id_perfil
        ).join(
            CategoriaModel, ServicioModel.id_categoria == CategoriaModel.id_categoria
        ).order_by(ServicioModel.created_at.desc())
        
        servicios_result = await db.execute(servicios_query)
        servicios_data = servicios_result.all()

        servicios_detallados = []
        for row in servicios_data:
            servicio = row.Servicio
            
            # Formatear fecha a DD/MM/AAAA
            fecha_formateada = None
            if hasattr(servicio, 'created_at') and servicio.created_at:
                fecha_formateada = servicio.created_at.strftime("%d/%m/%Y")
            
            # Formatear estado: true -> "Activa", false -> "Inactiva"
            estado_formateado = "Activa" if servicio.estado else "Inactiva"
            
            servicios_detallados.append({
                "nombre": servicio.nombre,
                "descripcion": servicio.descripcion,
                "precio": float(servicio.precio) if servicio.precio else 0,
                "estado": estado_formateado,
                "empresa": row.razon_social,
                "nombre_fantasia": row.nombre_fantasia,
                "categoria": row.categoria_nombre,
                "fecha_creacion": fecha_formateada
            })

        return {
            "total_servicios": len(servicios_detallados),
            "servicios": servicios_detallados,
            "fecha_generacion": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error generando reporte de servicios: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte")

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
        from app.supabase_client.auth_service import supabase_admin

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
            from app.supabase_client.auth_service import supabase_admin
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
            from app.supabase_client.auth_service import supabase_admin
            if supabase_admin:
                result = supabase_admin.auth.admin.update_user_by_id(
                    str(user.id),
                    {
                        "user_metadata": {"status": "inactive"},
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
            "status": "inactive",
            "estado_anterior": "ACTIVO",
            "estado_nuevo": "INACTIVO",
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
        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Obtener roles del usuario en una consulta separada
        roles_query = select(UsuarioRolModel).where(UsuarioRolModel.id_usuario == user.id)
        roles_result = await db.execute(roles_query)
        user_roles = roles_result.scalars().all()
        
        # Extraer información de roles
        roles_data = []
        for user_role in user_roles:
            if user_role.rol:
                roles_data.append({
                    "id": str(user_role.rol.id),
                    "nombre": user_role.rol.nombre,
                    "descripcion": user_role.rol.descripcion
                })
        
        # Obtener información de Supabase Auth
        try:
            from app.supabase_client.auth_service import supabase_auth
            auth_user = supabase_auth.auth.admin.get_user_by_id(str(user.id))
            
            user_data = {
                "id": str(user.id),
                "nombre_persona": user.nombre_persona,
                "nombre_empresa": user.nombre_empresa,
                "email": auth_user.user.email if auth_user and auth_user.user else "No disponible",
                "email_verificado": auth_user.user.email_confirmed_at is not None if auth_user and auth_user.user else False,
                "telefono": auth_user.user.phone if auth_user and auth_user.user else None,
                "telefono_verificado": auth_user.user.phone_confirmed_at is not None if auth_user and auth_user.user else False,
                "roles": roles_data,
                "estado": user.estado if user else "ACTIVO",
                "ultimo_acceso": auth_user.user.last_sign_in_at if auth_user and auth_user.user else None,
                "ultima_actividad": auth_user.user.last_sign_in_at if auth_user and auth_user.user else None
            }
            
        except Exception as e:
            print(f"Error obteniendo información de auth para usuario {user.id}: {e}")
            user_data = {
                "id": str(user.id),
                "nombre_persona": user.nombre_persona,
                "nombre_empresa": user.nombre_empresa,
                "email": "No disponible",
                "email_verificado": False,
                "telefono": None,
                "telefono_verificado": False,
                "roles": roles_data,
                "estado": user.estado if user else "ACTIVO",
                "ultimo_acceso": None,
                "ultima_actividad": None
            }
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo detalles del usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo detalles del usuario: {str(e)}"
        )

