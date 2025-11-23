# app/api/v1/routers/services/provider_services.py

import logging
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import date

logger = logging.getLogger(__name__)

from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.models.servicio.service import ServicioModel
from app.models.publicar_servicio.tarifa_servicio import TarifaServicio
from app.models.publicar_servicio.tipo_tarifa_servicio import TipoTarifaServicio
from app.models.publicar_servicio.moneda import Moneda
from app.models.publicar_servicio.category import CategoriaModel
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.schemas.servicio.service import ServicioUpdate, ServicioCreate, ServicioOut
from app.schemas.publicar_servicio.tarifa_servicio import TarifaServicioIn, TarifaServicioOut
from app.services.direct_db_service import direct_db_service
from pydantic import BaseModel

router = APIRouter(prefix="/provider/services", tags=["provider-services"])

# Constantes para mensajes de error
MSG_PERFIL_EMPRESA_NO_ENCONTRADO = "Perfil de empresa no encontrado."
MSG_SERVICIO_NO_ENCONTRADO_SIN_PERMISOS_VER = "Servicio no encontrado o no tienes permisos para verlo."
MSG_SERVICIO_NO_ENCONTRADO_SIN_PERMISOS_EDITAR = "Servicio no encontrado o no tienes permisos para editarlo."
MSG_SERVICIO_NO_ENCONTRADO_SIN_PERMISOS_MODIFICAR = "Servicio no encontrado o no tienes permisos para modificarlo"
MSG_TARIFA_NO_ENCONTRADA = "Tarifa no encontrada."
MSG_PLANTILLA_SERVICIO_NO_ENCONTRADA = "Plantilla de servicio no encontrada"
MSG_ERROR_INTERNO_SERVIDOR = "Error interno del servidor: {error}"
MSG_ERROR_INTERNO_ACTUALIZAR_ESTADO = "Error interno del servidor al actualizar el estado del servicio"
MSG_ERROR_INTERNO_CREAR_DESDE_PLANTILLA = "Error interno del servidor al crear el servicio desde plantilla"
MSG_ERROR_FORMATO_FECHA = "Error en formato de fecha: {error}"
MSG_ERROR_PROCESAR_IMAGEN = "Error al procesar la imagen: {error}"
MSG_ERROR_ELIMINAR_IMAGEN = "Error al eliminar la imagen: {error}"
MSG_SOLO_PERMITEN_ARCHIVOS_IMAGEN = "Solo se permiten archivos PNG, JPG y WEBP."
MSG_ARCHIVO_SUPERA_TAMANO = "El archivo no puede superar los 5MB."
MSG_ERROR_SUBIR_IMAGEN_STORAGE = "Error al subir la imagen a Supabase Storage."
MSG_URL_IMAGEN_NO_VALIDA = "URL de imagen no válida para eliminación"
MSG_ERROR_ELIMINAR_IMAGEN_BUCKET = "Error al eliminar la imagen del bucket"

# Constantes para mensajes de éxito
MSG_SERVICIO_ACTUALIZADO = "Servicio actualizado exitosamente."
MSG_TARIFA_AGREGADA = "Tarifa agregada exitosamente."
MSG_TARIFA_ELIMINADA = "Tarifa eliminada exitosamente."
MSG_IMAGEN_SUBIDA = "Imagen subida exitosamente a Supabase Storage."
MSG_IMAGEN_ELIMINADA = "Imagen eliminada exitosamente del bucket de Supabase Storage."
MSG_SERVICIO_CREADO_DESDE_PLANTILLA = "Servicio creado exitosamente desde plantilla"
MSG_SERVICIO_ACTIVADO = "Servicio activado exitosamente"
MSG_SERVICIO_DESACTIVADO = "Servicio desactivado exitosamente"

# Constantes para valores por defecto
VALOR_DEFAULT_TIPO_TARIFA = "Tipo de tarifa"
VALOR_DEFAULT_SIN_TIPO = "Sin tipo"
TIPO_TARIFA_POR_HORA = "Por hora"
TIPO_TARIFA_POR_DIA = "Por día"
TIPO_TARIFA_POR_PROYECTO = "Por proyecto"
TIPO_TARIFA_POR_SEMANA = "Por semana"
TIPO_TARIFA_POR_MES = "Por mes"

# Modelos Pydantic para las respuestas
class ServicioCompleto(BaseModel):
    id_servicio: int
    nombre: str
    descripcion: str
    precio: float | None  # Hacer precio opcional para servicios sin precio
    estado: bool | None  # Hacer estado opcional para servicios con estado null
    imagen: str | None  # Ruta de la imagen representativa del servicio
    id_categoria: int | None
    id_moneda: int | None
    nombre_categoria: str | None
    nombre_moneda: str | None
    simbolo_moneda: str | None
    created_at: str
    tarifas: List[dict] = []

    class Config:
        from_attributes = True

class TarifaResponse(BaseModel):
    id_tarifa_servicio: int
    monto: float
    descripcion: str
    fecha_inicio: str
    fecha_fin: str | None
    id_tarifa: int
    nombre_tipo_tarifa: str

# Usar TarifaServicioIn que ya existe

# Funciones helper para get_provider_services
async def get_provider_profile(conn, user_id: str) -> dict:
    """Obtiene el perfil de empresa del proveedor usando direct_db_service"""
    perfil_query = "SELECT id_perfil FROM perfil_empresa WHERE user_id = $1"
    perfil_row = await conn.fetchrow(perfil_query, user_id)
    
    if not perfil_row:
        logger.warning(f"❌ Perfil no encontrado para usuario: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
        )
    
    logger.info(f"✅ Perfil encontrado: {perfil_row['id_perfil']}")
    return perfil_row

async def get_servicios_by_perfil(conn, id_perfil: int) -> List[dict]:
    """Obtiene todos los servicios del proveedor con información relacionada usando direct_db_service"""
    query = """
        SELECT 
            s.id_servicio,
            s.nombre,
            s.descripcion,
            s.precio,
            s.estado,
            s.imagen,
            s.id_categoria,
            s.id_moneda,
            s.created_at,
            c.nombre AS nombre_categoria,
            m.nombre AS nombre_moneda,
            m.simbolo AS simbolo_moneda,
            m.codigo_iso_moneda
        FROM servicio s
        LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
        LEFT JOIN moneda m ON s.id_moneda = m.id_moneda
        WHERE s.id_perfil = $1
        ORDER BY s.created_at DESC
    """
    return await conn.fetch(query, id_perfil)

async def get_tarifas_for_servicio(conn, id_servicio: int) -> List[dict]:
    """Obtiene todas las tarifas de un servicio usando direct_db_service"""
    query = """
        SELECT 
            ts.id_tarifa_servicio,
            ts.monto,
            ts.descripcion,
            ts.fecha_inicio,
            ts.fecha_fin,
            ts.id_tarifa,
            tts.nombre AS nombre_tipo_tarifa
        FROM tarifa_servicio ts
        LEFT JOIN tipo_tarifa_servicio tts ON ts.id_tarifa = tts.id_tarifa
        WHERE ts.id_servicio = $1
        ORDER BY ts.fecha_inicio DESC
    """
    return await conn.fetch(query, id_servicio)

def format_tarifa(tarifa_row: dict) -> dict:
    """Formatea una tarifa en el formato de respuesta"""
    return {
        "id_tarifa_servicio": tarifa_row['id_tarifa_servicio'],
        "monto": float(tarifa_row['monto']),
        "descripcion": tarifa_row['descripcion'],
        "fecha_inicio": tarifa_row['fecha_inicio'].isoformat() if tarifa_row['fecha_inicio'] else None,
        "fecha_fin": tarifa_row['fecha_fin'].isoformat() if tarifa_row['fecha_fin'] else None,
        "id_tarifa": tarifa_row['id_tarifa'],
        "nombre_tipo_tarifa": tarifa_row['nombre_tipo_tarifa'] or VALOR_DEFAULT_TIPO_TARIFA
    }

async def format_servicio_completo(
    conn,
    servicio_row: dict
) -> dict:
    """Formatea un servicio con todas sus tarifas"""
    # Obtener tarifas del servicio
    tarifas_data = await get_tarifas_for_servicio(conn, servicio_row['id_servicio'])
    
    # Formatear tarifas
    tarifas = [format_tarifa(tarifa) for tarifa in tarifas_data]
    
    return {
        "id_servicio": servicio_row['id_servicio'],
        "nombre": servicio_row['nombre'],
        "descripcion": servicio_row['descripcion'],
        "precio": float(servicio_row['precio']) if servicio_row['precio'] is not None else None,
        "estado": servicio_row['estado'],
        "imagen": servicio_row['imagen'],
        "id_categoria": servicio_row['id_categoria'],
        "id_moneda": servicio_row['id_moneda'],
        "nombre_categoria": servicio_row['nombre_categoria'],
        "nombre_moneda": servicio_row['nombre_moneda'],
        "simbolo_moneda": servicio_row['simbolo_moneda'],
        "codigo_iso_moneda": servicio_row['codigo_iso_moneda'],
        "created_at": servicio_row['created_at'].isoformat() if servicio_row['created_at'] else None,
        "tarifas": tarifas
    }

@router.get("/", response_model=List[ServicioCompleto])
async def get_provider_services(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene todos los servicios del proveedor actual con información completa.
    Usa direct_db_service para evitar problemas con PgBouncer y prepared statements.
    """
    try:
        logger.info(f"🔍 Obteniendo servicios para usuario: {current_user.email}")
        
        conn = await direct_db_service.get_connection()
        try:
            # Obtener el perfil del usuario
            perfil = await get_provider_profile(conn, current_user.id)
            
            # Obtener servicios del proveedor
            servicios = await get_servicios_by_perfil(conn, perfil['id_perfil'])
            
            # Formatear servicios con sus tarifas
            servicios_formateados = []
            for servicio_row in servicios:
                servicio_formateado = await format_servicio_completo(conn, servicio_row)
                servicios_formateados.append(servicio_formateado)
            
            return servicios_formateados
        finally:
            await direct_db_service.pool.release(conn)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en get_provider_services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_SERVIDOR.format(error=str(e))
        )

@router.get("/{service_id}", response_model=ServicioCompleto)
async def get_provider_service(
    service_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene un servicio específico del proveedor con información completa.
    """
    # Obtener el perfil del usuario
    perfil_result = await db.execute(
        select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
    )
    perfil = perfil_result.scalars().first()

    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
        )

    # Obtener el servicio específico
    result = await db.execute(
        select(ServicioModel)
        .options(
            joinedload(ServicioModel.categoria),
            joinedload(ServicioModel.moneda),
            joinedload(ServicioModel.tarifa_servicio).joinedload(TarifaServicio.tipo_tarifa_servicio)
        )
        .where(ServicioModel.id_servicio == service_id)
        .where(ServicioModel.id_perfil == perfil.id_perfil)
    )

    servicio = result.scalars().first()

    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_SERVICIO_NO_ENCONTRADO_SIN_PERMISOS_VER
        )

    # Obtener tarifas del servicio
    tarifas = []
    for tarifa in servicio.tarifa_servicio or []:
        tarifas.append({
            "id_tarifa_servicio": tarifa.id_tarifa_servicio,
            "monto": float(tarifa.monto),
            "descripcion": tarifa.descripcion,
            "fecha_inicio": tarifa.fecha_inicio.isoformat(),
            "fecha_fin": tarifa.fecha_fin.isoformat() if tarifa.fecha_fin else None,
            "id_tarifa": tarifa.id_tarifa,
            "nombre_tipo_tarifa": tarifa.tipo_tarifa_servicio.nombre if tarifa.tipo_tarifa_servicio else VALOR_DEFAULT_SIN_TIPO
        })

    return {
        "id_servicio": servicio.id_servicio,
        "nombre": servicio.nombre,
        "descripcion": servicio.descripcion,
        "precio": float(servicio.precio),
        "estado": servicio.estado,
        "id_categoria": servicio.id_categoria,
        "id_moneda": servicio.id_moneda,
        "nombre_categoria": servicio.categoria.nombre if servicio.categoria else None,
        "nombre_moneda": servicio.moneda.nombre if servicio.moneda else None,
        "simbolo_moneda": servicio.moneda.simbolo if servicio.moneda else None,
        "created_at": servicio.created_at.isoformat() if servicio.created_at else None,
        "tarifas": tarifas
    }

# Funciones helper para update_provider_service
async def get_servicio_by_id_and_perfil(
    db: AsyncSession,
    service_id: int,
    id_perfil: int
) -> ServicioModel:
    """Obtiene un servicio específico del proveedor"""
    result = await db.execute(
        select(ServicioModel)
        .where(ServicioModel.id_servicio == service_id)
        .where(ServicioModel.id_perfil == id_perfil)
    )
    
    servicio = result.scalars().first()
    
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_SERVICIO_NO_ENCONTRADO_SIN_PERMISOS_EDITAR
        )
    
    return servicio

def update_servicio_fields(servicio: ServicioModel, service_data: dict) -> None:
    """Actualiza los campos del servicio con los datos proporcionados"""
    if 'nombre' in service_data:
        servicio.nombre = service_data['nombre']
    if 'descripcion' in service_data:
        servicio.descripcion = service_data['descripcion']
    if 'precio' in service_data:
        servicio.precio = service_data['precio']
    if 'id_moneda' in service_data:
        servicio.id_moneda = service_data['id_moneda']
    if 'imagen' in service_data:
        servicio.imagen = service_data['imagen']
    if 'estado' in service_data:
        servicio.estado = service_data['estado']

def convert_fecha_field(fecha_value) -> Optional[date]:
    """Convierte un valor de fecha a objeto date"""
    if not fecha_value:
        return None
    
    if isinstance(fecha_value, str):
        return date.fromisoformat(fecha_value)
    
    return fecha_value

def parse_tarifa_fechas(tarifa_data: dict) -> tuple[Optional[date], Optional[date]]:
    """Convierte las fechas de una tarifa de string a objetos date"""
    fecha_inicio = convert_fecha_field(tarifa_data.get('fecha_inicio'))
    fecha_fin = convert_fecha_field(tarifa_data.get('fecha_fin'))
    return fecha_inicio, fecha_fin

def create_tarifa_from_data(
    db: AsyncSession,
    tarifa_data: dict,
    service_id: int
) -> None:
    """Crea una nueva tarifa desde los datos proporcionados"""
    try:
        fecha_inicio, fecha_fin = parse_tarifa_fechas(tarifa_data)
        
        nueva_tarifa = TarifaServicio(
            monto=tarifa_data['monto'],
            descripcion=tarifa_data['descripcion'],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_servicio=service_id,
            id_tarifa=tarifa_data['id_tarifa']
        )
        db.add(nueva_tarifa)
        
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Error al convertir fecha en tarifa: {e}")
        logger.error(f"   Datos de tarifa: {tarifa_data}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_ERROR_FORMATO_FECHA.format(error=str(e))
        )

async def delete_existing_tarifas(db: AsyncSession, service_id: int) -> None:
    """Elimina todas las tarifas existentes de un servicio"""
    await db.execute(
        TarifaServicio.__table__.delete().where(TarifaServicio.id_servicio == service_id)
    )

async def process_tarifas_update(
    db: AsyncSession,
    service_id: int,
    tarifas_data: List[dict]
) -> None:
    """Procesa la actualización de tarifas: elimina las existentes y crea las nuevas"""
    # Eliminar tarifas existentes
    await delete_existing_tarifas(db, service_id)
    
    # Agregar nuevas tarifas
    for tarifa_data in tarifas_data:
        create_tarifa_from_data(db, tarifa_data, service_id)

@router.put("/{service_id}")
async def update_provider_service(
    service_id: int,
    service_data: dict,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza un servicio del proveedor con toda su información.
    """
    # Obtener el perfil del usuario
    perfil = await get_provider_profile(db, current_user.id)
    
    # Obtener el servicio específico
    servicio = await get_servicio_by_id_and_perfil(db, service_id, perfil.id_perfil)
    
    # Actualizar los campos del servicio
    update_servicio_fields(servicio, service_data)
    
    # Gestionar tarifas si se incluyen
    if 'tarifas' in service_data:
        await process_tarifas_update(db, service_id, service_data['tarifas'])
    
    await db.commit()
    
    return {"message": MSG_SERVICIO_ACTUALIZADO}

@router.get("/options/monedas", response_model=List[dict])
async def get_monedas_options(db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todas las monedas disponibles para los servicios.
    Usa direct_db_service para evitar problemas con PgBouncer y prepared statements.
    """
    try:
        conn = await direct_db_service.get_connection()
        try:
            query = """
                SELECT id_moneda, nombre, simbolo, codigo_iso_moneda
                FROM moneda
                ORDER BY nombre
            """
            monedas = await conn.fetch(query)

            return [
                {
                    "id_moneda": moneda['id_moneda'],
                    "nombre": moneda['nombre'],
                    "simbolo": moneda['simbolo'],
                    "codigo_iso": moneda['codigo_iso_moneda']
                }
                for moneda in monedas
            ]
        finally:
            await direct_db_service.pool.release(conn)
    except Exception as e:
        logger.error(f"❌ Error en get_monedas_options: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo monedas: {e}"
        )

@router.get("/options/tipos-tarifa", response_model=List[dict])
async def get_tipos_tarifa_options(db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todos los tipos de tarifa disponibles.
    Usa direct_db_service para evitar problemas con PgBouncer y prepared statements.
    """
    try:
        conn = await direct_db_service.get_connection()
        try:
            # Consultar tipos de tarifa existentes
            query = """
                SELECT id_tarifa, nombre
                FROM tipo_tarifa_servicio
                ORDER BY nombre
            """
            tipos_tarifa = await conn.fetch(query)

            # Si no hay tipos de tarifa, insertar algunos por defecto
            if not tipos_tarifa:
                print("📝 Insertando tipos de tarifa por defecto...")

                # Insertar tipos de tarifa por defecto usando SQL directo
                default_tipos = [
                    {'nombre': TIPO_TARIFA_POR_HORA, 'descripcion': 'Tarifa por hora de trabajo'},
                    {'nombre': TIPO_TARIFA_POR_DIA, 'descripcion': 'Tarifa por día de trabajo'},
                    {'nombre': TIPO_TARIFA_POR_PROYECTO, 'descripcion': 'Tarifa fija por proyecto'},
                    {'nombre': TIPO_TARIFA_POR_SEMANA, 'descripcion': 'Tarifa por semana de trabajo'},
                    {'nombre': TIPO_TARIFA_POR_MES, 'descripcion': 'Tarifa por mes de trabajo'}
                ]

                insert_query = """
                    INSERT INTO tipo_tarifa_servicio (nombre, descripcion, estado)
                    VALUES ($1, $2, $3)
                """
                
                for tipo in default_tipos:
                    await conn.execute(insert_query, tipo['nombre'], tipo['descripcion'], True)

                # Volver a consultar después de insertar
                tipos_tarifa = await conn.fetch(query)

            return [
                {
                    "id_tarifa": tipo['id_tarifa'],
                    "nombre": tipo['nombre']
                }
                for tipo in tipos_tarifa
            ]
        finally:
            await direct_db_service.pool.release(conn)

    except Exception as e:
        logger.error(f"❌ Error en get_tipos_tarifa_options: {e}")
        # Retornar tipos por defecto si hay error
        return [
            {"id_tarifa": 1, "nombre": TIPO_TARIFA_POR_HORA},
            {"id_tarifa": 2, "nombre": TIPO_TARIFA_POR_DIA},
            {"id_tarifa": 3, "nombre": TIPO_TARIFA_POR_PROYECTO}
        ]

@router.post("/{service_id}/tarifas")
async def add_tarifa_to_service(
    service_id: int,
    tarifa_data: TarifaServicioIn,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Agrega una nueva tarifa a un servicio del proveedor.
    """
    # Verificar que el servicio pertenece al usuario
    perfil_result = await db.execute(
        select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
    )
    perfil = perfil_result.scalars().first()

    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
        )

    # Verificar que el servicio existe y pertenece al usuario
    service_result = await db.execute(
        select(ServicioModel)
        .where(ServicioModel.id_servicio == service_id)
        .where(ServicioModel.id_perfil == perfil.id_perfil)
    )

    servicio = service_result.scalars().first()

    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_SERVICIO_NO_ENCONTRADO_SIN_PERMISOS_EDITAR
        )

    # Crear nueva tarifa
    # Las fechas ya vienen como objetos date desde Pydantic
    nueva_tarifa = TarifaServicio(
        monto=tarifa_data.monto,
        descripcion=tarifa_data.descripcion,
        fecha_inicio=tarifa_data.fecha_inicio,
        fecha_fin=tarifa_data.fecha_fin,
        id_servicio=service_id,
        id_tarifa=tarifa_data.id_tarifa
    )

    db.add(nueva_tarifa)
    await db.commit()

    return {"message": MSG_TARIFA_AGREGADA}

@router.delete("/{service_id}/tarifas/{tarifa_id}")
async def remove_tarifa_from_service(
    service_id: int,
    tarifa_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina una tarifa de un servicio del proveedor.
    """
    # Verificar que el servicio pertenece al usuario
    perfil_result = await db.execute(
        select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
    )
    perfil = perfil_result.scalars().first()

    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
        )

    # Verificar que el servicio existe y pertenece al usuario
    service_result = await db.execute(
        select(ServicioModel)
        .where(ServicioModel.id_servicio == service_id)
        .where(ServicioModel.id_perfil == perfil.id_perfil)
    )

    servicio = service_result.scalars().first()

    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_SERVICIO_NO_ENCONTRADO_SIN_PERMISOS_EDITAR
        )

    # Eliminar la tarifa
    result = await db.execute(
        TarifaServicio.__table__.delete()
        .where(TarifaServicio.id_tarifa_servicio == tarifa_id)
        .where(TarifaServicio.id_servicio == service_id)
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_TARIFA_NO_ENCONTRADA
        )

    await db.commit()

    return {"message": MSG_TARIFA_ELIMINADA}

# Directorio para almacenar imágenes subidas
UPLOAD_DIRECTORY = "uploads/services"

# Crear directorio si no existe
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


@router.post("/upload-image")
async def upload_service_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Sube una imagen para un servicio usando Supabase Storage (PNG/JPG, máximo 5MB).
    """
    # Validar tipo de archivo
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_SOLO_PERMITEN_ARCHIVOS_IMAGEN
        )

    # Validar tamaño del archivo (5MB máximo)
    content = await file.read()
    file_size = len(content)

    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_ARCHIVO_SUPERA_TAMANO
        )

    # Usar Supabase Storage
    from app.services.supabase_storage_service import supabase_storage_service
    
    try:
        # Subir imagen a Supabase Storage en la carpeta servicios/
        success, public_url = await supabase_storage_service.upload_service_image(
            file_content=content,
            file_name=file.filename,
            content_type=file.content_type
        )
        
        if success and public_url:
            logger.info(f"✅ Imagen subida exitosamente a Supabase Storage: {public_url}")
            return {
                "message": MSG_IMAGEN_SUBIDA,
                "image_path": public_url
            }
        else:
            logger.error("❌ Error subiendo imagen a Supabase Storage")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=MSG_ERROR_SUBIR_IMAGEN_STORAGE
            )
            
    except Exception as e:
        logger.error(f"❌ Error en upload_service_image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_PROCESAR_IMAGEN.format(error=str(e))
        )

@router.delete("/delete-image")
async def delete_service_image(
    image_url: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina una imagen de servicio del bucket de Supabase Storage.
    """
    try:
        from app.services.supabase_storage_service import supabase_storage_service
        
        # Verificar que la URL es de Supabase Storage
        if not image_url or not image_url.startswith('https://') or 'supabase.co' not in image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_URL_IMAGEN_NO_VALIDA
            )
        
        # Extraer el nombre del archivo de la URL
        import os
        file_name = os.path.basename(image_url.split('?')[0])  # Remover query parameters
        
        # Eliminar imagen del bucket
        success = await supabase_storage_service.delete_image(image_url)
        
        if success:
            logger.info(f"✅ Imagen eliminada exitosamente del bucket: {file_name}")
            return {
                "message": MSG_IMAGEN_ELIMINADA,
                "deleted_file": file_name
            }
        else:
            logger.error(f"❌ Error eliminando imagen del bucket: {file_name}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=MSG_ERROR_ELIMINAR_IMAGEN_BUCKET
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en delete_service_image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_ELIMINAR_IMAGEN.format(error=str(e))
        )

# Modelo para actualizar estado del servicio
class ServicioStatusUpdate(BaseModel):
    estado: bool

@router.patch("/{service_id}/status")
async def update_service_status(
    service_id: int,
    status_data: ServicioStatusUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza el estado (activo/inactivo) de un servicio del proveedor.
    """
    try:
        # Obtener el perfil de la empresa del usuario actual
        perfil_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
        perfil_result = await db.execute(perfil_query)
        perfil = perfil_result.scalar_one_or_none()
        
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
            )

        # Verificar que el servicio pertenece al proveedor
        servicio_query = select(ServicioModel).where(
            ServicioModel.id_servicio == service_id,
            ServicioModel.id_perfil == perfil.id_perfil
        )
        servicio_result = await db.execute(servicio_query)
        servicio = servicio_result.scalar_one_or_none()
        
        if not servicio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_SERVICIO_NO_ENCONTRADO_SIN_PERMISOS_MODIFICAR
            )

        # Actualizar el estado del servicio
        servicio.estado = status_data.estado
        await db.commit()
        await db.refresh(servicio)

        return {
            "message": MSG_SERVICIO_ACTIVADO if status_data.estado else MSG_SERVICIO_DESACTIVADO,
            "servicio": {
                "id_servicio": servicio.id_servicio,
                "nombre": servicio.nombre,
                "estado": servicio.estado
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar estado del servicio: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_ACTUALIZAR_ESTADO
        )


# Modelo para crear servicio desde plantilla
class ServicioFromTemplate(BaseModel):
    template_id: int
    nombre: str
    descripcion: str
    precio: float
    id_moneda: int
    imagen: Optional[str] = None

@router.post("/from-template")
async def create_service_from_template(
    service_data: ServicioFromTemplate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un nuevo servicio basado en una plantilla existente.
    """
    try:
        # Obtener el perfil de la empresa del usuario actual
        perfil_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
        perfil_result = await db.execute(perfil_query)
        perfil = perfil_result.scalar_one_or_none()
        
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
            )

        # Obtener la plantilla del servicio
        template_query = select(ServicioModel).where(ServicioModel.id_servicio == service_data.template_id)
        template_result = await db.execute(template_query)
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_PLANTILLA_SERVICIO_NO_ENCONTRADA
            )

        # Crear nuevo servicio basado en la plantilla
        nuevo_servicio = ServicioModel(
            nombre=service_data.nombre,
            descripcion=service_data.descripcion,
            precio=service_data.precio,
            id_categoria=template.id_categoria,  # Usar la misma categoría
            id_moneda=service_data.id_moneda,
            id_perfil=perfil.id_perfil,  # Asignar al proveedor actual
            estado=True,  # Activo por defecto
            imagen=service_data.imagen
        )
        
        db.add(nuevo_servicio)
        await db.commit()
        await db.refresh(nuevo_servicio)

        return {
            "message": MSG_SERVICIO_CREADO_DESDE_PLANTILLA,
            "servicio": {
                "id_servicio": nuevo_servicio.id_servicio,
                "nombre": nuevo_servicio.nombre,
                "descripcion": nuevo_servicio.descripcion,
                "precio": nuevo_servicio.precio,
                "id_categoria": nuevo_servicio.id_categoria,
                "estado": nuevo_servicio.estado
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear servicio desde plantilla: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_CREAR_DESDE_PLANTILLA
        )
