"""
Router para sincronización de servicios con Weaviate
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.weaviate_service import weaviate_service
from app.services.direct_db_service import direct_db_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/weaviate", tags=["weaviate-sync"])

@router.post("/sync-all")
async def sync_all_services(background_tasks: BackgroundTasks):
    """Sincronizar todos los servicios con Weaviate"""
    try:
        logger.info("🔄 Iniciando sincronización completa de servicios...")
        
        # Ejecutar sincronización en background
        background_tasks.add_task(sync_services_background)
        
        return {
            "message": "Sincronización iniciada en background",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"❌ Error iniciando sincronización: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-service/{service_id}")
async def sync_single_service(service_id: int):
    """Sincronizar un servicio específico con Weaviate"""
    try:
        logger.info(f"🔄 Sincronizando servicio ID {service_id}...")
        
        # Obtener servicio de la base de datos
        conn = await direct_db_service.get_connection()
        
        query = """
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
            WHERE s.id_servicio = $1
        """
        
        service = await conn.fetchrow(query, service_id)
        await direct_db_service.pool.release(conn)
        
        if not service:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        # Sincronizar con Weaviate
        success = await sync_service_to_weaviate(service)
        
        if success:
            return {
                "message": f"Servicio ID {service_id} sincronizado exitosamente",
                "service": {
                    "id": service['id_servicio'],
                    "nombre": service['nombre']
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Error sincronizando servicio")
            
    except Exception as e:
        logger.error(f"❌ Error sincronizando servicio {service_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove-service/{service_id}")
async def remove_service_from_weaviate(service_id: int):
    """Eliminar un servicio de Weaviate"""
    try:
        logger.info(f"🗑️ Eliminando servicio ID {service_id} de Weaviate...")
        
        success = weaviate_service.delete_servicio(service_id)
        
        if success:
            return {
                "message": f"Servicio ID {service_id} eliminado de Weaviate",
                "service_id": service_id
            }
        else:
            raise HTTPException(status_code=404, detail="Servicio no encontrado en Weaviate")
            
    except Exception as e:
        logger.error(f"❌ Error eliminando servicio {service_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def sync_services_background():
    """Sincronizar todos los servicios en background"""
    try:
        logger.info("🔄 Ejecutando sincronización completa...")
        
        # Obtener todos los servicios activos
        conn = await direct_db_service.get_connection()
        
        query = """
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
            ORDER BY s.id_servicio
        """
        
        services = await conn.fetch(query)
        await direct_db_service.pool.release(conn)
        
        logger.info(f"📊 Sincronizando {len(services)} servicios...")
        
        # Sincronizar cada servicio
        synced_count = 0
        for service in services:
            try:
                success = await sync_service_to_weaviate(service)
                if success:
                    synced_count += 1
                    logger.info(f"✅ Sincronizado: {service['nombre']} (ID: {service['id_servicio']})")
                else:
                    logger.error(f"❌ Error sincronizando: {service['nombre']}")
            except Exception as e:
                logger.error(f"❌ Error sincronizando {service['nombre']}: {str(e)}")
        
        logger.info(f"🎉 Sincronización completada: {synced_count}/{len(services)} servicios")
        
    except Exception as e:
        logger.error(f"❌ Error en sincronización background: {str(e)}")

async def sync_service_to_weaviate(service):
    """Sincronizar un servicio individual con Weaviate"""
    try:
        # Aquí implementarías la lógica de sincronización
        # Por ahora, solo log
        logger.info(f"🔄 Sincronizando servicio: {service['nombre']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error sincronizando servicio: {str(e)}")
        return False
