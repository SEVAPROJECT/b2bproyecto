import os
import shutil
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class LocalStorageService:
    def __init__(self):
        # Crear directorio de uploads si no existe
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
        # Crear subdirectorios para diferentes tipos de documentos
        self.documents_dir = self.upload_dir / "documents"
        self.documents_dir.mkdir(exist_ok=True)
        
        self.provider_docs_dir = self.upload_dir / "provider_documents"
        self.provider_docs_dir.mkdir(exist_ok=True)
        
        logger.info(f"📁 Directorio de uploads configurado: {self.upload_dir.absolute()}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Limpia el nombre del archivo para evitar problemas de directorios"""
        # Reemplazar caracteres problemáticos
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Reemplazar espacios con guiones bajos
        sanitized = sanitized.replace(' ', '_')
        # Limitar longitud
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:95] + ext
        return sanitized
    
    def _create_safe_path(self, base_path: str, sub_paths: list) -> Path:
        """Crea una ruta segura con directorios anidados"""
        try:
            # Construir ruta paso a paso
            current_path = Path(base_path)
            
            for sub_path in sub_paths:
                # Sanitizar cada parte del path
                safe_sub_path = self._sanitize_filename(str(sub_path))
                current_path = current_path / safe_sub_path
                
                # Crear directorio si no existe
                if not current_path.exists():
                    current_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"📁 Directorio creado: {current_path}")
            
            return current_path
            
        except Exception as e:
            logger.error(f"❌ Error creando directorios: {str(e)}")
            # Fallback: usar directorio base
            return Path(base_path)
    
    def save_file(self, file_content: bytes, filename: str, document_type: str = "general") -> Tuple[bool, str, Optional[str]]:
        """Guarda un archivo localmente y retorna la ruta"""
        try:
            # Generar nombre único para evitar conflictos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            # Sanitizar el nombre del archivo original
            original_filename = Path(filename).name
            safe_filename = self._sanitize_filename(original_filename)
            
            # Crear nombre único
            unique_filename = f"{timestamp}_{unique_id}_{safe_filename}"
            
            # Determinar directorio según tipo de documento
            if document_type == "provider":
                target_dir = self.provider_docs_dir
            else:
                target_dir = self.documents_dir
            
            # Crear directorio si no existe
            target_dir.mkdir(exist_ok=True)
            
            # Ruta completa del archivo
            file_path = target_dir / unique_filename
            
            # Guardar archivo
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Generar URL relativa para la base de datos
            relative_path = f"local://{file_path.relative_to(self.upload_dir)}"
            
            logger.info(f"✅ Archivo guardado localmente: {file_path}")
            return True, "Archivo guardado localmente", relative_path
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error guardando archivo localmente: {error_msg}")
            return False, f"Error guardando archivo: {error_msg}", None
    
    def save_file_with_path(self, file_content: bytes, file_key: str, document_type: str = "provider") -> Tuple[bool, str, Optional[str]]:
        """Guarda un archivo con estructura de directorios personalizada"""
        try:
            # Parsear la estructura del file_key (ej: "OMPRA SRL/RUC/documento.pdf")
            path_parts = file_key.split('/')
            
            if len(path_parts) >= 2:
                # El primer elemento es la empresa, el segundo es el tipo de documento
                empresa = path_parts[0]
                tipo_documento = path_parts[1]
                nombre_archivo = path_parts[-1] if len(path_parts) > 2 else "documento.pdf"
                
                # Crear estructura de directorios segura
                if document_type == "provider":
                    base_dir = self.provider_docs_dir
                else:
                    base_dir = self.documents_dir
                
                # Crear directorios anidados de forma segura
                target_path = self._create_safe_path(
                    str(base_dir), 
                    [empresa, tipo_documento]
                )
                
                # Generar nombre único para el archivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_id = str(uuid.uuid4())[:8]
                safe_filename = self._sanitize_filename(nombre_archivo)
                unique_filename = f"{timestamp}_{unique_id}_{safe_filename}"
                
                # Ruta completa del archivo
                file_path = target_path / unique_filename
                
                # Guardar archivo
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                # Generar URL relativa para la base de datos
                relative_path = f"local://{file_path.relative_to(self.upload_dir)}"
                
                logger.info(f"✅ Archivo guardado con estructura personalizada: {file_path}")
                return True, "Archivo guardado con estructura personalizada", relative_path
            else:
                # Fallback al método simple
                return self.save_file(file_content, file_key, document_type)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error guardando archivo con estructura personalizada: {error_msg}")
            # Fallback al método simple
            return self.save_file(file_content, file_key, document_type)
    
    def get_file_path(self, file_url: str) -> Optional[Path]:
        """Convierte una URL local en ruta de archivo"""
        try:
            if file_url.startswith("local://"):
                relative_path = file_url.replace("local://", "")
                return self.upload_dir / relative_path
            return None
        except Exception as e:
            logger.error(f"❌ Error convirtiendo URL local: {str(e)}")
            return None
    
    def serve_file(self, file_url: str) -> Tuple[bool, str, Optional[bytes]]:
        """Sirve un archivo local para descarga"""
        try:
            file_path = self.get_file_path(file_url)
            if not file_path or not file_path.exists():
                return False, "Archivo no encontrado", None
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"✅ Archivo servido localmente: {file_path}")
            return True, "Archivo servido exitosamente", content
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error sirviendo archivo: {error_msg}")
            return False, f"Error sirviendo archivo: {error_msg}", None
    
    def delete_file(self, file_url: str) -> Tuple[bool, str]:
        """Elimina un archivo local"""
        try:
            file_path = self.get_file_path(file_url)
            if not file_path or not file_path.exists():
                return False, "Archivo no encontrado"
            
            file_path.unlink()
            logger.info(f"✅ Archivo eliminado localmente: {file_path}")
            return True, "Archivo eliminado exitosamente"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error eliminando archivo: {error_msg}")
            return False, f"Error eliminando archivo: {error_msg}"
    
    def get_file_info(self, file_url: str) -> Tuple[bool, str, Optional[dict]]:
        """Obtiene información de un archivo local"""
        try:
            file_path = self.get_file_path(file_url)
            if not file_path or not file_path.exists():
                return False, "Archivo no encontrado", None
            
            stat = file_path.stat()
            file_info = {
                "filename": file_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(file_path.absolute())
            }
            
            return True, "Información obtenida exitosamente", file_info
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error obteniendo información del archivo: {error_msg}")
            return False, f"Error obteniendo información: {error_msg}", None

# Instancia global del servicio
local_storage_service = LocalStorageService()

async def upload_file_locally(file_content: bytes, filename: str, document_type: str = "general") -> str:
    """Función de compatibilidad para subir archivos localmente"""
    success, message, file_url = local_storage_service.save_file(file_content, filename, document_type)
    if success:
        return file_url
    else:
        raise Exception(f"Error guardando archivo localmente: {message}")
