"""
Servicio para conexión y operaciones con Weaviate
Configurado para usar HTTP directo con Railway
"""
import requests
import logging
import os
import json
from typing import List, Dict, Any, Optional
from app.services.direct_db_service import direct_db_service

logger = logging.getLogger(__name__)

'''
class WeaviateService:
    def __init__(self):
        """Inicializar el cliente de Weaviate con configuración para Ollama"""
        self.client = None
        self.class_name = "Servicios"
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializar la conexión con Weaviate v4 usando la nueva API"""
        try:
            # Configuración para Weaviate con Ollama local
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8082")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            
            logger.info(f"🔗 Conectando a Weaviate en: {weaviate_url}")
            logger.info("🤖 Configurado para usar Ollama local como proveedor de embeddings")
            
            # Usar la nueva API de Weaviate v4
            if weaviate_api_key and weaviate_api_key.strip():
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=weaviate_url,
                    auth_credentials=weaviate.AuthApiKey(api_key=weaviate_api_key)
                )
                logger.info("🔑 Usando autenticación con API key")
            else:
                # Limpiar la URL para conexión local
                clean_host = weaviate_url.replace("http://", "").replace("https://", "")
                # Remover puerto duplicado si existe
                if ":8082:8080" in clean_host:
                    clean_host = clean_host.replace(":8082:8080", ":8082")
                elif ":8080:8080" in clean_host:
                    clean_host = clean_host.replace(":8080:8080", ":8080")
                self.client = weaviate.connect_to_local(host=clean_host)
                logger.info(f"🔓 Usando acceso local en: {clean_host}")
            
            # Verificar conexión
            if self.client.is_ready():
                logger.info("✅ Conexión a Weaviate establecida exitosamente")
                self._setup_schema()
            else:
                logger.error("❌ No se pudo conectar a Weaviate")
                
        except Exception as e:
            logger.error(f"❌ Error al inicializar Weaviate: {str(e)}")
            self.client = None
 '''
 
class WeaviateService:
    def __init__(self):
        """Inicializar el servicio de Weaviate usando HTTP directo"""
        # Detectar si estamos en desarrollo local
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        
        # Si la URL contiene 'railway.app' pero estamos en local, usar localhost
        if "railway.app" in weaviate_url and "localhost" not in weaviate_url:
            # Estamos en desarrollo local pero la URL es de Railway
            # Usar localhost para desarrollo
            self.base_url = "http://localhost:8080"
            logger.info("🔧 Modo desarrollo: usando localhost en lugar de Railway")
        else:
            self.base_url = weaviate_url
            
        self.api_key = os.getenv("WEAVIATE_API_KEY", "")
        self.class_name = "Servicios"
        self.connected = False
        self._initialize_connection()

    def _initialize_connection(self):
        """Inicializar la conexión HTTP con Weaviate"""
        try:
            # Limpiar URL
            if not self.base_url.startswith(('http://', 'https://')):
                self.base_url = f"https://{self.base_url}"
            
            # Remover puerto duplicado si existe
            if ":8080:8080" in self.base_url:
                self.base_url = self.base_url.replace(":8080:8080", ":8080")
            
            logger.info(f"🔗 Conectando a Weaviate en: {self.base_url}")
            
            # Probar conexión
            response = requests.get(f"{self.base_url}/v1/meta", timeout=10)
            
            if response.status_code == 200:
                self.connected = True
                logger.info("✅ Conexión a Weaviate establecida exitosamente")
            else:
                logger.error(f"❌ Error de conexión: {response.status_code}")
                self.connected = False
                
        except Exception as e:
            logger.error(f"❌ Error al inicializar Weaviate: {str(e)}")
            self.connected = False

    def _setup_schema(self):
        """Configurar el esquema de Weaviate para servicios con Ollama v4"""
        try:
            if not self.client:
                return
                
            # Verificar si la colección ya existe
            if self.client.collections.exists(self.class_name):
                logger.info(f"✅ Colección '{self.class_name}' ya existe en Weaviate")
                return
            
            # Configuración de Ollama - usar host.docker.internal para acceso desde contenedor
            ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://host.docker.internal:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
            
            logger.info(f"🤖 Configurando Ollama: {ollama_endpoint} con modelo: {ollama_model}")
            
            # Crear la colección con vectorizador Ollama
            self.client.collections.create(
                name=self.class_name,
                description="Servicios de la plataforma B2B",
                vector_config=[
                    Configure.Vectors.text2vec_ollama(
                        name="servicio_vector",
                        source_properties=["nombre", "descripcion", "categoria", "empresa"],
                        api_endpoint=ollama_endpoint,
                        model=ollama_model,
                    )
                ],
                properties=[
                    weaviate.classes.config.Property(
                        name="id_servicio",
                        data_type=weaviate.classes.config.DataType.INT,
                        description="ID del servicio en la base de datos"
                    ),
                    weaviate.classes.config.Property(
                        name="nombre",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Nombre del servicio"
                    ),
                    weaviate.classes.config.Property(
                        name="descripcion",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Descripción del servicio"
                    ),
                    weaviate.classes.config.Property(
                        name="precio",
                        data_type=weaviate.classes.config.DataType.NUMBER,
                        description="Precio del servicio"
                    ),
                    weaviate.classes.config.Property(
                        name="categoria",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Categoría del servicio"
                    ),
                    weaviate.classes.config.Property(
                        name="empresa",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Nombre de la empresa proveedora"
                    ),
                    weaviate.classes.config.Property(
                        name="ubicacion",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Ubicación del servicio"
                    ),
                    weaviate.classes.config.Property(
                        name="estado",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Estado del servicio (activo/inactivo)"
                    )
                ]
            )
            
            logger.info(f"✅ Colección '{self.class_name}' creada exitosamente con Ollama")
            
        except Exception as e:
            logger.error(f"❌ Error al configurar esquema de Weaviate: {str(e)}")
    
    async def index_servicios(self, limit: int = 100):
        """Indexar servicios desde la base de datos a Weaviate"""
        if not self.client:
            logger.error("❌ Cliente de Weaviate no disponible")
            return False
        
        try:
            logger.info(f"🔍 Iniciando indexación de servicios (límite: {limit})")
            
            # Obtener servicios de la base de datos
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
                LIMIT $1
            """
            
            result = await conn.fetch(query, limit)
            logger.info(f"📊 Servicios encontrados: {len(result)}")
            
            # Indexar cada servicio
            for servicio in result:
                self._index_servicio(servicio)
            
            await direct_db_service.pool.release(conn)
            logger.info("✅ Indexación de servicios completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al indexar servicios: {str(e)}")
            return False
    
    def _index_servicio(self, servicio: Dict[str, Any]):
        """Indexar un servicio individual en Weaviate"""
        try:
            # Preparar datos para Weaviate
            servicio_data = {
                "id_servicio": servicio['id_servicio'],
                "nombre": servicio['nombre'] or "",
                "descripcion": servicio['descripcion'] or "",
                "precio": float(servicio['precio']) if servicio['precio'] else 0.0,
                "categoria": servicio['categoria'] or "",
                "empresa": servicio['empresa'] or "",
                "ubicacion": "",  # Campo vacío por ahora
                "estado": "activo" if servicio['estado'] else "inactivo"
            }
            
            # Obtener la colección y crear objeto (con vectorización automática)
            collection = self.client.collections.get(self.class_name)
            collection.data.insert(servicio_data)
            
            logger.debug(f"✅ Servicio {servicio['id_servicio']} indexado con Ollama")
            
        except Exception as e:
            logger.error(f"❌ Error al indexar servicio {servicio.get('id_servicio', 'unknown')}: {str(e)}")
    
    def search_servicios(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Buscar servicios usando HTTP directo con Weaviate"""
        if not self.connected:
            logger.error("❌ Conexión a Weaviate no disponible")
            return []
        
        try:
            logger.info(f"🔍 Buscando servicios con query: '{query}' (usando HTTP directo)")
            
            # Usar búsqueda HTTP directa
            search_url = f"{self.base_url}/v1/objects"
            params = {
                'class': self.class_name,
                'limit': limit
            }
            
            # Obtener todos los objetos (sin filtro HTTP para evitar 404)
            logger.info("🔍 Obteniendo todos los objetos de Weaviate (filtro local se aplicará después)")
            
            # Headers para la petición
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Debug: mostrar URL completa
            full_url = f"{search_url}?{requests.compat.urlencode(params)}"
            logger.info(f"🔍 URL completa: {full_url}")
            
            # Realizar búsqueda
            response = requests.get(search_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                objects = data.get('objects', [])
                
                # Procesar resultados
                servicios = []
                for obj in objects:
                    properties = obj.get('properties', {})
                    servicios.append({
                        "id_servicio": properties.get("id_servicio"),
                        "nombre": properties.get("nombre"),
                        "descripcion": properties.get("descripcion"),
                        "precio": properties.get("precio"),
                        "categoria": properties.get("categoria"),
                        "empresa": properties.get("empresa"),
                        "ubicacion": properties.get("ubicacion"),
                        "estado": properties.get("estado")
                    })
                
                # Aplicar filtro local si hay query
                if query and query.strip():
                    query_lower = query.lower().strip()
                    servicios_filtrados = []
                    for servicio in servicios:
                        # Buscar en nombre, descripción, categoría y empresa
                        if (query_lower in servicio.get('nombre', '').lower() or
                            query_lower in servicio.get('descripcion', '').lower() or
                            query_lower in servicio.get('categoria', '').lower() or
                            query_lower in servicio.get('empresa', '').lower()):
                            servicios_filtrados.append(servicio)
                    
                    servicios = servicios_filtrados
                    logger.info(f"🔍 Filtro local aplicado: {len(servicios)} resultados de {len(objects)} objetos")
                
                logger.info(f"📊 Resultados encontrados: {len(servicios)}")
                return servicios
            else:
                logger.error(f"❌ Error en búsqueda HTTP: {response.status_code}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda HTTP: {str(e)}")
            return []
    
    def get_servicio_by_id(self, id_servicio: int) -> Optional[Dict[str, Any]]:
        """Obtener un servicio específico por ID"""
        if not self.client:
            return None
        
        try:
            # Obtener la colección
            collection = self.client.collections.get(self.class_name)
            
            # Buscar por ID
            result = collection.query.fetch_objects(
                where=weaviate.classes.query.Filter.by_property("id_servicio").equal(id_servicio),
                limit=1
            )
            
            if result.objects:
                obj = result.objects[0]
                return {
                    "id_servicio": obj.properties.get("id_servicio"),
                    "nombre": obj.properties.get("nombre"),
                    "descripcion": obj.properties.get("descripcion"),
                    "precio": obj.properties.get("precio"),
                    "categoria": obj.properties.get("categoria"),
                    "empresa": obj.properties.get("empresa"),
                    "ubicacion": obj.properties.get("ubicacion"),
                    "estado": obj.properties.get("estado")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error al obtener servicio {id_servicio}: {str(e)}")
            return None
    
    def delete_servicio(self, id_servicio: int) -> bool:
        """Eliminar un servicio del índice de Weaviate"""
        if not self.client:
            return False
        
        try:
            # Obtener la colección
            collection = self.client.collections.get(self.class_name)
            
            # Buscar el objeto por ID
            result = collection.query.fetch_objects(
                where=weaviate.classes.query.Filter.by_property("id_servicio").equal(id_servicio),
                limit=1
            )
            
            if result.objects:
                # Eliminar el objeto usando su UUID
                obj_uuid = result.objects[0].uuid
                collection.data.delete_by_id(obj_uuid)
                logger.info(f"✅ Servicio {id_servicio} eliminado del índice")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error al eliminar servicio {id_servicio}: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del índice de Weaviate usando HTTP"""
        if not self.connected:
            return {"error": "Conexión no disponible"}
        
        try:
            # Obtener información de la colección usando HTTP
            stats_url = f"{self.base_url}/v1/objects"
            params = {
                'class': self.class_name,
                'limit': 1
            }
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.get(stats_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                total_objects = data.get('totalResults', 0)
                
                return {
                    "collection_name": self.class_name,
                    "total_objects": total_objects,
                    "connection_type": "HTTP",
                    "base_url": self.base_url,
                    "status": "active"
                }
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas: {str(e)}")
            return {"error": str(e)}

# Instancia global del servicio
weaviate_service = WeaviateService()
