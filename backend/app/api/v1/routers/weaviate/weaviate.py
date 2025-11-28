"""
Endpoints para operaciones con Weaviate
Búsquedas semánticas y recomendaciones
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from app.services.weaviate_service import weaviate_service
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weaviate", tags=["weaviate"])

@router.get(
    "/status",
    description="Verificar el estado de la conexión con Weaviate"
)
async def get_weaviate_status():
    """Verificar si Weaviate está disponible y configurado"""
    try:
        stats = weaviate_service.get_stats()
        return {
            "status": "connected" if "error" not in stats else "error",
            "details": stats
        }
    except Exception as e:
        logger.error(f"❌ Error al verificar estado de Weaviate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar Weaviate: {str(e)}"
        )

@router.post(
    "/index-servicios",
    description="Indexar todos los servicios en Weaviate"
)
async def index_servicios(
    limit: int = Query(100, ge=1, le=1000),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Indexar servicios desde la base de datos a Weaviate"""
    try:
        logger.info(f"🔍 Iniciando indexación de servicios por usuario: {current_user.id}")
        
        success = await weaviate_service.index_servicios(limit=limit)
        
        if success:
            return {
                "message": "Servicios indexados exitosamente",
                "limit": limit,
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al indexar servicios"
            )
            
    except Exception as e:
        logger.error(f"❌ Error en indexación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al indexar servicios: {str(e)}"
        )

@router.get(
    "/search",
    description="Buscar servicios usando búsqueda semántica"
)
async def search_servicios(
    query: str = Query(..., description="Texto de búsqueda semántica"),
    limit: int = Query(10, ge=1, le=50),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Buscar servicios usando búsqueda semántica con Weaviate"""
    try:
        logger.info(f"🔍 Búsqueda semántica: '{query}' por usuario: {current_user.id}")
        
        resultados = weaviate_service.search_servicios(query=query, limit=limit)
        
        return {
            "query": query,
            "results": resultados,
            "total": len(resultados),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda semántica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
        )

@router.get(
    "/servicio/{servicio_id}",
    description="Obtener un servicio específico del índice de Weaviate"
)
async def get_servicio_weaviate(
    servicio_id: int,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Obtener un servicio específico del índice de Weaviate"""
    try:
        servicio = weaviate_service.get_servicio_by_id(servicio_id)
        
        if servicio:
            return {
                "servicio": servicio,
                "found": True
            }
        else:
            return {
                "servicio": None,
                "found": False,
                "message": f"Servicio {servicio_id} no encontrado en el índice"
            }
            
    except Exception as e:
        logger.error(f"❌ Error al obtener servicio {servicio_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servicio: {str(e)}"
        )

@router.delete(
    "/servicio/{servicio_id}",
    description="Eliminar un servicio del índice de Weaviate"
)
async def delete_servicio_weaviate(
    servicio_id: int,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Eliminar un servicio del índice de Weaviate"""
    try:
        success = weaviate_service.delete_servicio(servicio_id)
        
        if success:
            return {
                "message": f"Servicio {servicio_id} eliminado del índice",
                "success": True
            }
        else:
            return {
                "message": f"Servicio {servicio_id} no encontrado en el índice",
                "success": False
            }
            
    except Exception as e:
        logger.error(f"❌ Error al eliminar servicio {servicio_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar servicio: {str(e)}"
        )

@router.get(
    "/search-public",
    description="Buscar servicios usando búsqueda semántica (público, sin autenticación)"
)
async def search_servicios_public(
    query: str = Query(..., description="Texto de búsqueda semántica"),
    limit: int = Query(100, ge=1, le=200)  # Aumentado a 200 para permitir más resultados
):
    """Buscar servicios usando búsqueda semántica con Weaviate (endpoint público)"""
    try:
        logger.info(f"🔍 Búsqueda semántica pública: '{query}'")
        
        resultados = weaviate_service.search_servicios(query=query, limit=limit)
        
        return {
            "query": query,
            "results": resultados,
            "total": len(resultados),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda semántica pública: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
        )

@router.get(
    "/recommendations/{servicio_id}",
    description="Obtener recomendaciones basadas en un servicio"
)
async def get_recommendations(
    servicio_id: int,
    limit: int = Query(5, ge=1, le=20),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Obtener recomendaciones de servicios similares"""
    try:
        # Obtener el servicio base
        servicio_base = weaviate_service.get_servicio_by_id(servicio_id)
        
        if not servicio_base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Servicio {servicio_id} no encontrado"
            )
        
        # Crear query de búsqueda basada en el servicio
        query_text = f"{servicio_base.get('nombre', '')} {servicio_base.get('descripcion', '')} {servicio_base.get('categoria', '')}"
        
        # Buscar servicios similares
        recomendaciones = weaviate_service.search_servicios(
            query=query_text, 
            limit=limit + 1  # +1 porque el servicio base aparecerá en los resultados
        )
        
        # Filtrar el servicio base de las recomendaciones
        recomendaciones_filtradas = [
            rec for rec in recomendaciones 
            if rec.get('id_servicio') != servicio_id
        ][:limit]
        
        return {
            "servicio_base": {
                "id": servicio_id,
                "nombre": servicio_base.get('nombre'),
                "categoria": servicio_base.get('categoria')
            },
            "recommendations": recomendaciones_filtradas,
            "total": len(recomendaciones_filtradas)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al obtener recomendaciones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener recomendaciones: {str(e)}"
        )
