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

# Constantes para descripciones de Query
DESC_FECHA_HORARIOS = "Fecha para la cual obtener horarios disponibles"
DESC_DURACION_SLOT = "Duración de cada slot en minutos"
DESC_FECHA_INICIO = "Fecha de inicio del rango"
DESC_FECHA_FIN = "Fecha de fin del rango"

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

# Funciones helper para eliminar código duplicado
async def get_horario_base_proveedor(
    db: AsyncSession,
    proveedor_id: int,
    dia_semana: int
) -> Optional[HorarioTrabajoModel]:
    """Obtiene el horario base del proveedor para un día de la semana"""
    horario_query = select(HorarioTrabajoModel).where(
        and_(
            HorarioTrabajoModel.id_proveedor == proveedor_id,
            HorarioTrabajoModel.dia_semana == dia_semana,
            HorarioTrabajoModel.activo == True
        )
    )
    horario_result = await db.execute(horario_query)
    return horario_result.scalar_one_or_none()

async def get_excepcion_horario(
    db: AsyncSession,
    proveedor_id: int,
    fecha: date
) -> Optional[ExcepcionHorarioModel]:
    """Obtiene la excepción de horario para un proveedor en una fecha específica"""
    excepcion_query = select(ExcepcionHorarioModel).where(
        and_(
            ExcepcionHorarioModel.id_proveedor == proveedor_id,
            ExcepcionHorarioModel.fecha == fecha
        )
    )
    excepcion_result = await db.execute(excepcion_query)
    return excepcion_result.scalar_one_or_none()

def get_horario_efectivo(
    horario_base: HorarioTrabajoModel,
    excepcion_dia: Optional[ExcepcionHorarioModel]
) -> tuple[time, time]:
    """Determina el horario efectivo considerando excepciones"""
    if excepcion_dia and excepcion_dia.tipo == TIPO_EXCEPCION_HORARIO_ESPECIAL:
        return excepcion_dia.hora_inicio, excepcion_dia.hora_fin
    return horario_base.hora_inicio, horario_base.hora_fin

async def get_reservas_por_proveedor(
    db: AsyncSession,
    proveedor_id: int,
    fecha: date
) -> List[ReservaModel]:
    """
    Obtiene las reservas confirmadas para un proveedor en una fecha.
    Solo considera reservas confirmadas para que no aparezcan como disponibles.
    """
    reservas_query = select(ReservaModel).where(
        and_(
            ReservaModel.fecha == fecha,
            ReservaModel.servicio.has(ServicioModel.id_perfil == proveedor_id),
            ReservaModel.estado == ESTADO_CONFIRMADA
        )
    )
    reservas_result = await db.execute(reservas_query)
    return reservas_result.scalars().all()

async def get_reservas_por_servicio(
    db: AsyncSession,
    servicio_id: int,
    fecha: date
) -> List[ReservaModel]:
    """
    Obtiene las reservas confirmadas para un servicio en una fecha.
    Solo considera reservas confirmadas para que no aparezcan como disponibles.
    """
    reservas_query = select(ReservaModel).where(
        and_(
            ReservaModel.id_servicio == servicio_id,
            ReservaModel.fecha == fecha,
            ReservaModel.estado == ESTADO_CONFIRMADA
        )
    )
    reservas_result = await db.execute(reservas_query)
    return reservas_result.scalars().all()

def filtrar_slots_disponibles(
    slots: List[time],
    reservas_existentes: List[ReservaModel],
    fecha: date,
    duracion_minutos: int
) -> List[HorarioDisponibleOut]:
    """Filtra los slots disponibles eliminando los que tienen conflictos con reservas"""
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
    return slots_disponibles

@router.get(
    "/proveedor/{proveedor_id}",
    response_model=List[HorarioDisponibleOut],
    description="Obtiene los horarios disponibles para un proveedor en una fecha específica."
)
async def obtener_horarios_disponibles_proveedor(
    proveedor_id: int,
    fecha: date = Query(..., description=DESC_FECHA_HORARIOS),
    duracion_minutos: int = Query(DEFAULT_DURACION_MINUTOS, ge=15, le=480, description=DESC_DURACION_SLOT),
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Genera automáticamente los horarios disponibles para un proveedor en una fecha específica.
    """
    try:
        # 1. Obtener horario base del día de la semana
        dia_semana = fecha.weekday()
        horario_base = await get_horario_base_proveedor(db, proveedor_id, dia_semana)
        
        if not horario_base:
            return []
        
        # 2. Verificar excepciones para esta fecha
        excepcion_dia = await get_excepcion_horario(db, proveedor_id, fecha)
        
        if excepcion_dia and excepcion_dia.tipo == TIPO_EXCEPCION_CERRADO:
            return []
        
        # 3. Determinar horario efectivo
        hora_inicio, hora_fin = get_horario_efectivo(horario_base, excepcion_dia)
        
        # 4. Generar slots disponibles
        slots = generar_slots_tiempo(hora_inicio, hora_fin, duracion_minutos)
        
        # 5. Obtener reservas existentes para esta fecha
        reservas_existentes = await get_reservas_por_proveedor(db, proveedor_id, fecha)
        
        # 6. Filtrar slots ocupados
        slots_disponibles = filtrar_slots_disponibles(slots, reservas_existentes, fecha, duracion_minutos)
        
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
    fecha: date = Query(..., description=DESC_FECHA_HORARIOS),
    duracion_minutos: int = Query(DEFAULT_DURACION_MINUTOS, ge=15, le=480, description=DESC_DURACION_SLOT),
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
        
        horario_base = await get_horario_base_proveedor(db, proveedor_id, dia_semana)
        
        if not horario_base:
            return []
        
        # 3. Verificar excepciones
        excepcion_dia = await get_excepcion_horario(db, proveedor_id, fecha)
        
        if excepcion_dia and excepcion_dia.tipo == TIPO_EXCEPCION_CERRADO:
            return []
        
        # 4. Determinar horario efectivo
        hora_inicio, hora_fin = get_horario_efectivo(horario_base, excepcion_dia)
        
        # 5. Generar slots
        slots = generar_slots_tiempo(hora_inicio, hora_fin, duracion_minutos)
        
        # 6. Obtener reservas existentes para este servicio
        reservas_existentes = await get_reservas_por_servicio(db, servicio_id, fecha)
        
        # 7. Filtrar slots ocupados
        slots_disponibles = filtrar_slots_disponibles(slots, reservas_existentes, fecha, duracion_minutos)
        
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
    fecha_inicio: date = Query(..., description=DESC_FECHA_INICIO),
    fecha_fin: date = Query(..., description=DESC_FECHA_FIN),
    duracion_minutos: int = Query(DEFAULT_DURACION_MINUTOS, ge=15, le=480, description=DESC_DURACION_SLOT),
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
