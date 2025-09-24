"""
Servicio de almacenamiento de imágenes usando Supabase Storage
"""
import os
import uuid
from typing import Optional, Tuple
import logging
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseStorageService:
    """Servicio para manejar almacenamiento de imágenes en Supabase Storage"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_SERVICE_ROLE_KEY
        self.supabase: Client = None
        self.bucket_name = "imagenes"  # Bucket para imágenes de servicios
        
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                logger.info("✅ Cliente Supabase Storage configurado")
            except Exception as e:
                logger.error(f"❌ Error configurando Supabase Storage: {str(e)}")
    
    async def create_bucket_if_not_exists(self) -> bool:
        """Crear el bucket si no existe"""
        try:
            if not self.supabase:
                logger.error("❌ Cliente Supabase no configurado")
                return False
            
            # Verificar si el bucket existe
            buckets = self.supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            if not bucket_exists:
                # Crear el bucket
                self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={
                        "public": True,  # Hacer el bucket público para acceso directo
                        "file_size_limit": 52428800,  # 50MB límite
                        "allowed_mime_types": ["image/jpeg", "image/png", "image/webp", "image/gif"]
                    }
                )
                logger.info(f"✅ Bucket '{self.bucket_name}' creado exitosamente")
            else:
                logger.info(f"✅ Bucket '{self.bucket_name}' ya existe")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando bucket: {str(e)}")
            return False
    
    async def auto_initialize(self) -> bool:
        """
        Inicialización automática del storage
        Se ejecuta automáticamente en la primera subida de imagen
        """
        try:
            if not self.supabase:
                logger.error("❌ Cliente Supabase no configurado")
                return False
            
            # Verificar si el bucket existe
            buckets = self.supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            if not bucket_exists:
                logger.info(f"🔧 Inicializando automáticamente el bucket '{self.bucket_name}'...")
                
                # Crear el bucket automáticamente
                self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={
                        "public": True,  # Hacer el bucket público
                        "file_size_limit": 5242880,  # 5MB límite
                        "allowed_mime_types": ["image/jpeg", "image/png", "image/webp", "image/gif"]
                    }
                )
                logger.info(f"✅ Bucket '{self.bucket_name}' creado automáticamente")
                
                # Crear carpetas automáticamente
                await self.create_folders()
                
            else:
                logger.info(f"✅ Bucket '{self.bucket_name}' ya existe")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en auto_initialize: {str(e)}")
            return False
    
    async def create_folders(self) -> bool:
        """
        Crear carpetas automáticamente en el bucket
        """
        try:
            # Crear archivos dummy para crear las carpetas
            folders = ["servicios", "perfiles"]
            
            for folder in folders:
                try:
                    # Crear un archivo dummy para crear la carpeta
                    dummy_content = b"# Carpeta creada automáticamente"
                    dummy_path = f"{folder}/.gitkeep"
                    
                    self.supabase.storage.from_(self.bucket_name).upload(
                        dummy_path,
                        dummy_content,
                        file_options={
                            "content-type": "text/plain"
                        }
                    )
                    logger.info(f"✅ Carpeta '{folder}' creada automáticamente")
                    
                except Exception as e:
                    # Si ya existe, no es un error
                    if "already exists" in str(e).lower():
                        logger.info(f"✅ Carpeta '{folder}' ya existe")
                    else:
                        logger.warning(f"⚠️ No se pudo crear carpeta '{folder}': {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando carpetas: {str(e)}")
            return False
    
    async def upload_image(self, file_content: bytes, file_name: str, content_type: str = "image/jpeg", folder: str = "servicios") -> Tuple[bool, Optional[str]]:
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
                logger.error("❌ Cliente Supabase no configurado")
                return False, None
            
            # Asegurar que el bucket existe
            await self.create_bucket_if_not_exists()
            
            # Generar nombre único para el archivo
            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Crear ruta con carpeta
            file_path = f"{folder}/{unique_filename}"
            
            # Subir el archivo
            result = self.supabase.storage.from_(self.bucket_name).upload(
                file_path,
                file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600"
                }
            )
            
            if result:
                # Obtener URL pública
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                logger.info(f"✅ Imagen subida exitosamente: {public_url}")
                return True, public_url
            else:
                logger.error("❌ Error subiendo imagen a Supabase Storage")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error en upload_image: {str(e)}")
            return False, None
    
    async def upload_service_image(self, file_content: bytes, file_name: str, content_type: str = "image/jpeg") -> Tuple[bool, Optional[str]]:
        """Subir imagen de servicio a la carpeta servicios/"""
        # Inicializar automáticamente si no está configurado
        await self.auto_initialize()
        return await self.upload_image(file_content, file_name, content_type, "servicios")
    
    async def upload_profile_image(self, file_content: bytes, file_name: str, content_type: str = "image/jpeg") -> Tuple[bool, Optional[str]]:
        """Subir imagen de perfil a la carpeta perfiles/"""
        # Inicializar automáticamente si no está configurado
        await self.auto_initialize()
        return await self.upload_image(file_content, file_name, content_type, "perfiles")
    
    
    async def delete_image(self, file_path: str) -> bool:
        """
        Eliminar una imagen del storage
        
        Args:
            file_path: Ruta del archivo en el storage
        
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            if not self.supabase:
                logger.error("❌ Cliente Supabase no configurado")
                return False
            
            # Extraer el nombre del archivo de la URL
            file_name = os.path.basename(file_path)
            
            # Eliminar el archivo
            result = self.supabase.storage.from_(self.bucket_name).remove([file_name])
            
            if result:
                logger.info(f"✅ Imagen eliminada exitosamente: {file_name}")
                return True
            else:
                logger.error(f"❌ Error eliminando imagen: {file_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en delete_image: {str(e)}")
            return False
    
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
                logger.error("❌ Cliente Supabase no configurado")
                return None
            
            # Extraer el nombre del archivo de la URL
            file_name = os.path.basename(file_path)
            
            # Obtener URL pública
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_name)
            logger.info(f"✅ URL pública obtenida: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"❌ Error en get_image_url: {str(e)}")
            return None

# Instancia global del servicio
supabase_storage_service = SupabaseStorageService()
