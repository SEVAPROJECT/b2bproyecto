# Configuración de Weaviate para Railway

## 🔧 Variables de Entorno para tu Backend

Agrega estas variables en tu servicio Backend en Railway:

```bash
# URL de Weaviate (reemplaza con tu dominio de Railway)
WEAVIATE_URL=https://tu-weaviate.railway.app

# No necesitas API key porque el acceso anónimo está habilitado
WEAVIATE_API_KEY=

# Configuración para Ollama (opcional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=nomic-embed-text
```

## 🌐 Cómo Obtener la URL de Weaviate

1. **Ve a tu servicio Weaviate en Railway**
2. **Haz clic en la pestaña "Deployments"**
3. **Busca el dominio público** (algo como `weaviate-production-abc123.up.railway.app`)
4. **Usa esa URL** como `WEAVIATE_URL`

## 🧪 Probar la Conexión

Una vez configuradas las variables:

```bash
# Probar conexión
curl https://tu-weaviate.railway.app/v1/meta

# Debería devolver información sobre Weaviate
```

## 📋 Checklist de Configuración

- [ ] Variables agregadas al Backend en Railway
- [ ] URL de Weaviate configurada correctamente
- [ ] Backend desplegado con las nuevas variables
- [ ] Prueba de conexión exitosa
- [ ] Indexación de servicios funcionando
