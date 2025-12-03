# backend/app/api/v1/routers/horario_trabajo.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.direct_db_service import direct_db_service
from app.api.v1.dependencies.auth_user import get_current_user
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

# Helper function para obtener el nombre del día de la semana
def get_nombre_dia_semana(dia_semana: int) -> str:
    """
    Convierte el número del día de la semana (0-6) al nombre del día.
    0 = Lunes, 1 = Martes, ..., 6 = Domingo
    """
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    if 0 <= dia_semana <= 6:
        return dias[dia_semana]
    return f"Día {dia_semana}"

# Helper function para obtener perfil usando direct_db_service
async def get_provider_profile_direct(user_id: str) -> int:
    """
    Obtener el id_perfil del proveedor usando direct_db_service.
    Retorna el id_perfil (bigint) o lanza HTTPException si no se encuentra.
    """
    conn = await direct_db_service.get_connection()
    try:
        perfil_query = """
            SELECT id_perfil FROM perfil_empresa 
            WHERE user_id = $1
        """
        perfil_result = await conn.fetchrow(perfil_query, user_id)
        
        if not perfil_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado. Solo los proveedores pueden gestionar horarios."
            )
        
        return perfil_result['id_perfil']
    finally:
        await direct_db_service.pool.release(conn)

# Helper function para ejecutar consultas con direct_db_service
async def execute_query(query: str, *params):
    """Ejecutar una consulta que no retorna datos"""
    conn = await direct_db_service.get_connection()
    try:
        return await conn.execute(query, *params)
    finally:
        await direct_db_service.pool.release(conn)

# Helper function para fetch_one con direct_db_service
async def fetch_one_query(query: str, *params):
    """Ejecutar una consulta que retorna una fila"""
    conn = await direct_db_service.get_connection()
    try:
        result = await conn.fetchrow(query, *params)
        return dict(result) if result else None
    finally:
        await direct_db_service.pool.release(conn)

# Helper function para fetch_all con direct_db_service
async def fetch_all_query(query: str, *params):
    """Ejecutar una consulta que retorna múltiples filas"""
    conn = await direct_db_service.get_connection()
    try:
        result = await conn.fetch(query, *params)
        return [dict(row) for row in result]
    finally:
        await direct_db_service.pool.release(conn)

router = APIRouter(prefix="/horario-trabajo", tags=["horario-trabajo"])

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
    logger.info(f"🔍 [POST /horario-trabajo/] Iniciando crear_horario_trabajo para user_id: {current_user.id}")
    logger.info(f"🔍 [POST /horario-trabajo/] Datos del horario: {horario.dict()}")
    
    try:
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [POST /horario-trabajo/] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [POST /horario-trabajo/] Perfil encontrado: id_perfil = {perfil_id}")
        
        # Validar horarios antes de verificar existencia
        # La validación del schema ya se ejecutó automáticamente, pero la hacemos explícita para mejor mensaje de error
        try:
            from app.schemas.horario_trabajo import validate_horario_times
            validate_horario_times(horario.hora_inicio, horario.hora_fin)
        except ValueError as e:
            logger.warning(f"❌ [POST /horario-trabajo/] Validación de horarios falló: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Verificar que no existe ya un horario para este día
        logger.info(f"🔍 [POST /horario-trabajo/] Verificando horario existente para día {horario.dia_semana}...")
        verificar_query = """
            SELECT id_horario FROM horario_trabajo 
            WHERE id_proveedor = $1 AND dia_semana = $2
        """
        horario_existente = await fetch_one_query(verificar_query, perfil_id, horario.dia_semana)
        logger.info(f"🔍 [POST /horario-trabajo/] Horario existente: {horario_existente}")
        
        if horario_existente:
            nombre_dia = get_nombre_dia_semana(horario.dia_semana)
            logger.warning(f"❌ [POST /horario-trabajo/] Ya existe horario para día {nombre_dia} ({horario.dia_semana})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un horario para el día {nombre_dia}. Actualiza el existente o elimínalo primero."
            )
        
        # Crear nuevo horario usando helper
        logger.info("🔍 [POST /horario-trabajo/] Creando nuevo horario en base de datos...")
        insert_query = """
            INSERT INTO horario_trabajo (id_proveedor, dia_semana, hora_inicio, hora_fin, activo)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id_horario, id_proveedor, dia_semana, hora_inicio, hora_fin, activo, created_at
        """
        nuevo_horario = await fetch_one_query(
            insert_query, 
            perfil_id, 
            horario.dia_semana, 
            horario.hora_inicio, 
            horario.hora_fin, 
            horario.activo
        )
        logger.info(f"🔍 [POST /horario-trabajo/] Horario insertado: {nuevo_horario}")
        
        logger.info(f"✅ [POST /horario-trabajo/] Horario creado exitosamente: {nuevo_horario['id_horario']}")
        
        return nuevo_horario
        
    except HTTPException:
        raise
    except ValueError as e:
        # Capturar errores de validación de horarios
        logger.warning(f"❌ [POST /horario-trabajo/] Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [POST /horario-trabajo/] Error crítico: {str(e)}")
        logger.error(f"❌ [POST /horario-trabajo/] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [POST /horario-trabajo/] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al crear horario: {str(e)}"
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
    logger.info(f"🔍 [GET /horario-trabajo/] Iniciando obtener_horarios_trabajo para user_id: {current_user.id}")
    
    try:
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [GET /horario-trabajo/] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [GET /horario-trabajo/] Perfil encontrado: id_perfil = {perfil_id}")
        
        # Verificar si existe la tabla horario_trabajo
        logger.info("🔍 [GET /horario-trabajo/] Verificando existencia de tabla horario_trabajo...")
        check_table_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'horario_trabajo'
            );
        """
        table_exists = await fetch_one_query(check_table_query)
        logger.info(f"🔍 [GET /horario-trabajo/] Tabla horario_trabajo existe: {table_exists}")
        
        # Obtener horarios usando helper
        logger.info(f"🔍 [GET /horario-trabajo/] Consultando horarios para proveedor {perfil_id}...")
        horarios_query = """
            SELECT id_horario, id_proveedor, dia_semana, hora_inicio, hora_fin, activo, created_at
            FROM horario_trabajo 
            WHERE id_proveedor = $1
            ORDER BY dia_semana
        """
        horarios_result = await fetch_all_query(horarios_query, perfil_id)
        logger.info(f"🔍 [GET /horario-trabajo/] Horarios encontrados: {len(horarios_result) if horarios_result else 0}")
        
        logger.info(f"✅ [GET /horario-trabajo/] Devolviendo {len(horarios_result)} horarios")
        return horarios_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET /horario-trabajo/] Error crítico: {str(e)}")
        logger.error(f"❌ [GET /horario-trabajo/] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [GET /horario-trabajo/] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al obtener horarios: {str(e)}"
        )

@router.put(
    "/{horario_id}",
    response_model=HorarioTrabajoOut,
    description="Actualiza un horario de trabajo existente."
)
async def actualizar_horario_trabajo(
    horario_id: int,
    horario_update: HorarioTrabajoUpdate,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Actualiza un horario de trabajo existente usando direct_db_service.
    """
    logger.info(f"🔍 [PUT /horario-trabajo/{horario_id}] Iniciando actualizar_horario_trabajo para user_id: {current_user.id}")
    logger.info(f"🔍 [PUT /horario-trabajo/{horario_id}] Datos de actualización: {horario_update.dict(exclude_unset=True)}")
    
    try:
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [PUT /horario-trabajo] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [PUT /horario-trabajo] Perfil encontrado: id_perfil = {perfil_id}")
    
        # Verificar que el horario existe y pertenece al usuario
        logger.info(f"🔍 [PUT /horario-trabajo] Verificando horario {horario_id} para proveedor {perfil_id}...")
        verificar_query = """
            SELECT id_horario, id_proveedor, dia_semana, hora_inicio, hora_fin, activo, created_at
            FROM horario_trabajo 
            WHERE id_horario = $1 AND id_proveedor = $2
        """
        horario_existente = await fetch_one_query(verificar_query, horario_id, perfil_id)
        logger.info(f"🔍 [PUT /horario-trabajo] Horario encontrado: {horario_existente}")
        
        if not horario_existente:
            logger.warning(f"❌ [PUT /horario-trabajo] Horario {horario_id} no encontrado para proveedor {perfil_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Horario no encontrado."
            )
        
        # Preparar datos de actualización
        update_data = horario_update.dict(exclude_unset=True)
        logger.info(f"🔍 [PUT /horario-trabajo] Campos a actualizar: {list(update_data.keys())}")
        
        if not update_data:
            logger.info("✅ [PUT /horario-trabajo] No hay cambios que aplicar, devolviendo horario actual")
            return horario_existente
        
        # Validar horarios: combinar valores nuevos con existentes para validación completa
        hora_inicio_final = update_data.get('hora_inicio', horario_existente['hora_inicio'])
        hora_fin_final = update_data.get('hora_fin', horario_existente['hora_fin'])
        
        # Validar que hora_inicio < hora_fin
        try:
            from app.schemas.horario_trabajo import validate_horario_times
            validate_horario_times(hora_inicio_final, hora_fin_final)
        except ValueError as e:
            logger.warning(f"❌ [PUT /horario-trabajo] Validación de horarios falló: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Construir query de actualización dinámicamente
        set_clauses = []
        params = [horario_id, perfil_id]
        param_index = 3
        
        for field, value in update_data.items():
            set_clauses.append(f"{field} = ${param_index}")
            params.append(value)
            param_index += 1
        
        update_query = f"""
            UPDATE horario_trabajo 
            SET {', '.join(set_clauses)}
            WHERE id_horario = $1 AND id_proveedor = $2
            RETURNING id_horario, id_proveedor, dia_semana, hora_inicio, hora_fin, activo, created_at
        """
        
        logger.info("🔍 [PUT /horario-trabajo] Ejecutando actualización...")
        horario_actualizado = await fetch_one_query(update_query, *params)
        logger.info(f"🔍 [PUT /horario-trabajo] Horario actualizado: {horario_actualizado}")
        
        logger.info(f"✅ [PUT /horario-trabajo] Horario {horario_id} actualizado exitosamente")
        return horario_actualizado
        
    except HTTPException:
        raise
    except ValueError as e:
        # Capturar errores de validación de horarios
        logger.warning(f"❌ [PUT /horario-trabajo] Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [PUT /horario-trabajo] Error crítico: {str(e)}")
        logger.error(f"❌ [PUT /horario-trabajo] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [PUT /horario-trabajo] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al actualizar horario: {str(e)}"
        )

@router.delete(
    "/{horario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Elimina un horario de trabajo."
)
async def eliminar_horario_trabajo(
    horario_id: int,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Elimina un horario de trabajo usando direct_db_service.
    """
    logger.info(f"🔍 [DELETE /horario-trabajo/{horario_id}] Iniciando eliminar_horario_trabajo para user_id: {current_user.id}")
    
    try:
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [DELETE /horario-trabajo] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [DELETE /horario-trabajo] Perfil encontrado: id_perfil = {perfil_id}")
        
        # Verificar que el horario existe y pertenece al usuario
        logger.info(f"🔍 [DELETE /horario-trabajo] Verificando horario {horario_id} para proveedor {perfil_id}...")
        verificar_query = """
            SELECT id_horario FROM horario_trabajo 
            WHERE id_horario = $1 AND id_proveedor = $2
        """
        horario_existente = await fetch_one_query(verificar_query, horario_id, perfil_id)
        logger.info(f"🔍 [DELETE /horario-trabajo] Horario encontrado: {horario_existente}")
        
        if not horario_existente:
            logger.warning(f"❌ [DELETE /horario-trabajo] Horario {horario_id} no encontrado para proveedor {perfil_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Horario no encontrado."
            )
        
        # Eliminar horario usando helper
        logger.info(f"🔍 [DELETE /horario-trabajo] Eliminando horario {horario_id}...")
        delete_query = """
            DELETE FROM horario_trabajo 
            WHERE id_horario = $1 AND id_proveedor = $2
        """
        await execute_query(delete_query, horario_id, perfil_id)
        
        logger.info(f"✅ [DELETE /horario-trabajo] Horario {horario_id} eliminado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [DELETE /horario-trabajo] Error crítico: {str(e)}")
        logger.error(f"❌ [DELETE /horario-trabajo] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [DELETE /horario-trabajo] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al eliminar horario: {str(e)}"
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
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Configura el horario completo de la semana usando direct_db_service.
    Elimina horarios existentes y crea los nuevos.
    """
    logger.info(f"🔍 [POST /configuracion-completa] Iniciando configurar_horario_completo para user_id: {current_user.id}")
    logger.info(f"🔍 [POST /configuracion-completa] Configuración recibida: {len(configuracion.horarios)} horarios")
    
    try:
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [POST /configuracion-completa] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [POST /configuracion-completa] Perfil encontrado: id_perfil = {perfil_id}")
    
        # Eliminar horarios existentes usando direct_db_service
        logger.info("🔍 [POST /configuracion-completa] Eliminando horarios existentes...")
        delete_horarios_query = """
            DELETE FROM horario_trabajo 
            WHERE id_proveedor = $1
        """
        await direct_db_service.execute(delete_horarios_query, perfil_id)
        logger.info("✅ [POST /configuracion-completa] Horarios existentes eliminados")
        
        # Validar todos los horarios antes de crear
        from app.schemas.horario_trabajo import validate_horario_times
        for i, horario_data in enumerate(configuracion.horarios):
            try:
                validate_horario_times(horario_data.hora_inicio, horario_data.hora_fin)
            except ValueError as e:
                nombre_dia = get_nombre_dia_semana(horario_data.dia_semana)
                logger.warning(f"❌ [POST /configuracion-completa] Validación falló para horario {i+1} (día {nombre_dia}): {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error en horario del día {nombre_dia}: {str(e)}"
                )
        
        # Crear nuevos horarios usando direct_db_service
        logger.info(f"🔍 [POST /configuracion-completa] Creando {len(configuracion.horarios)} nuevos horarios...")
        horarios_creados = []
        for i, horario_data in enumerate(configuracion.horarios):
            logger.info(f"🔍 [POST /configuracion-completa] Creando horario {i+1}: día {horario_data.dia_semana}")
            insert_horario_query = """
                INSERT INTO horario_trabajo (id_proveedor, dia_semana, hora_inicio, hora_fin, activo)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id_horario, id_proveedor, dia_semana, hora_inicio, hora_fin, activo, created_at
            """
            nuevo_horario = await fetch_one_query(
                insert_horario_query,
                perfil_id,
                horario_data.dia_semana,
                horario_data.hora_inicio,
                horario_data.hora_fin,
                horario_data.activo
            )
            horarios_creados.append(nuevo_horario)
        logger.info(f"✅ [POST /configuracion-completa] {len(horarios_creados)} horarios creados")
        
        # Validar excepciones antes de crear
        if configuracion.excepciones:
            for i, excepcion_data in enumerate(configuracion.excepciones):
                if excepcion_data.tipo == 'horario_especial':
                    try:
                        if excepcion_data.hora_inicio and excepcion_data.hora_fin:
                            validate_horario_times(excepcion_data.hora_inicio, excepcion_data.hora_fin)
                    except ValueError as e:
                        logger.warning(f"❌ [POST /configuracion-completa] Validación falló para excepción {i+1} (fecha {excepcion_data.fecha}): {str(e)}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Error en excepción del {excepcion_data.fecha}: {str(e)}"
                        )
        
        # Crear excepciones si se proporcionan
        excepciones_creadas = []
        if configuracion.excepciones:
            logger.info(f"🔍 [POST /configuracion-completa] Creando {len(configuracion.excepciones)} excepciones...")
            for i, excepcion_data in enumerate(configuracion.excepciones):
                logger.info(f"🔍 [POST /configuracion-completa] Creando excepción {i+1}: {excepcion_data.fecha}")
                insert_excepcion_query = """
                    INSERT INTO excepciones_horario (id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id_excepcion, id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo, created_at
                """
                nueva_excepcion = await fetch_one_query(
                    insert_excepcion_query,
                    perfil_id,
                    excepcion_data.fecha,
                    excepcion_data.tipo,
                    excepcion_data.hora_inicio,
                    excepcion_data.hora_fin,
                    excepcion_data.motivo
                )
                excepciones_creadas.append(nueva_excepcion)
            logger.info(f"✅ [POST /configuracion-completa] {len(excepciones_creadas)} excepciones creadas")
        
        logger.info(f"✅ [POST /configuracion-completa] Configuración completa creada para proveedor {perfil_id}")
        
        return {
            "horarios": horarios_creados,
            "excepciones": excepciones_creadas
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        # Capturar errores de validación de horarios
        logger.warning(f"❌ [POST /configuracion-completa] Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [POST /configuracion-completa] Error crítico: {str(e)}")
        logger.error(f"❌ [POST /configuracion-completa] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [POST /configuracion-completa] Traceback: {traceback.format_exc()}")
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
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Crea una excepción de horario usando direct_db_service.
    """
    logger.info(f"🔍 [POST /excepciones] Iniciando crear_excepcion_horario para user_id: {current_user.id}")
    logger.info(f"🔍 [POST /excepciones] Datos de excepción: {excepcion.dict()}")
    
    try:
        # Asegurar que la fecha sea un objeto date puro, sin timezone
        # Esto previene problemas de conversión de zona horaria que pueden restar un día
        from datetime import date as date_type
        fecha_date = excepcion.fecha
        
        # Procesar la fecha de manera segura para evitar problemas de timezone
        if isinstance(fecha_date, str):
            # Si viene como string, parsearlo como date puro
            # Asegurarse de tomar solo la parte de fecha (YYYY-MM-DD) sin hora ni timezone
            fecha_str = fecha_date.split('T')[0].split(' ')[0]  # Tomar solo YYYY-MM-DD
            fecha_date = date_type.fromisoformat(fecha_str)
        elif isinstance(fecha_date, date_type):
            # Si ya es date, usarlo directamente
            pass
        elif hasattr(fecha_date, 'date'):
            # Si es datetime, extraer solo la parte de fecha
            fecha_date = fecha_date.date()
        else:
            # Si es otro tipo, intentar convertirlo
            logger.warning(f"⚠️ [POST /excepciones] Tipo de fecha inesperado: {type(fecha_date).__name__}, valor: {fecha_date}")
            if hasattr(fecha_date, 'isoformat'):
                fecha_str = fecha_date.isoformat().split('T')[0]
                fecha_date = date_type.fromisoformat(fecha_str)
            else:
                raise ValueError(f"Tipo de fecha no soportado: {type(fecha_date).__name__}")
        
        logger.info(f"🔍 [POST /excepciones] Fecha recibida: {excepcion.fecha} (tipo: {type(excepcion.fecha).__name__})")
        logger.info(f"🔍 [POST /excepciones] Fecha procesada: {fecha_date} (tipo: {type(fecha_date).__name__})")
        
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [POST /excepciones] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [POST /excepciones] Perfil encontrado: id_perfil = {perfil_id}")
        
        # Verificar que no existe ya una excepción para esta fecha
        logger.info(f"🔍 [POST /excepciones] Verificando excepción existente para fecha {fecha_date}...")
        verificar_query = """
            SELECT id_excepcion FROM excepciones_horario 
            WHERE id_proveedor = $1 AND fecha = $2
        """
        excepcion_existente = await fetch_one_query(verificar_query, perfil_id, fecha_date)
        logger.info(f"🔍 [POST /excepciones] Excepción existente: {excepcion_existente}")
        
        if excepcion_existente:
            logger.warning(f"❌ [POST /excepciones] Ya existe excepción para fecha {fecha_date}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una excepción para la fecha {fecha_date}. Actualiza la existente o elimínala primero."
            )
        
        # Validar horarios si es horario_especial
        # La validación del schema ya se ejecutó automáticamente, pero la hacemos explícita para mejor mensaje de error
        if excepcion.tipo == 'horario_especial':
            try:
                from app.schemas.horario_trabajo import validate_horario_times
                if excepcion.hora_inicio and excepcion.hora_fin:
                    validate_horario_times(excepcion.hora_inicio, excepcion.hora_fin)
            except ValueError as e:
                logger.warning(f"❌ [POST /excepciones] Validación de horarios falló: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        # Crear nueva excepción usando helper
        logger.info("🔍 [POST /excepciones] Creando nueva excepción en base de datos...")
        logger.info(f"🔍 [POST /excepciones] Insertando fecha: {fecha_date} (tipo: {type(fecha_date).__name__})")
        insert_query = """
            INSERT INTO excepciones_horario (id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id_excepcion, id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo, created_at
        """
        nueva_excepcion = await fetch_one_query(
            insert_query,
            perfil_id,
            fecha_date,  # Usar fecha_date procesada en lugar de excepcion.fecha
            excepcion.tipo,
            excepcion.hora_inicio,
            excepcion.hora_fin,
            excepcion.motivo
        )
        logger.info(f"🔍 [POST /excepciones] Fecha guardada en BD: {nueva_excepcion.get('fecha')} (tipo: {type(nueva_excepcion.get('fecha')).__name__})")
        logger.info(f"🔍 [POST /excepciones] Excepción insertada: {nueva_excepcion}")
        
        logger.info(f"✅ [POST /excepciones] Excepción creada exitosamente: {nueva_excepcion['id_excepcion']}")
        
        return nueva_excepcion
        
    except HTTPException:
        raise
    except ValueError as e:
        # Capturar errores de validación de horarios
        logger.warning(f"❌ [POST /excepciones] Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [POST /excepciones] Error crítico: {str(e)}")
        logger.error(f"❌ [POST /excepciones] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [POST /excepciones] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al crear excepción: {str(e)}"
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
    logger.info(f"🔍 [GET /horario-trabajo/excepciones] Iniciando obtener_excepciones_horario para user_id: {current_user.id}")
    
    try:
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [GET /excepciones] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [GET /excepciones] Perfil encontrado: id_perfil = {perfil_id}")
        
        # Verificar si existe la tabla excepciones_horario
        logger.info("🔍 [GET /excepciones] Verificando existencia de tabla excepciones_horario...")
        check_table_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'excepciones_horario'
            );
        """
        table_exists = await fetch_one_query(check_table_query)
        logger.info(f"🔍 [GET /excepciones] Tabla excepciones_horario existe: {table_exists}")
        
        # Obtener excepciones usando helper
        logger.info(f"🔍 [GET /excepciones] Consultando excepciones para proveedor {perfil_id}...")
        excepciones_query = """
            SELECT id_excepcion, id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo, created_at
            FROM excepciones_horario 
            WHERE id_proveedor = $1
            ORDER BY fecha
        """
        excepciones_result = await fetch_all_query(excepciones_query, perfil_id)
        logger.info(f"🔍 [GET /excepciones] Excepciones encontradas: {len(excepciones_result) if excepciones_result else 0}")
        
        # Normalizar fechas para asegurar que sean objetos date puros, sin timezone
        from datetime import date as date_type
        if excepciones_result:
            for excepcion in excepciones_result:
                if 'fecha' in excepcion and excepcion['fecha']:
                    fecha_original = excepcion['fecha']
                    if isinstance(fecha_original, str):
                        # Si viene como string, parsearlo como date puro
                        excepcion['fecha'] = date_type.fromisoformat(fecha_original.split('T')[0])  # Tomar solo la parte de fecha
                    elif hasattr(fecha_original, 'date'):
                        # Si es datetime, extraer solo la parte de fecha
                        excepcion['fecha'] = fecha_original.date()
                    # Si ya es date, dejarlo como está
        
        logger.info(f"✅ [GET /excepciones] Devolviendo {len(excepciones_result)} excepciones")
        return excepciones_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET /excepciones] Error crítico: {str(e)}")
        logger.error(f"❌ [GET /excepciones] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [GET /excepciones] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al obtener excepciones: {str(e)}"
        )

@router.delete(
    "/excepciones/{excepcion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Elimina una excepción de horario."
)
async def eliminar_excepcion_horario(
    excepcion_id: int,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Elimina una excepción de horario usando direct_db_service.
    """
    logger.info(f"🔍 [DELETE /excepciones/{excepcion_id}] Iniciando eliminar_excepcion_horario para user_id: {current_user.id}")
    
    try:
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [DELETE /excepciones] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [DELETE /excepciones] Perfil encontrado: id_perfil = {perfil_id}")
        
        # Verificar que la excepción existe y pertenece al usuario
        logger.info(f"🔍 [DELETE /excepciones] Verificando excepción {excepcion_id} (tipo: {type(excepcion_id).__name__}) para proveedor {perfil_id} (tipo: {type(perfil_id).__name__})...")
        
        # Primero verificar si la excepción existe (sin verificar el proveedor)
        verificar_existencia_query = """
            SELECT id_excepcion, id_proveedor FROM excepciones_horario 
            WHERE id_excepcion = $1
        """
        excepcion_data = await fetch_one_query(verificar_existencia_query, excepcion_id)
        logger.info(f"🔍 [DELETE /excepciones] Datos de excepción en BD: {excepcion_data}")
        
        if not excepcion_data:
            # Intentar buscar todas las excepciones del proveedor para debugging
            todas_excepciones_query = """
                SELECT id_excepcion, id_proveedor, fecha FROM excepciones_horario 
                WHERE id_proveedor = $1
                ORDER BY id_excepcion
            """
            todas_excepciones = await fetch_all_query(todas_excepciones_query, perfil_id)
            logger.warning(f"❌ [DELETE /excepciones] Excepción {excepcion_id} no existe en la base de datos")
            logger.warning(f"🔍 [DELETE /excepciones] Excepciones disponibles para este proveedor: {todas_excepciones}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Excepción no encontrada."
            )
        
        # Verificar que pertenece al proveedor (comparar como enteros para evitar problemas de tipo)
        id_proveedor_bd = int(excepcion_data.get('id_proveedor')) if excepcion_data.get('id_proveedor') is not None else None
        perfil_id_int = int(perfil_id) if perfil_id is not None else None
        
        logger.info(f"🔍 [DELETE /excepciones] Comparando: id_proveedor_bd={id_proveedor_bd} (tipo: {type(id_proveedor_bd).__name__}) vs perfil_id={perfil_id_int} (tipo: {type(perfil_id_int).__name__})")
        
        if id_proveedor_bd != perfil_id_int:
            logger.warning(f"❌ [DELETE /excepciones] Excepción {excepcion_id} pertenece a proveedor {id_proveedor_bd}, pero el usuario actual es {perfil_id_int}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta excepción."
            )
        
        # Eliminar excepción usando helper
        delete_query = """
            DELETE FROM excepciones_horario 
            WHERE id_excepcion = $1 AND id_proveedor = $2
        """
        await execute_query(delete_query, excepcion_id, perfil_id)
        
        logger.info(f"✅ [DELETE /excepciones] Excepción {excepcion_id} eliminada exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [DELETE /excepciones] Error crítico: {str(e)}")
        logger.error(f"❌ [DELETE /excepciones] Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [DELETE /excepciones] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al eliminar excepción: {str(e)}"
        )
