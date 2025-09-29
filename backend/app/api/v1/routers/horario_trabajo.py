# backend/app/api/v1/routers/horario_trabajo.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from app.services.direct_db_service import direct_db_service
from app.api.v1.dependencies.auth_user import get_current_user
from app.models.horario_trabajo import HorarioTrabajoModel, ExcepcionHorarioModel
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.schemas.horario_trabajo import (
    HorarioTrabajoIn, HorarioTrabajoOut, HorarioTrabajoUpdate,
    ExcepcionHorarioIn, ExcepcionHorarioOut, ExcepcionHorarioUpdate,
    ConfiguracionHorarioCompletaIn, ConfiguracionHorarioCompletaOut
)
from app.schemas.auth_user import SupabaseUser
import logging
from typing import List, Optional
from datetime import datetime, date, time, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/horario-trabajo", tags=["horario-trabajo"])

# ===== FUNCIONES AUXILIARES =====

async def get_provider_profile(current_user: SupabaseUser, db: AsyncSession) -> PerfilEmpresa:
    """
    Obtiene el perfil de empresa del usuario autenticado.
    """
    perfil_result = await db.execute(
        select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
    )
    perfil = perfil_result.scalar_one_or_none()
    
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de empresa no encontrado. Solo los proveedores pueden gestionar horarios."
        )
    
    return perfil

# ===== HORARIOS DE TRABAJO =====

@router.post(
    "/",
    response_model=HorarioTrabajoOut,
    status_code=status.HTTP_201_CREATED,
    description="Crea un nuevo horario de trabajo para el proveedor autenticado."
)
async def crear_horario_trabajo(
    horario: HorarioTrabajoIn,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Crea un nuevo horario de trabajo usando direct_db_service.
    Solo los proveedores pueden crear horarios.
    """
    try:
        # Obtener el perfil del proveedor usando direct_db_service
        perfil_query = """
            SELECT id_perfil FROM perfil_empresa 
            WHERE user_id = $1
        """
        perfil_result = await direct_db_service.fetch_one(perfil_query, current_user.id)
        
        if not perfil_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado. Solo los proveedores pueden gestionar horarios."
            )
        
        perfil_id = perfil_result['id_perfil']
        logger.info(f"Creando horario de trabajo para proveedor {perfil_id}")
        
        # Verificar que no existe ya un horario para este día
        verificar_query = """
            SELECT id_horario FROM horario_trabajo 
            WHERE id_proveedor = $1 AND dia_semana = $2
        """
        horario_existente = await direct_db_service.fetch_one(verificar_query, perfil_id, horario.dia_semana)
        
        if horario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un horario para el día {horario.dia_semana}. Actualiza el existente o elimínalo primero."
            )
        
        # Crear nuevo horario usando direct_db_service
        insert_query = """
            INSERT INTO horario_trabajo (id_proveedor, dia_semana, hora_inicio, hora_fin, activo)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id_horario, id_proveedor, dia_semana, hora_inicio, hora_fin, activo, created_at
        """
        nuevo_horario = await direct_db_service.fetch_one(
            insert_query, 
            perfil_id, 
            horario.dia_semana, 
            horario.hora_inicio, 
            horario.hora_fin, 
            horario.activo
        )
        
        logger.info(f"Horario creado exitosamente: {nuevo_horario['id_horario']}")
        
        return {
            "id_horario": nuevo_horario['id_horario'],
            "id_proveedor": nuevo_horario['id_proveedor'],
            "dia_semana": nuevo_horario['dia_semana'],
            "hora_inicio": nuevo_horario['hora_inicio'],
            "hora_fin": nuevo_horario['hora_fin'],
            "activo": nuevo_horario['activo'],
            "created_at": nuevo_horario['created_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear horario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear horario"
        )

@router.get(
    "/",
    response_model=List[HorarioTrabajoOut],
    description="Obtiene todos los horarios de trabajo del proveedor autenticado."
)
async def obtener_horarios_trabajo(
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Obtiene todos los horarios de trabajo del proveedor usando direct_db_service.
    """
    try:
        # Obtener el perfil del proveedor usando direct_db_service
        perfil_query = """
            SELECT id_perfil FROM perfil_empresa 
            WHERE user_id = $1
        """
        perfil_result = await direct_db_service.fetch_one(perfil_query, current_user.id)
        
        if not perfil_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado. Solo los proveedores pueden gestionar horarios."
            )
        
        perfil_id = perfil_result['id_perfil']
        
        # Obtener horarios usando direct_db_service
        horarios_query = """
            SELECT id_horario, id_proveedor, dia_semana, hora_inicio, hora_fin, activo, created_at
            FROM horario_trabajo 
            WHERE id_proveedor = $1
            ORDER BY dia_semana
        """
        horarios_result = await direct_db_service.fetch_all(horarios_query, perfil_id)
        
        # Convertir a formato de respuesta
        horarios = []
        for row in horarios_result:
            horarios.append({
                "id_horario": row['id_horario'],
                "id_proveedor": row['id_proveedor'],
                "dia_semana": row['dia_semana'],
                "hora_inicio": row['hora_inicio'],
                "hora_fin": row['hora_fin'],
                "activo": row['activo'],
                "created_at": row['created_at']
            })
        
        return horarios
        
    except Exception as e:
        logger.error(f"Error al obtener horarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener horarios"
        )

@router.put(
    "/{horario_id}",
    response_model=HorarioTrabajoOut,
    description="Actualiza un horario de trabajo existente."
)
async def actualizar_horario_trabajo(
    horario_id: int,
    horario_update: HorarioTrabajoUpdate,
    current_user: SupabaseUser = Depends(get_current_user),
    db = Depends(direct_db_service.get_connection)
):
    """
    Actualiza un horario de trabajo existente.
    """
    # Obtener el perfil del proveedor
    perfil = await get_provider_profile(current_user, db)
    
    # Obtener el horario
    horario_query = select(HorarioTrabajoModel).where(
        and_(
            HorarioTrabajoModel.id_horario == horario_id,
            HorarioTrabajoModel.id_proveedor == perfil.id_perfil
        )
    )
    horario_result = await db.execute(horario_query)
    horario = horario_result.scalar_one_or_none()
    
    if not horario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horario no encontrado."
        )
    
    # Actualizar campos
    update_data = horario_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(horario, field, value)
    
    try:
        await db.commit()
        await db.refresh(horario)
        logger.info(f"Horario {horario_id} actualizado exitosamente.")
        return horario
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al actualizar horario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el horario."
        )

@router.delete(
    "/{horario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Elimina un horario de trabajo."
)
async def eliminar_horario_trabajo(
    horario_id: int,
    current_user: SupabaseUser = Depends(get_current_user),
    db = Depends(direct_db_service.get_connection)
):
    """
    Elimina un horario de trabajo.
    """
    # Obtener el perfil del proveedor
    perfil = await get_provider_profile(current_user, db)
    
    # Verificar que el horario existe y pertenece al usuario
    horario_query = select(HorarioTrabajoModel).where(
        and_(
            HorarioTrabajoModel.id_horario == horario_id,
            HorarioTrabajoModel.id_proveedor == perfil.id_perfil
        )
    )
    horario_result = await db.execute(horario_query)
    horario = horario_result.scalar_one_or_none()
    
    if not horario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horario no encontrado."
        )
    
    try:
        await db.delete(horario)
        await db.commit()
        logger.info(f"Horario {horario_id} eliminado exitosamente.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al eliminar horario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el horario."
        )

# ===== CONFIGURACIÓN COMPLETA =====

@router.post(
    "/configuracion-completa",
    response_model=ConfiguracionHorarioCompletaOut,
    status_code=status.HTTP_201_CREATED,
    description="Configura el horario completo de la semana de una vez."
)
async def configurar_horario_completo(
    configuracion: ConfiguracionHorarioCompletaIn,
    current_user: SupabaseUser = Depends(get_current_user),
    db = Depends(direct_db_service.get_connection)
):
    """
    Configura el horario completo de la semana.
    Elimina horarios existentes y crea los nuevos.
    """
    # Obtener el perfil del proveedor
    perfil = await get_provider_profile(current_user, db)
    
    try:
        # Eliminar horarios existentes
        delete_horarios_query = delete(HorarioTrabajoModel).where(
            HorarioTrabajoModel.id_proveedor == perfil.id_perfil
        )
        await db.execute(delete_horarios_query)
        
        # Crear nuevos horarios
        horarios_creados = []
        for horario_data in configuracion.horarios:
            nuevo_horario = HorarioTrabajoModel(
                id_proveedor=perfil.id_perfil,
                dia_semana=horario_data.dia_semana,
                hora_inicio=horario_data.hora_inicio,
                hora_fin=horario_data.hora_fin,
                activo=horario_data.activo
            )
            db.add(nuevo_horario)
            horarios_creados.append(nuevo_horario)
        
        # Crear excepciones si se proporcionan
        excepciones_creadas = []
        if configuracion.excepciones:
            for excepcion_data in configuracion.excepciones:
                nueva_excepcion = ExcepcionHorarioModel(
                    id_proveedor=perfil.id_perfil,
                    fecha=excepcion_data.fecha,
                    tipo=excepcion_data.tipo,
                    hora_inicio=excepcion_data.hora_inicio,
                    hora_fin=excepcion_data.hora_fin,
                    motivo=excepcion_data.motivo
                )
                db.add(nueva_excepcion)
                excepciones_creadas.append(nueva_excepcion)
        
        await db.commit()
        
        # Refrescar objetos para obtener IDs
        for horario in horarios_creados:
            await db.refresh(horario)
        for excepcion in excepciones_creadas:
            await db.refresh(excepcion)
        
        logger.info(f"Configuración completa creada para proveedor {current_user.id}")
        
        return ConfiguracionHorarioCompletaOut(
            horarios=horarios_creados,
            excepciones=excepciones_creadas
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al configurar horario completo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al configurar el horario completo."
        )

# ===== EXCEPCIONES DE HORARIO =====

@router.post(
    "/excepciones",
    response_model=ExcepcionHorarioOut,
    status_code=status.HTTP_201_CREATED,
    description="Crea una excepción de horario (día cerrado o horario especial)."
)
async def crear_excepcion_horario(
    excepcion: ExcepcionHorarioIn,
    current_user: SupabaseUser = Depends(get_current_user),
    db = Depends(direct_db_service.get_connection)
):
    """
    Crea una excepción de horario.
    """
    # Obtener el perfil del proveedor
    perfil = await get_provider_profile(current_user, db)
    
    # Verificar que no existe ya una excepción para esta fecha
    excepcion_existente_query = select(ExcepcionHorarioModel).where(
        and_(
            ExcepcionHorarioModel.id_proveedor == perfil.id_perfil,
            ExcepcionHorarioModel.fecha == excepcion.fecha
        )
    )
    excepcion_existente_result = await db.execute(excepcion_existente_query)
    excepcion_existente = excepcion_existente_result.scalar_one_or_none()
    
    if excepcion_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una excepción para la fecha {excepcion.fecha}. Actualiza la existente o elimínala primero."
        )
    
    # Crear nueva excepción
    nueva_excepcion = ExcepcionHorarioModel(
        id_proveedor=perfil.id_perfil,
        fecha=excepcion.fecha,
        tipo=excepcion.tipo,
        hora_inicio=excepcion.hora_inicio,
        hora_fin=excepcion.hora_fin,
        motivo=excepcion.motivo
    )
    
    try:
        db.add(nueva_excepcion)
        await db.commit()
        await db.refresh(nueva_excepcion)
        logger.info(f"Excepción {nueva_excepcion.id_excepcion} creada exitosamente.")
        return nueva_excepcion
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al crear excepción: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la excepción de horario."
        )

@router.get(
    "/excepciones",
    response_model=List[ExcepcionHorarioOut],
    description="Obtiene todas las excepciones de horario del proveedor."
)
async def obtener_excepciones_horario(
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Obtiene todas las excepciones de horario del proveedor usando direct_db_service.
    """
    try:
        # Obtener el perfil del proveedor usando direct_db_service
        perfil_query = """
            SELECT id_perfil FROM perfil_empresa 
            WHERE user_id = $1
        """
        perfil_result = await direct_db_service.fetch_one(perfil_query, current_user.id)
        
        if not perfil_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado. Solo los proveedores pueden gestionar horarios."
            )
        
        perfil_id = perfil_result['id_perfil']
        
        # Obtener excepciones usando direct_db_service
        excepciones_query = """
            SELECT id_excepcion, id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo, created_at
            FROM excepciones_horario 
            WHERE id_proveedor = $1
            ORDER BY fecha
        """
        excepciones_result = await direct_db_service.fetch_all(excepciones_query, perfil_id)
        
        # Convertir a formato de respuesta
        excepciones = []
        for row in excepciones_result:
            excepciones.append({
                "id_excepcion": row['id_excepcion'],
                "id_proveedor": row['id_proveedor'],
                "fecha": row['fecha'],
                "tipo": row['tipo'],
                "hora_inicio": row['hora_inicio'],
                "hora_fin": row['hora_fin'],
                "motivo": row['motivo'],
                "created_at": row['created_at']
            })
        
        return excepciones
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener excepciones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener excepciones"
        )
