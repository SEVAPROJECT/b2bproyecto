"""
Servicio para conexión y operaciones con Weaviate
Configurado para usar HTTP directo con Railway
"""
import requests
import logging
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from app.services.direct_db_service import direct_db_service

logger = logging.getLogger(__name__)
 
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
    
    def _build_search_request_params(self) -> dict:
        """Construye los parámetros para la petición de búsqueda"""
        return {
            'class': self.class_name,
            'limit': 100
        }
    
    def _build_search_headers(self) -> dict:
        """Construye los headers para la petición de búsqueda"""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    def _fetch_objects_from_weaviate(self) -> Optional[List[Dict[str, Any]]]:
        """Obtiene objetos de Weaviate mediante HTTP"""
        search_url = f"{self.base_url}/v1/objects"
        params = self._build_search_request_params()
        headers = self._build_search_headers()
        
        try:
            response = requests.get(search_url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('objects', [])
            else:
                logger.error(f"❌ Error en búsqueda: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error al obtener objetos de Weaviate: {str(e)}")
            return None
    
    def _process_object_to_servicio(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un objeto de Weaviate y lo convierte en un diccionario de servicio"""
        properties = obj.get('properties', {})
        return {
            "id_servicio": properties.get("id_servicio"),
            "nombre": properties.get("nombre"),
            "descripcion": properties.get("descripcion"),
            "precio": properties.get("precio"),
            "categoria": properties.get("categoria"),
            "empresa": properties.get("empresa"),
            "ubicacion": properties.get("ubicacion"),
            "estado": properties.get("estado")
        }
    
    def _process_objects_to_servicios(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesa todos los objetos y los convierte en servicios"""
        servicios = []
        for obj in objects:
            servicio = self._process_object_to_servicio(obj)
            servicios.append(servicio)
        return servicios
    
    def _check_exact_match(self, query_lower: str, nombre: str, descripcion: str) -> bool:
        """Verifica si hay un match exacto con la query"""
        return query_lower in nombre or query_lower in descripcion
    
    def _check_semantic_match(self, palabras_relacionadas: List[str], nombre: str, descripcion: str) -> bool:
        """Verifica si hay un match semántico con las palabras relacionadas"""
        return any(palabra in nombre or palabra in descripcion for palabra in palabras_relacionadas)
    
    def _should_include_servicio(self, servicio: Dict[str, Any], query_lower: str, 
                                  palabras_relacionadas: List[str], ids_vistos: set) -> Tuple[bool, str]:
        """Determina si un servicio debe incluirse en los resultados y el tipo de match"""
        nombre = servicio.get('nombre', '').lower()
        descripcion = servicio.get('descripcion', '').lower()
        id_servicio = servicio.get('id_servicio')
        
        match_exacto = self._check_exact_match(query_lower, nombre, descripcion)
        match_semantico = self._check_semantic_match(palabras_relacionadas, nombre, descripcion)
        
        if not (match_exacto or match_semantico):
            return False, ""
        
        if id_servicio in ids_vistos:
            return False, ""
        
        tipo_match = "exacto" if match_exacto else "semántico"
        return True, tipo_match
    
    def _apply_hybrid_search_filter(self, servicios: List[Dict[str, Any]], 
                                     query: str, limit: int) -> List[Dict[str, Any]]:
        """Aplica el filtro de búsqueda híbrida a los servicios"""
        if not query or not query.strip():
            return servicios
        
        query_lower = query.lower().strip()
        palabras_relacionadas = self._get_palabras_relacionadas(query_lower)
        logger.info(f"🔍 Palabras relacionadas para '{query_lower}': {palabras_relacionadas}")
        
        servicios_filtrados = []
        ids_vistos = set()
        
        for servicio in servicios:
            should_include, tipo_match = self._should_include_servicio(
                servicio, query_lower, palabras_relacionadas, ids_vistos
            )
            
            if should_include:
                id_servicio = servicio.get('id_servicio')
                servicios_filtrados.append(servicio)
                ids_vistos.add(id_servicio)
                logger.info(f"✅ Match {tipo_match}: {servicio.get('nombre')} (ID: {id_servicio})")
        
        servicios_limitados = servicios_filtrados[:limit]
        logger.info(f"🔍 Búsqueda híbrida: {len(servicios_limitados)} resultados de {len(servicios)} servicios")
        return servicios_limitados
    
    def search_servicios(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Buscar servicios usando búsqueda híbrida (texto + semántica)"""
        if not self.connected:
            logger.error("❌ Conexión a Weaviate no disponible")
            return []
        
        try:
            logger.info(f"🔍 Búsqueda híbrida con query: '{query}' (texto + semántica)")
            
            # Obtener objetos de Weaviate
            objects = self._fetch_objects_from_weaviate()
            if objects is None:
                return []
            
            # Procesar objetos a servicios
            servicios = self._process_objects_to_servicios(objects)
            
            # Aplicar búsqueda híbrida si hay query
            servicios = self._apply_hybrid_search_filter(servicios, query, limit)
            
            logger.info(f"📊 Resultados encontrados: {len(servicios)}")
            return servicios
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda híbrida: {str(e)}")
            return []
    
    def _get_palabras_relacionadas(self, query: str) -> List[str]:
        """Obtener palabras relacionadas semánticamente"""
        # Diccionario de palabras relacionadas
        relaciones = {
            'desarrollo': ['programacion', 'codigo', 'software', 'aplicacion', 'web', 'sitio', 'pagina', 'tienda', 'ecommerce', 'e-commerce', 'online', 'digital', 'tecnologia', 'sistema', 'plataforma'],
            'marketing': ['publicidad', 'promocion', 'ventas', 'comercial', 'campaña', 'redes', 'social', 'digital', 'online', 'seo', 'posicionamiento'],
            'diseño': ['grafico', 'visual', 'creativo', 'logo', 'imagen', 'flyer', 'banner', 'publicitario'],
            'seo': ['posicionamiento', 'google', 'buscadores', 'optimizacion', 'ranking', 'visibilidad'],
            'email': ['correo', 'mailing', 'newsletter', 'campaña', 'marketing', 'promocional']
        }
        
        # Buscar relaciones directas
        palabras = relaciones.get(query, [])
        
        # Buscar relaciones inversas
        for palabra_clave, palabras_relacionadas in relaciones.items():
            if query in palabras_relacionadas:
                palabras.append(palabra_clave)
        
        return list(set(palabras))  # Eliminar duplicados
    
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
