# Configuraciones de Almacenamiento

## 🎯 Respuesta a tu pregunta

**No, no necesariamente necesitas usar `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`.** Depende del proveedor que uses.

## 📋 Opciones de Configuración

### 1. **AWS S3 (Amazon)**
```env
# AWS S3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
IDRIVE_ENDPOINT_URL=https://s3.amazonaws.com
IDRIVE_BUCKET_NAME=mi-bucket-aws
```

### 2. **iDrive2 (Proveedor específico)**
```env
# iDrive2 - Opción 1 (nombres AWS)
AWS_ACCESS_KEY_ID=tu_access_key_idrive
AWS_SECRET_ACCESS_KEY=tu_secret_key_idrive
IDRIVE_ENDPOINT_URL=https://tu-endpoint-idrive.com
IDRIVE_BUCKET_NAME=mi-bucket-idrive

# iDrive2 - Opción 2 (nombres específicos)
IDRIVE_ACCESS_KEY=tu_access_key_idrive
IDRIVE_SECRET_KEY=tu_secret_key_idrive
IDRIVE_ENDPOINT_URL=https://tu-endpoint-idrive.com
IDRIVE_BUCKET_NAME=mi-bucket-idrive
```

### 3. **DigitalOcean Spaces**
```env
# DigitalOcean Spaces
AWS_ACCESS_KEY_ID=tu_access_key_do
AWS_SECRET_ACCESS_KEY=tu_secret_key_do
IDRIVE_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
IDRIVE_BUCKET_NAME=mi-bucket-do
```

### 4. **Cloudflare R2**
```env
# Cloudflare R2
AWS_ACCESS_KEY_ID=tu_access_key_r2
AWS_SECRET_ACCESS_KEY=tu_secret_key_r2
IDRIVE_ENDPOINT_URL=https://tu-account-id.r2.cloudflarestorage.com
IDRIVE_BUCKET_NAME=mi-bucket-r2
```

### 5. **MinIO (Local/Self-hosted)**
```env
# MinIO
AWS_ACCESS_KEY_ID=tu_access_key_minio
AWS_SECRET_ACCESS_KEY=tu_secret_key_minio
IDRIVE_ENDPOINT_URL=http://localhost:9000
IDRIVE_BUCKET_NAME=mi-bucket-minio
```

## 🔧 Cómo Funciona el Código

El código ahora soporta **múltiples nombres de variables**:

```python
# En config.py
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("IDRIVE_ACCESS_KEY") or os.getenv("ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("IDRIVE_SECRET_KEY") or os.getenv("SECRET_ACCESS_KEY")
```

## 🎯 Para iDrive2 Específicamente

**Verifica en el panel de iDrive2 qué nombres de variables usan:**

1. **Accede al panel de iDrive2**
2. **Busca la sección de API/S3**
3. **Mira qué nombres de variables te proporcionan**

### Posibles nombres que usa iDrive2:
- `IDRIVE_ACCESS_KEY` / `IDRIVE_SECRET_KEY`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (compatible con AWS)
- `ACCESS_KEY_ID` / `SECRET_ACCESS_KEY`

## 🧪 Probar Configuración

Ejecuta el script de verificación:
```bash
cd b2bproyecto/backend
python check_env_variables.py
```

## 💡 Recomendación

1. **Verifica qué credenciales te da iDrive2**
2. **Usa los nombres que te proporcionen**
3. **Si no funciona, prueba con los nombres AWS**
4. **El código soporta múltiples opciones automáticamente**
