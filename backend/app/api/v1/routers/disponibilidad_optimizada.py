from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.models.disponibilidad import DisponibilidadModel
from app.models.servicio import ServicioModel
from app.schemas.disponibilidad.disponibilidad import DisponibilidadOut
from typing import List

router = APIRouter()

@router.get("/proveedor", response_model=List[DisponibilidadOut])
async def get_disponibilidades_proveedor(
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene todas las disponibilidades de un proveedor de una sola vez.
    Optimizado para evitar múltiples peticiones.
    """
    try:
        # Obtener todos los servicios del proveedor
        servicios_query = select(ServicioModel).where(
            and_(
                ServicioModel.id_perfil == current_user.id,
                ServicioModel.estado == True
            )
        )
        servicios_result = await db.execute(servicios_query)
        servicios = servicios_result.scalars().all()
        
        if not servicios:
            return []
        
        # Obtener IDs de servicios
        servicio_ids = [servicio.id_servicio for servicio in servicios]
        
        # Obtener todas las disponibilidades de estos servicios
        disponibilidades_query = select(DisponibilidadModel).where(
            DisponibilidadModel.id_servicio.in_(servicio_ids)
        )
        disponibilidades_result = await db.execute(disponibilidades_query)
        disponibilidades = disponibilidades_result.scalars().all()
        
        return disponibilidades
        
    except Exception as e:
        print(f"Error obteniendo disponibilidades del proveedor: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/masivo")
async def crear_disponibilidades_masivo(
    disponibilidades: List[dict],
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """
    Crea múltiples disponibilidades de una vez.
    Optimizado para creación masiva.
    """
    try:
        # Validar que no exceda el límite de seguridad
        if len(disponibilidades) > 100:
            raise HTTPException(
                status_code=400, 
                detail="Límite de seguridad: máximo 100 disponibilidades por lote"
            )
        
        creadas = 0
        errores = 0
        
        for disp_data in disponibilidades:
            try:
                # Validar que el servicio pertenece al usuario
                servicio_query = select(ServicioModel).where(
                    and_(
                        ServicioModel.id_servicio == disp_data.get('id_servicio'),
                        ServicioModel.id_perfil == current_user.id
                    )
                )
                servicio_result = await db.execute(servicio_query)
                servicio = servicio_result.scalar_one_or_none()
                
                if not servicio:
                    errores += 1
                    continue
                
                # Crear disponibilidad
                disponibilidad = DisponibilidadModel(
                    id_servicio=disp_data.get('id_servicio'),
                    fecha_inicio=disp_data.get('fecha_inicio'),
                    fecha_fin=disp_data.get('fecha_fin'),
                    disponible=disp_data.get('disponible', True),
                    precio_adicional=disp_data.get('precio_adicional', 0),
                    observaciones=disp_data.get('observaciones')
                )
                
                db.add(disponibilidad)
                creadas += 1
                
            except Exception as e:
                print(f"Error creando disponibilidad individual: {e}")
                errores += 1
                continue
        
        # Commit de todas las disponibilidades
        await db.commit()
        
        return {
            "mensaje": f"Proceso completado: {creadas} creadas, {errores} errores",
            "creadas": creadas,
            "errores": errores
        }
        
    except Exception as e:
        await db.rollback()
        print(f"Error en creación masiva: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
