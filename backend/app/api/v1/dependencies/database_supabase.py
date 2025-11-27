from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.supabase.db.db_supabase import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Proporciona una sesión de base de datos asíncrona con manejo robusto de errores.
    Configurado para evitar problemas con PgBouncer deshabilitando prepared statements.
    """
    try:
        # Verificar que AsyncSessionLocal esté disponible
        if AsyncSessionLocal is None:
            logger.error("❌ AsyncSessionLocal no está configurado")
            raise ValueError("Base de datos no configurada")

        async with AsyncSessionLocal() as session:
            try:
                # La configuración de prepared=False ya está en el engine
                # No es necesario configurarlo por sesión
                yield session
            except Exception as e:
                # No registrar HTTPException como errores críticos (son respuestas HTTP normales)
                from fastapi import HTTPException
                if not isinstance(e, HTTPException):
                    logger.error(f"❌ Error en sesión de base de datos: {e}")
                await session.rollback()
                raise
    except Exception as e:
        # No registrar HTTPException como errores críticos (son respuestas HTTP normales)
        from fastapi import HTTPException
        if not isinstance(e, HTTPException):
            logger.error(f"❌ Error crítico en configuración de BD: {e}")
        raise  # Re-lanzar la excepción para que FastAPI la maneje correctamente