# app/api/v1/routers/providers/services_router.py
"""
Router para endpoints de servicios de proveedores.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.dependencies.auth_user import get_approved_provider
from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.publicar_servicio.solicitud_servicio import SolicitudServicio
from app.models.publicar_servicio.category import CategoriaModel
from app.models.perfil import UserModel
from app.schemas.publicar_servicio.solicitud_servicio import SolicitudServicioIn
from app.api.v1.routers.providers.constants import (
    VALOR_DEFAULT_ESTADO_APROBACION,
    VALOR_DEFAULT_NO_ESPECIFICADO,
    MSG_ERROR_INESPERADO_SERVICIO
)

router = APIRouter(tags=["providers"])  # Sin prefix - el router principal ya lo tiene


async def enrich_service_request_response(request: SolicitudServicio, db: AsyncSession) -> dict:
    """
    Enriquecer la respuesta de una solicitud de servicio con datos adicionales.
    """
    # Consulta para obtener datos completos
    enriched_query = select(
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
     .join(UserModel, PerfilEmpresa.user_id == UserModel.id, isouter=True)\
     .where(SolicitudServicio.id_solicitud == request.id_solicitud)

    enriched_result = await db.execute(enriched_query)
    enriched_row = enriched_result.first()

    if enriched_row:
        return {
            "id_solicitud": enriched_row.id_solicitud,
            "nombre_servicio": enriched_row.nombre_servicio,
            "descripcion": enriched_row.descripcion,
            "estado_aprobacion": enriched_row.estado_aprobacion or VALOR_DEFAULT_ESTADO_APROBACION,
            "comentario_admin": enriched_row.comentario_admin,
            "created_at": enriched_row.created_at.isoformat() if enriched_row.created_at else None,
            "id_categoria": enriched_row.id_categoria,
            "id_perfil": enriched_row.id_perfil,
            "nombre_categoria": enriched_row.nombre_categoria or VALOR_DEFAULT_NO_ESPECIFICADO,
            "nombre_empresa": enriched_row.nombre_empresa or VALOR_DEFAULT_NO_ESPECIFICADO,
            "nombre_contacto": enriched_row.nombre_contacto or VALOR_DEFAULT_NO_ESPECIFICADO,
            "email_contacto": None  # Email no disponible en UserModel
        }
    else:
        # Fallback básico si la consulta enriquecida falla
        return {
            "id_solicitud": request.id_solicitud,
            "nombre_servicio": request.nombre_servicio,
            "descripcion": request.descripcion,
            "estado_aprobacion": request.estado_aprobacion or VALOR_DEFAULT_ESTADO_APROBACION,
            "comentario_admin": request.comentario_admin,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "id_categoria": request.id_categoria,
            "id_perfil": request.id_perfil,
            "nombre_categoria": VALOR_DEFAULT_NO_ESPECIFICADO,
            "nombre_empresa": VALOR_DEFAULT_NO_ESPECIFICADO,
            "nombre_contacto": VALOR_DEFAULT_NO_ESPECIFICADO,
            "email_contacto": None
        }


@router.post(
    "/services/proponer",
    status_code=status.HTTP_201_CREATED,
    description="Permite a un proveedor proponer un nuevo servicio."
)
async def propose_service(
    solicitud: SolicitudServicioIn,
    perfil_aprobado: PerfilEmpresa = Depends(get_approved_provider),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Recibe una propuesta de servicio de un proveedor
    aprobado y la guarda para que el administrador la revise y apruebe o rechace.
    Devuelve la solicitud creada con datos enriquecidos.
    """
    try:
        # Validar longitud de descripción
        if len(solicitud.descripcion) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La descripción no puede superar los 500 caracteres. Por favor, acorta tu descripción."
            )
        
        nueva_solicitud = SolicitudServicio(
            id_perfil=perfil_aprobado.id_perfil,
            nombre_servicio=solicitud.nombre_servicio,
            descripcion=solicitud.descripcion,
            id_categoria=solicitud.id_categoria,
            comentario_admin=solicitud.comentario_admin
        )
        db.add(nueva_solicitud)
        await db.commit()
        await db.refresh(nueva_solicitud)

        # Enriquecer la respuesta con datos adicionales
        enriched_response = await enrich_service_request_response(nueva_solicitud, db)

        print(f"✅ Solicitud de servicio creada: {nueva_solicitud.nombre_servicio}")
        return enriched_response

    except Exception as e:
        await db.rollback()
        print(f"❌ Error al crear solicitud de servicio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INESPERADO_SERVICIO.format(error=str(e))
        )

