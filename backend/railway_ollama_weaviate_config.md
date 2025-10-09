# Configuración Ollama + Weaviate en Railway

## 🚀 Configuración Completa

### 1. Servicios en Railway

#### Ollama Service
- **Imagen**: `ollama/ollama`
- **Puerto**: `11434`
- **Variables de entorno**:
  ```
  OLLAMA_HOST=0.0.0.0
  OLLAMA_ORIGINS=*
  ```

#### Weaviate Service
- **Imagen**: `semitechnologies/weaviate:latest`
- **Puerto**: `8080`
- **Variables de entorno**:
  ```
  QUERY_DEFAULTS_LIMIT=25
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
  PERSISTENCE_DATA_PATH=/var/lib/weaviate
  DEFAULT_VECTORIZER_MODULE=none
  ENABLE_MODULES=text2vec-ollama
  CLUSTER_HOSTNAME=node1
  ```

### 2. Variables de Entorno en tu App Principal

```bash
# Weaviate
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=
WEAVIATE_CLASS_NAME=Servicios

# Ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=nomic-embed-text
```

### 3. Configuración del WeaviateService

El servicio ya está configurado para usar Ollama como proveedor de embeddings.

### 4. Scripts de Prueba

Ejecuta estos scripts para verificar la configuración:

```bash
# Configurar
python configurar_ollama_weaviate_railway.py

# Probar conexión
python test_ollama_weaviate_railway.py
```

### 5. Verificación

1. **Ollama**: Debe estar funcionando en `http://ollama:11434`
2. **Weaviate**: Debe estar funcionando en `http://weaviate:8080`
3. **Integración**: Weaviate debe poder usar Ollama para embeddings

### 6. Troubleshooting

#### Si Ollama no funciona:
- Verifica que el servicio esté desplegado
- Revisa los logs de Railway
- Verifica que el puerto 11434 esté expuesto

#### Si Weaviate no funciona:
- Verifica que el servicio esté desplegado
- Revisa las variables de entorno
- Verifica que el puerto 8080 esté expuesto

#### Si la integración falla:
- Verifica que ambos servicios estén funcionando
- Revisa la configuración de módulos en Weaviate
- Verifica que Ollama tenga el modelo correcto

### 7. Modelos Recomendados

Para embeddings en español:
- `nomic-embed-text` (recomendado)
- `mxbai-embed-large`
- `snowflake-arctic-embed`

### 8. Comandos Útiles

```bash
# Verificar estado de Ollama
curl http://ollama:11434/api/tags

# Verificar estado de Weaviate
curl http://weaviate:8080/v1/meta

# Probar integración
python test_ollama_weaviate_railway.py
```
