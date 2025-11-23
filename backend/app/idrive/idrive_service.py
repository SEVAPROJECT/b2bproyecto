import boto3
import logging
from typing import Optional, Tuple, Dict, Any
from app.core.config import IDRIVE_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, IDRIVE_BUCKET_NAME

# Constantes
AWS_REGION_US_EAST_1 = "us-east-1"
AWS_SERVICE_S3 = "s3"
MSG_FALTAN_CREDENCIALES_IDRIVE = "❌ Faltan credenciales de iDrive"
MSG_CLIENTE_IDRIVE_INICIALIZADO = "✅ Cliente iDrive inicializado correctamente"
MSG_CLIENTE_NO_INICIALIZADO = "Cliente no inicializado"
MSG_CONEXION_BUCKET_EXITOSA = "✅ Conexión a bucket {bucket_name} exitosa"
MSG_PERMISOS_ESCRITURA_VERIFICADOS = "✅ Permisos de escritura verificados"
MSG_ARCHIVO_PRUEBA_ELIMINADO = "✅ Archivo de prueba eliminado"
MSG_CONEXION_EXITOSA = "Conexión exitosa"
MSG_ARCHIVO_SUBIDO_EXITOSAMENTE = "Archivo subido exitosamente"
MSG_ARCHIVO_ELIMINADO_EXITOSAMENTE = "Archivo eliminado exitosamente"
MSG_PERMISOS_INSUFICIENTES = "Permisos insuficientes - Verificar credenciales y políticas"
MSG_PERMISOS_INSUFICIENTES_SUBIR = "Permisos insuficientes para subir archivo"
MSG_BUCKET_NO_ENCONTRADO = "Bucket no encontrado - Verificar nombre del bucket"
MSG_ACCESS_KEY_INVALIDA = "Access Key inválida - Verificar credenciales"
MSG_ERROR_CONEXION = "Error de conexión: {error_msg}"
MSG_ERROR_SUBIDA = "Error de subida: {error_msg}"
MSG_ERROR_ELIMINANDO_ARCHIVO = "Error eliminando archivo: {error_msg}"
ERROR_ACCESS_DENIED = "Access Denied"
ERROR_NO_SUCH_BUCKET = "NoSuchBucket"
ERROR_INVALID_ACCESS_KEY_ID = "InvalidAccessKeyId"
TEST_KEY_CONNECTION = "test_connection.txt"
TEST_CONTENT_IDRIVE = b"Test de conexion iDrive2"
CONTENT_TYPE_KEY = "ContentType"

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
                logger.error(MSG_FALTAN_CREDENCIALES_IDRIVE)
                return None
            
            self.client = boto3.client(
                AWS_SERVICE_S3,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url,
                region_name=AWS_REGION_US_EAST_1  # iDrive2 requiere región
            )
            logger.info(MSG_CLIENTE_IDRIVE_INICIALIZADO)
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente iDrive: {str(e)}")
            self.client = None
    
    def test_connection(self) -> Tuple[bool, str]:
        """Prueba la conexión a iDrive y verifica permisos"""
        try:
            if not self.client:
                return False, MSG_CLIENTE_NO_INICIALIZADO
            
            # Verificar que el bucket existe y es accesible
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(MSG_CONEXION_BUCKET_EXITOSA.format(bucket_name=self.bucket_name))
            
            # Verificar permisos de escritura con un archivo de prueba
            test_key = TEST_KEY_CONNECTION
            test_content = TEST_CONTENT_IDRIVE
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=test_content
            )
            logger.info(MSG_PERMISOS_ESCRITURA_VERIFICADOS)
            
            # Limpiar archivo de prueba
            self.client.delete_object(Bucket=self.bucket_name, Key=test_key)
            logger.info(MSG_ARCHIVO_PRUEBA_ELIMINADO)
            
            return True, MSG_CONEXION_EXITOSA
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error en prueba de conexión: {error_msg}")
            
            if ERROR_ACCESS_DENIED in error_msg:
                return False, MSG_PERMISOS_INSUFICIENTES
            elif ERROR_NO_SUCH_BUCKET in error_msg:
                return False, MSG_BUCKET_NO_ENCONTRADO
            elif ERROR_INVALID_ACCESS_KEY_ID in error_msg:
                return False, MSG_ACCESS_KEY_INVALIDA
            else:
                return False, MSG_ERROR_CONEXION.format(error_msg=error_msg)
    
    def upload_file(self, file_content: bytes, file_key: str, content_type: str = None) -> Tuple[bool, str, Optional[str]]:
        """Sube un archivo a iDrive con manejo de errores"""
        try:
            if not self.client:
                return False, MSG_CLIENTE_NO_INICIALIZADO, None
            
            # Verificar conexión antes de subir
            connection_ok, connection_msg = self.test_connection()
            if not connection_ok:
                return False, MSG_ERROR_CONEXION.format(error_msg=connection_msg), None
            
            # Subir archivo
            extra_args = {}
            if content_type:
                extra_args[CONTENT_TYPE_KEY] = content_type
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                **extra_args
            )
            
            # Generar URL del archivo
            file_url = f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
            logger.info(f"✅ {MSG_ARCHIVO_SUBIDO_EXITOSAMENTE}: {file_key}")
            
            return True, MSG_ARCHIVO_SUBIDO_EXITOSAMENTE, file_url
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error subiendo archivo {file_key}: {error_msg}")
            
            if ERROR_ACCESS_DENIED in error_msg:
                return False, MSG_PERMISOS_INSUFICIENTES_SUBIR, None
            else:
                return False, MSG_ERROR_SUBIDA.format(error_msg=error_msg), None
    
    def get_file_url(self, file_key: str) -> str:
        """Genera la URL pública del archivo"""
        return f"{self.endpoint_url}/{self.bucket_name}/{file_key}"
    
    def delete_file(self, file_key: str) -> Tuple[bool, str]:
        """Elimina un archivo de iDrive"""
        try:
            if not self.client:
                return False, MSG_CLIENTE_NO_INICIALIZADO
            
            self.client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"✅ Archivo eliminado: {file_key}")
            return True, MSG_ARCHIVO_ELIMINADO_EXITOSAMENTE
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error eliminando archivo {file_key}: {error_msg}")
            return False, MSG_ERROR_ELIMINANDO_ARCHIVO.format(error_msg=error_msg)

# Instancia global del servicio
idrive_service = IDriveService()

# Cliente S3 para compatibilidad con código existente
idrive_s3_client = idrive_service.client


