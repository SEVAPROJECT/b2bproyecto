# app/api/v1/routers/services/category_requests.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.publicar_servicio.solicitud_categoria import SolicitudCategoria
from app.models.publicar_servicio.category import CategoriaModel
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.perfil import UserModel
from app.schemas.publicar_servicio.solicitud_categoria import (
    SolicitudCategoriaIn,
    SolicitudCategoriaOut,
    SolicitudCategoriaWithDetails,
    SolicitudCategoriaUpdate,
    SolicitudCategoriaDecision
)
from app.api.v1.dependencies.auth_user import get_current_user

router = APIRouter(prefix="/category-requests", tags=["Solicitudes de Categorías"])

# Función helper para enriquecer respuesta de solicitud de categoría creada
async def enrich_category_request_response(request: SolicitudCategoria, db: AsyncSession) -> dict:
    """
    Enriquecer la respuesta de una solicitud de categoría con datos adicionales.
    """
    # Consulta para obtener datos completos
    enriched_query = select(
        SolicitudCategoria.id_solicitud,
        SolicitudCategoria.id_perfil,
        SolicitudCategoria.nombre_categoria,
        SolicitudCategoria.descripcion,
        SolicitudCategoria.estado_aprobacion,
        SolicitudCategoria.comentario_admin,
        SolicitudCategoria.created_at,
        PerfilEmpresa.razon_social.label('nombre_empresa'),
        UserModel.nombre_persona.label('nombre_contacto'),
        UserModel.email.label('email_contacto')
    ).select_from(SolicitudCategoria)\
     .join(PerfilEmpresa, SolicitudCategoria.id_perfil == PerfilEmpresa.id_perfil, isouter=True)\
     .join(UserModel, PerfilEmpresa.user_id == UserModel.id, isouter=True)\
     .where(SolicitudCategoria.id_solicitud == request.id_solicitud)

    enriched_result = await db.execute(enriched_query)
    enriched_row = enriched_result.first()

    if enriched_row:
        return {
            "id_solicitud": enriched_row.id_solicitud,
            "id_perfil": enriched_row.id_perfil,
            "nombre_categoria": enriched_row.nombre_categoria,
            "descripcion": enriched_row.descripcion,
            "estado_aprobacion": enriched_row.estado_aprobacion or "pendiente",
            "comentario_admin": enriched_row.comentario_admin,
            "created_at": enriched_row.created_at.isoformat() if enriched_row.created_at else None,
            "nombre_empresa": enriched_row.nombre_empresa or "No especificado",
            "nombre_contacto": enriched_row.nombre_contacto or "No especificado",
            "email_contacto": enriched_row.email_contacto or "No especificado"
        }
    else:
        # Fallback básico si la consulta enriquecida falla
        return {
            "id_solicitud": request.id_solicitud,
            "id_perfil": request.id_perfil,
            "nombre_categoria": request.nombre_categoria,
            "descripcion": request.descripcion,
            "estado_aprobacion": request.estado_aprobacion or "pendiente",
            "comentario_admin": request.comentario_admin,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "nombre_empresa": "No especificado",
            "nombre_contacto": "No especificado",
            "email_contacto": "No especificado"
        }

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Crear una nueva solicitud de categoría"
)
async def create_category_request(
    request: SolicitudCategoriaIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Permite a un proveedor crear una solicitud para agregar una nueva categoría.
    Devuelve la solicitud creada con datos enriquecidos.
    """
    try:
        # Obtener el perfil de empresa del usuario
        perfil_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
        perfil_result = await db.execute(perfil_query)
        perfil = perfil_result.scalars().first()

        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado"
            )

        # Verificar que no existe una categoría con el mismo nombre
        categoria_existente = await db.execute(
            select(CategoriaModel).where(CategoriaModel.nombre.ilike(request.nombre_categoria))
        )
        if categoria_existente.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una categoría con ese nombre"
            )

        # Verificar que no existe una solicitud pendiente con el mismo nombre
        solicitud_existente = await db.execute(
            select(SolicitudCategoria).where(
                SolicitudCategoria.nombre_categoria.ilike(request.nombre_categoria),
                SolicitudCategoria.estado_aprobacion == 'pendiente'
            )
        )
        if solicitud_existente.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una solicitud pendiente para esta categoría"
            )

        # Crear la nueva solicitud
        nueva_solicitud = SolicitudCategoria(
            id_perfil=perfil.id_perfil,
            nombre_categoria=request.nombre_categoria,
            descripcion=request.descripcion,
            estado_aprobacion='pendiente'
        )

        db.add(nueva_solicitud)
        await db.commit()
        await db.refresh(nueva_solicitud)

        # Enriquecer la respuesta con datos adicionales
        enriched_response = await enrich_category_request_response(nueva_solicitud, db)

        print(f"✅ Solicitud de categoría creada: {nueva_solicitud.nombre_categoria}")
        return enriched_response

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"❌ Error al crear solicitud de categoría: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la solicitud: {str(e)}"
        )

@router.get(
    "/",
    response_model=List[SolicitudCategoriaWithDetails],
    status_code=status.HTTP_200_OK,
    description="Obtener solicitudes de categorías del proveedor actual"
)
async def get_my_category_requests(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene las solicitudes de categorías del proveedor actual.
    """
    try:
        # Obtener el perfil de empresa del usuario
        perfil_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
        perfil_result = await db.execute(perfil_query)
        perfil = perfil_result.scalars().first()

        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado"
            )

        # Obtener las solicitudes del proveedor
        query = select(
            SolicitudCategoria.id_solicitud,
            SolicitudCategoria.id_perfil,
            SolicitudCategoria.nombre_categoria,
            SolicitudCategoria.descripcion,
            SolicitudCategoria.estado_aprobacion,
            SolicitudCategoria.comentario_admin,
            SolicitudCategoria.created_at,
            PerfilEmpresa.razon_social.label('nombre_empresa'),
            UserModel.nombre_persona.label('nombre_contacto'),
            PerfilEmpresa.user_id.label('user_id')  # ✅ USAR user_id de PerfilEmpresa
        ).select_from(SolicitudCategoria)\
         .join(PerfilEmpresa, SolicitudCategoria.id_perfil == PerfilEmpresa.id_perfil)\
         .join(UserModel, PerfilEmpresa.user_id == UserModel.id)\
         .where(SolicitudCategoria.id_perfil == perfil.id_perfil)\
         .order_by(SolicitudCategoria.created_at.desc())

        try:
            result = await db.execute(query)
            rows = result.fetchall()
        except Exception as db_error:
            # Manejar errores de PgBouncer
            if "DuplicatePreparedStatementError" in str(db_error):
                print(f"🔄 Error de PgBouncer detectado, reintentando...")
                await db.rollback()
                # Reintentar la consulta
                result = await db.execute(query)
                rows = result.fetchall()
            else:
                raise db_error

        # Formatear respuesta
        formatted_requests = []
        for row in rows:
            formatted_requests.append({
                'id_solicitud': row.id_solicitud,
                'id_perfil': row.id_perfil,
                'nombre_categoria': row.nombre_categoria,
                'descripcion': row.descripcion,
                'estado_aprobacion': row.estado_aprobacion,
                'comentario_admin': row.comentario_admin,
                'created_at': row.created_at,
                'nombre_empresa': row.nombre_empresa,
                'nombre_contacto': row.nombre_contacto,
                'user_id': str(row.user_id) if row.user_id else None,  # ✅ CONVERTIR UUID A STRING
                'email_contacto': None  # Email se obtendrá en el frontend usando user_id
            })

        return formatted_requests

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las solicitudes: {str(e)}"
        )

@router.get(
    "/admin/todas",
    response_model=List[SolicitudCategoriaWithDetails],
    status_code=status.HTTP_200_OK,
    description="Obtener TODAS las solicitudes de categorías para administradores"
)
async def get_all_category_requests_for_admin(
    limit: int = Query(100, description="Límite de solicitudes a retornar"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene todas las solicitudes de categorías para administradores.
    """
    try:
        # Obtener todas las solicitudes con información completa
        query = select(
            SolicitudCategoria.id_solicitud,
            SolicitudCategoria.id_perfil,
            SolicitudCategoria.nombre_categoria,
            SolicitudCategoria.descripcion,
            SolicitudCategoria.estado_aprobacion,
            SolicitudCategoria.comentario_admin,
            SolicitudCategoria.created_at,
            PerfilEmpresa.razon_social.label('nombre_empresa'),
            UserModel.nombre_persona.label('nombre_contacto'),
            PerfilEmpresa.user_id.label('user_id')  # ✅ USAR user_id de PerfilEmpresa
        ).select_from(SolicitudCategoria)\
         .join(PerfilEmpresa, SolicitudCategoria.id_perfil == PerfilEmpresa.id_perfil)\
         .join(UserModel, PerfilEmpresa.user_id == UserModel.id)\
         .order_by(SolicitudCategoria.created_at.desc())

        if limit > 0:
            query = query.limit(limit)

        try:
            result = await db.execute(query)
            rows = result.fetchall()
        except Exception as db_error:
            # Manejar errores de PgBouncer
            if "DuplicatePreparedStatementError" in str(db_error):
                print(f"🔄 Error de PgBouncer detectado, reintentando...")
                await db.rollback()
                # Reintentar la consulta
                result = await db.execute(query)
                rows = result.fetchall()
            else:
                raise db_error

        # Formatear respuesta
        formatted_requests = []
        for row in rows:
            formatted_requests.append({
                'id_solicitud': row.id_solicitud,
                'id_perfil': row.id_perfil,
                'nombre_categoria': row.nombre_categoria,
                'descripcion': row.descripcion,
                'estado_aprobacion': row.estado_aprobacion,
                'comentario_admin': row.comentario_admin,
                'created_at': row.created_at,
                'nombre_empresa': row.nombre_empresa,
                'nombre_contacto': row.nombre_contacto,
                'user_id': str(row.user_id) if row.user_id else None,  # ✅ CONVERTIR UUID A STRING
                'email_contacto': None  # Email se obtendrá en el frontend usando user_id
            })

        return formatted_requests

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las solicitudes: {str(e)}"
        )

@router.put(
    "/{request_id}/approve",
    status_code=status.HTTP_200_OK,
    description="Aprobar una solicitud de categoría y crear la categoría"
)
async def approve_category_request(
    request_id: int,
    decision: SolicitudCategoriaDecision,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Aprueba una solicitud de categoría y crea automáticamente la categoría correspondiente.
    """
    try:
        async with db.begin():
            # Obtener la solicitud
            request_result = await db.execute(
                select(SolicitudCategoria).where(SolicitudCategoria.id_solicitud == request_id)
            )
            request = request_result.scalars().first()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Solicitud no encontrada"
                )

            if request.estado_aprobacion != 'pendiente':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La solicitud ya ha sido procesada"
                )

            # Verificar que no existe una categoría con el mismo nombre
            categoria_existente = await db.execute(
                select(CategoriaModel).where(CategoriaModel.nombre.ilike(request.nombre_categoria))
            )
            if categoria_existente.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una categoría con ese nombre"
                )

            # Crear la nueva categoría
            nueva_categoria = CategoriaModel(
                nombre=request.nombre_categoria,
                estado=True
            )

            db.add(nueva_categoria)
            await db.flush()

            # Actualizar la solicitud
            request.estado_aprobacion = 'aprobada'
            request.comentario_admin = decision.comentario

            return {
                "message": "Solicitud aprobada y categoría creada exitosamente",
                "categoria_id": nueva_categoria.id_categoria,
                "categoria_nombre": nueva_categoria.nombre
            }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aprobar la solicitud: {str(e)}"
        )

@router.put(
    "/{request_id}/reject",
    status_code=status.HTTP_200_OK,
    description="Rechazar una solicitud de categoría"
)
async def reject_category_request(
    request_id: int,
    decision: SolicitudCategoriaDecision,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Rechaza una solicitud de categoría.
    """
    try:
        # Obtener la solicitud
        request_result = await db.execute(
            select(SolicitudCategoria).where(SolicitudCategoria.id_solicitud == request_id)
        )
        request = request_result.scalars().first()

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )

        if request.estado_aprobacion != 'pendiente':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La solicitud ya ha sido procesada"
            )

        # Actualizar la solicitud
        request.estado_aprobacion = 'rechazada'
        request.comentario_admin = decision.comentario

        await db.commit()

        return {"message": "Solicitud rechazada exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al rechazar la solicitud: {str(e)}"
        )

@router.get(
    "/debug/test-query",
    status_code=status.HTTP_200_OK,
    description="Endpoint de prueba para verificar la consulta SQL"
)
async def test_category_query(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Endpoint de prueba para verificar la consulta SQL.
    """
    try:
        # Consulta simple para verificar la estructura
        query = select(
            SolicitudCategoria.id_solicitud,
            SolicitudCategoria.id_perfil,
            PerfilEmpresa.user_id.label('user_id'),
            UserModel.nombre_persona.label('nombre_contacto'),
            PerfilEmpresa.razon_social.label('nombre_empresa')
        ).select_from(SolicitudCategoria)\
         .join(PerfilEmpresa, SolicitudCategoria.id_perfil == PerfilEmpresa.id_perfil)\
         .join(UserModel, PerfilEmpresa.user_id == UserModel.id)\
         .limit(1)

        result = await db.execute(query)
        rows = result.fetchall()
        
        if rows:
            row_dict = dict(rows[0]._mapping)
            return {
                "success": True,
                "data": row_dict,
                "message": "Consulta exitosa"
            }
        else:
            return {
                "success": False,
                "message": "No se encontraron datos"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en la consulta"
        }
