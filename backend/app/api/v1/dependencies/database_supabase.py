from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.supabase.db.db_supabase import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Proporciona una sesión de base de datos asíncrona con manejo robusto de errores.
    """
    try:
        # Verificar que AsyncSessionLocal esté disponible
        if AsyncSessionLocal is None:
            logger.error("❌ AsyncSessionLocal no está configurado")
            raise ValueError("Base de datos no configurada")

        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"❌ Error en sesión de base de datos: {e}")
                await session.rollback()
                raise
    except Exception as e:
        logger.error(f"❌ Error crítico en configuración de BD: {e}")
        raise  # Re-lanzar la excepción para que FastAPI la maneje correctamente