# app/api/v1/routers/services.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from pydantic import BaseModel

from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.publicar_servicio.publish_service import Servicio
from app.models.publicar_servicio.category import Categoria
from app.models.publicar_servicio.tarifa_servicio import TarifaServicio
from app.models.publicar_servicio.tipo_tarifa_servicio import TipoTarifaServicio
from app.models.perfil import UserModel
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.direccion import Direccion
from app.models.empresa.barrio import Barrio
from app.models.empresa.ciudad import Ciudad
from app.models.empresa.departamento import Departamento
from app.models.publicar_servicio.moneda import Moneda
from app.schemas.publicar_servicio.publish_service import ServicioOut, ServicioIn, ServicioWithProvider


# Asegúrate de que los routers se importen en main.py
router = APIRouter(prefix="/services", tags=["services"])


@router.get(
    "/list",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de todos los servicios activos disponibles en la plataforma."
)
async def get_all_services_list(db: AsyncSession = Depends(get_async_db)):
    """
    Este endpoint devuelve una lista de todos los servicios activos.
    """
    result = await db.execute(
        select(Servicio).where(Servicio.estado)
    )
    
    services = result.scalars().all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron servicios activos."
        )
    return list(services)


@router.get(
    "/templates",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de todos los servicios activos para usar como plantillas."
)
async def get_service_templates(db: AsyncSession = Depends(get_async_db)):
    """
    Este endpoint devuelve una lista de todos los servicios activos que pueden ser usados como plantillas.
    """
    result = await db.execute(
        select(Servicio).where(Servicio.estado == True)
    )
    
    services = result.scalars().all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron servicios disponibles como plantillas."
        )
    return list(services)


@router.get(
    "/templates/category/{category_id}",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de servicios activos de una categoría específica para usar como plantillas."
)
async def get_service_templates_by_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Este endpoint devuelve una lista de servicios activos de una categoría específica que pueden ser usados como plantillas.
    """
    result = await db.execute(
        select(Servicio).where(
            Servicio.estado == True,
            Servicio.id_categoria == category_id
        )
    )
    
    services = result.scalars().all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron servicios disponibles en esta categoría como plantillas."
        )
    return list(services)


@router.get(
    "/all/category/{category_id}",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de TODOS los servicios (activos e inactivos) de una categoría específica."
)
async def get_all_services_by_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Este endpoint devuelve una lista de TODOS los servicios (activos e inactivos) de una categoría específica.
    Permite a los proveedores ver todos los servicios disponibles antes de decidir si reutilizar o solicitar uno nuevo.
    """
    result = await db.execute(
        select(Servicio).where(
            Servicio.id_categoria == category_id
        )
    )
    
    services = result.scalars().all()

    # Devolver lista vacía en lugar de error 404
    return list(services)


@router.get(
    "/test-connection",
    status_code=status.HTTP_200_OK,
    description="Endpoint de prueba para verificar conexión a base de datos."
)
async def test_connection(db: AsyncSession = Depends(get_async_db)):
    """
    Endpoint simple para verificar que la conexión a la base de datos funciona.
    """
    try:
        # Query simple para contar servicios
        query = select(Servicio).where(Servicio.estado == True)
        result = await db.execute(query)
        services = result.scalars().all()
        return {
            "status": "success", 
            "message": f"Conexión exitosa. Servicios activos: {len(services)}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Error de conexión: {str(e)}"
        }

@router.get(
    "/with-providers",
    response_model=List[ServicioWithProvider],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de todos los servicios activos con información del proveedor."
)
async def get_services_with_providers(db: AsyncSession = Depends(get_async_db)):
    """
    Este endpoint devuelve una lista de todos los servicios activos con información del proveedor.
    """
    try:
        # Query con JOIN para obtener información del proveedor incluyendo ciudad, departamento y moneda
        query = select(
            Servicio.id_servicio,
            Servicio.id_categoria,
            Servicio.id_perfil,
            Servicio.id_moneda,
            Servicio.nombre,
            Servicio.descripcion,
            Servicio.precio,
            Servicio.imagen,
            Servicio.estado,
            Servicio.created_at,
            PerfilEmpresa.razon_social,
            UserModel.nombre_persona.label('nombre_contacto'),
            Ciudad.nombre.label('ciudad'),  # Ciudad de la empresa
            Departamento.nombre.label('departamento'),  # Departamento de la empresa
            Moneda.codigo_iso_moneda,  # Código ISO de la moneda
            Moneda.nombre.label('nombre_moneda'),  # Nombre de la moneda
            Moneda.simbolo.label('simbolo_moneda')  # Símbolo de la moneda
        ).join(
            PerfilEmpresa, Servicio.id_perfil == PerfilEmpresa.id_perfil
        ).join(
            UserModel, PerfilEmpresa.user_id == UserModel.id
        ).outerjoin(  # Usar outerjoin para casos donde no hay dirección
            Direccion, PerfilEmpresa.id_direccion == Direccion.id_direccion
        ).outerjoin(  # Usar outerjoin para casos donde no hay barrio
            Barrio, Direccion.id_barrio == Barrio.id_barrio
        ).outerjoin(  # Usar outerjoin para casos donde no hay ciudad
            Ciudad, Barrio.id_ciudad == Ciudad.id_ciudad
        ).outerjoin(  # Usar outerjoin para casos donde no hay departamento
            Departamento, Ciudad.id_departamento == Departamento.id_departamento
        ).outerjoin(  # Usar outerjoin para casos donde no hay moneda
            Moneda, Servicio.id_moneda == Moneda.id_moneda
        ).where(Servicio.estado == True)
        
        result = await db.execute(query)
        services_data = result.fetchall()

        if not services_data:
            # En lugar de lanzar una excepción, devolvemos una lista vacía
            return []
        
        # Convertir los resultados a la estructura del schema
        services = []
        for row in services_data:
            # Obtener tarifas del servicio con JOIN al tipo de tarifa
            tarifas_result = await db.execute(
                select(TarifaServicio, TipoTarifaServicio.nombre.label('nombre_tipo_tarifa'))
                .outerjoin(TipoTarifaServicio, TarifaServicio.id_tarifa == TipoTarifaServicio.id_tarifa)
                .where(TarifaServicio.id_servicio == row.id_servicio)
            )
            tarifas_data = tarifas_result.fetchall()

            # Formatear tarifas
            tarifas = []
            for tarifa_row in tarifas_data:
                tarifa = tarifa_row[0]  # TarifaServicio
                nombre_tipo_tarifa = tarifa_row[1]  # nombre_tipo_tarifa
                tarifas.append({
                    "id_tarifa_servicio": tarifa.id_tarifa_servicio,
                    "monto": float(tarifa.monto),
                    "descripcion": tarifa.descripcion,
                    "fecha_inicio": tarifa.fecha_inicio.isoformat(),
                    "fecha_fin": tarifa.fecha_fin.isoformat() if tarifa.fecha_fin else None,
                    "id_tarifa": tarifa.id_tarifa,
                    "nombre_tipo_tarifa": nombre_tipo_tarifa or "Sin especificar"
                })

            service_dict = {
                'id_servicio': row.id_servicio,
                'id_categoria': row.id_categoria,
                'id_perfil': row.id_perfil,
                'id_moneda': row.id_moneda,
                'nombre': row.nombre,
                'descripcion': row.descripcion,
                'precio': row.precio,
                'imagen': row.imagen,
                'estado': row.estado,
                'created_at': row.created_at,
                'razon_social': row.razon_social,
                'nombre_contacto': row.nombre_contacto,
                'ciudad': row.ciudad,  # Ciudad de la empresa
                'departamento': row.departamento,  # Departamento de la empresa
                'codigo_iso_moneda': row.codigo_iso_moneda,  # Código ISO de la moneda
                'nombre_moneda': row.nombre_moneda,  # Nombre de la moneda
                'simbolo_moneda': row.simbolo_moneda,  # Símbolo de la moneda
                'tarifas': tarifas  # Agregar tarifas
            }
            services.append(ServicioWithProvider(**service_dict))
        
        return services
        
    except Exception as e:
        print(f"❌ Error en get_services_with_providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/category/{category_id}",
    response_model=List[ServicioOut],
    status_code=status.HTTP_200_OK,
    description="Obtiene el listado de servicios activos de una categoría específica."
)
async def get_services_by_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene todos los servicios activos de una categoría específica.
    """
    result = await db.execute(
        select(Servicio).where(
            Servicio.estado == True,
            Servicio.id_categoria == category_id
        )
    )

    services = result.scalars().all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron servicios activos en la categoría {category_id}."
        )
    return list(services)


@router.post(
    "/",
    response_model=ServicioOut,
    status_code=status.HTTP_201_CREATED,
    description="Crea un nuevo servicio."
)
async def create_service(
    service_in: ServicioIn,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea un nuevo servicio.
    """
    try:
        # Verificar que la categoría existe
        category_result = await db.execute(
            select(Categoria).where(Categoria.id_categoria == service_in.id_categoria)
        )
        category = category_result.scalars().first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada."
            )

        nuevo_servicio = Servicio(
            nombre=service_in.nombre,
            descripcion=service_in.descripcion,
            precio=service_in.precio,
            id_categoria=service_in.id_categoria,
            id_moneda=service_in.id_moneda,
            estado=True
        )
        db.add(nuevo_servicio)
        await db.commit()
        await db.refresh(nuevo_servicio)

        return nuevo_servicio
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el servicio: {str(e)}"
        )


@router.put(
    "/{service_id}",
    response_model=ServicioOut,
    status_code=status.HTTP_200_OK,
    description="Actualiza un servicio existente."
)
async def update_service(
    service_id: int,
    service_data: dict,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza un servicio existente.
    """
    try:
        # Verificar que el servicio existe
        service_result = await db.execute(
            select(Servicio).where(Servicio.id_servicio == service_id)
        )
        service = service_result.scalars().first()

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servicio no encontrado."
            )

        # Actualizar campos del servicio
        if "nombre" in service_data:
            service.nombre = service_data["nombre"]
        if "descripcion" in service_data:
            service.descripcion = service_data["descripcion"]
        if "precio" in service_data:
            service.precio = service_data["precio"]
        if "estado" in service_data:
            service.estado = service_data["estado"]
        if "imagen" in service_data:
            service.imagen = service_data["imagen"]

        await db.commit()
        await db.refresh(service)

        return service
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el servicio: {str(e)}"
        )


# Modelo para actualizar estado del servicio
class ServicioStatusUpdate(BaseModel):
    estado: bool

@router.patch(
    "/{service_id}/status",
    status_code=status.HTTP_200_OK,
    description="Actualiza el estado (activo/inactivo) de un servicio."
)
async def update_service_status(
    service_id: int,
    status_data: ServicioStatusUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza el estado (activo/inactivo) de un servicio.
    """
    try:
        # Verificar que el servicio existe
        service_result = await db.execute(
            select(Servicio).where(Servicio.id_servicio == service_id)
        )
        service = service_result.scalars().first()

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servicio no encontrado."
            )

        # Actualizar el estado del servicio
        service.estado = status_data.estado
        await db.commit()
        await db.refresh(service)

        return {
            "message": f"Servicio {'activado' if status_data.estado else 'desactivado'} exitosamente",
            "servicio": {
                "id_servicio": service.id_servicio,
                "nombre": service.nombre,
                "estado": service.estado
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el estado del servicio: {str(e)}"
        )