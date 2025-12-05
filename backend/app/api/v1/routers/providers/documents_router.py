# app/api/v1/routers/providers/documents_router.py
"""
Router para endpoints de documentos de proveedores.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import mimetypes
import urllib.parse

from app.api.v1.dependencies.auth_user import get_current_user
from app.api.v1.dependencies.database_supabase import get_async_db
from app.schemas.auth_user import SupabaseUser
from app.models.empresa.documento import Documento
from app.models.empresa.tipo_documento import TipoDocumento
from app.services.providers.document_service import DocumentService
from app.repositories.providers.provider_repository import ProviderRepository
from app.supabase.auth_service import supabase_auth
from app.idrive.idrive_service import idrive_s3_client
from app.api.v1.routers.providers.constants import (
    PREFIX_DOCUMENTOS,
    PREFIX_TEMP,
    MSG_DOCUMENTO_NO_ENCONTRADO,
    MSG_DOCUMENTO_NO_DISPONIBLE,
    MSG_ERROR_INTERNO_SERVIDOR,
    MSG_PERFIL_EMPRESA_NO_ENCONTRADO,
    MSG_SOLICITUD_VERIFICACION_NO_ENCONTRADA,
    VALOR_DEFAULT_TIPO_NO_ENCONTRADO
)
from sqlalchemy import select

router = APIRouter(tags=["providers"])  # Sin prefix - el router principal ya lo tiene


def validate_token_and_get_user_id(token: Optional[str]) -> Optional[str]:
    """Valida el token y retorna el ID del usuario"""
    if not token:
        print("⚠️ No se recibió token, continuando sin autenticación...")
        return None
    
    try:
        user_response = supabase_auth.auth.get_user(token)
        if user_response and user_response.user:
            current_user_id = user_response.user.id
            print(f"✅ Token válido para usuario: {current_user_id}")
            return current_user_id
        else:
            print("⚠️ Token inválido, continuando sin validación completa...")
        return None
    except Exception as auth_error:
        print(f"⚠️ Error validando token: {auth_error}, continuando sin validación...")
        return None


def extract_file_key_from_url(url_completa: str) -> str:
    """Extrae la clave del archivo desde la URL completa"""
    if PREFIX_DOCUMENTOS in url_completa:
        file_key = url_completa.split(PREFIX_DOCUMENTOS, 1)[1]
        file_key = urllib.parse.unquote(file_key)
        print(f"🔍 Clave extraída para S3: {file_key}")
        return file_key
    else:
        print(f"⚠️ No se encontró '{PREFIX_DOCUMENTOS}' en la URL, usando URL completa como clave")
        return url_completa


def get_content_type_from_filename(file_key: str) -> str:
    """Determina el tipo de contenido basado en el nombre del archivo"""
    file_name = file_key.split('/')[-1] if '/' in file_key else file_key
    content_type, _ = mimetypes.guess_type(file_name)
    return content_type if content_type else 'application/octet-stream'


def get_file_from_s3(file_key: str) -> bytes:
    """Obtiene el archivo desde S3 usando la clave"""
    print(f"🔍 Intentando acceder a archivo: {file_key}")
    response = idrive_s3_client.get_object(
        Bucket='documentos',
        Key=file_key
    )
    file_content = response['Body'].read()
    print(f"✅ Archivo obtenido exitosamente: {file_key}")
    return file_content


@router.get(
    "/mis-documentos/{documento_id}/servir",
    description="Sirve directamente el archivo de documento del proveedor autenticado."
)
async def servir_mi_documento(
    documento_id: int,
    token: str = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Sirve directamente el archivo de documento del proveedor autenticado"""
    
    try:
        print(f"🔍 Intentando servir documento {documento_id}...")
        print(f"🔍 Token recibido: {token[:20] if token else 'None'}...")

        # Validar token y obtener ID de usuario
        current_user_id = validate_token_and_get_user_id(token)

        # Buscar el documento
        documento = await DocumentService.get_document_by_id(db, documento_id)

        if not documento:
            print(f"❌ Documento {documento_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_DOCUMENTO_NO_ENCONTRADO
            )

        print(f"✅ Documento encontrado: {documento.url_archivo}")

        # Verificar permisos del documento
        await DocumentService.verify_document_permissions(db, documento, current_user_id)
        
        # Verificar que el documento tiene una URL válida
        if not documento.url_archivo or documento.url_archivo.startswith(PREFIX_TEMP):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_DOCUMENTO_NO_DISPONIBLE
            )
        
        # Intentar servir el archivo desde Idrive2
        try:
            url_completa = documento.url_archivo
            print(f"🔍 URL completa del documento: {url_completa}")

            # Extraer clave del archivo desde la URL
            file_key = extract_file_key_from_url(url_completa)
            
            # Obtener archivo desde S3
            file_content = get_file_from_s3(file_key)
            
            # Determinar tipo de contenido
            content_type = get_content_type_from_filename(file_key)
            file_name = file_key.split('/')[-1] if '/' in file_key else file_key
            
            # Devolver el archivo
            return Response(
                content=file_content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename={file_name}"
                }
            )
            
        except Exception as s3_error:
            print(f"❌ Error accediendo a S3: {s3_error}")
            print(f"🔍 URL del archivo: {documento.url_archivo}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_DOCUMENTO_NO_DISPONIBLE
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sirviendo documento: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )


@router.get(
    "/mis-documentos",
    description="Obtiene los documentos de la solicitud de verificación del proveedor autenticado."
)
async def get_mis_documentos(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene los documentos de la solicitud de verificación del proveedor autenticado"""

    try:
        # Buscar el perfil de empresa del usuario
        empresa = await ProviderRepository.get_empresa_with_sucursales_orm(db, current_user.id)
        
        # Buscar la solicitud de verificación más reciente
        solicitud = await ProviderRepository.get_latest_verification_request_orm(db, empresa.id_perfil)
        
        # Obtener documentos de la solicitud
        documentos = await DocumentService.get_documents_by_verification(db, solicitud.id_verificacion)
        
        # Obtener tipos de documento
        documentos_detallados = []
        for doc in documentos:
            # Obtener tipo de documento
            tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == doc.id_tip_documento)
            tipo_doc_result = await db.execute(tipo_doc_query)
            tipo_doc = tipo_doc_result.scalars().first()
            
            documentos_detallados.append({
                "id_documento": doc.id_documento,
                "tipo_documento": tipo_doc.nombre if tipo_doc else VALOR_DEFAULT_TIPO_NO_ENCONTRADO,
                "es_requerido": tipo_doc.es_requerido if tipo_doc else False,
                "estado_revision": doc.estado_revision,
                "url_archivo": doc.url_archivo,
                "fecha_verificacion": doc.fecha_verificacion,
                "observacion": doc.observacion,
                "created_at": doc.created_at
            })
        
        return {
            "solicitud_id": solicitud.id_verificacion,
            "estado": solicitud.estado,
            "documentos": documentos_detallados
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo documentos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )

