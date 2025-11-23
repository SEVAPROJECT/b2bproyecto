"""
Servicio de almacenamiento de imágenes usando Supabase Storage
"""
import os
import uuid
import asyncio
from typing import Optional, Tuple
import logging
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Constantes de nombres
BUCKET_NAME_IMAGENES = "imagenes"
CARPETA_SERVICIOS = "servicios"
CARPETA_PERFILES = "perfiles"
ARCHIVO_GITKEEP = ".gitkeep"
SEPARADOR_RUTA = "/"
PREFIJO_IMAGENES = "imagenes/"

# Constantes de mensajes
MSG_CLIENTE_SUPABASE_STORAGE_CONFIGURADO = "✅ Cliente Supabase Storage configurado"
MSG_ERROR_CONFIGURANDO_SUPABASE_STORAGE = "❌ Error configurando Supabase Storage: {error}"
MSG_CLIENTE_SUPABASE_NO_CONFIGURADO = "❌ Cliente Supabase no configurado"
MSG_BUCKET_CREADO_EXITOSAMENTE = "✅ Bucket '{bucket}' creado exitosamente"
MSG_BUCKET_YA_EXISTE = "✅ Bucket '{bucket}' ya existe"
MSG_ERROR_CREANDO_BUCKET = "❌ Error creando bucket: {error}"
MSG_INICIALIZANDO_BUCKET = "🔧 Inicializando automáticamente el bucket '{bucket}'..."
MSG_BUCKET_CREADO_AUTOMATICAMENTE = "✅ Bucket '{bucket}' creado automáticamente"
MSG_ERROR_AUTO_INITIALIZE = "❌ Error en auto_initialize: {error}"
MSG_CARPETA_CREADA_AUTOMATICAMENTE = "✅ Carpeta '{folder}' creada automáticamente"
MSG_CARPETA_YA_EXISTE = "✅ Carpeta '{folder}' ya existe"
MSG_NO_SE_PUDO_CREAR_CARPETA = "⚠️ No se pudo crear carpeta '{folder}': {error}"
MSG_ERROR_CREANDO_CARPETAS = "❌ Error creando carpetas: {error}"
MSG_IMAGEN_SUBIDA_EXITOSAMENTE = "✅ Imagen subida exitosamente: {url}"
MSG_ERROR_SUBIENDO_IMAGEN = "❌ Error subiendo imagen a Supabase Storage"
MSG_ERROR_UPLOAD_IMAGE = "❌ Error en upload_image: {error}"
MSG_ELIMINANDO_ARCHIVO = "🔍 Eliminando archivo: {path}"
MSG_IMAGEN_ELIMINADA_EXITOSAMENTE = "✅ Imagen eliminada exitosamente: {path}"
MSG_ERROR_ELIMINANDO_IMAGEN = "❌ Error eliminando imagen: {path}"
MSG_NO_SE_PUDO_EXTRAER_RUTA = "❌ No se pudo extraer la ruta del archivo de: {path}"
MSG_URL_NO_VALIDA = "❌ URL no válida para eliminación: {path}"
MSG_ERROR_DELETE_IMAGE = "❌ Error en delete_image: {error}"
MSG_URL_PUBLICA_OBTENIDA = "✅ URL pública obtenida: {url}"
MSG_ERROR_GET_IMAGE_URL = "❌ Error en get_image_url: {error}"

# Constantes de contenido
CONTENIDO_CARPETA_DUMMY = b"Carpeta creada automaticamente"
TEXTO_ALREADY_EXISTS = "already exists"

# Constantes de tipos MIME
MIME_TYPE_JPEG = "image/jpeg"
MIME_TYPE_PLAIN = "text/plain"
TIPOS_MIME_PERMITIDOS = ["image/jpeg", "image/png", "image/webp", "image/gif"]

# Constantes de opciones de bucket
OPCION_PUBLIC = "public"
OPCION_FILE_SIZE_LIMIT = "file_size_limit"
OPCION_ALLOWED_MIME_TYPES = "allowed_mime_types"
OPCION_CONTENT_TYPE = "content-type"
OPCION_CACHE_CONTROL = "cache-control"

# Constantes de valores
VALOR_TRUE = True
VALOR_FALSE = False
LIMITE_ARCHIVO_50MB = 52428800  # 50MB
LIMITE_ARCHIVO_5MB = 5242880  # 5MB
CACHE_CONTROL_3600 = "3600"

# Constantes de carpetas
CARPETAS_DEFAULT = [CARPETA_SERVICIOS, CARPETA_PERFILES]

class SupabaseStorageService:
    """Servicio para manejar almacenamiento de imágenes en Supabase Storage"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_SERVICE_ROLE_KEY
        self.supabase: Client = None
        self.bucket_name = BUCKET_NAME_IMAGENES  # Bucket para imágenes de servicios
        
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                logger.info(MSG_CLIENTE_SUPABASE_STORAGE_CONFIGURADO)
            except Exception as e:
                logger.error(MSG_ERROR_CONFIGURANDO_SUPABASE_STORAGE.format(error=str(e)))
    
    async def create_bucket_if_not_exists(self) -> bool:
        """Crear el bucket si no existe"""
        try:
            if not self.supabase:
                logger.error(MSG_CLIENTE_SUPABASE_NO_CONFIGURADO)
                return False
            
            # Verificar si el bucket existe (ejecutar llamada síncrona en thread separado)
            buckets = await asyncio.to_thread(
                self.supabase.storage.list_buckets
            )
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            if not bucket_exists:
                # Crear el bucket (ejecutar llamada síncrona en thread separado)
                await asyncio.to_thread(
                    self.supabase.storage.create_bucket,
                    self.bucket_name,
                    {
                        OPCION_PUBLIC: VALOR_TRUE,  # Hacer el bucket público para acceso directo
                        OPCION_FILE_SIZE_LIMIT: LIMITE_ARCHIVO_50MB,  # 50MB límite
                        OPCION_ALLOWED_MIME_TYPES: TIPOS_MIME_PERMITIDOS
                    }
                )
                logger.info(MSG_BUCKET_CREADO_EXITOSAMENTE.format(bucket=self.bucket_name))
            else:
                logger.info(MSG_BUCKET_YA_EXISTE.format(bucket=self.bucket_name))
            
            return True
            
        except Exception as e:
            logger.error(MSG_ERROR_CREANDO_BUCKET.format(error=str(e)))
            return False
    
    async def auto_initialize(self) -> bool:
        """
        Inicialización automática del storage
        Se ejecuta automáticamente en la primera subida de imagen
        """
        try:
            if not self.supabase:
                logger.error(MSG_CLIENTE_SUPABASE_NO_CONFIGURADO)
                return False
            
            # Verificar si el bucket existe (ejecutar llamada síncrona en thread separado)
            buckets = await asyncio.to_thread(
                self.supabase.storage.list_buckets
            )
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            if not bucket_exists:
                logger.info(MSG_INICIALIZANDO_BUCKET.format(bucket=self.bucket_name))
                
                # Crear el bucket automáticamente (ejecutar llamada síncrona en thread separado)
                await asyncio.to_thread(
                    self.supabase.storage.create_bucket,
                    self.bucket_name,
                    {
                        OPCION_PUBLIC: VALOR_TRUE,  # Hacer el bucket público
                        OPCION_FILE_SIZE_LIMIT: LIMITE_ARCHIVO_5MB,  # 5MB límite
                        OPCION_ALLOWED_MIME_TYPES: TIPOS_MIME_PERMITIDOS
                    }
                )
                logger.info(MSG_BUCKET_CREADO_AUTOMATICAMENTE.format(bucket=self.bucket_name))
                
                # Crear carpetas automáticamente
                await self.create_folders()
                
            else:
                logger.info(MSG_BUCKET_YA_EXISTE.format(bucket=self.bucket_name))
            
            return True
            
        except Exception as e:
            logger.error(MSG_ERROR_AUTO_INITIALIZE.format(error=str(e)))
            return False
    
    async def create_folders(self) -> bool:
        """
        Crear carpetas automáticamente en el bucket
        """
        try:
            # Crear archivos dummy para crear las carpetas
            folders = CARPETAS_DEFAULT
            
            for folder in folders:
                try:
                    # Crear un archivo dummy para crear la carpeta (ejecutar llamada síncrona en thread separado)
                    dummy_content = CONTENIDO_CARPETA_DUMMY
                    dummy_path = f"{folder}{SEPARADOR_RUTA}{ARCHIVO_GITKEEP}"
                    
                    await asyncio.to_thread(
                        self.supabase.storage.from_(self.bucket_name).upload,
                        dummy_path,
                        dummy_content,
                        {
                            OPCION_CONTENT_TYPE: MIME_TYPE_PLAIN
                        }
                    )
                    logger.info(MSG_CARPETA_CREADA_AUTOMATICAMENTE.format(folder=folder))
                    
                except Exception as e:
                    # Si ya existe, no es un error
                    if TEXTO_ALREADY_EXISTS in str(e).lower():
                        logger.info(MSG_CARPETA_YA_EXISTE.format(folder=folder))
                    else:
                        logger.warning(MSG_NO_SE_PUDO_CREAR_CARPETA.format(folder=folder, error=str(e)))
            
            return True
            
        except Exception as e:
            logger.error(MSG_ERROR_CREANDO_CARPETAS.format(error=str(e)))
            return False
    
    async def upload_image(self, file_content: bytes, file_name: str, content_type: str = MIME_TYPE_JPEG, folder: str = CARPETA_SERVICIOS) -> Tuple[bool, Optional[str]]:
        """
        Subir una imagen al storage de Supabase
        
        Args:
            file_content: Contenido del archivo en bytes
            file_name: Nombre del archivo
            content_type: Tipo de contenido (MIME type)
            folder: Carpeta donde subir (servicios, perfiles, documentos)
        
        Returns:
            Tuple[bool, Optional[str]]: (éxito, URL_publica)
        """
        try:
            if not self.supabase:
                logger.error(MSG_CLIENTE_SUPABASE_NO_CONFIGURADO)
                return False, None
            
            # Asegurar que el bucket existe
            await self.create_bucket_if_not_exists()
            
            # Generar nombre único para el archivo
            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Crear ruta con carpeta
            file_path = f"{folder}{SEPARADOR_RUTA}{unique_filename}"
            
            # Subir el archivo (ejecutar llamada síncrona en thread separado)
            result = await asyncio.to_thread(
                self.supabase.storage.from_(self.bucket_name).upload,
                file_path,
                file_content,
                {
                    OPCION_CONTENT_TYPE: content_type,
                    OPCION_CACHE_CONTROL: CACHE_CONTROL_3600
                }
            )
            
            if result:
                # Obtener URL pública (ejecutar llamada síncrona en thread separado)
                public_url = await asyncio.to_thread(
                    self.supabase.storage.from_(self.bucket_name).get_public_url,
                    file_path
                )
                logger.info(MSG_IMAGEN_SUBIDA_EXITOSAMENTE.format(url=public_url))
                return VALOR_TRUE, public_url
            else:
                logger.error(MSG_ERROR_SUBIENDO_IMAGEN)
                return VALOR_FALSE, None
                
        except Exception as e:
            logger.error(MSG_ERROR_UPLOAD_IMAGE.format(error=str(e)))
            return VALOR_FALSE, None
    
    async def upload_service_image(self, file_content: bytes, file_name: str, content_type: str = MIME_TYPE_JPEG) -> Tuple[bool, Optional[str]]:
        """Subir imagen de servicio a la carpeta servicios/"""
        # Inicializar automáticamente si no está configurado
        await self.auto_initialize()
        return await self.upload_image(file_content, file_name, content_type, CARPETA_SERVICIOS)
    
    async def upload_profile_image(self, file_content: bytes, file_name: str, content_type: str = MIME_TYPE_JPEG) -> Tuple[bool, Optional[str]]:
        """Subir imagen de perfil a la carpeta perfiles/"""
        # Inicializar automáticamente si no está configurado
        await self.auto_initialize()
        return await self.upload_image(file_content, file_name, content_type, CARPETA_PERFILES)
    
    
    async def delete_image(self, file_path: str) -> bool:
        """
        Eliminar una imagen del storage
        
        Args:
            file_path: URL completa del archivo en el storage
        
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            if not self.supabase:
                logger.error(MSG_CLIENTE_SUPABASE_NO_CONFIGURADO)
                return VALOR_FALSE
            
            # Extraer la ruta del archivo de la URL completa
            # Ejemplo: https://tu-proyecto.supabase.co/storage/v1/object/public/imagenes/servicios/uuid.png
            # Necesitamos: servicios/uuid.png
            
            if PREFIJO_IMAGENES in file_path:
                # Extraer la parte después de 'imagenes/'
                path_parts = file_path.split(PREFIJO_IMAGENES)
                if len(path_parts) > 1:
                    # Remover query parameters si existen
                    full_path = path_parts[1].split('?')[0]
                    logger.info(MSG_ELIMINANDO_ARCHIVO.format(path=full_path))
                    
                    # Eliminar el archivo usando la ruta completa (ejecutar llamada síncrona en thread separado)
                    result = await asyncio.to_thread(
                        self.supabase.storage.from_(self.bucket_name).remove,
                        [full_path]
                    )
                    
                    if result:
                        logger.info(MSG_IMAGEN_ELIMINADA_EXITOSAMENTE.format(path=full_path))
                        return VALOR_TRUE
                    else:
                        logger.error(MSG_ERROR_ELIMINANDO_IMAGEN.format(path=full_path))
                        return VALOR_FALSE
                else:
                    logger.error(MSG_NO_SE_PUDO_EXTRAER_RUTA.format(path=file_path))
                    return VALOR_FALSE
            else:
                logger.error(MSG_URL_NO_VALIDA.format(path=file_path))
                return VALOR_FALSE
                
        except Exception as e:
            logger.error(MSG_ERROR_DELETE_IMAGE.format(error=str(e)))
            return VALOR_FALSE
    
    async def get_image_url(self, file_path: str) -> Optional[str]:
        """
        Obtener URL pública de una imagen
        
        Args:
            file_path: Ruta del archivo en el storage
        
        Returns:
            Optional[str]: URL pública de la imagen
        """
        try:
            if not self.supabase:
                logger.error(MSG_CLIENTE_SUPABASE_NO_CONFIGURADO)
                return None
            
            # Extraer el nombre del archivo de la URL
            file_name = os.path.basename(file_path)
            
            # Obtener URL pública (ejecutar llamada síncrona en thread separado)
            public_url = await asyncio.to_thread(
                self.supabase.storage.from_(self.bucket_name).get_public_url,
                file_name
            )
            logger.info(MSG_URL_PUBLICA_OBTENIDA.format(url=public_url))
            return public_url
            
        except Exception as e:
            logger.error(MSG_ERROR_GET_IMAGE_URL.format(error=str(e)))
            return None

# Instancia global del servicio
supabase_storage_service = SupabaseStorageService()
