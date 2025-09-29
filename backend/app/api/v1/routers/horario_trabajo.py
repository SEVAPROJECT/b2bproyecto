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
        
        # Verificar que no existe ya un horario para este día
        logger.info(f"🔍 [POST /horario-trabajo/] Verificando horario existente para día {horario.dia_semana}...")
        verificar_query = """
            SELECT id_horario FROM horario_trabajo 
            WHERE id_proveedor = $1 AND dia_semana = $2
        """
        horario_existente = await fetch_one_query(verificar_query, perfil_id, horario.dia_semana)
        logger.info(f"🔍 [POST /horario-trabajo/] Horario existente: {horario_existente}")
        
        if horario_existente:
            logger.warning(f"❌ [POST /horario-trabajo/] Ya existe horario para día {horario.dia_semana}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un horario para el día {horario.dia_semana}. Actualiza el existente o elimínalo primero."
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
            logger.info(f"✅ [PUT /horario-trabajo] No hay cambios que aplicar, devolviendo horario actual")
            return horario_existente
        
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
        
        logger.info(f"🔍 [PUT /horario-trabajo] Ejecutando actualización...")
        horario_actualizado = await fetch_one_query(update_query, *params)
        logger.info(f"🔍 [PUT /horario-trabajo] Horario actualizado: {horario_actualizado}")
        
        logger.info(f"✅ [PUT /horario-trabajo] Horario {horario_id} actualizado exitosamente")
        return horario_actualizado
        
    except HTTPException:
        raise
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
        # Obtener el perfil del proveedor usando direct_db_service
        logger.info("🔍 [POST /configuracion-completa] Consultando perfil de empresa...")
        perfil_query = """
            SELECT id_perfil FROM perfil_empresa 
            WHERE user_id = $1
        """
        perfil_result = await direct_db_service.fetch_one(perfil_query, current_user.id)
        logger.info(f"🔍 [POST /configuracion-completa] Resultado perfil: {perfil_result}")
        
        if not perfil_result:
            logger.warning(f"❌ [POST /configuracion-completa] Perfil no encontrado para user_id: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado. Solo los proveedores pueden gestionar horarios."
            )
        
        perfil_id = perfil_result['id_perfil']
        logger.info(f"✅ [POST /configuracion-completa] Perfil encontrado: id_perfil = {perfil_id}")
    
        # Eliminar horarios existentes usando direct_db_service
        logger.info("🔍 [POST /configuracion-completa] Eliminando horarios existentes...")
        delete_horarios_query = """
            DELETE FROM horario_trabajo 
            WHERE id_proveedor = $1
        """
        await direct_db_service.execute(delete_horarios_query, perfil_id)
        logger.info("✅ [POST /configuracion-completa] Horarios existentes eliminados")
        
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
            nuevo_horario = await direct_db_service.fetch_one(
                insert_horario_query,
                perfil_id,
                horario_data.dia_semana,
                horario_data.hora_inicio,
                horario_data.hora_fin,
                horario_data.activo
            )
            horarios_creados.append({
                "id_horario": nuevo_horario['id_horario'],
                "id_proveedor": nuevo_horario['id_proveedor'],
                "dia_semana": nuevo_horario['dia_semana'],
                "hora_inicio": nuevo_horario['hora_inicio'],
                "hora_fin": nuevo_horario['hora_fin'],
                "activo": nuevo_horario['activo'],
                "created_at": nuevo_horario['created_at']
            })
        logger.info(f"✅ [POST /configuracion-completa] {len(horarios_creados)} horarios creados")
        
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
                nueva_excepcion = await direct_db_service.fetch_one(
                    insert_excepcion_query,
                    perfil_id,
                    excepcion_data.fecha,
                    excepcion_data.tipo,
                    excepcion_data.hora_inicio,
                    excepcion_data.hora_fin,
                    excepcion_data.motivo
                )
                excepciones_creadas.append({
                    "id_excepcion": nueva_excepcion['id_excepcion'],
                    "id_proveedor": nueva_excepcion['id_proveedor'],
                    "fecha": nueva_excepcion['fecha'],
                    "tipo": nueva_excepcion['tipo'],
                    "hora_inicio": nueva_excepcion['hora_inicio'],
                    "hora_fin": nueva_excepcion['hora_fin'],
                    "motivo": nueva_excepcion['motivo'],
                    "created_at": nueva_excepcion['created_at']
                })
            logger.info(f"✅ [POST /configuracion-completa] {len(excepciones_creadas)} excepciones creadas")
        
        logger.info(f"✅ [POST /configuracion-completa] Configuración completa creada para proveedor {perfil_id}")
        
        return {
            "horarios": horarios_creados,
            "excepciones": excepciones_creadas
        }
        
    except HTTPException:
        raise
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
        # Obtener el perfil del proveedor usando helper
        logger.info("🔍 [POST /excepciones] Consultando perfil de empresa...")
        perfil_id = await get_provider_profile_direct(current_user.id)
        logger.info(f"✅ [POST /excepciones] Perfil encontrado: id_perfil = {perfil_id}")
        
        # Verificar que no existe ya una excepción para esta fecha
        logger.info(f"🔍 [POST /excepciones] Verificando excepción existente para fecha {excepcion.fecha}...")
        verificar_query = """
            SELECT id_excepcion FROM excepciones_horario 
            WHERE id_proveedor = $1 AND fecha = $2
        """
        excepcion_existente = await fetch_one_query(verificar_query, perfil_id, excepcion.fecha)
        logger.info(f"🔍 [POST /excepciones] Excepción existente: {excepcion_existente}")
        
        if excepcion_existente:
            logger.warning(f"❌ [POST /excepciones] Ya existe excepción para fecha {excepcion.fecha}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una excepción para la fecha {excepcion.fecha}. Actualiza la existente o elimínala primero."
            )
        
        # Crear nueva excepción usando helper
        logger.info("🔍 [POST /excepciones] Creando nueva excepción en base de datos...")
        insert_query = """
            INSERT INTO excepciones_horario (id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id_excepcion, id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo, created_at
        """
        nueva_excepcion = await fetch_one_query(
            insert_query,
            perfil_id,
            excepcion.fecha,
            excepcion.tipo,
            excepcion.hora_inicio,
            excepcion.hora_fin,
            excepcion.motivo
        )
        logger.info(f"🔍 [POST /excepciones] Excepción insertada: {nueva_excepcion}")
        
        logger.info(f"✅ [POST /excepciones] Excepción creada exitosamente: {nueva_excepcion['id_excepcion']}")
        
        return nueva_excepcion
        
    except HTTPException:
        raise
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
        # Obtener el perfil del proveedor usando direct_db_service
        logger.info("🔍 [GET /excepciones] Consultando perfil de empresa...")
        perfil_query = """
            SELECT id_perfil FROM perfil_empresa 
            WHERE user_id = $1
        """
        perfil_result = await direct_db_service.fetch_one(perfil_query, current_user.id)
        logger.info(f"🔍 [GET /excepciones] Resultado perfil: {perfil_result}")
        
        if not perfil_result:
            logger.warning(f"❌ [GET /excepciones] Perfil no encontrado para user_id: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de empresa no encontrado. Solo los proveedores pueden gestionar horarios."
            )
        
        perfil_id = perfil_result['id_perfil']
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
        table_exists = await direct_db_service.fetch_one(check_table_query)
        logger.info(f"🔍 [GET /excepciones] Tabla excepciones_horario existe: {table_exists}")
        
        # Obtener excepciones usando direct_db_service
        logger.info(f"🔍 [GET /excepciones] Consultando excepciones para proveedor {perfil_id}...")
        excepciones_query = """
            SELECT id_excepcion, id_proveedor, fecha, tipo, hora_inicio, hora_fin, motivo, created_at
            FROM excepciones_horario 
            WHERE id_proveedor = $1
            ORDER BY fecha
        """
        excepciones_result = await direct_db_service.fetch_all(excepciones_query, perfil_id)
        logger.info(f"🔍 [GET /excepciones] Excepciones encontradas: {len(excepciones_result) if excepciones_result else 0}")
        
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
        
        logger.info(f"✅ [GET /excepciones] Devolviendo {len(excepciones)} excepciones")
        return excepciones
        
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
