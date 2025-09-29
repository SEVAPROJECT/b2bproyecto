"""
Eventos de inicialización de la aplicación
"""
import logging
from app.services.direct_db_service import direct_db_service

logger = logging.getLogger(__name__)

async def startup_events():
    """Eventos de inicialización al arrancar la aplicación"""
    try:
        logger.info("🚀 Inicializando servicios de la aplicación...")
        
        # Inicializar pool de conexiones del direct_db_service
        await direct_db_service._ensure_pool()
        
        logger.info("✅ Servicios inicializados exitosamente")
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")
        raise

async def shutdown_events():
    """Eventos de limpieza al cerrar la aplicación"""
    try:
        logger.info("🔄 Cerrando servicios de la aplicación...")
        
        # Cerrar pool de conexiones del direct_db_service
        await direct_db_service.close_pool()
        
        logger.info("✅ Servicios cerrados exitosamente")
    except Exception as e:
        logger.error(f"❌ Error cerrando servicios: {e}")
