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
        
        # En Railway, preferir usar la URL pública del servicio si está disponible
        railway_weaviate_url = os.getenv("RAILWAY_SERVICE_WEAVIATE_URL")
        if railway_weaviate_url and "railway.app" in railway_weaviate_url:
            # Usar la URL pública de Railway (más confiable que nombres internos)
            if not railway_weaviate_url.startswith(('http://', 'https://')):
                railway_weaviate_url = f"https://{railway_weaviate_url}"
            self.base_url = railway_weaviate_url
            logger.info(f"🔧 Usando URL pública de Weaviate desde Railway: {self.base_url}")
        elif "railway.app" in weaviate_url and "localhost" not in weaviate_url:
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
        # Configurar schema si la conexión es exitosa
        if self.connected:
            self._setup_schema()

    def _initialize_connection(self):
        """Inicializar la conexión HTTP con Weaviate"""
        try:
            # Limpiar URL
            if not self.base_url.startswith(('http://', 'https://')):
                self.base_url = f"https://{self.base_url}"
            
            # Remover puerto duplicado si existe
            if ":8080:8080" in self.base_url:
                self.base_url = self.base_url.replace(":8080:8080", ":8080")
            
            # Si la URL es pública de Railway, puede requerir HTTPS
            # Si es interna (weaviate:8080), usar HTTP
            if "railway.app" in self.base_url:
                # URL pública, asegurar HTTPS
                if not self.base_url.startswith('https://'):
                    self.base_url = self.base_url.replace('http://', 'https://')
            elif "weaviate" in self.base_url.lower() and ":8080" in self.base_url:
                # URL interna, usar HTTP
                if not self.base_url.startswith('http://'):
                    self.base_url = self.base_url.replace('https://', 'http://')
                # Intentar diferentes variaciones del nombre del servicio
                test_urls = [
                    self.base_url.replace("weaviate", "Weaviate"),
                    self.base_url.replace("Weaviate", "weaviate"),
                    self.base_url
                ]
            else:
                test_urls = [self.base_url]
            
            logger.info(f"🔗 Conectando a Weaviate en: {self.base_url}")
            
            # Probar conexión
            if "test_urls" in locals():
                # Probar con diferentes variaciones
                connected = False
                for test_url in test_urls:
                    try:
                        response = requests.get(f"{test_url}/v1/meta", timeout=10, verify=False)
                        if response.status_code == 200:
                            self.base_url = test_url
                            self.connected = True
                            connected = True
                            logger.info(f"✅ Conexión a Weaviate establecida exitosamente en: {test_url}")
                            break
                    except Exception as e:
                        logger.debug(f"⚠️ No se pudo conectar a {test_url}: {str(e)}")
                        continue
                
                if not connected:
                    logger.error(f"❌ No se pudo conectar a Weaviate con ninguna de las URLs probadas")
                    self.connected = False
            else:
                # Probar con la URL única
                try:
                    response = requests.get(f"{self.base_url}/v1/meta", timeout=10, verify=False)
                    if response.status_code == 200:
                        self.connected = True
                        logger.info("✅ Conexión a Weaviate establecida exitosamente")
                    else:
                        logger.error(f"❌ Error de conexión: {response.status_code}")
                        self.connected = False
                except Exception as e:
                    logger.error(f"❌ Error al conectar: {str(e)}")
                    self.connected = False
                
        except Exception as e:
            logger.error(f"❌ Error al inicializar Weaviate: {str(e)}")
            self.connected = False

    def _check_schema_exists(self) -> bool:
        """Verificar si el schema de la clase existe en Weaviate"""
        try:
            url = f"{self.base_url}/v1/schema/{self.class_name}"
            headers = self._build_search_headers()
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error al verificar schema: {str(e)}")
            return False
    
    def _get_schema(self) -> Optional[Dict[str, Any]]:
        """Obtener el schema actual de la clase"""
        try:
            url = f"{self.base_url}/v1/schema/{self.class_name}"
            headers = self._build_search_headers()
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Error al obtener schema: {str(e)}")
            return None
    
    def _check_schema_has_vectorizer(self) -> bool:
        """Verificar si el schema tiene vectorizador configurado"""
        schema = self._get_schema()
        if not schema:
            return False
        
        # Verificar si tiene vectorizer configurado
        vectorizer = schema.get('vectorizer')
        if not vectorizer or vectorizer == 'none':
            logger.warning(f"⚠️ Schema '{self.class_name}' no tiene vectorizador configurado")
            return False
        
        # Verificar si tiene moduleConfig para text2vec-ollama
        module_config = schema.get('moduleConfig', {})
        if 'text2vec-ollama' not in module_config:
            logger.warning(f"⚠️ Schema '{self.class_name}' no tiene módulo text2vec-ollama configurado")
            return False
        
        logger.info(f"✅ Schema '{self.class_name}' tiene vectorizador '{vectorizer}' configurado")
        return True
    
    def _delete_schema(self) -> bool:
        """Eliminar el schema existente (para recrearlo)"""
        try:
            url = f"{self.base_url}/v1/schema/{self.class_name}"
            headers = self._build_search_headers()
            response = requests.delete(url, headers=headers, timeout=30)
            if response.status_code in [200, 204]:
                logger.info(f"✅ Schema '{self.class_name}' eliminado exitosamente")
                return True
            else:
                logger.error(f"❌ Error al eliminar schema: HTTP {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error al eliminar schema: {str(e)}")
            return False
    
    def _setup_schema(self):
        """Configurar el esquema de Weaviate para servicios con Ollama usando REST API v1"""
        try:
            if not self.connected:
                logger.error("❌ Conexión a Weaviate no disponible para configurar schema")
                return
            
            # Verificar si el schema ya existe y tiene vectorizador
            if self._check_schema_exists():
                if self._check_schema_has_vectorizer():
                    logger.info(f"✅ Schema '{self.class_name}' ya existe y tiene vectorizador configurado")
                    return
                else:
                    logger.warning(f"⚠️ Schema '{self.class_name}' existe pero no tiene vectorizador. Eliminando para recrearlo...")
                    self._delete_schema()
            
            # Configuración de Ollama
            # En Railway, los servicios se comunican usando nombres de servicio internos
            # Si OLLAMA_ENDPOINT no está configurado, intentar detectar el endpoint correcto
            ollama_endpoint = os.getenv("OLLAMA_ENDPOINT") or os.getenv("OLLAMA_URL")
            if not ollama_endpoint:
                # En Railway, usar el nombre del servicio interno
                # Si estamos en Railway, usar el nombre del servicio
                if "railway" in os.getenv("RAILWAY_ENVIRONMENT", "").lower() or os.getenv("RAILWAY_SERVICE_NAME"):
                    ollama_endpoint = "http://ollama:11434"
                    logger.info("🔧 Detectado Railway: usando endpoint interno de Ollama")
                else:
                    ollama_endpoint = "http://host.docker.internal:11434"
                    logger.info("🔧 Modo local: usando host.docker.internal")
            else:
                logger.info(f"🔧 Usando endpoint de Ollama desde variable de entorno: {ollama_endpoint}")
            
            ollama_model = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
            
            logger.info(f"🤖 Configurando schema con Ollama: {ollama_endpoint} con modelo: {ollama_model}")
            
            # Crear el schema usando REST API v1
            schema_url = f"{self.base_url}/v1/schema"
            headers = self._build_search_headers()
            headers['Content-Type'] = 'application/json'
            
            schema_definition = {
                "class": self.class_name,
                "description": "Servicios de la plataforma B2B",
                "vectorizer": "text2vec-ollama",
                "moduleConfig": {
                    "text2vec-ollama": {
                        "model": ollama_model,
                        "apiEndpoint": ollama_endpoint,
                        "vectorizeClassName": False
                    }
                },
                "properties": [
                    {
                        "name": "id_servicio",
                        "dataType": ["int"],
                        "description": "ID del servicio en la base de datos"
                    },
                    {
                        "name": "nombre",
                        "dataType": ["text"],
                        "description": "Nombre del servicio",
                        "moduleConfig": {
                            "text2vec-ollama": {
                                "skip": False,
                                "vectorizePropertyName": False
                            }
                        }
                    },
                    {
                        "name": "descripcion",
                        "dataType": ["text"],
                        "description": "Descripción del servicio",
                        "moduleConfig": {
                            "text2vec-ollama": {
                                "skip": False,
                                "vectorizePropertyName": False
                            }
                        }
                    },
                    {
                        "name": "precio",
                        "dataType": ["number"],
                        "description": "Precio del servicio",
                        "moduleConfig": {
                            "text2vec-ollama": {
                                "skip": True
                            }
                        }
                    },
                    {
                        "name": "categoria",
                        "dataType": ["text"],
                        "description": "Categoría del servicio",
                        "moduleConfig": {
                            "text2vec-ollama": {
                                "skip": False,
                                "vectorizePropertyName": False
                            }
                        }
                    },
                    {
                        "name": "empresa",
                        "dataType": ["text"],
                        "description": "Nombre de la empresa proveedora",
                        "moduleConfig": {
                            "text2vec-ollama": {
                                "skip": False,
                                "vectorizePropertyName": False
                            }
                        }
                    },
                    {
                        "name": "ubicacion",
                        "dataType": ["text"],
                        "description": "Ubicación del servicio",
                        "moduleConfig": {
                            "text2vec-ollama": {
                                "skip": True
                            }
                        }
                    },
                    {
                        "name": "estado",
                        "dataType": ["text"],
                        "description": "Estado del servicio (activo/inactivo)",
                        "moduleConfig": {
                            "text2vec-ollama": {
                                "skip": True
                            }
                        }
                    }
                ]
            }
            
            response = requests.post(schema_url, json=schema_definition, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Schema '{self.class_name}' creado exitosamente con Ollama")
            else:
                logger.error(f"❌ Error al crear schema: HTTP {response.status_code} - {response.text}")
            
        except Exception as e:
            logger.error(f"❌ Error al configurar schema de Weaviate: {str(e)}")
    
    async def index_servicios(self, limit: int = 100):
        """Indexar servicios desde la base de datos a Weaviate"""
        if not self.connected:
            logger.error("❌ Conexión a Weaviate no disponible")
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
        """Indexar un servicio individual en Weaviate usando HTTP directo"""
        if not self.connected:
            logger.error("❌ Conexión a Weaviate no disponible")
            return False
        
        try:
            # Preparar datos para Weaviate (formato HTTP API)
            servicio_data = {
                "class": self.class_name,
                "properties": {
                    "id_servicio": servicio.get('id_servicio'),
                    "nombre": servicio.get('nombre') or "",
                    "descripcion": servicio.get('descripcion') or "",
                    "precio": float(servicio.get('precio', 0)) if servicio.get('precio') else 0.0,
                    "categoria": servicio.get('categoria') or "",
                    "empresa": servicio.get('empresa') or "",
                    "ubicacion": "",  # Campo vacío por ahora
                    "estado": "activo" if servicio.get('estado') else "inactivo"
                }
            }
            
            # Insertar objeto en Weaviate usando HTTP POST
            url = f"{self.base_url}/v1/objects"
            headers = self._build_search_headers()
            headers['Content-Type'] = 'application/json'
            
            response = requests.post(url, json=servicio_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.debug(f"✅ Servicio {servicio.get('id_servicio', 'unknown')} indexado exitosamente")
                return True
            else:
                logger.error(f"❌ Error al indexar servicio {servicio.get('id_servicio', 'unknown')}: HTTP {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error al indexar servicio {servicio.get('id_servicio', 'unknown')}: {str(e)}")
            return False
    
    def _build_search_request_params(self, limit: int = 1000) -> dict:
        """Construye los parámetros para la petición de búsqueda"""
        return {
            'class': self.class_name,
            'limit': limit
        }
    
    def _build_search_headers(self) -> dict:
        """Construye los headers para la petición de búsqueda"""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    def _fetch_objects_from_weaviate(self, limit: int = 1000) -> Optional[List[Dict[str, Any]]]:
        """Obtiene objetos de Weaviate mediante HTTP"""
        search_url = f"{self.base_url}/v1/objects"
        params = self._build_search_request_params(limit=limit)
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
    
    def _search_vectorial_nativa(self, query: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Búsqueda vectorial nativa usando REST API v1 con GraphQL (nearText)"""
        try:
            # Escapar comillas y caracteres especiales para GraphQL
            query_escaped = query.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            
            # Construir query GraphQL para búsqueda vectorial
            graphql_query = {
                "query": f"""{{
                    Get {{
                        {self.class_name} (
                            nearText: {{
                                concepts: ["{query_escaped}"]
                            }}
                            limit: {limit}
                        ) {{
                            id_servicio
                            nombre
                            descripcion
                            precio
                            categoria
                            empresa
                            ubicacion
                            estado
                            _additional {{
                                distance
                                id
                            }}
                        }}
                    }}
                }}"""
            }
            
            # Enviar query a Weaviate usando REST API v1 /v1/graphql
            url = f"{self.base_url}/v1/graphql"
            headers = self._build_search_headers()
            headers['Content-Type'] = 'application/json'
            
            response = requests.post(url, json=graphql_query, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    logger.error(f"❌ Error en query GraphQL: {data['errors']}")
                    return None
                
                # Extraer resultados
                get_data = data.get('data', {}).get('Get', {}).get(self.class_name, [])
                logger.info(f"✅ Búsqueda vectorial: {len(get_data)} resultados encontrados")
                return get_data
            else:
                logger.error(f"❌ Error en búsqueda vectorial: HTTP {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda vectorial nativa: {str(e)}")
            return None
    
    def _search_hibrida_nativa(self, query: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Búsqueda híbrida nativa usando REST API v1 con GraphQL (hybrid search con BM25 + Vectorial)"""
        try:
            # Escapar comillas y caracteres especiales para GraphQL
            query_escaped = query.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            
            # Construir query GraphQL para búsqueda híbrida
            graphql_query = {
                "query": f"""{{
                    Get {{
                        {self.class_name} (
                            hybrid: {{
                                query: "{query_escaped}"
                            }}
                            limit: {limit}
                        ) {{
                            id_servicio
                            nombre
                            descripcion
                            precio
                            categoria
                            empresa
                            ubicacion
                            estado
                            _additional {{
                                distance
                                score
                                id
                            }}
                        }}
                    }}
                }}"""
            }
            
            # Enviar query a Weaviate usando REST API v1 /v1/graphql
            url = f"{self.base_url}/v1/graphql"
            headers = self._build_search_headers()
            headers['Content-Type'] = 'application/json'
            
            response = requests.post(url, json=graphql_query, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    logger.error(f"❌ Error en query GraphQL híbrida: {data['errors']}")
                    return None
                
                # Extraer resultados
                get_data = data.get('data', {}).get('Get', {}).get(self.class_name, [])
                logger.info(f"✅ Búsqueda híbrida nativa: {len(get_data)} resultados encontrados")
                return get_data
            else:
                logger.error(f"❌ Error en búsqueda híbrida: HTTP {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda híbrida nativa: {str(e)}")
            return None
    
    def _process_graphql_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesa los resultados de GraphQL y los convierte en formato de servicio"""
        servicios = []
        for result in results:
            servicio = {
                "id_servicio": result.get("id_servicio"),
                "nombre": result.get("nombre", ""),
                "descripcion": result.get("descripcion", ""),
                "precio": result.get("precio", 0.0),
                "categoria": result.get("categoria", ""),
                "empresa": result.get("empresa", ""),
                "ubicacion": result.get("ubicacion", ""),
                "estado": result.get("estado", "activo")
            }
            servicios.append(servicio)
        return servicios
    
    def search_servicios(self, query: str, limit: int = 10, use_hybrid: bool = True) -> List[Dict[str, Any]]:
        """
        Buscar servicios usando búsqueda nativa de Weaviate (REST API v1)
        
        Args:
            query: Texto de búsqueda
            limit: Número máximo de resultados
            use_hybrid: Si True, usa búsqueda híbrida (BM25 + Vectorial). Si False, solo vectorial.
        """
        if not self.connected:
            logger.error("❌ Conexión a Weaviate no disponible")
            return []
        
        if not query or not query.strip():
            logger.warning("⚠️ Query vacía, retornando lista vacía")
            return []
        
        # Asegurar que el schema esté configurado antes de buscar
        if not self._check_schema_exists():
            logger.warning("⚠️ Schema no existe, intentando crearlo...")
            self._setup_schema()
        
        try:
            # Escapar comillas en la query para GraphQL
            query_escaped = query.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            
            if use_hybrid:
                logger.info(f"🔍 Búsqueda híbrida nativa (BM25 + Vectorial) con query: '{query}'")
                results = self._search_hibrida_nativa(query_escaped, limit)
            else:
                logger.info(f"🔍 Búsqueda vectorial nativa con query: '{query}'")
                results = self._search_vectorial_nativa(query_escaped, limit)
            
            if results is None:
                logger.warning("⚠️ No se obtuvieron resultados de Weaviate")
                return []
            
            # Procesar resultados
            servicios = self._process_graphql_results(results)
            
            logger.info(f"📊 Resultados encontrados: {len(servicios)}")
            return servicios
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {str(e)}")
            # Fallback a método anterior si hay error
            logger.info("🔄 Intentando fallback a método anterior...")
            return self._search_fallback(query, limit)
    
    def _search_fallback(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Método de fallback si la búsqueda nativa falla"""
        try:
            # Obtener objetos de Weaviate (aumentar límite para obtener más resultados)
            fetch_limit = max(limit * 10, 1000)
            objects = self._fetch_objects_from_weaviate(limit=fetch_limit)
            if objects is None:
                return []
            
            # Procesar objetos a servicios
            servicios = self._process_objects_to_servicios(objects)
            
            # Aplicar búsqueda híbrida si hay query
            servicios = self._apply_hybrid_search_filter(servicios, query, limit)
            
            logger.info(f"📊 Resultados fallback: {len(servicios)}")
            return servicios
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda fallback: {str(e)}")
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
