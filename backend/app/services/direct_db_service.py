"""
Servicio de base de datos directo usando asyncpg (sin SQLAlchemy)
Para evitar problemas con PgBouncer
"""
import asyncpg
import asyncio
import logging
from typing import Optional, Dict, Any
from app.core.config import DATABASE_URL
from railway_config import (
    POOL_MIN_SIZE, POOL_MAX_SIZE, POOL_TIMEOUT, 
    POOL_COMMAND_TIMEOUT, POOL_KEEPALIVE_IDLE,
    POOL_KEEPALIVE_INTERVAL, POOL_KEEPALIVE_COUNT
)

logger = logging.getLogger(__name__)

class DirectDBService:
    """Servicio de base de datos directo con asyncpg"""
    
    def __init__(self):
        self.connection_params = self._parse_database_url()
        self.pool = None
        self._pool_initialized = False
        
    def _parse_database_url(self) -> Dict[str, Any]:
        """Parsear URL de base de datos"""
        try:
            # postgresql://user:pass@host:port/db
            url_parts = DATABASE_URL.replace('postgresql://', '').split('@')
            if len(url_parts) != 2:
                raise ValueError("URL de base de datos inválida")
                
            user_pass = url_parts[0].split(':')
            if len(user_pass) != 2:
                raise ValueError("Credenciales de base de datos inválidas")
                
            user = user_pass[0]
            password = user_pass[1]
            
            host_port_db = url_parts[1].split('/')
            if len(host_port_db) != 2:
                raise ValueError("Host/port/db de base de datos inválido")
                
            host_port = host_port_db[0].split(':')
            if len(host_port) != 2:
                raise ValueError("Host/port de base de datos inválido")
                
            host = host_port[0]
            port = int(host_port[1])
            database = host_port_db[1]
            
            return {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": database
            }
        except Exception as e:
            logger.error(f"❌ Error parseando URL de base de datos: {e}")
            raise
    
    async def _ensure_pool(self):
        """Asegurar que el pool esté inicializado"""
        if not self._pool_initialized:
            try:
                logger.info("🔄 Inicializando pool de conexiones para direct_db_service...")
                # Configuración optimizada para Railway/Desarrollo
                self.pool = await asyncpg.create_pool(
                    **self.connection_params,
                    min_size=POOL_MIN_SIZE,
                    max_size=POOL_MAX_SIZE,
                    timeout=POOL_TIMEOUT,
                    command_timeout=POOL_COMMAND_TIMEOUT,
                    statement_cache_size=0,  # CRÍTICO: Deshabilitar prepared statements
                    server_settings={
                        "application_name": "seva_b2b_direct_service",
                        "default_transaction_isolation": "read committed",
                        "tcp_keepalives_idle": str(POOL_KEEPALIVE_IDLE),
                        "tcp_keepalives_interval": str(POOL_KEEPALIVE_INTERVAL),
                        "tcp_keepalives_count": str(POOL_KEEPALIVE_COUNT)
                    }
                )
                self._pool_initialized = True
                logger.info("✅ Pool de conexiones inicializado exitosamente")
            except Exception as e:
                logger.error(f"❌ Error inicializando pool de conexiones: {e}")
                raise
        # El pool ya está inicializado, no necesitamos verificar nada más
    
    async def get_connection(self) -> asyncpg.Connection:
        """Obtener conexión del pool con manejo de errores para Railway"""
        try:
            await self._ensure_pool()
            conn = await self.pool.acquire()
            return conn
        except asyncio.TimeoutError as e:
            logger.error(f"❌ Timeout obteniendo conexión del pool (Railway): {e}")
            # Intentar reconectar si hay timeout
            await self._reconnect_pool()
            conn = await self.pool.acquire()
            return conn
        except Exception as e:
            logger.error(f"❌ Error obteniendo conexión del pool: {e}")
            raise
    
    async def _reconnect_pool(self):
        """Reconectar el pool en caso de problemas con Railway"""
        try:
            if self.pool:
                await self.pool.close()
            self._pool_initialized = False
            await self._ensure_pool()
            logger.info("🔄 Pool reconectado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error reconectando pool: {e}")
            raise
    
    async def check_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Verificar si existe el perfil del usuario"""
        try:
            conn = await self.get_connection()
            try:
                result = await conn.fetchrow(
                    "SELECT id, nombre_persona, nombre_empresa, ruc, estado FROM users WHERE id = $1",
                    user_id
                )
                if result:
                    return dict(result)
                return None
            finally:
                await self.pool.release(conn)
        except Exception as e:
            logger.error(f"❌ Error verificando perfil de usuario {user_id}: {e}")
            return None
    
    async def check_user_role(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Verificar si existe el rol del usuario"""
        try:
            conn = await self.get_connection()
            try:
                result = await conn.fetchrow(
                    """
                    SELECT ur.id_usuario, r.nombre as role_name 
                    FROM usuario_rol ur 
                    JOIN rol r ON ur.id_rol = r.id 
                    WHERE ur.id_usuario = $1 AND r.nombre = 'Cliente'
                    """,
                    user_id
                )
                if result:
                    return dict(result)
                return None
            finally:
                await self.pool.release(conn)
        except Exception as e:
            logger.error(f"❌ Error verificando rol de usuario {user_id}: {e}")
            return None
    
    async def create_user_profile(self, user_id: str, nombre_persona: str, nombre_empresa: str, ruc: str = None):
        """Crear perfil de usuario manualmente"""
        try:
            conn = await self.get_connection()
            try:
                await conn.execute("""
                    INSERT INTO users (id, nombre_persona, nombre_empresa, ruc, estado, created_at)
                    VALUES ($1, $2, $3, $4, 'ACTIVO', NOW())
                    ON CONFLICT (id) DO NOTHING
                """, user_id, nombre_persona, nombre_empresa, ruc)
                logger.info(f"✅ Perfil creado manualmente para usuario: {user_id}")
            finally:
                await self.pool.release(conn)
        except Exception as e:
            logger.error(f"❌ Error creando perfil manualmente para {user_id}: {e}")
            raise
    
    async def assign_client_role(self, user_id: str):
        """Asignar rol 'Cliente' manualmente"""
        try:
            conn = await self.get_connection()
            try:
                # Obtener ID del rol 'Cliente'
                cliente_role = await conn.fetchrow("SELECT id FROM rol WHERE nombre = 'Cliente'")
                if not cliente_role:
                    raise Exception("Rol 'Cliente' no encontrado")
                
                # Asignar rol
                await conn.execute("""
                    INSERT INTO usuario_rol (id_usuario, id_rol, created_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (id_usuario, id_rol) DO NOTHING
                """, user_id, cliente_role['id'])
                
                logger.info(f"✅ Rol 'Cliente' asignado manualmente para usuario: {user_id}")
            finally:
                await self.pool.release(conn)
        except Exception as e:
            logger.error(f"❌ Error asignando rol manualmente para {user_id}: {e}")
            raise
    
    async def get_user_profile_with_roles(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener perfil de usuario con sus roles"""
        conn = None
        try:
            logger.info(f"🔍 Iniciando búsqueda de perfil para usuario: {user_id}")
            conn = await self.get_connection()
            logger.info(f"✅ Conexión establecida para usuario: {user_id}")
            
            # Consulta optimizada combinada para obtener perfil y roles en una sola query
            result = await conn.fetchrow("""
                SELECT 
                    u.id,
                    u.nombre_persona,
                    u.nombre_empresa,
                    u.ruc,
                    u.estado,
                    u.foto_perfil,
                    u.created_at,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'id', r.id,
                                'nombre', r.nombre,
                                'descripcion', r.descripcion,
                                'role_assigned_at', ur.created_at
                            )
                        ) FILTER (WHERE r.id IS NOT NULL),
                        '[]'::json
                    ) as roles
                FROM users u
                LEFT JOIN usuario_rol ur ON u.id = ur.id_usuario
                LEFT JOIN rol r ON ur.id_rol = r.id
                WHERE u.id = $1
                GROUP BY u.id, u.nombre_persona, u.nombre_empresa, u.ruc, u.estado, u.foto_perfil, u.created_at
            """, user_id)
            
            if not result:
                logger.warning(f"⚠️ Perfil no encontrado para usuario: {user_id}")
                return None
            
            logger.info(f"✅ Perfil encontrado para usuario: {user_id}")
            
            # Construir respuesta
            user_data = dict(result)
            # Los roles ya vienen como JSON en la consulta
            user_data['roles'] = user_data['roles'] if user_data['roles'] != '[]' else []
            
            logger.info(f"✅ Perfil con roles obtenido exitosamente para usuario: {user_id}")
            return user_data
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo perfil con roles para {user_id}: {e}")
            logger.error(f"❌ Tipo de error: {type(e).__name__}")
            logger.error(f"❌ Detalles del error: {str(e)}")
            return None
        finally:
            if conn:
                try:
                    await self.pool.release(conn)
                    logger.info(f"✅ Conexión devuelta al pool para usuario: {user_id}")
                except Exception as close_error:
                    logger.error(f"❌ Error devolviendo conexión al pool para usuario {user_id}: {close_error}")
    
    async def test_connection(self) -> bool:
        """
        Test rápido de conexión para health checks.
        Retorna True si la conexión es exitosa.
        """
        conn = None
        try:
            conn = await self.get_connection()
            # Query simple para verificar conexión
            await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"❌ Test de conexión falló: {str(e)}")
            return False
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def close_pool(self):
        """Cerrar el pool de conexiones"""
        if self.pool and self._pool_initialized:
            try:
                await self.pool.close()
                self._pool_initialized = False
                logger.info("✅ Pool de conexiones cerrado exitosamente")
            except Exception as e:
                logger.error(f"❌ Error cerrando pool de conexiones: {e}")

# Instancia global del servicio
direct_db_service = DirectDBService()
