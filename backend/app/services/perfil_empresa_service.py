"""
Servicio para manejar operaciones relacionadas con perfil_empresa
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.services.date_service import DateService
import logging

logger = logging.getLogger(__name__)

class PerfilEmpresaService:
    """Servicio para operaciones de perfil_empresa"""
    
    @staticmethod
    async def update_fecha_fin_by_user_id(
        db: AsyncSession, 
        user_id: str, 
        fecha_fin: Optional[datetime] = None
    ) -> bool:
        """
        Actualiza la fecha_fin del perfil_empresa de un usuario
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            fecha_fin: Fecha de fin (None para reactivar)
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            logger.info(f"🔄 Actualizando fecha_fin para usuario {user_id} -> {fecha_fin}")
            
            # Buscar el perfil_empresa del usuario
            query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == user_id)
            result = await db.execute(query)
            perfil_empresa = result.scalars().first()
            
            if not perfil_empresa:
                logger.warning(f"⚠️ No se encontró perfil_empresa para usuario {user_id}")
                return False
            
            # Actualizar la fecha_fin
            perfil_empresa.fecha_fin = fecha_fin
            
            logger.info(f"✅ Fecha_fin actualizada para usuario {user_id}: {fecha_fin}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando fecha_fin para usuario {user_id}: {str(e)}")
            return False
    
    @staticmethod
    async def deactivate_user_profile(
        db: AsyncSession, 
        user_id: str
    ) -> bool:
        """
        Desactiva el perfil de empresa de un usuario (establece fecha_fin)
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            bool: True si se desactivó correctamente
        """
        return await PerfilEmpresaService.update_fecha_fin_by_user_id(
            db=db,
            user_id=user_id,
            fecha_fin=DateService.now_for_database()
        )
    
    @staticmethod
    async def reactivate_user_profile(
        db: AsyncSession, 
        user_id: str
    ) -> bool:
        """
        Reactiva el perfil de empresa de un usuario (establece fecha_fin a None)
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            bool: True si se reactivó correctamente
        """
        return await PerfilEmpresaService.update_fecha_fin_by_user_id(
            db=db,
            user_id=user_id,
            fecha_fin=None
        )
