# app/api/v1/routers/providers/verification_router.py
"""
Router para endpoints de verificación de proveedores.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.api.v1.dependencies.auth_user import get_current_user
from app.api.v1.dependencies.database_supabase import get_async_db
from app.schemas.auth_user import SupabaseUser
from app.services.providers.verification_service import VerificationService
from app.repositories.providers.provider_repository import ProviderRepository
from app.services.providers.address_service import AddressService
from app.services.providers.company_service import CompanyService
from app.api.v1.routers.providers.constants import (
    MSG_ERROR_INTERNO_SERVIDOR,
    MSG_ERROR_INESPERADO
)

router = APIRouter(tags=["providers"])  # Sin prefix - el router principal ya lo tiene


@router.post(
    "/solicitar-verificacion",
    status_code=status.HTTP_201_CREATED,
    description="Registra un perfil de empresa y una solicitud de verificación con documentos adjuntos."
)
async def solicitar_verificacion_completa(
    perfil_in: str = Form(...),
    nombres_tip_documento: List[str] = Form(...),
    documentos: List[UploadFile] = File(...),
    comentario_solicitud: Optional[str] = Form(None),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Registra un perfil de empresa y una solicitud de verificación con documentos adjuntos.
    
    Nota: Este endpoint está disponible en /providers/solicitar-verificacion porque
    verification_router está incluido en el router principal (providers.py).
    
    Las validaciones de negocio se realizan en VerificationService (capa de servicios).
    El router solo maneja la entrada HTTP y delega toda la lógica al servicio.
    """
    try:
        # El router solo recibe y delega - toda la validación y lógica está en el servicio
        result = await VerificationService.process_verification_request(
            perfil_in=perfil_in,
            nombres_tip_documento=nombres_tip_documento,
            documentos=documentos,
            comentario_solicitud=comentario_solicitud,
            current_user_id=current_user.id
        )
        
        return result

    except HTTPException:
        # Re-lanzar excepciones HTTP (validaciones del servicio)
        raise
    except Exception as e:
        # Manejar errores inesperados
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Error inesperado en solicitar_verificacion_completa: {str(e)}")
        print(f"📋 Traceback completo:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=MSG_ERROR_INESPERADO.format(error=str(e))
        )


@router.get(
    "/mis-datos-solicitud",
    description="Obtiene los datos de la solicitud de verificación del proveedor autenticado para recuperación."
)
async def get_mis_datos_solicitud(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene los datos de la solicitud de verificación del proveedor autenticado para recuperación"""
    try:
        empresa = await ProviderRepository.get_empresa_with_sucursales_orm(db, current_user.id)
        solicitud = await ProviderRepository.get_latest_verification_request_orm(db, empresa.id_perfil)
        direccion_data = await AddressService.get_direccion_data(db, empresa.id_direccion)
        sucursal_data = CompanyService.get_sucursal_data(empresa)
        
        # Construir respuesta
        empresa_data = CompanyService.build_empresa_data(empresa, sucursal_data)
        solicitud_data = VerificationService.build_solicitud_data(solicitud)
        
        datos_solicitud = {
            "empresa": empresa_data,
            "direccion": direccion_data,
            "solicitud": solicitud_data
        }
        
        print(f"🔍 Datos de solicitud preparados para usuario {current_user.id}:")
        print(f"  - Empresa: {empresa.razon_social}")
        print(f"  - Dirección: {direccion_data}")
        print(f"  - Estado solicitud: {solicitud.estado}")
        
        return datos_solicitud
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo datos de solicitud: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )

