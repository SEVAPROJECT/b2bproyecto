# app/services/ruc_verification_service.py
"""
Servicio para gestión de verificación de RUC durante el registro.
"""

import asyncpg
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
import logging

from app.services.direct_db_service import direct_db_service
from app.services.business_days_service import BusinessDaysService

logger = logging.getLogger(__name__)


class RUCVerificationService:
    """Servicio para gestión de verificación de RUC"""
    
    @staticmethod
    async def crear_verificacion_ruc(
        user_id: UUID,
        ruc_documento: UploadFile,
        nombre_empresa: str
    ) -> int:
        """
        Crea una verificación de RUC para un usuario recién registrado.
        
        Args:
            user_id: ID del usuario
            ruc_documento: Archivo de constancia de RUC
            nombre_empresa: Nombre de la empresa (para generar file_key)
            
        Returns:
            ID de la verificación creada
        """
        conn = None
        try:
            conn = await direct_db_service.get_connection()
            
            # 1. Importar ProviderRepository aquí para evitar importación circular
            from app.repositories.providers.provider_repository import ProviderRepository
            
            # 2. Obtener ID del tipo de documento "Constancia de RUC"
            tipo_doc_data = await ProviderRepository.get_tipo_documento_by_name(
                conn, "Constancia de RUC"
            )
            id_tip_documento = tipo_doc_data['id_tip_documento']
            logger.info(f"✅ Tipo de documento 'Constancia de RUC' encontrado: ID {id_tip_documento}")
            
            # 2. Leer contenido del archivo
            file_content = await ruc_documento.read()
            
            # Validar que el archivo no esté vacío
            if len(file_content) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo de RUC está vacío"
                )
            
            # Validar tamaño (10MB máximo)
            MAX_SIZE = 10 * 1024 * 1024  # 10MB
            if len(file_content) > MAX_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El archivo de RUC excede el tamaño máximo permitido (10MB)"
                )
            
            # 3. Importar StorageService aquí para evitar importación circular
            from app.services.storage_service import StorageService
            storage_service = StorageService()
            
            # 4. Generar file_key para almacenamiento
            file_key = storage_service.generate_file_key(
                razon_social=nombre_empresa,
                tipo_documento="Constancia de RUC",
                original_filename=ruc_documento.filename or "ruc.pdf"
            )
            
            # 5. Subir archivo a storage (iDrive o fallback)
            url_documento = storage_service.upload_document(
                file_content=file_content,
                file_key=file_key,
                document_type="provider",
                fallback_to_temp=True,
                fallback_suffix=f"{user_id}_{id_tip_documento}"
            )
            logger.info(f"✅ Documento RUC subido: {url_documento}")
            
            # 5. Calcular fecha límite (72 horas hábiles desde ahora)
            # Usar DateService para mantener consistencia con otras fechas del sistema
            from app.services.date_service import DateService
            fecha_creacion = DateService.now_for_database()
            fecha_limite = BusinessDaysService.calcular_72_horas_habiles(fecha_creacion)
            logger.info(f"📅 Fecha límite de verificación: {fecha_limite}")
            
            # 6. Crear registro en verificacion_ruc
            async with conn.transaction():
                # asyncpg acepta objetos UUID directamente, pasarlo sin conversión
                # El tipo de columna en PostgreSQL ya es UUID, así que asyncpg lo maneja automáticamente
                logger.info(f"🔍 Intentando insertar verificación RUC para user_id: {user_id} (tipo: {type(user_id)})")
                verificacion_row = await conn.fetchrow("""
                    INSERT INTO verificacion_ruc (
                        user_id,
                        id_tip_documento,
                        url_documento,
                        estado,
                        fecha_creacion,
                        fecha_limite_verificacion
                    )
                    VALUES ($1, $2, $3, 'pendiente', $4, $5)
                    RETURNING id_verificacion_ruc
                """, user_id, id_tip_documento, url_documento, fecha_creacion, fecha_limite)
                
                id_verificacion_ruc = verificacion_row['id_verificacion_ruc']
                logger.info(f"✅ Verificación de RUC creada: ID {id_verificacion_ruc}")
                
                return id_verificacion_ruc
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error creando verificación de RUC: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear verificación de RUC: {str(e)}"
            )
        finally:
            if conn:
                await direct_db_service.pool.release(conn)
    
    @staticmethod
    async def actualizar_estado_usuario(user_id: UUID, estado: str) -> None:
        """
        Actualiza el estado del usuario en la tabla users.
        
        Args:
            user_id: ID del usuario
            estado: Nuevo estado ('ACTIVO' o 'INACTIVO')
        """
        conn = None
        try:
            conn = await direct_db_service.get_connection()
            # asyncpg acepta objetos UUID directamente, no necesita conversión
            await conn.execute("""
                UPDATE users
                SET estado = $1
                WHERE id = $2
            """, estado, user_id)
            logger.info(f"✅ Estado del usuario {user_id} actualizado a {estado}")
        except Exception as e:
            logger.error(f"❌ Error actualizando estado del usuario: {str(e)}")
            raise
        finally:
            if conn:
                await direct_db_service.pool.release(conn)

