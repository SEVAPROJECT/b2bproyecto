# app/api/v1/routers/services.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, case, func, String, Integer, Numeric, Boolean, DateTime
from typing import List
from pydantic import BaseModel

from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.models.servicio.service import ServicioModel
from app.models.publicar_servicio.category import CategoriaModel
from app.models.publicar_servicio.tarifa_servicio import TarifaServicio
from app.models.publicar_servicio.tipo_tarifa_servicio import TipoTarifaServicio
from app.models.perfil import UserModel
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.direccion import Direccion
from app.models.empresa.barrio import Barrio
from app.models.empresa.ciudad import Ciudad
from app.models.empresa.departamento import Departamento
from app.models.publicar_servicio.moneda import Moneda
from app.schemas.servicio.service import ServicioOut, ServicioIn, ServicioWithProvider


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
        select(ServicioModel).where(ServicioModel.estado == True)
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
        select(ServicioModelModel).where(ServicioModelModel.estado == True)
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
        select(ServicioModel).where(
            ServicioModel.estado == True,
            ServicioModel.id_categoria == category_id
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
        select(ServicioModel).where(
            ServicioModel.id_categoria == category_id
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
        query = select(ServicioModel).where(ServicioModel.estado == True)
        result = await db.execute(query)
        services = result.scalars().all()
        return {
            "status": "success", 
            "message": f"Conexión exitosa. ServicioModels activos: {len(services)}"
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
        # Usar consulta SQL directa que sabemos que funciona
        from sqlalchemy import text
        query = text("""
            SELECT 
                s.id_servicio,
                s.id_categoria,
                s.id_perfil,
                s.id_moneda,
                s.nombre,
                s.descripcion,
                s.precio,
                s.imagen,
                s.estado,
                s.created_at,
                pe.razon_social,
                u.nombre_persona as nombre_contacto,
                d.nombre as departamento,
                c.nombre as ciudad,
                b.nombre as barrio,
                m.codigo_iso_moneda,
                m.nombre as nombre_moneda,
                m.simbolo as simbolo_moneda
            FROM servicio s
            JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            JOIN users u ON pe.user_id = u.id
            LEFT JOIN direccion dir ON pe.id_direccion = dir.id_direccion
            LEFT JOIN departamento d ON dir.id_departamento = d.id_departamento
            LEFT JOIN ciudad c ON dir.id_ciudad = c.id_ciudad
            LEFT JOIN barrio b ON dir.id_barrio = b.id_barrio
            LEFT JOIN moneda m ON s.id_moneda = m.id_moneda
            WHERE s.estado = true
            AND pe.verificado = true
            ORDER BY s.created_at DESC
        """)
        
        result = await db.execute(query)
        services_data = result.fetchall()
        
        print(f"🔍 Backend - Raw query results: {len(services_data)} rows")
        if services_data:
            first_row = services_data[0]
            print(f"🔍 Backend - First row: {first_row}")
            print(f"🔍 Backend - Barrio value: '{first_row[14]}', type: {type(first_row[14])}")
            print(f"🔍 Backend - Imagen del primer servicio: '{first_row[7]}'")
            
            # Verificar todas las imágenes
            for i, row in enumerate(services_data[:5]):  # Solo los primeros 5
                print(f"🔍 Backend - Servicio {i+1} imagen: '{row[7]}'")
        
        # Convertir los resultados a diccionarios para que funcionen correctamente
        services_list = []
        for row in services_data:
            # Procesar la imagen para que funcione correctamente
            imagen_original = row[7]
            imagen_procesada = imagen_original
            
            # Solo procesar servicios con imágenes de iDrive
            if imagen_original and imagen_original.startswith('http'):
                print(f"✅ Imagen iDrive mantenida: {imagen_original}")
                imagen_procesada = imagen_original
            else:
                # Filtrar servicios sin imagen o con rutas locales
                if imagen_original:
                    print(f"🚫 Imagen local filtrada: {imagen_original}")
                else:
                    print(f"🚫 Servicio sin imagen filtrado")
                continue  # Saltar este servicio completamente
            
            service_dict = {
                'id_servicio': row[0],
                'id_categoria': row[1],
                'id_perfil': row[2],
                'id_moneda': row[3],
                'nombre': row[4],
                'descripcion': row[5],
                'precio': row[6],
                'imagen': imagen_procesada,  # Usar imagen procesada
                'estado': row[8],
                'created_at': row[9],
                'razon_social': row[10],
                'nombre_contacto': row[11],
                'departamento': row[12],
                'ciudad': row[13],
                'barrio': row[14],
                'codigo_iso_moneda': row[15],
                'nombre_moneda': row[16],
                'simbolo_moneda': row[17]
            }
            services_list.append(service_dict)
        
        services_data = services_list

        # Debug: verificar datos de barrio
        print(f"🔍 Backend - Total servicios: {len(services_data)}")
        if services_data:
            first_service = services_data[0]
            print(f"🔍 Backend - Primer servicio: departamento={first_service['departamento']}, ciudad={first_service['ciudad']}, barrio={first_service['barrio']}")
            print(f"🔍 Backend - Barrio type: {type(first_service['barrio'])}")
            
            # Verificar Limpio SA específicamente
            limpo_services = [s for s in services_data if s['razon_social'] == 'Limpio SA']
            if limpo_services:
                limpo = limpo_services[0]
                print(f"🔍 Backend - Limpio SA: barrio={limpo['barrio']}, type={type(limpo['barrio'])}")
            else:
                print("🔍 Backend - Limpio SA no encontrado")

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
                .where(TarifaServicio.id_servicio == row['id_servicio'])
            )
            tarifas_data = tarifas_result.fetchall()

            # Formatear tarifas
            tarifas = []
            for tarifa_row in tarifas_data:
                tarifa = tarifa_row[0]  # TarifaServicioModel
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
                'id_servicio': row['id_servicio'],
                'id_categoria': row['id_categoria'],
                'id_perfil': row['id_perfil'],
                'id_moneda': row['id_moneda'],
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'precio': row['precio'],
                'imagen': row['imagen'],
                'estado': row['estado'],
                'created_at': row['created_at'],
                'razon_social': row['razon_social'],
                'nombre_contacto': row['nombre_contacto'],
                'ciudad': row['ciudad'],  # Ciudad de la empresa
                'departamento': row['departamento'],  # Departamento de la empresa
                'barrio': row['barrio'],  # Barrio de la empresa (opcional)
                'codigo_iso_moneda': row['codigo_iso_moneda'],  # Código ISO de la moneda
                'nombre_moneda': row['nombre_moneda'],  # Nombre de la moneda
                'simbolo_moneda': row['simbolo_moneda'],  # Símbolo de la moneda
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
    "/debug-images",
    status_code=status.HTTP_200_OK,
    description="Endpoint de debug para verificar las imágenes en la base de datos."
)
async def debug_images(db: AsyncSession = Depends(get_async_db)):
    """
    Endpoint de debug para verificar las imágenes en la base de datos.
    """
    try:
        from sqlalchemy import text
        query = text("""
            SELECT 
                s.id_servicio,
                s.nombre,
                s.imagen
            FROM servicio s
            WHERE s.imagen IS NOT NULL
            ORDER BY s.created_at DESC
            LIMIT 10
        """)
        
        result = await db.execute(query)
        images_data = result.fetchall()
        
        debug_info = []
        for row in images_data:
            debug_info.append({
                'id_servicio': row[0],
                'nombre': row[1],
                'imagen': row[2],
                'es_url_completa': row[2].startswith('http') if row[2] else False,
                'es_ruta_local': row[2].startswith('/uploads/') if row[2] else False
            })
        
        return {
            'total_servicios_con_imagen': len(images_data),
            'imagenes': debug_info
        }
        
    except Exception as e:
        print(f"❌ Error en debug_images: {str(e)}")
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
        select(ServicioModel).where(
            ServicioModel.estado == True,
            ServicioModel.id_categoria == category_id
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
            select(CategoriaModel).where(CategoriaModel.id_categoria == service_in.id_categoria)
        )
        category = category_result.scalars().first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada."
            )

        nuevo_servicio = ServicioModel(
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
            select(ServicioModel).where(ServicioModel.id_servicio == service_id)
        )
        service = service_result.scalars().first()

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ServicioModel no encontrado."
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
class ServicioModelStatusUpdate(BaseModel):
    estado: bool

@router.patch(
    "/{service_id}/status",
    status_code=status.HTTP_200_OK,
    description="Actualiza el estado (activo/inactivo) de un servicio."
)
async def update_service_status(
    service_id: int,
    status_data: ServicioModelStatusUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza el estado (activo/inactivo) de un servicio.
    """
    try:
        # Verificar que el servicio existe
        service_result = await db.execute(
            select(ServicioModel).where(ServicioModel.id_servicio == service_id)
        )
        service = service_result.scalars().first()

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ServicioModel no encontrado."
            )

        # Actualizar el estado del servicio
        service.estado = status_data.estado
        await db.commit()
        await db.refresh(service)

        return {
            "message": f"ServicioModel {'activado' if status_data.estado else 'desactivado'} exitosamente",
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

@router.get("/servir-imagen/{servicio_id}")
async def servir_imagen(servicio_id: int, db: AsyncSession = Depends(get_async_db)):
    """Endpoint para servir imágenes de servicios descargándolas de iDrive"""
    try:
        print(f"🔍 Sirviendo imagen para servicio {servicio_id}")
        
        # Obtener la imagen del servicio
        from sqlalchemy import text
        query = text("""
            SELECT id_servicio, nombre, imagen 
            FROM servicio 
            WHERE id_servicio = :servicio_id
        """)
        
        result = await db.execute(query, {"servicio_id": servicio_id})
        row = result.fetchone()
        
        if not row:
            print(f"❌ Servicio {servicio_id} no encontrado")
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        imagen = row[2]
        print(f"🔍 Imagen encontrada: {imagen}")
        
        if not imagen or not imagen.startswith('http'):
            print(f"❌ Servicio {servicio_id} sin imagen de iDrive")
            raise HTTPException(status_code=404, detail="Servicio sin imagen de iDrive")
        
        print(f"✅ Descargando imagen de iDrive: {imagen}")
        
        # Descargar la imagen de iDrive con headers de autenticación
        import httpx
        import asyncio
        
        try:
            # Headers para simular un navegador y evitar bloqueos
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                verify=False  # Deshabilitar verificación SSL para evitar problemas de certificado
            ) as client:
                response = await client.get(imagen, headers=headers)
                
                if response.status_code == 200:
                    print(f"✅ Imagen descargada exitosamente de iDrive")
                    from fastapi.responses import Response
                    
                    # Determinar el tipo de contenido
                    content_type = response.headers.get("content-type", "image/jpeg")
                    if "image" not in content_type:
                        content_type = "image/jpeg"
                    
                    return Response(
                        content=response.content,
                        media_type=content_type,
                        headers={
                            "Cache-Control": "public, max-age=3600",
                            "Content-Disposition": f"inline; filename=service_{servicio_id}.jpg"
                        }
                    )
                else:
                    print(f"❌ Error descargando imagen de iDrive: {response.status_code}")
                    # Si falla, devolver un placeholder
                    return Response(
                        content=b"",  # Imagen vacía
                        media_type="image/jpeg",
                        status_code=404
                    )
                    
        except Exception as e:
            print(f"❌ Error descargando imagen: {e}")
            # Si falla, devolver un placeholder
            return Response(
                content=b"",  # Imagen vacía
                media_type="image/jpeg",
                status_code=404
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sirviendo imagen: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")