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
import os

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

@router.get(
    "/schema/check",
    description="Verificar el schema de Weaviate y su configuración de vectorizador"
)
async def check_schema():
    """Verificar si el schema existe y tiene vectorizador configurado"""
    try:
        schema_exists = weaviate_service._check_schema_exists()
        has_vectorizer = False
        schema_data = None
        model_info = None
        
        if schema_exists:
            schema_data = weaviate_service._get_schema()
            has_vectorizer = weaviate_service._check_schema_has_vectorizer()
            
            # Extraer información del modelo configurado
            if schema_data:
                module_config = schema_data.get('moduleConfig', {})
                if 'text2vec-huggingface' in module_config:
                    hf_config = module_config['text2vec-huggingface']
                    model_info = {
                        "type": "huggingface",
                        "model": hf_config.get('model', 'no especificado'),
                        "has_token": bool(hf_config.get('token'))
                    }
                elif 'text2vec-ollama' in module_config:
                    ollama_config = module_config['text2vec-ollama']
                    model_info = {
                        "type": "ollama",
                        "model": ollama_config.get('model', 'no especificado'),
                        "endpoint": ollama_config.get('apiEndpoint', 'no especificado')
                    }
        
        # Modelo esperado desde variables de entorno
        expected_model = os.getenv("HUGGINGFACE_MODEL", "no configurado")
        
        return {
            "schema_exists": schema_exists,
            "has_vectorizer": has_vectorizer,
            "schema": schema_data,
            "class_name": weaviate_service.class_name,
            "model_info": model_info,
            "expected_model": expected_model,
            "model_matches": model_info and model_info.get("model") == expected_model if model_info else False
        }
    except Exception as e:
        logger.error(f"❌ Error al verificar schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar schema: {str(e)}"
        )

@router.post(
    "/schema/setup",
    description="Crear o actualizar el schema de Weaviate con vectorizador"
)
async def setup_schema(
    force: bool = Query(False, description="Forzar recreación del schema aunque ya exista")
):
    """Crear o actualizar el schema de Weaviate con vectorizador configurado"""
    try:
        if force:
            logger.info("🔄 Forzando recreación del schema...")
            weaviate_service._delete_schema()
        
        # Intentar crear/verificar el schema
        weaviate_service._setup_schema()
        
        # Verificar que se creó correctamente
        schema_exists = weaviate_service._check_schema_exists()
        has_vectorizer = weaviate_service._check_schema_has_vectorizer()
        
        return {
            "message": "Schema configurado exitosamente" if (schema_exists and has_vectorizer) else "Error al configurar schema",
            "schema_exists": schema_exists,
            "has_vectorizer": has_vectorizer,
            "class_name": weaviate_service.class_name
        }
    except Exception as e:
        logger.error(f"❌ Error al configurar schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al configurar schema: {str(e)}"
        )

@router.post(
    "/migrate-model",
    description="Migrar a un nuevo modelo de embeddings: detecta cambio, elimina schema, recrea schema y reindexa servicios"
)
async def migrate_model(
    limit: int = Query(1000, ge=1, le=10000, description="Límite de servicios a reindexar"),
    force: bool = Query(False, description="Forzar migración aunque no se detecte cambio de modelo"),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Migrar a un nuevo modelo de embeddings.
    
    Este endpoint:
    1. Detecta si el modelo configurado en HUGGINGFACE_MODEL difiere del modelo en el schema
    2. Si hay cambio (o force=True), elimina el schema (y todos los objetos indexados)
    3. Recrea el schema con el nuevo modelo
    4. Reindexa todos los servicios con el nuevo modelo
    """
    try:
        logger.info(f"🔄 Iniciando migración de modelo por usuario: {current_user.id}")
        
        # Paso 1: Detectar cambio de modelo
        huggingface_model = os.getenv("HUGGINGFACE_MODEL")
        model_changed = False
        current_model = None
        expected_model = None
        
        if huggingface_model:
            # Verificar si el schema existe y obtener el modelo actual
            if weaviate_service._check_schema_exists():
                schema_actual = weaviate_service._get_schema_config()
                if schema_actual:
                    config_hf = schema_actual.get('moduleConfig', {}).get('text2vec-huggingface', {})
                    current_model = config_hf.get('model', '')
                    expected_model = huggingface_model.strip()
                    
                    if current_model != expected_model:
                        model_changed = True
                        logger.info(f"🔍 Cambio de modelo detectado:")
                        logger.info(f"   Modelo actual: {current_model}")
                        logger.info(f"   Modelo esperado: {expected_model}")
                    else:
                        logger.info(f"✅ El modelo ya está actualizado: {expected_model}")
            else:
                # No hay schema, necesitamos crearlo
                model_changed = True
                expected_model = huggingface_model.strip()
                logger.info(f"🔍 No existe schema, se creará con modelo: {expected_model}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HUGGINGFACE_MODEL no está configurado. Configura la variable de entorno primero."
            )
        
        # Verificar si hay servicios indexados
        stats = weaviate_service.get_stats()
        total_objects = stats.get('total_objects', 0)
        
        # Contar servicios activos en la base de datos para comparar
        from app.services.direct_db_service import direct_db_service
        conn = None
        total_servicios_db = 0
        try:
            conn = await direct_db_service.get_connection()
            count_query = "SELECT COUNT(*) as total FROM servicio WHERE estado = true"
            count_result = await conn.fetchrow(count_query)
            total_servicios_db = count_result['total'] if count_result else 0
            logger.info(f"📊 Servicios activos en BD: {total_servicios_db}, Servicios indexados en Weaviate: {total_objects}")
        except Exception as e:
            logger.warning(f"⚠️ Error al contar servicios en BD: {e}")
        finally:
            if conn:
                await direct_db_service.pool.release(conn)
        
        # Determinar si necesita reindexación:
        # 1. Si no hay servicios indexados (total_objects == 0)
        # 2. Si hay muy pocos servicios indexados comparado con la BD (menos del 10% o menos de 50)
        needs_reindex = total_objects == 0
        if not needs_reindex and total_servicios_db > 0:
            porcentaje_indexado = (total_objects / total_servicios_db) * 100
            # Reindexar si hay menos del 10% indexado O menos de 50 servicios indexados
            needs_reindex = porcentaje_indexado < 10.0 or total_objects < 50
            if needs_reindex:
                logger.warning(f"⚠️ Pocos servicios indexados: {total_objects}/{total_servicios_db} ({porcentaje_indexado:.1f}%)")
        
        # Si no hay cambio y no se fuerza, pero necesita reindexación, reindexar
        if not model_changed and not force:
            if needs_reindex:
                logger.warning(f"⚠️ El modelo está actualizado pero hay pocos servicios indexados (total_objects: {total_objects}, total_BD: {total_servicios_db})")
                logger.info(f"📦 Reindexando servicios (límite: {limit})...")
                index_success = await weaviate_service.index_servicios(limit=limit)
                
                if not index_success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error al reindexar servicios"
                    )
                
                logger.info("✅ Reindexación completada exitosamente")
                
                return {
                    "message": "Servicios reindexados exitosamente (el modelo ya estaba actualizado)",
                    "current_model": current_model,
                    "expected_model": expected_model,
                    "model_changed": False,
                    "services_reindexed": True,
                    "reindex_limit": limit,
                    "total_objects_before": total_objects,
                    "total_servicios_db": total_servicios_db,
                    "status": "success"
                }
            else:
                return {
                    "message": "No se detectó cambio de modelo. El schema ya está actualizado y hay suficientes servicios indexados.",
                    "current_model": current_model,
                    "expected_model": expected_model,
                    "total_objects": total_objects,
                    "total_servicios_db": total_servicios_db,
                    "migration_skipped": True
                }
        
        # Paso 2: Eliminar schema (esto elimina todos los objetos automáticamente)
        if model_changed or force:
            if weaviate_service._check_schema_exists():
                logger.info("🗑️ Eliminando schema existente (esto eliminará todos los objetos indexados)...")
                schema_deleted = weaviate_service._delete_schema()
                
                if not schema_deleted and weaviate_service._check_schema_exists():
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error al eliminar el schema existente"
                    )
            else:
                logger.info("ℹ️ No existe schema previo, se creará uno nuevo")
        
        # Paso 3: Recrear schema con el nuevo modelo
        logger.info(f"🔨 Recreando schema con modelo: {expected_model}")
        weaviate_service._setup_schema()
        
        # Verificar que se creó correctamente
        schema_exists = weaviate_service._check_schema_exists()
        has_vectorizer = weaviate_service._check_schema_has_vectorizer()
        
        if not schema_exists or not has_vectorizer:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al recrear el schema con el nuevo modelo"
            )
        
        logger.info("✅ Schema recreado exitosamente")
        
        # Paso 4: Reindexar todos los servicios
        logger.info(f"📦 Reindexando servicios (límite: {limit})...")
        index_success = await weaviate_service.index_servicios(limit=limit)
        
        if not index_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al reindexar servicios"
            )
        
        logger.info("✅ Migración completada exitosamente")
        
        return {
            "message": "Migración de modelo completada exitosamente",
            "model_changed": model_changed,
            "previous_model": current_model,
            "new_model": expected_model,
            "schema_recreated": True,
            "services_reindexed": True,
            "reindex_limit": limit,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en migración de modelo: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en migración de modelo: {str(e)}"
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

@router.post(
    "/index-servicios-public",
    description="Indexar todos los servicios en Weaviate (público, sin autenticación - solo para inicialización)"
)
async def index_servicios_public(
    limit: int = Query(1000, ge=1, le=10000),
    secret_key: str = Query(..., description="Clave secreta para autorizar la indexación")
):
    """Indexar servicios desde la base de datos a Weaviate (endpoint público para inicialización)"""
    # Verificar clave secreta (configurar en variables de entorno)
    expected_key = os.getenv("WEAVIATE_INDEX_SECRET_KEY", "change-me-in-production")
    
    if secret_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave secreta inválida"
        )
    
    try:
        logger.info(f"🔍 Iniciando indexación pública de servicios (límite: {limit})")
        
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
    min_relevance: float = Query(0.3, ge=0.0, le=1.0, description="Score mínimo de relevancia (0-1)"),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """Buscar servicios usando búsqueda semántica con Weaviate"""
    try:
        logger.info(f"🔍 Búsqueda semántica: '{query}' por usuario: {current_user.id} (relevancia mínima: {min_relevance})")
        
        resultados = weaviate_service.search_servicios(query=query, limit=limit, min_relevance_score=min_relevance)
        
        # Si Weaviate no devuelve resultados con buena relevancia, usar fallback
        if not resultados or len(resultados) == 0:
            logger.warning("⚠️ Weaviate no devolvió resultados con relevancia suficiente, usando fallback a búsqueda normal")
            resultados = await _fallback_search_normal(query, limit)
        
        return {
            "query": query,
            "results": resultados,
            "total": len(resultados),
            "limit": limit,
            "min_relevance": min_relevance
        }
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda semántica: {str(e)}")
        logger.info("🔄 Intentando fallback a búsqueda normal...")
        try:
            resultados = await _fallback_search_normal(query, limit)
            return {
                "query": query,
                "results": resultados,
                "total": len(resultados),
                "limit": limit
            }
        except Exception as fallback_error:
            logger.error(f"❌ Error en fallback también: {str(fallback_error)}")
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
    limit: int = Query(100, ge=1, le=200),  # Aumentado a 200 para permitir más resultados
    min_relevance: float = Query(0.25, ge=0.0, le=1.0, description="Score mínimo de relevancia (0-1)")
):
    """Buscar servicios usando búsqueda semántica con Weaviate (endpoint público)"""
    try:
        logger.info(f"🔍 Búsqueda semántica pública: '{query}' (relevancia mínima: {min_relevance})")
        
        resultados = weaviate_service.search_servicios(query=query, limit=limit, min_relevance_score=min_relevance)
        
        # Si Weaviate no devuelve resultados con buena relevancia, usar fallback a búsqueda normal
        if not resultados or len(resultados) == 0:
            logger.warning("⚠️ Weaviate no devolvió resultados con relevancia suficiente, usando fallback a búsqueda normal")
            resultados = await _fallback_search_normal(query, limit)
        
        logger.info(f"✅ Búsqueda completada: {len(resultados)} resultados encontrados")
        return {
            "query": query,
            "results": resultados,
            "total": len(resultados),
            "limit": limit,
            "min_relevance": min_relevance
        }
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda semántica pública: {str(e)}")
        logger.info("🔄 Intentando fallback a búsqueda normal...")
        try:
            resultados = await _fallback_search_normal(query, limit)
            logger.info(f"✅ Fallback completado: {len(resultados)} resultados encontrados")
            return {
                "query": query,
                "results": resultados,
                "total": len(resultados),
                "limit": limit
            }
        except Exception as fallback_error:
            logger.error(f"❌ Error en fallback también: {str(fallback_error)}")
            import traceback
            logger.error(f"❌ Traceback del fallback: {traceback.format_exc()}")
            # Devolver respuesta vacía en lugar de lanzar error para que el frontend pueda manejarlo
            return {
                "query": query,
                "results": [],
                "total": 0,
                "limit": limit,
                "error": str(fallback_error)
            }

async def _fallback_search_normal(query: str, limit: int):
    """Fallback a búsqueda normal cuando Weaviate falla"""
    try:
        from app.services.direct_db_service import direct_db_service
        
        conn = await direct_db_service.get_connection()
        try:
            # Búsqueda simple por nombre o descripción
            # Usar la misma estructura que en weaviate_service.py para indexar
            # Escapar caracteres especiales de regex para PostgreSQL
            query_escaped = query.replace("\\", "\\\\").replace("'", "''")
            # Usar expresiones regulares con word boundaries (\y) para buscar palabras completas
            search_pattern = rf"\y{query_escaped}\y"
            
            search_query = """
                SELECT DISTINCT
                    s.id_servicio,
                    s.nombre,
                    s.descripcion,
                    s.precio,
                    s.estado,
                    cat.nombre as categoria,
                    pe.nombre_fantasia as empresa,
                    COALESCE(ci.nombre || ', ' || dep.nombre, '') as ubicacion,
                    s.created_at
                FROM servicio s
                LEFT JOIN categoria cat ON s.id_categoria = cat.id_categoria
                LEFT JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
                LEFT JOIN direccion dir ON pe.id_direccion = dir.id_direccion
                LEFT JOIN departamento dep ON dir.id_departamento = dep.id_departamento
                LEFT JOIN ciudad ci ON dir.id_ciudad = ci.id_ciudad
                WHERE s.estado = true
                    AND (
                        s.nombre ~* $1 
                        OR s.descripcion ~* $1
                        OR cat.nombre ~* $1
                        OR pe.nombre_fantasia ~* $1
                    )
                ORDER BY s.created_at DESC
                LIMIT $2
            """
            rows = await conn.fetch(search_query, search_pattern, limit)
            
            resultados = []
            for row in rows:
                resultados.append({
                    "id_servicio": row["id_servicio"],
                    "nombre": row["nombre"],
                    "descripcion": row["descripcion"],
                    "precio": row["precio"],
                    "categoria": row["categoria"],
                    "empresa": row["empresa"],
                    "ubicacion": row["ubicacion"],
                    "created_at": str(row["created_at"]) if row["created_at"] else None
                })
            
            logger.info(f"✅ Fallback: {len(resultados)} resultados encontrados")
            return resultados
        finally:
            await direct_db_service.pool.release(conn)
    except Exception as e:
        logger.error(f"❌ Error en fallback: {str(e)}")
        return []

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
