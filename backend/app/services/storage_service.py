# app/services/storage_service.py
"""
Servicio unificado para gestión de almacenamiento de archivos.
Capa de Lógica de Negocio - Maneja la subida de archivos a diferentes proveedores de almacenamiento.
"""

import logging
import uuid
from typing import Tuple, Optional
from fastapi import HTTPException, status

from app.idrive.idrive_service import idrive_service
from app.api.v1.dependencies.local_storage import local_storage_service
from app.api.v1.routers.providers.constants import PREFIX_TEMP

logger = logging.getLogger(__name__)


class StorageService:
    """
    Servicio unificado para gestión de almacenamiento de archivos.
    Abstrae la lógica de subida de archivos a diferentes proveedores (iDrive, Local, Supabase).
    """
    
    def __init__(self):
        self.idrive_service = idrive_service
        self.local_storage = local_storage_service
    
    def upload_file_with_fallback(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: str = "provider",
        force_local: bool = False
    ) -> Tuple[bool, str, str, str]:
        """
        Sube un archivo con fallback inteligente:
        - Intenta iDrive primero (a menos que force_local=True)
        - Si falla, usa almacenamiento local
        - Retorna: (success, message, file_url, storage_type)
        """
        
        # Si se fuerza almacenamiento local, saltar iDrive
        if force_local:
            logger.info("🔄 Forzando almacenamiento local")
            return self._upload_to_local(file_content, filename, document_type)
        
        # Intentar iDrive primero
        logger.info("🚀 Intentando subir a iDrive...")
        idrive_success, idrive_message, idrive_url = self.idrive_service.upload_file(
            file_content, filename, document_type
        )
        
        if idrive_success:
            logger.info("✅ Archivo subido exitosamente a iDrive")
            return True, idrive_message, idrive_url, "idrive"
        
        # iDrive falló, usar almacenamiento local como fallback
        logger.warning(f"⚠️ iDrive falló: {idrive_message}")
        logger.info("🔄 Cambiando a almacenamiento local como fallback")
        
        return self._upload_to_local(file_content, filename, document_type)
    
    def _upload_to_local(
        self, 
        file_content: bytes, 
        filename: str, 
        document_type: str
    ) -> Tuple[bool, str, str, str]:
        """Sube archivo a almacenamiento local"""
        try:
            # Usar el método que maneja estructura de directorios
            if document_type == "provider" and "/" in filename:
                # Si es un proveedor y tiene estructura de directorios, usar save_file_with_path
                success, message, file_url = self.local_storage.save_file_with_path(
                    file_content, filename, document_type
                )
            else:
                # Usar el método simple para otros casos
                success, message, file_url = self.local_storage.save_file(
                    file_content, filename, document_type
                )
            
            if success:
                logger.info("✅ Archivo guardado localmente como fallback")
                return True, f"{message} (fallback)", file_url, "local"
            else:
                logger.error(f"❌ Fallback local también falló: {message}")
                return False, f"Error en fallback local: {message}", "", "none"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error en fallback local: {error_msg}")
            return False, f"Error en fallback local: {error_msg}", "", "none"
    
    def upload_document(
        self,
        file_content: bytes,
        file_key: str,
        document_type: str = "provider",
        fallback_to_temp: bool = True,
        fallback_suffix: Optional[str] = None
    ) -> str:
        """
        Sube un documento con manejo de errores y fallback.
        
        Args:
            file_content: Contenido del archivo en bytes
            file_key: Clave/nombre del archivo (puede incluir estructura de directorios)
            document_type: Tipo de documento (provider, general, etc.)
            fallback_to_temp: Si True, retorna URL temporal si falla la subida
            fallback_suffix: Sufijo para URL temporal (ej: user_id + tipo_doc_id)
            
        Returns:
            str: URL del archivo subido o URL temporal si fallback_to_temp=True
        """
        try:
            success, message, file_url, storage_type = self.upload_file_with_fallback(
                file_content, file_key, document_type
            )
            
            if success:
                logger.info(f"✅ Archivo subido exitosamente usando {storage_type}: {file_url}")
                return file_url
            else:
                if fallback_to_temp:
                    # Generar URL temporal como último recurso
                    temp_url = f"{PREFIX_TEMP}{file_key}"
                    if fallback_suffix:
                        temp_url = f"{PREFIX_TEMP}{file_key}_{fallback_suffix}"
                    logger.warning(f"⚠️ Usando URL temporal como fallback: {temp_url}")
                    return temp_url
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error subiendo archivo: {message}"
                    )
        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error inesperado subiendo archivo: {error_msg}")
            if fallback_to_temp:
                temp_url = f"{PREFIX_TEMP}{file_key}"
                if fallback_suffix:
                    temp_url = f"{PREFIX_TEMP}{file_key}_{fallback_suffix}"
                logger.warning(f"⚠️ Usando URL temporal como fallback: {temp_url}")
                return temp_url
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error subiendo archivo: {error_msg}"
                )
    
    def generate_file_key(
        self,
        razon_social: str,
        tipo_documento: str,
        original_filename: str
    ) -> str:
        """
        Genera una clave única para el archivo con estructura de directorios.
        
        Args:
            razon_social: Razón social de la empresa
            tipo_documento: Tipo de documento
            original_filename: Nombre original del archivo
            
        Returns:
            str: Clave del archivo con estructura: razon_social/tipo_documento/uuid_filename
        """
        unique_id = str(uuid.uuid4())
        return f"{razon_social}/{tipo_documento}/{unique_id}_{original_filename}"
    
    def test_services(self) -> dict:
        """Prueba la conectividad de ambos servicios de almacenamiento"""
        results = {
            "idrive": {"status": "unknown", "message": ""},
            "local": {"status": "unknown", "message": ""}
        }
        
        # Probar iDrive
        try:
            idrive_ok, idrive_msg = self.idrive_service.test_connection()
            results["idrive"]["status"] = "ok" if idrive_ok else "error"
            results["idrive"]["message"] = idrive_msg
        except Exception as e:
            results["idrive"]["status"] = "error"
            results["idrive"]["message"] = str(e)
        
        # Probar almacenamiento local
        try:
            # Crear archivo de prueba
            test_content = b"Test de almacenamiento local"
            success, message, _ = self.local_storage.save_file(
                test_content, "test.txt", "test"
            )
            
            if success:
                results["local"]["status"] = "ok"
                results["local"]["message"] = "Almacenamiento local funcionando"
                
                # Limpiar archivo de prueba
                try:
                    self.local_storage.delete_file("local://test.txt")
                except:
                    pass  # Ignorar errores al limpiar
            else:
                results["local"]["status"] = "error"
                results["local"]["message"] = message
                
        except Exception as e:
            results["local"]["status"] = "error"
            results["local"]["message"] = str(e)
        
        return results


# Instancia global del servicio
storage_service = StorageService()

