# app/api/v1/routers/providers/providers.py
"""
Router principal para proveedores.
Consolida todos los routers de proveedores en un solo router.
"""

from fastapi import APIRouter, HTTPException, status, Response
import mimetypes
import urllib.parse

from app.api.v1.dependencies.local_storage import local_storage_service
from app.api.v1.routers.providers.constants import (
    PREFIX_LOCAL,
    MSG_URL_INVALIDA_LOCAL,
    MSG_ARCHIVO_NO_ENCONTRADO,
    MSG_ERROR_SIRVIENDO_ARCHIVO,
    MSG_ERROR_INESPERADO_GENERAL
)

# Importar routers específicos
from app.api.v1.routers.providers.verification_router import router as verification_router
from app.api.v1.routers.providers.documents_router import router as documents_router
from app.api.v1.routers.providers.services_router import router as services_router
from app.api.v1.routers.providers.diagnostic_router import router as diagnostic_router

# Crear router principal
router = APIRouter(prefix="/providers", tags=["providers"])

# Incluir todos los routers específicos
# Nota: Los endpoints de estos routers estarán disponibles bajo /providers/
# Ejemplo: verification_router tiene "/solicitar-verificacion" → disponible en /providers/solicitar-verificacion
router.include_router(verification_router)  # Incluye: /solicitar-verificacion, /mis-datos-solicitud
router.include_router(documents_router)      # Incluye: /mis-documentos, /mis-documentos/{id}/servir
router.include_router(services_router)      # Incluye: /services/proponer
router.include_router(diagnostic_router)    # Incluye: /diagnostic, /diagnostic/storage


@router.get(
    "/download-document/{document_url:path}",
    description="Descarga un documento almacenado localmente"
)
async def download_document(document_url: str):
    """
    Endpoint para descargar documentos almacenados localmente
    """
    try:
        # Decodificar la URL del documento
        decoded_url = urllib.parse.unquote(document_url)
        
        # Verificar que sea una URL local
        if not decoded_url.startswith(PREFIX_LOCAL):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_URL_INVALIDA_LOCAL
            )
        
        # Obtener información del archivo
        success, message, file_info = local_storage_service.get_file_info(decoded_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_ARCHIVO_NO_ENCONTRADO.format(message=message)
            )
        
        # Servir el archivo
        serve_success, serve_message, file_content = local_storage_service.serve_file(decoded_url)
        
        if not serve_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=MSG_ERROR_SIRVIENDO_ARCHIVO.format(serve_message=serve_message)
            )
        
        # Obtener el nombre del archivo original
        filename = file_info["filename"] if file_info else "documento"
        
        # Determinar el tipo de contenido
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"
        
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INESPERADO_GENERAL.format(error=str(e))
        )


