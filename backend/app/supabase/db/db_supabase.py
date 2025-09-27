# Configuración de base de datos para Supabase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import DATABASE_URL
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la base para los modelos SQLAlchemy
Base = declarative_base()

# Verificar que DATABASE_URL esté configurado
if not DATABASE_URL:
    logger.error("❌ DATABASE_URL no está configurado")
    logger.error("💡 Asegúrate de crear el archivo .env en la carpeta backend")
    logger.error("💡 Con la connection string del Transaction Pooler")
    # En lugar de lanzar error, usar configuración por defecto para desarrollo
    DATABASE_URL = "postgresql://user:password@localhost:5432/b2b_db"
    logger.warning("⚠️ Usando configuración por defecto para desarrollo")

# Crear engine síncrono con manejo de errores
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
        connect_args={
            "statement_cache_size": 0,  # Deshabilitar prepared statements para PgBouncer
            "prepared_statement_cache_size": 0,
            "command_timeout": 60,  # Timeout para comandos
            "server_settings": {
                "jit": "off",  # Deshabilitar JIT para evitar problemas con PgBouncer
                "application_name": "seva_b2b_app",
                "default_transaction_isolation": "read committed"
            }
        }
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("✅ Engine síncrono creado exitosamente")
except Exception as e:
    logger.error(f"❌ Error al crear la conexión síncrona: {e}")
    # Crear engine dummy para evitar errores
    engine = None
    SessionLocal = None

# Crear engine asíncrono con manejo de errores
try:
    # Convertir URL síncrona a asíncrona
    async_database_url = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    logger.info("🔄 Creando engine asíncrono...")
    logger.info("🔧 Configurando para compatibilidad con PgBouncer (prepared statements deshabilitados)")

    # SOLUCIÓN DEFINITIVA: Configurar para PgBouncer sin prepared statements
    async_engine = create_async_engine(
        async_database_url,
        pool_size=1,  # Pool mínimo para evitar conflictos
        max_overflow=0,  # Sin overflow para evitar prepared statements
        pool_pre_ping=False,  # Deshabilitar pre_ping que causa prepared statements
        pool_recycle=60,  # Reciclar conexiones cada minuto para evitar conflictos
        echo=False,
        connect_args={
            "statement_cache_size": 0,  # CRÍTICO: Deshabilitar prepared statements
            "prepared_statement_cache_size": 0,  # CRÍTICO: Deshabilitar cache de prepared statements
            "command_timeout": 10,  # Timeout más corto
            "server_settings": {
                "jit": "off",
                "application_name": "seva_b2b_app",
                "default_transaction_isolation": "read committed"
            }
        }
    )

    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    logger.info("✅ Engine asíncrono creado exitosamente")
except Exception as e:
    logger.error(f"❌ Error al crear la conexión asíncrona: {e}")
    # Crear variables dummy para evitar errores de import
    async_engine = None
    AsyncSessionLocal = None


