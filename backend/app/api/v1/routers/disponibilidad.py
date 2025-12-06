# backend/app/api/v1/routers/disponibilidad.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.schemas.disponibilidad import DisponibilidadIn, DisponibilidadOut, DisponibilidadUpdate
from app.models.disponibilidad import DisponibilidadModel
from app.models.servicio.service import ServicioModel
from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time, timezone, timedelta
from app.services.direct_db_service import direct_db_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disponibilidades", tags=["disponibilidades"])

@router.post(
    "/",
    response_model=DisponibilidadOut,
    status_code=status.HTTP_201_CREATED,
    description="Crea una nueva disponibilidad para un servicio (solo proveedores)."
)
async def crear_disponibilidad(
    disponibilidad: DisponibilidadIn,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea una nueva disponibilidad para un servicio.
    Solo el proveedor del servicio puede crear disponibilidades.
    """
    logger.info(f"Creando disponibilidad para servicio {disponibilidad.id_servicio} por usuario {current_user.id}")
    
    # Verificar que el servicio existe y pertenece al usuario
    servicio_query = select(ServicioModel).where(
        and_(
            ServicioModel.id_servicio == disponibilidad.id_servicio,
            ServicioModel.id_perfil == current_user.id,
            ServicioModel.estado == True
        )
    )
    servicio_result = await db.execute(servicio_query)
    servicio = servicio_result.scalar_one_or_none()
    
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no tienes permisos para gestionarlo."
        )
    
    # Verificar que no hay solapamiento de horarios
    solapamiento_query = select(DisponibilidadModel).where(
        and_(
            DisponibilidadModel.id_servicio == disponibilidad.id_servicio,
            DisponibilidadModel.disponible == True,
            or_(
                and_(
                    DisponibilidadModel.fecha_inicio <= disponibilidad.fecha_inicio,
                    DisponibilidadModel.fecha_fin > disponibilidad.fecha_inicio
                ),
                and_(
                    DisponibilidadModel.fecha_inicio < disponibilidad.fecha_fin,
                    DisponibilidadModel.fecha_fin >= disponibilidad.fecha_fin
                ),
                and_(
                    DisponibilidadModel.fecha_inicio >= disponibilidad.fecha_inicio,
                    DisponibilidadModel.fecha_fin <= disponibilidad.fecha_fin
                )
            )
        )
    )
    solapamiento_result = await db.execute(solapamiento_query)
    solapamiento = solapamiento_result.scalar_one_or_none()
    
    if solapamiento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una disponibilidad en ese horario."
        )
    
    # Crear nueva disponibilidad
    nueva_disponibilidad = DisponibilidadModel(
        id_servicio=disponibilidad.id_servicio,
        fecha_inicio=disponibilidad.fecha_inicio,
        fecha_fin=disponibilidad.fecha_fin,
        disponible=disponibilidad.disponible,
        precio_adicional=disponibilidad.precio_adicional or 0,
        observaciones=disponibilidad.observaciones
    )
    
    try:
        db.add(nueva_disponibilidad)
        await db.commit()
        await db.refresh(nueva_disponibilidad)
        logger.info(f"Disponibilidad {nueva_disponibilidad.id_disponibilidad} creada exitosamente.")
        return nueva_disponibilidad
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al crear la disponibilidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar la disponibilidad."
        )

@router.get(
    "/",
    response_model=List[DisponibilidadOut],
    description="Obtiene las disponibilidades de los servicios del proveedor autenticado."
)
async def obtener_mis_disponibilidades(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    id_servicio: Optional[int] = Query(None, description="Filtrar por servicio específico"),
    disponible: Optional[bool] = Query(None, description="Filtrar por disponibilidad"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Obtiene las disponibilidades de los servicios del proveedor autenticado.
    """
    # Obtener servicios del proveedor
    servicios_query = select(ServicioModel.id_servicio).where(
        ServicioModel.id_perfil == current_user.id
    )
    servicios_result = await db.execute(servicios_query)
    servicio_ids = [row[0] for row in servicios_result.fetchall()]
    
    if not servicio_ids:
        return []
    
    # Filtrar por servicio específico si se proporciona
    if id_servicio:
        if id_servicio not in servicio_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver disponibilidades de este servicio."
            )
        servicio_ids = [id_servicio]
    
    # Obtener disponibilidades
    query = select(DisponibilidadModel).where(
        DisponibilidadModel.id_servicio.in_(servicio_ids)
    )
    
    if disponible is not None:
        query = query.where(DisponibilidadModel.disponible == disponible)
    
    query = query.order_by(DisponibilidadModel.fecha_inicio.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    disponibilidades = result.scalars().all()
    
    return disponibilidades

@router.get(
    "/servicio/{servicio_id}",
    response_model=List[DisponibilidadOut],
    description="Obtiene las disponibilidades de un servicio específico (público)."
)
async def obtener_disponibilidades_servicio(
    servicio_id: int,
    db: AsyncSession = Depends(get_async_db),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Obtiene las disponibilidades de un servicio específico (público).
    """
    # Verificar que el servicio existe y está activo
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
            detail="Servicio no encontrado o no disponible."
        )
    
    # Obtener disponibilidades
    query = select(DisponibilidadModel).where(
        and_(
            DisponibilidadModel.id_servicio == servicio_id,
            DisponibilidadModel.disponible == True
        )
    )
    
    if fecha_desde:
        query = query.where(DisponibilidadModel.fecha_inicio >= fecha_desde)
    
    if fecha_hasta:
        query = query.where(DisponibilidadModel.fecha_fin <= fecha_hasta)
    
    query = query.order_by(DisponibilidadModel.fecha_inicio.asc()).limit(limit)
    
    result = await db.execute(query)
    disponibilidades = result.scalars().all()
    
    return disponibilidades

@router.put(
    "/{disponibilidad_id}",
    response_model=DisponibilidadOut,
    description="Actualiza una disponibilidad existente (solo proveedores)."
)
async def actualizar_disponibilidad(
    disponibilidad_id: int,
    disponibilidad_update: DisponibilidadUpdate,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza una disponibilidad existente.
    Solo el proveedor del servicio puede actualizar disponibilidades.
    """
    # Obtener la disponibilidad con el servicio
    query = select(DisponibilidadModel).options(
        selectinload(DisponibilidadModel.servicio)
    ).where(DisponibilidadModel.id_disponibilidad == disponibilidad_id)
    
    result = await db.execute(query)
    disponibilidad = result.scalar_one_or_none()
    
    if not disponibilidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disponibilidad no encontrada."
        )
    
    # Verificar que el usuario es el proveedor del servicio
    if disponibilidad.servicio.id_perfil != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta disponibilidad."
        )
    
    # Actualizar campos proporcionados
    update_data = disponibilidad_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(disponibilidad, field, value)
    
    disponibilidad.updated_at = datetime.now(timezone.utc)
    
    try:
        await db.commit()
        await db.refresh(disponibilidad)
        logger.info(f"Disponibilidad {disponibilidad_id} actualizada exitosamente.")
        return disponibilidad
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al actualizar disponibilidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la disponibilidad."
        )

@router.delete(
    "/{disponibilidad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Elimina una disponibilidad (solo proveedores)."
)
async def eliminar_disponibilidad(
    disponibilidad_id: int,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Elimina una disponibilidad.
    Solo el proveedor del servicio puede eliminar disponibilidades.
    """
    # Obtener la disponibilidad con el servicio
    query = select(DisponibilidadModel).options(
        selectinload(DisponibilidadModel.servicio)
    ).where(DisponibilidadModel.id_disponibilidad == disponibilidad_id)
    
    result = await db.execute(query)
    disponibilidad = result.scalar_one_or_none()
    
    if not disponibilidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disponibilidad no encontrada."
        )
    
    # Verificar que el usuario es el proveedor del servicio
    if disponibilidad.servicio.id_perfil != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta disponibilidad."
        )
    
    try:
        await db.delete(disponibilidad)
        await db.commit()
        logger.info(f"Disponibilidad {disponibilidad_id} eliminada exitosamente.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al eliminar disponibilidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar la disponibilidad."
        )

# Funciones helper para reducir complejidad cognitiva
async def _verificar_servicio(conn: Any, servicio_id: int) -> Dict[str, Any]:
    """Verifica que el servicio existe y retorna su información."""
    logger.info(f"🔍 [GET /disponibilidades] Verificando servicio {servicio_id}...")
    servicio_query = """
        SELECT s.id_servicio, s.id_perfil, s.estado, s.nombre, s.duracion_minutos
        FROM servicio s
        WHERE s.id_servicio = $1 AND s.estado = true
    """
    servicio_result = await conn.fetchrow(servicio_query, servicio_id)
    
    if not servicio_result:
        logger.warning(f"❌ [GET /disponibilidades] Servicio {servicio_id} no encontrado")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )
    
    proveedor_id = servicio_result['id_perfil']
    duracion_minutos = servicio_result['duracion_minutos'] or 60
    logger.info(f"✅ [GET /disponibilidades] Servicio válido. Proveedor: {proveedor_id}, Duración: {duracion_minutos}min")
    
    return {
        'proveedor_id': proveedor_id,
        'duracion_minutos': duracion_minutos
    }


async def _obtener_horarios_trabajo(conn: Any, proveedor_id: int) -> Dict[int, Any]:
    """Obtiene todos los horarios de trabajo del proveedor."""
    logger.info(f"🔍 [GET /disponibilidades] Obteniendo horarios de trabajo para proveedor {proveedor_id}...")
    horarios_query = """
        SELECT dia_semana, hora_inicio, hora_fin, activo, id_horario
        FROM horario_trabajo
        WHERE id_proveedor = $1 AND activo = true
        ORDER BY dia_semana
    """
    horarios_result = await conn.fetch(horarios_query, proveedor_id)
    
    # Log detallado de los horarios obtenidos
    dias_nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    for row in horarios_result:
        dia_nombre = dias_nombres[row['dia_semana']] if 0 <= row['dia_semana'] <= 6 else f"Día {row['dia_semana']}"
        logger.info(f"📅 [GET /disponibilidades] Horario encontrado: {dia_nombre} (dia_semana={row['dia_semana']}) - {row['hora_inicio']} a {row['hora_fin']} (id_horario={row['id_horario']})")
    
    # Si hay múltiples horarios para el mismo día, tomar el más reciente (mayor id_horario)
    horarios_map: Dict[int, Any] = {}
    for row in horarios_result:
        dia_semana = row['dia_semana']
        # Si ya existe un horario para este día, mantener el que tenga mayor id_horario (más reciente)
        if dia_semana in horarios_map:
            if row['id_horario'] > horarios_map[dia_semana].get('id_horario', 0):
                logger.warning(f"⚠️ [GET /disponibilidades] Múltiples horarios para {dias_nombres[dia_semana]}, usando el más reciente (id_horario={row['id_horario']})")
                horarios_map[dia_semana] = row
        else:
            horarios_map[dia_semana] = row
    
    logger.info(f"✅ [GET /disponibilidades] Obtenidos {len(horarios_map)} horarios de trabajo únicos")
    return horarios_map


async def _obtener_excepciones_horario(conn: Any, proveedor_id: int, fecha_inicio: date, fecha_fin: date) -> Dict[date, Any]:
    """Obtiene todas las excepciones de horario en el rango de fechas."""
    logger.info("🔍 [GET /disponibilidades] Obteniendo excepciones de horario...")
    excepciones_query = """
        SELECT fecha, tipo, hora_inicio, hora_fin
        FROM excepciones_horario
        WHERE id_proveedor = $1 AND fecha >= $2 AND fecha <= $3
    """
    excepciones_result = await conn.fetch(excepciones_query, proveedor_id, fecha_inicio, fecha_fin)
    excepciones_map = {row['fecha']: row for row in excepciones_result}
    logger.info(f"✅ [GET /disponibilidades] Obtenidas {len(excepciones_map)} excepciones")
    return excepciones_map


async def _obtener_reservas(conn: Any, servicio_id: int, fecha_inicio: date, fecha_fin: date) -> Dict[date, List[Dict[str, Any]]]:
    """
    Obtiene todas las reservas confirmadas del servicio en el rango de fechas.
    Solo considera reservas confirmadas para que no aparezcan como disponibles.
    """
    logger.info("🔍 [GET /disponibilidades] Obteniendo reservas confirmadas existentes...")
    reservas_query = """
        SELECT fecha, hora_inicio, hora_fin
        FROM reserva
        WHERE id_servicio = $1 
        AND fecha >= $2 
        AND fecha <= $3 
        AND estado = 'confirmada'
    """
    reservas_result = await conn.fetch(reservas_query, servicio_id, fecha_inicio, fecha_fin)
    reservas_map: Dict[date, List[Dict[str, Any]]] = {}
    for reserva in reservas_result:
        fecha_reserva = reserva['fecha']
        if fecha_reserva not in reservas_map:
            reservas_map[fecha_reserva] = []
        reservas_map[fecha_reserva].append({
            'hora_inicio': reserva['hora_inicio'],
            'hora_fin': reserva['hora_fin']
        })
    logger.info(f"✅ [GET /disponibilidades] Obtenidas {len(reservas_map)} fechas con reservas confirmadas")
    return reservas_map


def _obtener_horarios_efectivos(
    horario_base: Dict[str, Any],
    excepcion: Optional[Dict[str, Any]]
) -> Optional[tuple]:
    """Determina los horarios efectivos para una fecha considerando excepciones."""
    if excepcion and excepcion['tipo'] == 'cerrado':
        return None
    
    if excepcion and excepcion['tipo'] == 'horario_especial':
        return (excepcion['hora_inicio'], excepcion['hora_fin'])
    
    return (horario_base['hora_inicio'], horario_base['hora_fin'])


def _generar_slots_fecha(
    fecha_actual: date,
    hora_inicio: Any,
    hora_fin: Any,
    duracion_minutos: int,
    servicio_id: int
) -> List[Dict[str, Any]]:
    """Genera los slots de tiempo para una fecha específica."""
    slots = []
    
    # Normalizar las horas para asegurar que no tengan segundos ni microsegundos
    # Esto evita problemas de comparación
    if isinstance(hora_inicio, time):
        hora_inicio = time(hora_inicio.hour, hora_inicio.minute, 0)
    if isinstance(hora_fin, time):
        hora_fin = time(hora_fin.hour, hora_fin.minute, 0)
    
    hora_actual = datetime.combine(fecha_actual, hora_inicio)
    hora_final = datetime.combine(fecha_actual, hora_fin)
    
    logger.debug(f"🔍 [GET /disponibilidades] Generando slots: fecha={fecha_actual}, desde={hora_inicio}, hasta={hora_fin}, duracion={duracion_minutos}min")
    logger.debug(f"🔍 [GET /disponibilidades] hora_actual inicial: {hora_actual}, hora_final: {hora_final}")
    
    # Generar slots mientras la hora de inicio del slot sea menor que la hora_fin
    # Incluir todos los slots que quepan completamente dentro del horario
    # Ejemplo: si horario es 11:00-17:00 y duracion es 60min:
    # - 11:00-12:00, 12:00-13:00, 13:00-14:00, 14:00-15:00, 15:00-16:00, 16:00-17:00
    iteracion = 0
    while hora_actual < hora_final:
        iteracion += 1
        hora_fin_slot = hora_actual + timedelta(minutes=duracion_minutos)
        
        logger.debug(f"🔍 [GET /disponibilidades] Iteración {iteracion}: hora_actual={hora_actual.time()}, hora_fin_slot={hora_fin_slot.time()}, hora_final={hora_final.time()}, hora_fin_slot <= hora_final: {hora_fin_slot <= hora_final}")
        
        # Solo agregar el slot si cabe completamente dentro del horario (hora_fin_slot <= hora_final)
        if hora_fin_slot <= hora_final:
            slots.append({
                "id_servicio": servicio_id,
                "fecha_inicio": hora_actual,
                "fecha_fin": hora_fin_slot,
                "disponible": True,
                "precio_adicional": 0,
                "observaciones": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            hora_actual += timedelta(minutes=duracion_minutos)
        else:
            # Si el slot excede la hora_fin, no lo agregamos y terminamos
            logger.debug(f"🔍 [GET /disponibilidades] Slot excede hora_final, terminando generación")
            break
    
    logger.info(f"🔍 [GET /disponibilidades] Generados {len(slots)} slots para {fecha_actual} desde {hora_inicio} hasta {hora_fin}")
    if slots:
        logger.info(f"🔍 [GET /disponibilidades] Primer slot: {slots[0]['fecha_inicio'].time()} - {slots[0]['fecha_fin'].time()}")
        logger.info(f"🔍 [GET /disponibilidades] Último slot: {slots[-1]['fecha_inicio'].time()} - {slots[-1]['fecha_fin'].time()}")
    else:
        logger.warning(f"⚠️ [GET /disponibilidades] No se generaron slots para {fecha_actual} desde {hora_inicio} hasta {hora_fin}")
    
    return slots


def _aplicar_reservas_a_slots(
    slots: List[Dict[str, Any]],
    reservas_fecha: List[Dict[str, Any]],
    fecha_actual: date
) -> None:
    """Marca los slots como no disponibles si hay solapamiento con reservas."""
    for reserva in reservas_fecha:
        reserva_inicio = datetime.combine(fecha_actual, reserva['hora_inicio'])
        reserva_fin = datetime.combine(fecha_actual, reserva['hora_fin'])
        
        for slot in slots:
            slot_inicio = slot["fecha_inicio"]
            slot_fin = slot["fecha_fin"]
            
            if (slot_inicio < reserva_fin and slot_fin > reserva_inicio):
                slot["disponible"] = False


def _obtener_siguiente_dia_habil(
    fecha_actual: date,
    horarios_map: Dict[int, Any],
    max_dias_busqueda: int = 7
) -> date:
    """
    Obtiene el siguiente día hábil a partir de la fecha actual.
    Un día hábil es un día que tiene horario de trabajo configurado.
    
    Args:
        fecha_actual: Fecha actual desde la cual buscar
        horarios_map: Mapa de horarios por día de la semana (0=Lunes, 6=Domingo)
        max_dias_busqueda: Máximo de días a buscar hacia adelante (default: 7)
    
    Returns:
        date: Siguiente día hábil
    """
    fecha_busqueda = fecha_actual + timedelta(days=1)  # Empezar desde mañana
    dias_buscados = 0
    
    while dias_buscados < max_dias_busqueda:
        dia_semana = fecha_busqueda.weekday()
        if dia_semana in horarios_map:
            logger.info(f"🔍 [GET /disponibilidades] Siguiente día hábil encontrado: {fecha_busqueda} ({['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia_semana]})")
            return fecha_busqueda
        fecha_busqueda += timedelta(days=1)
        dias_buscados += 1
    
    # Si no se encuentra un día hábil en los próximos 7 días, retornar mañana
    logger.warning(f"⚠️ [GET /disponibilidades] No se encontró día hábil en los próximos {max_dias_busqueda} días, retornando mañana")
    return fecha_actual + timedelta(days=1)


def _generar_horarios_disponibles(
    servicio_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    horarios_map: Dict[int, Any],
    excepciones_map: Dict[date, Any],
    reservas_map: Dict[date, List[Dict[str, Any]]],
    duracion_minutos: int
) -> List[Dict[str, Any]]:
    """Genera todos los horarios disponibles en el rango de fechas."""
    logger.info("🔍 [GET /disponibilidades] Generando horarios disponibles...")
    todos_horarios = []
    fecha_actual = fecha_inicio
    
    dias_nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    while fecha_actual <= fecha_fin:
        dia_semana = fecha_actual.weekday()  # 0=Lunes, 6=Domingo
        dia_nombre = dias_nombres[dia_semana]
        
        if dia_semana not in horarios_map:
            logger.debug(f"🔍 [GET /disponibilidades] No hay horario configurado para {dia_nombre} ({fecha_actual})")
            fecha_actual += timedelta(days=1)
            continue
        
        horario_base = horarios_map[dia_semana]
        logger.info(f"📅 [GET /disponibilidades] Procesando {dia_nombre} ({fecha_actual}): horario base {horario_base['hora_inicio']} - {horario_base['hora_fin']}")
        
        excepcion = excepciones_map.get(fecha_actual)
        if excepcion:
            logger.info(f"⚠️ [GET /disponibilidades] Excepción encontrada para {fecha_actual}: {excepcion['tipo']}")
        
        horarios_efectivos = _obtener_horarios_efectivos(horario_base, excepcion)
        if not horarios_efectivos:
            logger.debug(f"🔍 [GET /disponibilidades] No hay horarios efectivos para {dia_nombre} ({fecha_actual})")
            fecha_actual += timedelta(days=1)
            continue
        
        hora_inicio, hora_fin = horarios_efectivos
        logger.info(f"⏰ [GET /disponibilidades] Horarios efectivos para {dia_nombre} ({fecha_actual}): {hora_inicio} - {hora_fin}")
        logger.info(f"⏰ [GET /disponibilidades] Tipo de hora_inicio: {type(hora_inicio)}, Tipo de hora_fin: {type(hora_fin)}")
        
        slots = _generar_slots_fecha(fecha_actual, hora_inicio, hora_fin, duracion_minutos, servicio_id)
        logger.info(f"📊 [GET /disponibilidades] Generados {len(slots)} slots para {dia_nombre} ({fecha_actual})")
        if slots:
            logger.info(f"📊 [GET /disponibilidades] Primer slot: {slots[0]['fecha_inicio'].time()} - {slots[0]['fecha_fin'].time()}")
            logger.info(f"📊 [GET /disponibilidades] Último slot: {slots[-1]['fecha_inicio'].time()} - {slots[-1]['fecha_fin'].time()}")
        logger.info(f"📊 [GET /disponibilidades] Generados {len(slots)} slots para {dia_nombre} ({fecha_actual})")
        
        reservas_fecha = reservas_map.get(fecha_actual, [])
        _aplicar_reservas_a_slots(slots, reservas_fecha, fecha_actual)
        
        todos_horarios.extend(slots)
        fecha_actual += timedelta(days=1)
    
    horarios_disponibles = [h for h in todos_horarios if h["disponible"]]
    
    # Filtrar para asegurar que solo se muestren disponibilidades a partir del día hábil siguiente
    # Esto es una validación adicional por si acaso alguna disponibilidad se generó para hoy
    fecha_hoy = date.today()
    horarios_disponibles = [
        h for h in horarios_disponibles 
        if h["fecha_inicio"].date() > fecha_hoy
    ]
    
    logger.info(f"✅ [GET /disponibilidades] Generados {len(horarios_disponibles)} horarios disponibles para servicio {servicio_id} (a partir del día hábil siguiente)")
    return horarios_disponibles


@router.get(
    "/servicio/{servicio_id}/disponibles",
    response_model=List[DisponibilidadOut],
    summary="Obtener disponibilidades disponibles de un servicio",
    description="Obtiene solo las disponibilidades disponibles (disponible=true) de un servicio específico"
)
async def obtener_disponibilidades_disponibles_servicio(
    servicio_id: int
):
    """
    Obtiene horarios disponibles para un servicio específico.
    Siempre usa la lógica de horario_trabajo + excepciones_horario del proveedor
    para respetar el horario configurado en la agenda del proveedor.
    """
    logger.info(f"🔍 [GET /disponibilidades/servicio/{servicio_id}/disponibles] ========== INICIO OBTENER DISPONIBILIDADES ==========")
    logger.info(f"🔍 [GET /disponibilidades] Servicio ID: {servicio_id}")
    
    try:
        conn = await direct_db_service.get_connection()
        try:
            # Verificar que el servicio existe
            servicio_info = await _verificar_servicio(conn, servicio_id)
            
            # SIEMPRE usar lógica de horario_trabajo para respetar el horario configurado por el proveedor
            # Las disponibilidades directas de la tabla disponibilidad se ignoran para priorizar el horario de trabajo
            logger.info(f"🔍 [GET /disponibilidades] Usando horario_trabajo del proveedor para generar disponibilidades...")
            proveedor_id = servicio_info['proveedor_id']
            
            fecha_hoy = date.today()
            logger.info(f"📅 [GET /disponibilidades] Fecha actual: {fecha_hoy}")
            
            # Obtener horarios de trabajo del proveedor
            horarios_map = await _obtener_horarios_trabajo(conn, proveedor_id)
            
            if not horarios_map or len(horarios_map) == 0:
                logger.warning(f"⚠️ [GET /disponibilidades] No hay horarios de trabajo configurados para proveedor {proveedor_id}")
                return []
            
            # Calcular el siguiente día hábil (día con horario configurado)
            # Las reservas solo pueden hacerse a partir del día hábil siguiente
            fecha_inicio = _obtener_siguiente_dia_habil(fecha_hoy, horarios_map)
            fecha_fin = fecha_inicio + timedelta(days=30)
            
            logger.info(f"📅 [GET /disponibilidades] Fecha inicio (siguiente día hábil): {fecha_inicio}")
            logger.info(f"📅 [GET /disponibilidades] Fecha fin: {fecha_fin}")
            
            excepciones_map = await _obtener_excepciones_horario(conn, proveedor_id, fecha_inicio, fecha_fin)
            reservas_map = await _obtener_reservas(conn, servicio_id, fecha_inicio, fecha_fin)
            
            # Forzar intervalos de 1 hora (60 minutos) para las disponibilidades
            # independientemente de la duración del servicio
            # Esto asegura que los horarios disponibles se muestren cada hora completa
            duracion_slots_disponibilidad = 60
            logger.info(f"🔍 [GET /disponibilidades] Usando duración de slots: {duracion_slots_disponibilidad} minutos (1 hora)")
            
            horarios_disponibles = _generar_horarios_disponibles(
                servicio_id,
                fecha_inicio,
                fecha_fin,
                horarios_map,
                excepciones_map,
                reservas_map,
                duracion_slots_disponibilidad
            )
            
            logger.info(f"✅ [GET /disponibilidades] Retornando {len(horarios_disponibles)} horarios generados")
            return horarios_disponibles
            
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET /disponibilidades] Error crítico: {str(e)}")
        logger.error(f"❌ [GET /disponibilidades] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [GET /disponibilidades] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al obtener disponibilidades: {str(e)}"
        )

@router.get(
    "/servicio/{servicio_id}/excepciones",
    summary="Obtener excepciones de horario para un servicio",
    description="Obtiene las excepciones de horario (días cerrados y horarios especiales) para un servicio específico en un rango de fechas"
)
async def obtener_excepciones_servicio(
    servicio_id: int,
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio (por defecto: hoy)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin (por defecto: hoy + 30 días)")
):
    """
    Obtiene las excepciones de horario para un servicio específico.
    """
    logger.info(f"🔍 [GET /disponibilidades/servicio/{servicio_id}/excepciones] Obteniendo excepciones...")
    
    try:
        conn = await direct_db_service.get_connection()
        try:
            # Verificar que el servicio existe y obtener proveedor_id
            servicio_info = await _verificar_servicio(conn, servicio_id)
            proveedor_id = servicio_info['proveedor_id']
            
            # Establecer rango de fechas por defecto
            if not fecha_inicio:
                fecha_inicio = date.today()
            if not fecha_fin:
                fecha_fin = fecha_inicio + timedelta(days=30)
            
            # Obtener excepciones
            excepciones_map = await _obtener_excepciones_horario(conn, proveedor_id, fecha_inicio, fecha_fin)
            
            # Convertir a lista de diccionarios con información formateada
            excepciones_list = []
            for fecha_excepcion, excepcion_data in excepciones_map.items():
                excepcion_info = {
                    "fecha": fecha_excepcion.isoformat(),
                    "tipo": excepcion_data['tipo'],
                    "hora_inicio": excepcion_data.get('hora_inicio').strftime('%H:%M') if excepcion_data.get('hora_inicio') else None,
                    "hora_fin": excepcion_data.get('hora_fin').strftime('%H:%M') if excepcion_data.get('hora_fin') else None,
                    "motivo": excepcion_data.get('motivo')
                }
                excepciones_list.append(excepcion_info)
            
            logger.info(f"✅ [GET /disponibilidades/servicio/{servicio_id}/excepciones] Retornando {len(excepciones_list)} excepciones")
            return excepciones_list
            
        finally:
            await direct_db_service.pool.release(conn)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET /disponibilidades/servicio/{servicio_id}/excepciones] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener excepciones: {str(e)}"
        )
