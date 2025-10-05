# Guía de Configuración de Weaviate en Railway

## 🔧 Variables de Entorno Necesarias

### 1. **WEAVIATE_URL**
- **Formato**: `https://tu-cluster.railway.app` o `http://localhost:8080`
- **Dónde encontrarla**: En Railway, en la sección "Variables" de tu servicio Weaviate
- **Ejemplo**: `https://weaviate-production-abc123.up.railway.app`

### 2. **WEAVIATE_API_KEY** (Opcional)
- **Cuándo se necesita**: Solo si tu instancia de Weaviate requiere autenticación
- **Dónde encontrarla**: En Railway, en la sección "Variables" de tu servicio Weaviate
- **Ejemplo**: `sk-1234567890abcdef`

## 🚀 Pasos para Configurar

### Paso 1: Verificar tu Servicio Weaviate
1. Ve a Railway Dashboard
2. Busca tu servicio Weaviate
3. Verifica que esté ejecutándose (estado "Running")

### Paso 2: Obtener la URL
1. Haz clic en tu servicio Weaviate
2. Ve a la pestaña "Variables" o "Environment"
3. Busca variables como:
   - `WEAVIATE_URL`
   - `WEAVIATE_HOST`
   - `PUBLIC_URL`
   - `RAILWAY_PUBLIC_DOMAIN`

### Paso 3: Configurar en tu Backend
1. Ve a tu servicio Backend en Railway
2. Agrega estas variables de entorno:
   ```
   WEAVIATE_URL=https://tu-weaviate-url.railway.app
   WEAVIATE_API_KEY=tu-api-key-si-es-necesaria
   ```

## 🔍 Si No Encuentras las Variables

### Opción 1: Crear Variables Manualmente
1. En Railway, ve a tu servicio Weaviate
2. Pestaña "Variables"
3. Agrega:
   - `WEAVIATE_URL` = `https://tu-dominio.railway.app`
   - `WEAVIATE_API_KEY` = `tu-clave-si-es-necesaria`

### Opción 2: Usar Variables por Defecto
Si no tienes Weaviate en Railway, puedes usar:
- `WEAVIATE_URL` = `http://localhost:8080` (para desarrollo local)
- `WEAVIATE_API_KEY` = (dejar vacío)

## 🧪 Probar la Conexión

### Script de Prueba
```bash
cd b2bproyecto/backend
python test_weaviate_connection.py
```

### Endpoint de Prueba
```bash
curl http://localhost:8000/api/v1/weaviate/status
```

## 📋 Checklist de Configuración

- [ ] Servicio Weaviate ejecutándose en Railway
- [ ] Variables de entorno configuradas
- [ ] Backend conectado a Weaviate
- [ ] Pruebas de conexión exitosas
- [ ] Indexación de servicios funcionando
- [ ] Búsqueda semántica operativa

## 🆘 Solución de Problemas

### Error: "No se puede conectar a Weaviate"
- Verifica que la URL sea correcta
- Asegúrate de que el servicio esté ejecutándose
- Revisa los logs de Railway

### Error: "Authentication failed"
- Verifica la API key
- Algunas instancias no requieren autenticación

### Error: "Schema not found"
- Ejecuta la indexación de servicios primero
- Verifica que el esquema se haya creado correctamente
