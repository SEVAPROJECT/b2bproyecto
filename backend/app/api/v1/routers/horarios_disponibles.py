# backend/app/api/v1/routers/horarios_disponibles.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.models.horario_trabajo import HorarioTrabajoModel, ExcepcionHorarioModel
from app.models.reserva_servicio.reserva import ReservaModel
from app.models.servicio.service import ServicioModel
from app.schemas.horario_trabajo import HorarioDisponibleOut
from app.schemas.auth_user import SupabaseUser
import logging
from typing import List, Optional
from datetime import datetime, date, time, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/horarios-disponibles", tags=["horarios-disponibles"])

# Constantes para tipos de excepción
TIPO_EXCEPCION_CERRADO = "cerrado"
TIPO_EXCEPCION_HORARIO_ESPECIAL = "horario_especial"

# Constantes para estados de reserva
ESTADO_CONFIRMADA = "confirmada"
ESTADO_PENDIENTE = "pendiente"

# Constantes para mensajes
MSG_ERROR_OBTENER_HORARIOS = "Error al obtener horarios disponibles."
MSG_ERROR_OBTENER_HORARIOS_SERVICIO = "Error al obtener horarios disponibles para el servicio."
MSG_ERROR_OBTENER_HORARIOS_RANGO = "Error al obtener horarios para el rango de fechas."
MSG_SERVICIO_NO_ENCONTRADO = "Servicio no encontrado o no disponible."
MSG_FECHA_FIN_POSTERIOR = "La fecha de fin debe ser posterior a la fecha de inicio."
MSG_RANGO_MAXIMO_DIAS = "El rango de fechas no puede ser mayor a 30 días."

# Constantes para valores por defecto
DEFAULT_DURACION_MINUTOS = 60
MAX_RANGO_DIAS = 30

def generar_slots_tiempo(hora_inicio: time, hora_fin: time, duracion_minutos: int = DEFAULT_DURACION_MINUTOS) -> List[time]:
    """
    Genera slots de tiempo entre hora_inicio y hora_fin con la duración especificada.
    """
    slots = []
    hora_actual = datetime.combine(date.today(), hora_inicio)
    hora_final = datetime.combine(date.today(), hora_fin)
    
    while hora_actual + timedelta(minutes=duracion_minutos) <= hora_final:
        slots.append(hora_actual.time())
        hora_actual += timedelta(minutes=duracion_minutos)
    
    return slots

def hay_conflicto_horario(slot_inicio: time, slot_fin: time, reservas: List) -> bool:
    """
    Verifica si hay conflicto entre un slot y las reservas existentes.
    """
    for reserva in reservas:
        # Verificar solapamiento
        if (slot_inicio < reserva.hora_fin and slot_fin > reserva.hora_inicio):
            return True
    return False

@router.get(
    "/proveedor/{proveedor_id}",
    response_model=List[HorarioDisponibleOut],
    description="Obtiene los horarios disponibles para un proveedor en una fecha específica."
)
async def obtener_horarios_disponibles_proveedor(
    proveedor_id: int,
    fecha: date = Query(..., description="Fecha para la cual obtener horarios disponibles"),
    duracion_minutos: int = Query(DEFAULT_DURACION_MINUTOS, ge=15, le=480, description="Duración de cada slot en minutos"),
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Genera automáticamente los horarios disponibles para un proveedor en una fecha específica.
    """
    try:
        # 1. Obtener horario base del día de la semana
        dia_semana = fecha.weekday()
        
        horario_query = select(HorarioTrabajoModel).where(
            and_(
                HorarioTrabajoModel.id_proveedor == proveedor_id,
                HorarioTrabajoModel.dia_semana == dia_semana,
                HorarioTrabajoModel.activo == True
            )
        )
        horario_result = await db.execute(horario_query)
        horario_base = horario_result.scalar_one_or_none()
        
        if not horario_base:
            return []
        
        # 2. Verificar excepciones para esta fecha
        excepcion_query = select(ExcepcionHorarioModel).where(
            and_(
                ExcepcionHorarioModel.id_proveedor == proveedor_id,
                ExcepcionHorarioModel.fecha == fecha
            )
        )
        excepcion_result = await db.execute(excepcion_query)
        excepcion_dia = excepcion_result.scalar_one_or_none()
        
        if excepcion_dia and excepcion_dia.tipo == TIPO_EXCEPCION_CERRADO:
            return []
        
        # 3. Determinar horario efectivo
        if excepcion_dia and excepcion_dia.tipo == TIPO_EXCEPCION_HORARIO_ESPECIAL:
            hora_inicio = excepcion_dia.hora_inicio
            hora_fin = excepcion_dia.hora_fin
        else:
            hora_inicio = horario_base.hora_inicio
            hora_fin = horario_base.hora_fin
        
        # 4. Generar slots disponibles
        slots = generar_slots_tiempo(hora_inicio, hora_fin, duracion_minutos)
        
        # 5. Obtener reservas existentes para esta fecha
        reservas_query = select(ReservaModel).where(
            and_(
                ReservaModel.fecha == fecha,
                ReservaModel.servicio.has(ServicioModel.id_perfil == proveedor_id),
                ReservaModel.estado.in_([ESTADO_CONFIRMADA, ESTADO_PENDIENTE])
            )
        )
        reservas_result = await db.execute(reservas_query)
        reservas_existentes = reservas_result.scalars().all()
        
        # 6. Filtrar slots ocupados
        slots_disponibles = []
        for slot_inicio in slots:
            slot_fin = (datetime.combine(date.today(), slot_inicio) + timedelta(minutes=duracion_minutos)).time()
            
            if not hay_conflicto_horario(slot_inicio, slot_fin, reservas_existentes):
                slots_disponibles.append(HorarioDisponibleOut(
                    fecha=fecha,
                    hora_inicio=slot_inicio,
                    hora_fin=slot_fin,
                    disponible=True
                ))
        
        logger.info(f"Generados {len(slots_disponibles)} horarios disponibles para proveedor {proveedor_id} en {fecha}")
        return slots_disponibles
        
    except Exception as e:
        logger.error(f"Error al obtener horarios disponibles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_OBTENER_HORARIOS
        )

@router.get(
    "/servicio/{servicio_id}",
    response_model=List[HorarioDisponibleOut],
    description="Obtiene los horarios disponibles para un servicio específico en una fecha."
)
async def obtener_horarios_disponibles_servicio(
    servicio_id: int,
    fecha: date = Query(..., description="Fecha para la cual obtener horarios disponibles"),
    duracion_minutos: int = Query(DEFAULT_DURACION_MINUTOS, ge=15, le=480, description="Duración de cada slot en minutos"),
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene horarios disponibles para un servicio específico.
    """
    try:
        # 1. Obtener el servicio y su proveedor
        servicio_query = select(ServicioModel).where(
            and_(
                ServicioModel.id_servicio == servicio_id,
                ServicioModel.estado == True
            )
        )
        servicio_result = await db.execute(servicio_query)
        servicio = servicio_result.scalar_one_or_none()
        
        if not servicio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_SERVICIO_NO_ENCONTRADO
            )
        
        # 2. Obtener horarios del proveedor
        proveedor_id = servicio.id_perfil
        dia_semana = fecha.weekday()
        
        horario_query = select(HorarioTrabajoModel).where(
            and_(
                HorarioTrabajoModel.id_proveedor == proveedor_id,
                HorarioTrabajoModel.dia_semana == dia_semana,
                HorarioTrabajoModel.activo == True
            )
        )
        horario_result = await db.execute(horario_query)
        horario_base = horario_result.scalar_one_or_none()
        
        if not horario_base:
            return []
        
        # 3. Verificar excepciones
        excepcion_query = select(ExcepcionHorarioModel).where(
            and_(
                ExcepcionHorarioModel.id_proveedor == proveedor_id,
                ExcepcionHorarioModel.fecha == fecha
            )
        )
        excepcion_result = await db.execute(excepcion_query)
        excepcion_dia = excepcion_result.scalar_one_or_none()
        
        if excepcion_dia and excepcion_dia.tipo == TIPO_EXCEPCION_CERRADO:
            return []
        
        # 4. Determinar horario efectivo
        if excepcion_dia and excepcion_dia.tipo == TIPO_EXCEPCION_HORARIO_ESPECIAL:
            hora_inicio = excepcion_dia.hora_inicio
            hora_fin = excepcion_dia.hora_fin
        else:
            hora_inicio = horario_base.hora_inicio
            hora_fin = horario_base.hora_fin
        
        # 5. Generar slots
        slots = generar_slots_tiempo(hora_inicio, hora_fin, duracion_minutos)
        
        # 6. Obtener reservas existentes para este servicio
        reservas_query = select(ReservaModel).where(
            and_(
                ReservaModel.id_servicio == servicio_id,
                ReservaModel.fecha == fecha,
                ReservaModel.estado.in_([ESTADO_CONFIRMADA, ESTADO_PENDIENTE])
            )
        )
        reservas_result = await db.execute(reservas_query)
        reservas_existentes = reservas_result.scalars().all()
        
        # 7. Filtrar slots ocupados
        slots_disponibles = []
        for slot_inicio in slots:
            slot_fin = (datetime.combine(date.today(), slot_inicio) + timedelta(minutes=duracion_minutos)).time()
            
            if not hay_conflicto_horario(slot_inicio, slot_fin, reservas_existentes):
                slots_disponibles.append(HorarioDisponibleOut(
                    fecha=fecha,
                    hora_inicio=slot_inicio,
                    hora_fin=slot_fin,
                    disponible=True
                ))
        
        logger.info(f"Generados {len(slots_disponibles)} horarios disponibles para servicio {servicio_id} en {fecha}")
        return slots_disponibles
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener horarios disponibles para servicio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_OBTENER_HORARIOS_SERVICIO
        )

@router.get(
    "/rango-fechas",
    response_model=List[HorarioDisponibleOut],
    description="Obtiene horarios disponibles para un rango de fechas."
)
async def obtener_horarios_rango_fechas(
    proveedor_id: int,
    fecha_inicio: date = Query(..., description="Fecha de inicio del rango"),
    fecha_fin: date = Query(..., description="Fecha de fin del rango"),
    duracion_minutos: int = Query(DEFAULT_DURACION_MINUTOS, ge=15, le=480, description="Duración de cada slot en minutos"),
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene horarios disponibles para un rango de fechas.
    """
    try:
        if fecha_fin < fecha_inicio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_FECHA_FIN_POSTERIOR
            )
        
        # Limitar el rango a máximo 30 días
        if (fecha_fin - fecha_inicio).days > MAX_RANGO_DIAS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_RANGO_MAXIMO_DIAS
            )
        
        todos_horarios = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            # Obtener horarios para esta fecha
            horarios_fecha = await obtener_horarios_disponibles_proveedor(
                proveedor_id=proveedor_id,
                fecha=fecha_actual,
                duracion_minutos=duracion_minutos,
                current_user=current_user,
                db=db
            )
            todos_horarios.extend(horarios_fecha)
            fecha_actual += timedelta(days=1)
        
        logger.info(f"Generados {len(todos_horarios)} horarios disponibles para rango {fecha_inicio} - {fecha_fin}")
        return todos_horarios
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener horarios para rango de fechas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_OBTENER_HORARIOS_RANGO
        )
