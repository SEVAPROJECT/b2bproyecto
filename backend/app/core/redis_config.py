# app/core/redis_config.py
'''
import redis
import json
import os
from typing import Optional, Any
import asyncio
from functools import wraps

class RedisCache:
    """Clase para manejar cache con Redis de manera profesional"""
    
    def __init__(self):
        # Configuración de Redis desde variables de entorno
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis_password = os.getenv('REDIS_PASSWORD', None)
        
        # Crear conexión Redis
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Verificar conexión
        try:
            self.redis_client.ping()
            print("✅ Redis conectado exitosamente")
        except redis.ConnectionError:
            print("⚠️ Redis no disponible, usando cache en memoria")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if not self.redis_client:
            return None
            
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"❌ Error obteniendo cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Guardar valor en cache con TTL"""
        if not self.redis_client:
            return False
            
        try:
            serialized_value = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            print(f"❌ Error guardando cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Eliminar valor del cache"""
        if not self.redis_client:
            return False
            
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Error eliminando cache: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Limpiar cache por patrón"""
        if not self.redis_client:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"❌ Error limpiando cache: {e}")
            return 0

# Instancia global de Redis
redis_cache = RedisCache()

def cache_key(prefix: str, *args) -> str:
    """Generar clave de cache consistente"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"

def cache_ttl(seconds: int = 300):
    """Decorador para cache con TTL"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar clave de cache
            cache_key_str = cache_key(func.__name__, *args, *kwargs.values())
            
            # Intentar obtener del cache
            cached_result = await redis_cache.get(cache_key_str)
            if cached_result is not None:
                print(f"🚀 Cache hit para {func.__name__}")
                return cached_result
            
            # Cache miss - ejecutar función
            print(f"🔍 Cache miss para {func.__name__} - ejecutando función")
            result = await func(*args, **kwargs)
            
            # Guardar en cache
            await redis_cache.set(cache_key_str, result, seconds)
            print(f"💾 Resultado guardado en cache por {seconds}s")
            
            return result
        return wrapper
    return decorator
'''



