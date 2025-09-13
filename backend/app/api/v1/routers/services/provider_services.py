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
from app.models.publicar_servicio.publish_service import Servicio
from app.models.publicar_servicio.tarifa_servicio import TarifaServicio
from app.models.publicar_servicio.tipo_tarifa_servicio import TipoTarifaServicio
from app.models.publicar_servicio.moneda import Moneda
from app.models.publicar_servicio.category import Categoria
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.schemas.publicar_servicio.publish_service import ServicioUpdate, ServicioCreate, ServicioOut
from app.schemas.publicar_servicio.tarifa_servicio import TarifaServicioIn, TarifaServicioOut
from pydantic import BaseModel

router = APIRouter(prefix="/provider/services", tags=["provider-services"])

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

@router.get("/", response_model=List[ServicioCompleto])
async def get_provider_services(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene todos los servicios del proveedor actual con información completa.
    """
    # Obtener el perfil del usuario
    perfil_result = await db.execute(
        select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
    )
    perfil = perfil_result.scalars().first()

    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de empresa no encontrado."
        )

    # Obtener servicios del proveedor con información relacionada (simplificada para evitar errores de columna)
    # QUITAR FILTRO DE ESTADO PARA MOSTRAR TODOS LOS SERVICIOS
    result = await db.execute(
        select(Servicio)
        .options(
            joinedload(Servicio.categoria),
            joinedload(Servicio.moneda)
        )
        .where(Servicio.id_perfil == perfil.id_perfil)
        # .where(Servicio.estado == True)  # QUITADO: Mostrar todos los servicios independientemente del estado
    )

    servicios = result.scalars().all()

    # Obtener tarifas por separado para evitar problemas de JOIN
    servicios_formateados = []
    for servicio in servicios:
        # Obtener tarifas del servicio por separado
        tarifas_result = await db.execute(
            select(TarifaServicio)
            .where(TarifaServicio.id_servicio == servicio.id_servicio)
        )
        tarifas_data = tarifas_result.scalars().all()

        # Formatear tarifas
        tarifas = []
        for tarifa in tarifas_data:
            tarifas.append({
                "id_tarifa_servicio": tarifa.id_tarifa_servicio,
                "monto": float(tarifa.monto),
                "descripcion": tarifa.descripcion,
                "fecha_inicio": tarifa.fecha_inicio.isoformat(),
                "fecha_fin": tarifa.fecha_fin.isoformat() if tarifa.fecha_fin else None,
                "id_tarifa": tarifa.id_tarifa,
                "nombre_tipo_tarifa": "Tipo de tarifa"  # Temporalmente simplificado
            })

        servicio_formateado = {
            "id_servicio": servicio.id_servicio,
            "nombre": servicio.nombre,
            "descripcion": servicio.descripcion,
            "precio": float(servicio.precio) if servicio.precio is not None else None,  # Manejar precios null
            "estado": servicio.estado,  # Ya es bool | None según el modelo
            "imagen": servicio.imagen,  # Ruta de la imagen representativa
            "id_categoria": servicio.id_categoria,
            "id_moneda": servicio.id_moneda,
            "nombre_categoria": servicio.categoria.nombre if servicio.categoria else None,
            "nombre_moneda": servicio.moneda.nombre if servicio.moneda else None,
            "simbolo_moneda": servicio.moneda.simbolo if servicio.moneda else None,
            "codigo_iso_moneda": servicio.moneda.codigo_iso_moneda if servicio.moneda else None,
            "created_at": servicio.created_at.isoformat() if servicio.created_at else None,
            "tarifas": tarifas
        }
        servicios_formateados.append(servicio_formateado)

    return servicios_formateados

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
            detail="Perfil de empresa no encontrado."
        )

    # Obtener el servicio específico
    result = await db.execute(
        select(Servicio)
        .options(
            joinedload(Servicio.categoria),
            joinedload(Servicio.moneda),
            joinedload(Servicio.tarifa_servicio).joinedload(TarifaServicio.tipo_tarifa_servicio)
        )
        .where(Servicio.id_servicio == service_id)
        .where(Servicio.id_perfil == perfil.id_perfil)
    )

    servicio = result.scalars().first()

    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no tienes permisos para verlo."
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
            "nombre_tipo_tarifa": tarifa.tipo_tarifa_servicio.nombre if tarifa.tipo_tarifa_servicio else "Sin tipo"
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
    perfil_result = await db.execute(
        select(PerfilEmpresa).where(PerfilEmpresa.user_id == current_user.id)
    )
    perfil = perfil_result.scalars().first()

    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de empresa no encontrado."
        )

    # Obtener el servicio específico
    result = await db.execute(
        select(Servicio)
        .where(Servicio.id_servicio == service_id)
        .where(Servicio.id_perfil == perfil.id_perfil)
    )

    servicio = result.scalars().first()

    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no tienes permisos para editarlo."
        )

    # Actualizar los campos del servicio
    if 'nombre' in service_data:
        servicio.nombre = service_data['nombre']
    if 'descripcion' in service_data:
        servicio.descripcion = service_data['descripcion']
    if 'precio' in service_data:
        servicio.precio = service_data['precio']
    if 'id_moneda' in service_data:
        servicio.id_moneda = service_data['id_moneda']
    if 'imagen' in service_data:
        servicio.imagen = service_data['imagen']  # Actualizar ruta de la imagen
    if 'estado' in service_data:
        servicio.estado = service_data['estado']

    # Gestionar tarifas si se incluyen
    if 'tarifas' in service_data:
        # Eliminar tarifas existentes
        await db.execute(
            TarifaServicio.__table__.delete().where(TarifaServicio.id_servicio == service_id)
        )

        # Agregar nuevas tarifas
        for tarifa_data in service_data['tarifas']:
            # Convertir fechas de string a objetos date con manejo robusto de errores
            from datetime import date

            try:
                fecha_inicio = None
                fecha_fin = None

                # Convertir fecha_inicio
                if tarifa_data.get('fecha_inicio'):
                    if isinstance(tarifa_data['fecha_inicio'], str):
                        fecha_inicio = date.fromisoformat(tarifa_data['fecha_inicio'])
                    else:
                        fecha_inicio = tarifa_data['fecha_inicio']

                # Convertir fecha_fin
                if tarifa_data.get('fecha_fin'):
                    if isinstance(tarifa_data['fecha_fin'], str):
                        fecha_fin = date.fromisoformat(tarifa_data['fecha_fin'])
                    else:
                        fecha_fin = tarifa_data['fecha_fin']

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
                    detail=f"Error en formato de fecha: {str(e)}"
                )

    await db.commit()

    return {"message": "Servicio actualizado exitosamente."}

@router.get("/options/monedas", response_model=List[dict])
async def get_monedas_options(db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todas las monedas disponibles para los servicios.
    """
    result = await db.execute(
        select(Moneda.id_moneda, Moneda.nombre, Moneda.simbolo, Moneda.codigo_iso_moneda)
    )

    monedas = result.fetchall()

    return [
        {
            "id_moneda": moneda[0],
            "nombre": moneda[1],
            "simbolo": moneda[2],
            "codigo_iso": moneda[3]
        }
        for moneda in monedas
    ]

@router.get("/options/tipos-tarifa", response_model=List[dict])
async def get_tipos_tarifa_options(db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene todos los tipos de tarifa disponibles.
    """
    try:
        # Verificar si la columna estado existe
        result = await db.execute(
            select(TipoTarifaServicio.id_tarifa, TipoTarifaServicio.nombre)
        )

        tipos_tarifa = result.fetchall()

        # Si no hay tipos de tarifa, insertar algunos por defecto
        if not tipos_tarifa:
            print("📝 Insertando tipos de tarifa por defecto...")

            # Insertar tipos de tarifa por defecto
            default_tipos = [
                {'nombre': 'Por hora', 'descripcion': 'Tarifa por hora de trabajo'},
                {'nombre': 'Por día', 'descripcion': 'Tarifa por día de trabajo'},
                {'nombre': 'Por proyecto', 'descripcion': 'Tarifa fija por proyecto'},
                {'nombre': 'Por semana', 'descripcion': 'Tarifa por semana de trabajo'},
                {'nombre': 'Por mes', 'descripcion': 'Tarifa por mes de trabajo'}
            ]

            for tipo in default_tipos:
                nueva_tarifa = TipoTarifaServicio(
                    nombre=tipo['nombre'],
                    descripcion=tipo['descripcion'],
                    estado=True
                )
                db.add(nueva_tarifa)

            await db.commit()

            # Volver a consultar después de insertar
            result = await db.execute(
                select(TipoTarifaServicio.id_tarifa, TipoTarifaServicio.nombre)
            )
            tipos_tarifa = result.fetchall()

        return [
            {
                "id_tarifa": tipo[0],
                "nombre": tipo[1]
            }
            for tipo in tipos_tarifa
        ]

    except Exception as e:
        print(f"❌ Error en get_tipos_tarifa_options: {e}")
        # Retornar tipos por defecto si hay error
        return [
            {"id_tarifa": 1, "nombre": "Por hora"},
            {"id_tarifa": 2, "nombre": "Por día"},
            {"id_tarifa": 3, "nombre": "Por proyecto"}
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
            detail="Perfil de empresa no encontrado."
        )

    # Verificar que el servicio existe y pertenece al usuario
    service_result = await db.execute(
        select(Servicio)
        .where(Servicio.id_servicio == service_id)
        .where(Servicio.id_perfil == perfil.id_perfil)
    )

    servicio = service_result.scalars().first()

    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no tienes permisos para editarlo."
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

    return {"message": "Tarifa agregada exitosamente."}

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
            detail="Perfil de empresa no encontrado."
        )

    # Verificar que el servicio existe y pertenece al usuario
    service_result = await db.execute(
        select(Servicio)
        .where(Servicio.id_servicio == service_id)
        .where(Servicio.id_perfil == perfil.id_perfil)
    )

    servicio = service_result.scalars().first()

    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no tienes permisos para editarlo."
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
            detail="Tarifa no encontrada."
        )

    await db.commit()

    return {"message": "Tarifa eliminada exitosamente."}

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
    Sube una imagen para un servicio (PNG/JPG, máximo 5MB).
    """
    # Validar tipo de archivo
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PNG y JPG."
        )

    # Validar tamaño del archivo (5MB máximo)
    file_size = 0
    content = await file.read()
    file_size = len(content)

    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no puede superar los 5MB."
        )

    # Generar nombre único para el archivo
    import uuid
    file_extension = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    # Guardar archivo
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        logger.error(f"Error al guardar imagen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al guardar la imagen."
        )

    # Retornar la ruta relativa del archivo
    return {
        "message": "Imagen subida exitosamente.",
        "image_path": f"/{UPLOAD_DIRECTORY}/{unique_filename}"
    }

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
                detail="Perfil de empresa no encontrado"
            )

        # Verificar que el servicio pertenece al proveedor
        servicio_query = select(Servicio).where(
            Servicio.id_servicio == service_id,
            Servicio.id_perfil == perfil.id_perfil
        )
        servicio_result = await db.execute(servicio_query)
        servicio = servicio_result.scalar_one_or_none()
        
        if not servicio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servicio no encontrado o no tienes permisos para modificarlo"
            )

        # Actualizar el estado del servicio
        servicio.estado = status_data.estado
        await db.commit()
        await db.refresh(servicio)

        return {
            "message": f"Servicio {'activado' if status_data.estado else 'desactivado'} exitosamente",
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
            detail="Error interno del servidor al actualizar el estado del servicio"
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
                detail="Perfil de empresa no encontrado"
            )

        # Obtener la plantilla del servicio
        template_query = select(Servicio).where(Servicio.id_servicio == service_data.template_id)
        template_result = await db.execute(template_query)
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plantilla de servicio no encontrada"
            )

        # Crear nuevo servicio basado en la plantilla
        nuevo_servicio = Servicio(
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
            "message": "Servicio creado exitosamente desde plantilla",
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
            detail="Error interno del servidor al crear el servicio desde plantilla"
        )
