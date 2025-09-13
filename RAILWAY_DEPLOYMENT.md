# 🚀 Guía de Despliegue en Railway - Servicios Múltiples

## 📋 Configuración Actual

Tu proyecto está configurado para desplegar **2 servicios** en el mismo proyecto de Railway:

1. **Backend** (FastAPI + Python)
2. **Frontend** (React + Vite + Nginx)

## 🛠️ Pasos para el Despliegue

### 1. **Crear el Proyecto en Railway**

1. Ve a [Railway.app](https://railway.app)
2. Crea un nuevo proyecto
3. Conecta tu repositorio de GitHub

### 2. **Configurar el Servicio Backend**

1. En Railway, haz clic en **"New Service"**
2. Selecciona **"GitHub Repo"**
3. Elige tu repositorio
4. Railway detectará automáticamente el `railway.toml` y usará el Dockerfile del backend
5. No necesitas configurar un directorio raíz específico

### 3. **Configurar el Servicio Frontend**

1. En Railway, haz clic en **"New Service"** (otra vez)
2. Selecciona **"GitHub Repo"**
3. Elige el mismo repositorio
4. En **"Root Directory"**, selecciona `frontend/`
5. Railway detectará automáticamente el `Dockerfile`

### 4. **Configurar Variables de Entorno**

#### **Backend:**
```
PORT=8000
NODE_ENV=production
DATABASE_URL=tu_url_de_base_de_datos
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_clave_de_supabase
```

#### **Frontend:**
```
PORT=3000
NODE_ENV=production
VITE_API_URL=https://backend-production-xxxx.up.railway.app
```

**⚠️ IMPORTANTE:** Reemplaza `xxxx` con el ID real de tu servicio backend.

### 5. **Obtener la URL del Backend**

1. Una vez desplegado el backend, copia la URL de Railway
2. Actualiza la variable `VITE_API_URL` en el frontend con esa URL
3. Haz redeploy del frontend

## 🔧 Configuración de Archivos

### **Estructura de Archivos:**
```
b2bproyecto/
├── backend/
│   ├── Dockerfile
│   ├── railway-backend.toml
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── railway-frontend.toml
│   └── ...
├── railway.toml (configuración principal)
└── Dockerfile (para el backend)
```

### **Dockerfiles Configurados:**
- ✅ **Backend**: Python 3.12 + FastAPI + Uvicorn
- ✅ **Frontend**: Node.js + Vite + Nginx
- ✅ **Optimizados** para producción
- ✅ **Health checks** incluidos

## 💰 Costo

- **Total**: $5/mes (un solo proyecto con 2 servicios)
- **Incluye**: Recursos ilimitados, mejor rendimiento

## 🚨 Solución de Problemas

### **Error de Nixpacks:**
- Asegúrate de que Railway esté usando Dockerfiles
- Verifica que los directorios raíz estén configurados correctamente

### **Error de CORS:**
- Configura CORS en el backend para permitir el dominio del frontend
- Verifica que `VITE_API_URL` esté configurada correctamente

### **Error de Build:**
- Verifica que todos los archivos estén en el repositorio
- Revisa los logs de build en Railway

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en Railway
2. Verifica las variables de entorno
3. Asegúrate de que ambos servicios estén desplegados

¡Tu aplicación estará lista en minutos! 🎉
