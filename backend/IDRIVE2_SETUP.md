# Configuración de iDrive2

## Problema Actual
El sistema está configurado para usar almacenamiento local temporal debido a errores de permisos en iDrive2.

## Solución Temporal
Los archivos se guardan localmente en la carpeta `temp_uploads/` con URLs del formato `local://filename`.

## Para Habilitar iDrive2

### 1. Verificar Variables de Entorno
Asegúrate de que tu archivo `.env` tenga estas variables:

```env
IDRIVE_ENDPOINT_URL=https://tu-endpoint-idrive.com
AWS_ACCESS_KEY_ID=tu_access_key_id
AWS_SECRET_ACCESS_KEY=tu_secret_access_key
IDRIVE_BUCKET_NAME=tu_bucket_name
```

### 2. Verificar Permisos del Bucket
El error "Access Denied" indica que las credenciales no tienen permisos suficientes. Verifica:

- **Bucket Policy**: El bucket debe permitir operaciones PUT/POST
- **IAM Permissions**: Las credenciales deben tener permisos para:
  - `s3:PutObject`
  - `s3:PutObjectAcl`
  - `s3:GetObject`
  - `s3:ListBucket`

### 3. Ejemplo de Bucket Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::tu-bucket-name/*"
        },
        {
            "Sid": "AllowUploads",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::tu-account-id:user/tu-iam-user"
            },
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::tu-bucket-name/*"
        }
    ]
}
```

### 4. Probar Conexión
Ejecuta el script de prueba:
```bash
cd b2bproyecto/backend
python test_idrive_connection.py
```

### 5. Habilitar iDrive2
Una vez que los permisos estén correctos, cambia en `providers.py`:

```python
# Cambiar esta línea:
from app.api.v1.dependencies.local_storage import upload_file_locally

# Por esta:
from app.api.v1.dependencies.idrive import upload_file_to_idrive

# Y cambiar la llamada:
idrive_url = await upload_file_locally(...)

# Por:
idrive_url = await upload_file_to_idrive(...)
```

## Estado Actual
- ✅ Almacenamiento local funcionando
- ✅ Archivos se guardan correctamente
- ✅ Endpoint para servir archivos locales
- ⚠️ iDrive2 con problemas de permisos

## Próximos Pasos
1. Resolver permisos de iDrive2
2. Probar conexión exitosa
3. Cambiar a iDrive2 en producción
4. Implementar limpieza de archivos locales
