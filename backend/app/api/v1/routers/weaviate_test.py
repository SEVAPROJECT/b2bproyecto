"""
Endpoints de prueba para Weaviate
Búsquedas simples sin vectorización
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from app.services.weaviate_service import weaviate_service
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weaviate-test", tags=["weaviate-test"])

@router.get(
    "/status",
    description="Verificar el estado de Weaviate"
)
async def get_weaviate_status():
    """Verificar estado de Weaviate"""
    try:
        stats = weaviate_service.get_stats()
        return {
            "status": "connected" if "error" not in stats else "error",
            "details": stats
        }
    except Exception as e:
        logger.error(f"❌ Error al verificar estado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar Weaviate: {str(e)}"
        )

@router.post(
    "/index-servicios",
    description="Indexar servicios en Weaviate"
)
async def index_servicios(
    limit: int = Query(10, ge=1, le=100),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Indexar servicios en Weaviate"""
    try:
        logger.info(f"🔍 Indexando servicios por usuario: {current_user.id}")
        
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
    "/servicios",
    description="Obtener todos los servicios indexados"
)
async def get_servicios(
    limit: int = Query(10, ge=1, le=50),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Obtener servicios indexados"""
    try:
        # Usar búsqueda simple con texto vacío para obtener todos
        resultados = weaviate_service.search_servicios("", limit=limit)
        
        return {
            "servicios": resultados,
            "total": len(resultados),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"❌ Error al obtener servicios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servicios: {str(e)}"
        )

@router.get(
    "/search",
    description="Buscar servicios usando Weaviate (búsqueda simple)"
)
async def search_servicios(
    query: str = Query(..., description="Texto de búsqueda"),
    limit: int = Query(10, ge=1, le=50),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Buscar servicios usando Weaviate con búsqueda simple"""
    try:
        logger.info(f"🔍 Búsqueda en Weaviate: '{query}' por usuario: {current_user.id}")
        
        # Para búsqueda simple, obtener todos los servicios y filtrar localmente
        # Esto es un workaround hasta que configuremos el vectorizador
        all_servicios = weaviate_service.search_servicios("", limit=100)  # Obtener más servicios
        
        # Filtrar localmente por el query
        filtered_servicios = []
        if query.strip():
            query_lower = query.lower()
            for servicio in all_servicios:
                if (query_lower in servicio.get('nombre', '').lower() or 
                    query_lower in servicio.get('descripcion', '').lower() or
                    query_lower in servicio.get('categoria', '').lower() or
                    query_lower in servicio.get('empresa', '').lower()):
                    filtered_servicios.append(servicio)
        else:
            filtered_servicios = all_servicios
        
        # Limitar resultados
        resultados = filtered_servicios[:limit]
        
        return {
            "query": query,
            "results": resultados,
            "total": len(resultados),
            "limit": limit,
            "message": "Búsqueda simple (sin vectorización)"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
        )

@router.get(
    "/search-public",
    description="Buscar servicios usando base de datos (sin autenticación para pruebas)"
)
async def search_servicios_public(
    query: str = Query(..., description="Texto de búsqueda"),
    limit: int = Query(10, ge=1, le=50)
):
    """Buscar servicios usando base de datos directamente (sin autenticación)"""
    try:
        logger.info(f"🔍 Búsqueda pública en BD: '{query}'")
        
        # Importar el servicio de base de datos
        from app.services.direct_db_service import direct_db_service
        
        # Obtener servicios de la base de datos
        conn = await direct_db_service.get_connection()
        
        search_query = """
            SELECT 
                s.id_servicio,
                s.nombre,
                s.descripcion,
                s.precio,
                s.estado,
                c.nombre as categoria,
                pe.nombre_fantasia as empresa
            FROM servicio s
            LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
            LEFT JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            WHERE s.estado = true
            AND (
                LOWER(s.nombre) LIKE LOWER($1) OR
                LOWER(s.descripcion) LIKE LOWER($1) OR
                LOWER(c.nombre) LIKE LOWER($1) OR
                LOWER(pe.nombre_fantasia) LIKE LOWER($1)
            )
            LIMIT $2
        """
        
        # Buscar con wildcards
        search_term = f"%{query}%"
        result = await conn.fetch(search_query, search_term, limit)
        
        await direct_db_service.pool.release(conn)
        
        # Convertir a formato esperado
        resultados = []
        for servicio in result:
            resultados.append({
                "id_servicio": servicio['id_servicio'],
                "nombre": servicio['nombre'],
                "descripcion": servicio['descripcion'],
                "precio": float(servicio['precio']) if servicio['precio'] else 0.0,
                "categoria": servicio['categoria'] or "",
                "empresa": servicio['empresa'] or "",
                "ubicacion": "",
                "estado": "activo" if servicio['estado'] else "inactivo"
            })
        
        return {
            "query": query,
            "results": resultados,
            "total": len(resultados),
            "limit": limit,
            "message": "Búsqueda en base de datos"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda pública: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
        )

@router.get(
    "/servicio/{servicio_id}",
    description="Obtener un servicio específico"
)
async def get_servicio(
    servicio_id: int,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Obtener un servicio específico"""
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
                "message": f"Servicio {servicio_id} no encontrado"
            }
            
    except Exception as e:
        logger.error(f"❌ Error al obtener servicio {servicio_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servicio: {str(e)}"
        )
