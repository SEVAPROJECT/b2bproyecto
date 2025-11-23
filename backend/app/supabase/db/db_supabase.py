# Configuración de base de datos para Supabase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import DATABASE_URL
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes de mensajes
MSG_DATABASE_URL_NO_CONFIGURADO = "❌ DATABASE_URL no está configurado"
MSG_ASEGURARSE_CREAR_ENV = "💡 Asegúrate de crear el archivo .env en la carpeta backend"
MSG_CONNECTION_STRING_POOLER = "💡 Con la connection string del Transaction Pooler"
MSG_USANDO_CONFIGURACION_DEFAULT = "⚠️ Usando configuración por defecto para desarrollo"
MSG_ENGINE_SINCRONO_CREADO = "✅ Engine síncrono creado exitosamente"
MSG_ERROR_CREAR_CONEXION_SINCRONA = "❌ Error al crear la conexión síncrona: {error}"
MSG_CREANDO_ENGINE_ASINCRONO = "🔄 Creando engine asíncrono..."
MSG_URL_BASE_DATOS = "🔗 URL de base de datos: {url}"
MSG_CONFIGURANDO_SUPAVISOR = "🔧 Configurando para compatibilidad con Supavisor (pooler nativo de Supabase)"
MSG_ENGINE_ASINCRONO_CREADO = "✅ Engine asíncrono creado exitosamente"
MSG_ERROR_CREAR_CONEXION_ASINCRONA = "❌ Error al crear la conexión asíncrona: {error}"

# Constantes de configuración de base de datos
DATABASE_URL_DEFAULT = "postgresql://user:password@localhost:5432/b2b_db"
PREFIJO_POSTGRESQL = "postgresql://"
PREFIJO_POSTGRESQL_ASYNCPG = "postgresql+asyncpg://"

# Constantes de valores de configuración
VALOR_TRUE = True
VALOR_FALSE = False
POOL_RECYCLE_1800 = 1800  # 30 minutos
POOL_RECYCLE_3600 = 3600  # 1 hora
COMMAND_TIMEOUT = 60  # 60 segundos
CACHE_SIZE_DISABLED = 0
JIT_OFF = "off"
ISOLATION_LEVEL_READ_COMMITTED = "read committed"
APP_NAME_SEVA_B2B = "seva_b2b_app"

# Constantes de claves de configuración
CLAVE_STATEMENT_CACHE_SIZE = "statement_cache_size"
CLAVE_PREPARED_STATEMENT_CACHE_SIZE = "prepared_statement_cache_size"
CLAVE_COMMAND_TIMEOUT = "command_timeout"
CLAVE_SERVER_SETTINGS = "server_settings"
CLAVE_JIT = "jit"
CLAVE_APPLICATION_NAME = "application_name"
CLAVE_DEFAULT_TRANSACTION_ISOLATION = "default_transaction_isolation"
CLAVE_POOL_PRE_PING = "pool_pre_ping"
CLAVE_POOL_RECYCLE = "pool_recycle"
CLAVE_ECHO = "echo"
CLAVE_CONNECT_ARGS = "connect_args"
CLAVE_EXECUTION_OPTIONS = "execution_options"
CLAVE_PREPARED = "prepared"
CLAVE_AUTOCOMMIT = "autocommit"
CLAVE_AUTOFLUSH = "autoflush"
CLAVE_EXPIRE_ON_COMMIT = "expire_on_commit"
CLAVE_CLASS = "class_"
CLAVE_BIND = "bind"

# Crear la base para los modelos SQLAlchemy
Base = declarative_base()

# Verificar que DATABASE_URL esté configurado
if not DATABASE_URL:
    logger.error(MSG_DATABASE_URL_NO_CONFIGURADO)
    logger.error(MSG_ASEGURARSE_CREAR_ENV)
    logger.error(MSG_CONNECTION_STRING_POOLER)
    # En lugar de lanzar error, usar configuración por defecto para desarrollo
    DATABASE_URL = DATABASE_URL_DEFAULT
    logger.warning(MSG_USANDO_CONFIGURACION_DEFAULT)

# Crear engine síncrono con manejo de errores
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=VALOR_TRUE,
        pool_recycle=POOL_RECYCLE_1800,
        echo=VALOR_FALSE,
        connect_args={
            CLAVE_STATEMENT_CACHE_SIZE: CACHE_SIZE_DISABLED,  # Deshabilitar prepared statements para PgBouncer
            CLAVE_PREPARED_STATEMENT_CACHE_SIZE: CACHE_SIZE_DISABLED,
            CLAVE_COMMAND_TIMEOUT: COMMAND_TIMEOUT,  # Timeout para comandos
            CLAVE_SERVER_SETTINGS: {
                CLAVE_JIT: JIT_OFF,  # Deshabilitar JIT para evitar problemas con PgBouncer
                CLAVE_APPLICATION_NAME: APP_NAME_SEVA_B2B,
                CLAVE_DEFAULT_TRANSACTION_ISOLATION: ISOLATION_LEVEL_READ_COMMITTED
            }
        }
    )
    SessionLocal = sessionmaker(autocommit=VALOR_FALSE, autoflush=VALOR_FALSE, bind=engine)
    logger.info(MSG_ENGINE_SINCRONO_CREADO)
except Exception as e:
    logger.error(MSG_ERROR_CREAR_CONEXION_SINCRONA.format(error=e))
    # Crear engine dummy para evitar errores
    engine = None
    SessionLocal = None

# Crear engine asíncrono con manejo de errores
try:
    # Convertir URL síncrona a asíncrona
    if DATABASE_URL.startswith(PREFIJO_POSTGRESQL):
        async_database_url = DATABASE_URL.replace(PREFIJO_POSTGRESQL, PREFIJO_POSTGRESQL_ASYNCPG)
    elif DATABASE_URL.startswith(PREFIJO_POSTGRESQL_ASYNCPG):
        async_database_url = DATABASE_URL
    else:
        # Fallback para otros formatos
        async_database_url = DATABASE_URL.replace(PREFIJO_POSTGRESQL, PREFIJO_POSTGRESQL_ASYNCPG)
    
    logger.info(MSG_CREANDO_ENGINE_ASINCRONO)
    logger.info(MSG_URL_BASE_DATOS.format(url=async_database_url))
    logger.info(MSG_CONFIGURANDO_SUPAVISOR)

    # CONFIGURACIÓN OPTIMIZADA PARA SUPAVISOR (no PgBouncer)
    # Supavisor es compatible con prepared statements y SQLAlchemy
    from sqlalchemy.pool import NullPool
    
    async_engine = create_async_engine(
        async_database_url,
        poolclass=None,  # Sin pool de conexiones para evitar PgBouncer
        echo=VALOR_FALSE,
        connect_args={
            "statement_cache_size": CACHE_SIZE_DISABLED,  # Deshabilitar prepared statements para PgBouncer (asyncpg)
            "command_timeout": COMMAND_TIMEOUT,  # Timeout para comandos
            "server_settings": {
                CLAVE_JIT: JIT_OFF,  # Deshabilitar JIT para evitar problemas con PgBouncer
                CLAVE_APPLICATION_NAME: APP_NAME_SEVA_B2B,
                CLAVE_DEFAULT_TRANSACTION_ISOLATION: ISOLATION_LEVEL_READ_COMMITTED
            }
        },
        
        # Configuración optimizada para PgBouncer (que sigue siendo usado)
        pool_pre_ping=VALOR_TRUE,  # Verificar conexiones antes de usar
        pool_recycle=POOL_RECYCLE_3600,  # Reciclar conexiones cada hora
        execution_options={CLAVE_PREPARED: VALOR_FALSE}  # 🚨 Clave para PgBouncer - deshabilitar prepared statements
    )

    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=VALOR_FALSE,
        autocommit=VALOR_FALSE,
        autoflush=VALOR_FALSE
    )
    logger.info(MSG_ENGINE_ASINCRONO_CREADO)
except Exception as e:
    logger.error(MSG_ERROR_CREAR_CONEXION_ASINCRONA.format(error=e))
    # Crear variables dummy para evitar errores de import
    async_engine = None
    AsyncSessionLocal = None


