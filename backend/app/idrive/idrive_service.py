import boto3
import logging
from typing import Optional, Tuple, Dict, Any
from app.core.config import IDRIVE_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, IDRIVE_BUCKET_NAME

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IDriveService:
    def __init__(self):
        self.client = None
        self.bucket_name = IDRIVE_BUCKET_NAME
        self.endpoint_url = IDRIVE_ENDPOINT_URL
        self.access_key = AWS_ACCESS_KEY_ID
        self.secret_key = AWS_SECRET_ACCESS_KEY
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente S3 de iDrive con verificación de credenciales"""
        try:
            if not all([self.access_key, self.secret_key, self.endpoint_url, self.bucket_name]):
                logger.error("❌ Faltan credenciales de iDrive")
                return None
            
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url,
                region_name='us-east-1'  # iDrive2 requiere región
            )
            logger.info("✅ Cliente iDrive inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente iDrive: {str(e)}")
            self.client = None
    
    def test_connection(self) -> Tuple[bool, str]:
        """Prueba la conexión a iDrive y verifica permisos"""
        try:
            if not self.client:
                return False, "Cliente no inicializado"
            
            # Verificar que el bucket existe y es accesible
            response = self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ Conexión a bucket {self.bucket_name} exitosa")
            
            # Verificar permisos de escritura con un archivo de prueba
            test_key = "test_connection.txt"
            test_content = b"Test de conexion iDrive2"
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=test_content
            )
            logger.info("✅ Permisos de escritura verificados")
            
            # Limpiar archivo de prueba
            self.client.delete_object(Bucket=self.bucket_name, Key=test_key)
            logger.info("✅ Archivo de prueba eliminado")
            
            return True, "Conexión exitosa"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error en prueba de conexión: {error_msg}")
            
            if "Access Denied" in error_msg:
                return False, "Permisos insuficientes - Verificar credenciales y políticas"
            elif "NoSuchBucket" in error_msg:
                return False, "Bucket no encontrado - Verificar nombre del bucket"
            elif "InvalidAccessKeyId" in error_msg:
                return False, "Access Key inválida - Verificar credenciales"
            else:
                return False, f"Error de conexión: {error_msg}"
    
    def upload_file(self, file_content: bytes, file_key: str, content_type: str = None) -> Tuple[bool, str, Optional[str]]:
        """Sube un archivo a iDrive con manejo de errores"""
        try:
            if not self.client:
                return False, "Cliente no inicializado", None
            
            # Verificar conexión antes de subir
            connection_ok, connection_msg = self.test_connection()
            if not connection_ok:
                return False, f"Error de conexión: {connection_msg}", None
            
            # Subir archivo
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                **extra_args
            )
            
            # Generar URL del archivo
            file_url = f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
            logger.info(f"✅ Archivo subido exitosamente: {file_key}")
            
            return True, "Archivo subido exitosamente", file_url
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error subiendo archivo {file_key}: {error_msg}")
            
            if "Access Denied" in error_msg:
                return False, "Permisos insuficientes para subir archivo", None
            else:
                return False, f"Error de subida: {error_msg}", None
    
    def get_file_url(self, file_key: str) -> str:
        """Genera la URL pública del archivo"""
        return f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
    
    def delete_file(self, file_key: str) -> Tuple[bool, str]:
        """Elimina un archivo de iDrive"""
        try:
            if not self.client:
                return False, "Cliente no inicializado"
            
            self.client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"✅ Archivo eliminado: {file_key}")
            return True, "Archivo eliminado exitosamente"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error eliminando archivo {file_key}: {error_msg}")
            return False, f"Error eliminando archivo: {error_msg}"

# Instancia global del servicio
idrive_service = IDriveService()

# Cliente S3 para compatibilidad con código existente
idrive_s3_client = idrive_service.client


