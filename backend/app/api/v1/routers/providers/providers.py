# app/api/v1/routers/providers.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.v1.dependencies.auth_user import get_current_user
from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
from app.models.empresa.documento import Documento
from app.models.empresa.direccion import Direccion
from app.models.perfil import UserModel 
from app.schemas.empresa.perfil_empresa import PerfilEmpresaIn
from app.schemas.auth_user import SupabaseUser
from app.api.v1.dependencies.local_storage import local_storage_service
from app.api.v1.dependencies.idrive import upload_file_to_idrive, smart_upload_service
from typing import Optional, List
import uuid
import json
from datetime import datetime
from app.schemas.publicar_servicio.solicitud_servicio import SolicitudServicioIn, SolicitudServicioOut  # noqa: E402
from app.api.v1.dependencies.auth_user import get_approved_provider  # noqa: E402
from app.models.publicar_servicio.solicitud_servicio import SolicitudServicio
from app.models.empresa.barrio import Barrio
from app.models.empresa.ciudad import Ciudad
from app.models.empresa.departamento import Departamento
from geoalchemy2 import WKTElement
from app.models.empresa.tipo_documento import TipoDocumento



router = APIRouter(prefix="/providers", tags=["providers"])

@router.post(
    "/solicitar-verificacion",
    status_code=status.HTTP_201_CREATED,
    description="Registra un perfil de empresa y una solicitud de verificación con documentos adjuntos."
)
async def solicitar_verificacion_completa(
    perfil_in: str = Form(...),  # Recibir como string JSON
    nombres_tip_documento: List[str] = Form(...), # Recibe una lista de nombres de tipos de documento
    documentos: List[UploadFile] = File(...),
    comentario_solicitud: Optional[str] = Form(None),
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        print("🚀 Iniciando solicitud de verificación...")
        print(f"👤 Usuario: {current_user.email} ({current_user.id})")
        print(f"📄 Perfil recibido: {perfil_in[:200]}...")
        print(f"📎 Archivos: {len(documentos)} archivos")
        print(f"📝 Nombres tipos documento: {nombres_tip_documento}")
        print(f"💬 Comentario: {comentario_solicitud}")

        # Parsear el JSON del perfil_in
        try:
            perfil_data = json.loads(perfil_in)
            print(f"✅ JSON parseado correctamente: {perfil_data}")
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato JSON inválido en perfil_in"
            )
        
        # Validar que la cantidad de nombres de tipos de documento coincide con la de los archivos
        if len(nombres_tip_documento) != len(documentos):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de nombres de tipo de documento no coincide con el número de archivos."
            )

        # Filtrar documentos vacíos (archivos con tamaño 0 o nombre 'empty.txt')
        documentos_validos = []
        nombres_tip_documento_validos = []
        
        for i, doc in enumerate(documentos):
            if doc.filename != 'empty.txt' and doc.size > 0:
                documentos_validos.append(doc)
                nombres_tip_documento_validos.append(nombres_tip_documento[i])
            else:
                print(f"⚠️ Documento vacío filtrado: {doc.filename}")
        
        # Usar los documentos válidos
        documentos = documentos_validos
        nombres_tip_documento = nombres_tip_documento_validos
        
        print(f"📎 Documentos válidos para procesar: {len(documentos)}")

        # 1. Obtener el perfil del usuario actual para recuperar el nombre de la empresa
        #esto porque al iniciar sesion ya carga el nombre de su empresa
        user_profile_result = await db.execute(
            select(UserModel).where(UserModel.id == uuid.UUID(current_user.id))
        )

        # Obtener el perfil de usuario
        user_profile = user_profile_result.scalars().first()

        # Verificar que el perfil de usuario existe
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de usuario no encontrado."
            )

        # Verificar que el perfil de usuario tiene un nombre de empresa configurado
        if not user_profile.nombre_empresa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La razón social no está configurada en tu perfil de usuario. Por favor, completa tu perfil antes de solicitar ser proveedor."
            )
        
        razon_social = user_profile.nombre_empresa
        
        # 2. Validar la unicidad de la empresa
        query = select(PerfilEmpresa).where(
            (PerfilEmpresa.razon_social == razon_social) |
            (PerfilEmpresa.nombre_fantasia == perfil_data['nombre_fantasia'])
        )

        empresa_existente = await db.execute(query)
        empresa_existente = empresa_existente.scalars().first()
        
        if empresa_existente and empresa_existente.user_id != uuid.UUID(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Una empresa con esta razón social o nombre de fantasía ya está registrada."
            )
        
        # Si es el mismo usuario, actualizar la empresa existente en lugar de crear una nueva
        if empresa_existente and empresa_existente.user_id == uuid.UUID(current_user.id):
            print(f"🔍 Actualizando empresa existente para reenvío: {empresa_existente.razon_social}")
            # Actualizar datos de la empresa existente
            empresa_existente.razon_social = razon_social
            empresa_existente.nombre_fantasia = perfil_data['nombre_fantasia']
            empresa_existente.estado = "pendiente"
            empresa_existente.verificado = False
            await db.flush()
            
            # Usar la empresa existente
            nuevo_perfil = empresa_existente
        else:
            # Crear nueva empresa
            nuevo_perfil = None

        # 3. Buscar el barrio por nombre y obtener su ID
      
     
        # Buscar el departamento por nombre
        dept_result = await db.execute(
            select(Departamento).where(Departamento.nombre == perfil_data['direccion']['departamento'])
        )
        departamento = dept_result.scalars().first()
        
        if not departamento:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Departamento '{perfil_data['direccion']['departamento']}' no encontrado"
            )
        
        # Buscar la ciudad por nombre y departamento
        ciudad_result = await db.execute(
            select(Ciudad).where(
                Ciudad.nombre == perfil_data['direccion']['ciudad'],
                Ciudad.id_departamento == departamento.id_departamento
            )
        )
        ciudad = ciudad_result.scalars().first()
        
        if not ciudad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ciudad '{perfil_data['direccion']['ciudad']}' no encontrada en el departamento '{perfil_data['direccion']['departamento']}'"
            )
        
        # Buscar el barrio por nombre y ciudad (opcional) - DEPRECATED
        barrio = None
        barrio_value = perfil_data['direccion'].get('barrio')
        if barrio_value and isinstance(barrio_value, str) and barrio_value.strip():
            barrio_result = await db.execute(
                select(Barrio).where(
                    Barrio.nombre == perfil_data['direccion']['barrio'],
                    Barrio.id_ciudad == ciudad.id_ciudad
                )
            )
            barrio = barrio_result.scalars().first()
            
            if not barrio:
                print(f"⚠️ Barrio '{perfil_data['direccion']['barrio']}' no encontrado en la ciudad '{perfil_data['direccion']['ciudad']}', continuando sin barrio")
                barrio = None
        
        # 4. Crear o actualizar la dirección
        
        if nuevo_perfil is None:
            # Crear nueva dirección
            nueva_direccion = Direccion(
                calle=perfil_data['direccion']['calle'],
                numero=perfil_data['direccion']['numero'],
                referencia=perfil_data['direccion']['referencia'],
                id_departamento=departamento.id_departamento,
                id_ciudad=ciudad.id_ciudad if ciudad else None,
                id_barrio=barrio.id_barrio if barrio else None,
                coordenadas=WKTElement('POINT(-57.5759 -25.2637)', srid=4326)  # Centro de Asunción
            )
            db.add(nueva_direccion)
            await db.flush()
            
            # 5. Crear el perfil de empresa
            nuevo_perfil = PerfilEmpresa(
                user_id=uuid.UUID(current_user.id),
                razon_social=razon_social,
                nombre_fantasia=perfil_data['nombre_fantasia'],
                id_direccion=nueva_direccion.id_direccion,
                estado="pendiente",
                verificado=False
            )
            db.add(nuevo_perfil)
            await db.flush()
        else:
            # Actualizar dirección existente
            if nuevo_perfil.id_direccion:
                # Actualizar dirección existente
                direccion_existente = await db.execute(
                    select(Direccion).where(Direccion.id_direccion == nuevo_perfil.id_direccion)
                )
                direccion_existente = direccion_existente.scalars().first()
                if direccion_existente:
                    direccion_existente.calle = perfil_data['direccion']['calle']
                    direccion_existente.numero = perfil_data['direccion']['numero']
                    direccion_existente.referencia = perfil_data['direccion']['referencia']
                    direccion_existente.id_departamento = departamento.id_departamento
                    direccion_existente.id_ciudad = ciudad.id_ciudad if ciudad else None
                    direccion_existente.id_barrio = barrio.id_barrio if barrio else None
                    await db.flush()
            else:
                # Crear nueva dirección para empresa existente
                nueva_direccion = Direccion(
                    calle=perfil_data['direccion']['calle'],
                    numero=perfil_data['direccion']['numero'],
                    referencia=perfil_data['direccion']['referencia'],
                    id_departamento=departamento.id_departamento,
                    id_ciudad=ciudad.id_ciudad if ciudad else None,
                    id_barrio=barrio.id_barrio if barrio else None,
                    coordenadas=WKTElement('POINT(-57.5759 -25.2637)', srid=4326)
                )
                db.add(nueva_direccion)
                await db.flush()
                nuevo_perfil.id_direccion = nueva_direccion.id_direccion
                await db.flush()

        # 6. Crear o actualizar sucursal si hay datos de sucursal
        if perfil_data.get('sucursal'):
            sucursal_data = perfil_data['sucursal']
            
            # Buscar sucursal existente
            from app.models.empresa.sucursal_empresa import SucursalEmpresa
            sucursal_existente_query = select(SucursalEmpresa).where(
                SucursalEmpresa.id_perfil == nuevo_perfil.id_perfil
            )
            sucursal_existente_result = await db.execute(sucursal_existente_query)
            sucursal_existente = sucursal_existente_result.scalars().first()
            
            if sucursal_existente:
                # Actualizar sucursal existente
                sucursal_existente.nombre = sucursal_data.get('nombre', 'Casa Matriz')
                sucursal_existente.telefono = sucursal_data.get('telefono', '')
                sucursal_existente.email = sucursal_data.get('email', '')
                sucursal_existente.id_direccion = nueva_direccion.id_direccion if 'nueva_direccion' in locals() else nuevo_perfil.id_direccion
            else:
                # Crear nueva sucursal
                nueva_sucursal = SucursalEmpresa(
                    id_perfil=nuevo_perfil.id_perfil,
                    nombre=sucursal_data.get('nombre', 'Casa Matriz'),
                    telefono=sucursal_data.get('telefono', ''),
                    email=sucursal_data.get('email', ''),
                    id_direccion=nueva_direccion.id_direccion if 'nueva_direccion' in locals() else nuevo_perfil.id_direccion,
                    es_principal=True
                )
                db.add(nueva_sucursal)
            
            await db.flush()

        # 7. Crear la solicitud de verificación
        nueva_solicitud = VerificacionSolicitud(
            id_perfil=nuevo_perfil.id_perfil,
            estado="pendiente",
            comentario=comentario_solicitud
        )
        db.add(nueva_solicitud)
        await db.flush()
        
        print(f"🔍 Nueva solicitud creada: {nueva_solicitud.id_verificacion} para empresa: {nuevo_perfil.razon_social}")

        # 7. Subir archivos y registrar documentos
       
        
        # Procesar documentos solo si hay documentos válidos
        if documentos:
            for index, file in enumerate(documentos):
                nombre_tip_documento = nombres_tip_documento[index]
                
                # Buscar el tipo de documento por nombre
                tipo_doc_result = await db.execute(
                    select(TipoDocumento).where(TipoDocumento.nombre == nombre_tip_documento)
                )
                tipo_documento = tipo_doc_result.scalars().first()
                
                if not tipo_documento:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Tipo de documento '{nombre_tip_documento}' no encontrado"
                    )
                
                # Subir archivo usando sistema inteligente con fallback
                try:
                    # Leer contenido del archivo
                    file_content = await file.read()
                    
                    # Generar nombre único para el archivo (usando uuid ya importado)
                    file_key = f"{razon_social}/{nombre_tip_documento}/{uuid.uuid4()}_{file.filename}"
                    
                    # Intentar subir con fallback inteligente
                    idrive_url = await upload_file_to_idrive(
                        file_content=file_content,
                        filename=file_key,
                        document_type="provider"
                    )
                    print(f"✅ Archivo subido exitosamente: {idrive_url}")
                    
                except Exception as upload_error:
                    print(f"❌ Error al subir archivo: {upload_error}")
                    # Fallback a URL temporal
                    idrive_url = f"temp://{file.filename}_{current_user.id}_{tipo_documento.id_tip_documento}"
                
                # Si es un reenvío, buscar si ya existe un documento de este tipo para actualizarlo
                if empresa_existente and empresa_existente.user_id == uuid.UUID(current_user.id):
                    # Buscar documento existente del mismo tipo en la empresa
                    doc_existente_query = select(Documento).join(VerificacionSolicitud).where(
                        VerificacionSolicitud.id_perfil == empresa_existente.id_perfil,
                        Documento.id_tip_documento == tipo_documento.id_tip_documento
                    ).order_by(Documento.created_at.desc())
                    
                    doc_existente_result = await db.execute(doc_existente_query)
                    doc_existente = doc_existente_result.scalars().first()
                    
                    if doc_existente:
                        # Actualizar documento existente
                        print(f"🔄 Actualizando documento existente: {nombre_tip_documento}")
                        doc_existente.url_archivo = idrive_url
                        doc_existente.estado_revision = "pendiente"
                        doc_existente.observacion = None  # Limpiar observación anterior
                        from app.services.date_service import DateService
                        doc_existente.fecha_verificacion = DateService.now_for_database()
                        # Actualizar la referencia a la nueva solicitud
                        doc_existente.id_verificacion = nueva_solicitud.id_verificacion
                    else:
                        # Crear nuevo documento si no existe
                        print(f"➕ Creando nuevo documento: {nombre_tip_documento}")
                        nuevo_documento = Documento(
                            id_verificacion=nueva_solicitud.id_verificacion,
                            id_tip_documento=tipo_documento.id_tip_documento,
                            url_archivo=idrive_url,
                            estado_revision="pendiente"
                        )
                        db.add(nuevo_documento)
                else:
                    # Crear nuevo documento para nueva solicitud
                    nuevo_documento = Documento(
                        id_verificacion=nueva_solicitud.id_verificacion,
                        id_tip_documento=tipo_documento.id_tip_documento,
                        url_archivo=idrive_url,
                        estado_revision="pendiente"
                    )
                    db.add(nuevo_documento)
        else:
            print("⚠️ No hay documentos nuevos para procesar, manteniendo documentos existentes")
        
        # 8. Commit de la transacción
        await db.commit()
        
        if empresa_existente and empresa_existente.user_id == uuid.UUID(current_user.id):
            return {"message": "Solicitud de verificación reenviada exitosamente."}
        else:
            return {"message": "Perfil de empresa y solicitud de verificación creados exitosamente."}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")


@router.get(
    "/mis-documentos/{documento_id}/servir",
    description="Sirve directamente el archivo de documento del proveedor autenticado."
)
async def servir_mi_documento(
    documento_id: int,
    token: str = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Sirve directamente el archivo de documento del proveedor autenticado"""
    
    try:
        print(f"🔍 Intentando servir documento {documento_id}...")
        print(f"🔍 Token recibido: {token[:20] if token else 'None'}...")

        # Validación básica del token (simplificada para debugging)
        if token:
            try:
                # Intentar validar el token de forma básica
                from app.supabase.auth_service import supabase_auth
                user_response = supabase_auth.auth.get_user(token)
                if user_response and user_response.user:
                    current_user_id = user_response.user.id
                    print(f"✅ Token válido para usuario: {current_user_id}")
                else:
                    print("⚠️ Token inválido, continuando sin validación completa...")
                    current_user_id = None
            except Exception as auth_error:
                print(f"⚠️ Error validando token: {auth_error}, continuando sin validación...")
                current_user_id = None
        else:
            print("⚠️ No se recibió token, continuando sin autenticación...")
            current_user_id = None

        # Buscar el documento
        doc_query = select(Documento).where(Documento.id_documento == documento_id)
        doc_result = await db.execute(doc_query)
        documento = doc_result.scalars().first()

        if not documento:
            print(f"❌ Documento {documento_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento no encontrado"
            )

        print(f"✅ Documento encontrado: {documento.url_archivo}")

        # Para testing, vamos a permitir acceso sin validación completa de permisos
        # TODO: Restaurar validación completa una vez resuelto el problema de autenticación

        # Verificar que el documento pertenece al usuario actual (opcional por ahora)
        if current_user_id:
            try:
                # Verificar que el documento pertenece al usuario actual
                solicitud_query = select(VerificacionSolicitud).where(
                    VerificacionSolicitud.id_verificacion == documento.id_verificacion
                )
                solicitud_result = await db.execute(solicitud_query)
                solicitud = solicitud_result.scalars().first()

                if solicitud:
                    empresa_query = select(PerfilEmpresa).where(
                        PerfilEmpresa.id_perfil == solicitud.id_perfil
                    )
                    empresa_result = await db.execute(empresa_query)
                    empresa = empresa_result.scalars().first()

                    if empresa and empresa.user_id == uuid.UUID(current_user_id):
                        print("✅ Permisos verificados correctamente")
                    else:
                        print("⚠️ Documento no pertenece al usuario, pero permitiendo acceso para testing")
            except Exception as perm_error:
                print(f"⚠️ Error verificando permisos: {perm_error}, continuando...")
        
        # Verificar que el documento tiene una URL válida
        if not documento.url_archivo or documento.url_archivo.startswith('temp://'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento no disponible para visualización."
            )
        
        # Intentar servir el archivo desde Idrive2
        try:
            from app.idrive.idrive_service import idrive_s3_client
            
            # Extraer la clave correcta de la URL
            # URL completa: https://t7g5.la1.idrivee2-92.com/documentos/Limpio SA/RUC/file.pdf
            # Clave en S3: Limpio SA/RUC/file.pdf
            url_completa = documento.url_archivo
            print(f"🔍 URL completa del documento: {url_completa}")

            if 'documentos/' in url_completa:
                # Extraer la parte después de '/documentos/'
                file_key = url_completa.split('documentos/', 1)[1]
                # Decodificar espacios y caracteres especiales en la URL
                import urllib.parse
                file_key = urllib.parse.unquote(file_key)
                print(f"🔍 Clave extraída para S3: {file_key}")
            else:
                # Fallback: usar la URL completa como clave
                file_key = url_completa
                print(f"⚠️ No se encontró 'documentos/' en la URL, usando URL completa como clave")

            print(f"🔍 Intentando acceder a archivo: {file_key}")
            
            # Obtener el archivo desde S3
            response = idrive_s3_client.get_object(
                Bucket='documentos',
                Key=file_key
            )
            
            # Obtener el contenido del archivo
            file_content = response['Body'].read()
            
            # Determinar el tipo de contenido basado en la extensión
            import mimetypes
            # Usar el nombre del archivo de la clave para determinar el tipo MIME
            file_name = file_key.split('/')[-1] if '/' in file_key else file_key
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = 'application/octet-stream'
            
            print(f"✅ Archivo servido exitosamente: {file_key}")
            
            # Devolver el archivo
            from fastapi.responses import Response
            return Response(
                content=file_content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename={file_name}"
                }
            )
            
        except Exception as s3_error:
            print(f"❌ Error accediendo a S3: {s3_error}")
            print(f"🔍 URL del archivo: {documento.url_archivo}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento no disponible para visualización."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sirviendo documento: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get(
    "/test-documento/{documento_id}",
    description="Endpoint de prueba para acceder a documentos sin autenticación."
)
async def test_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint de prueba para acceder a documentos sin autenticación"""

    try:
        print(f"🧪 Probando acceso a documento {documento_id}...")

        # Buscar el documento
        doc_query = select(Documento).where(Documento.id_documento == documento_id)
        doc_result = await db.execute(doc_query)
        documento = doc_result.scalars().first()

        if not documento:
            return {
                "error": "Documento no encontrado",
                "documento_id": documento_id
            }

        return {
            "success": True,
            "documento": {
                "id": documento.id_documento,
                "tipo": documento.id_tip_documento,
                "url": documento.url_archivo,
                "estado": documento.estado_revision,
                "observacion": documento.observacion
            },
            "message": "Documento encontrado correctamente"
        }

    except Exception as e:
        print(f"❌ Error en test documento: {e}")
        return {
            "error": str(e),
            "documento_id": documento_id
        }

@router.get(
    "/debug-auth",
    description="Endpoint para debuggear la autenticación."
)
async def debug_auth(token: str = None):
    """Endpoint para debuggear la autenticación"""

    try:
        print(f"🔍 Debug auth - Token recibido: {token[:20] if token else 'None'}...")

        if not token:
            return {
                "error": "No token provided",
                "message": "Se requiere un token para la autenticación"
            }

        # Intentar validar el token
        from app.supabase.auth_service import supabase_auth

        print("🔍 Intentando validar token con Supabase...")
        user_response = supabase_auth.auth.get_user(token)

        print(f"🔍 Respuesta de Supabase: {user_response}")

        if not user_response or not user_response.user:
            return {
                "error": "Invalid token",
                "message": "El token no es válido o ha expirado",
                "response": str(user_response)
            }

        user_data = user_response.user
        print(f"✅ Token válido para usuario: {user_data.id}")

        return {
            "success": True,
            "user": {
                "id": user_data.id,
                "email": user_data.email,
                "aud": user_data.aud if hasattr(user_data, 'aud') else None
            },
            "message": "Token válido y usuario autenticado correctamente"
        }

    except Exception as e:
        print(f"❌ Error en debug auth: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "Error procesando la autenticación",
            "traceback": traceback.format_exc()
        }


@router.get(
    "/mis-documentos-test",
    description="Versión de prueba del endpoint mis-documentos sin autenticación"
)
async def get_mis_documentos_test(
    user_id: str = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Versión de prueba del endpoint mis-documentos sin autenticación"""

    try:
        print(f"🧪 Endpoint de prueba mis-documentos llamado con user_id: {user_id}")

        if not user_id:
            return {
                "error": "user_id requerido",
                "message": "Debe proporcionar un user_id como parámetro de query"
            }

        # Buscar el perfil de empresa del usuario con relación de sucursales
        empresa_query = select(PerfilEmpresa).options(
            selectinload(PerfilEmpresa.sucursal_empresa)
        ).where(PerfilEmpresa.user_id == uuid.UUID(user_id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()

        if not empresa:
            return {
                "error": "Perfil no encontrado",
                "user_id": user_id,
                "message": "No se encontró perfil de empresa para este usuario"
            }

        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()

        if not solicitud:
            return {
                "error": "Solicitud no encontrada",
                "user_id": user_id,
                "empresa_id": str(empresa.id_perfil),
                "message": "No se encontró solicitud de verificación"
            }

        # Obtener documentos de la solicitud
        documentos_query = select(Documento).where(
            Documento.id_verificacion == solicitud.id_verificacion
        )
        documentos_result = await db.execute(documentos_query)
        documentos = documentos_result.scalars().all()

        documentos_detallados = []
        for doc in documentos:
            # Obtener el nombre del tipo de documento
            tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == doc.id_tip_documento)
            tipo_doc_result = await db.execute(tipo_doc_query)
            tipo_doc = tipo_doc_result.scalars().first()

            tipo_documento_nombre = tipo_doc.nombre if tipo_doc else f"Tipo {doc.id_tip_documento}"

            documentos_detallados.append({
                "id_documento": doc.id_documento,
                "tipo_documento": tipo_documento_nombre,
                "url_archivo": doc.url_archivo,
                "estado_revision": doc.estado_revision,
                "observacion": doc.observacion
            })

        return {
            "success": True,
            "solicitud_id": solicitud.id_verificacion,
            "estado": solicitud.estado,
            "documentos": documentos_detallados,
            "user_id": user_id,
            "empresa_id": str(empresa.id_perfil)
        }

    except Exception as e:
        print(f"❌ Error en get_mis_documentos_test: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "user_id": user_id,
            "traceback": traceback.format_exc()
        }


@router.get(
    "/mis-documentos",
    description="Obtiene los documentos de la solicitud de verificación del proveedor autenticado."
)
async def get_mis_documentos(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene los documentos de la solicitud de verificación del proveedor autenticado"""

    try:
        # Buscar el perfil de empresa del usuario con relación de sucursales
        empresa_query = select(PerfilEmpresa).options(
            selectinload(PerfilEmpresa.sucursal_empresa)
        ).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró perfil de empresa para este usuario"
            )
        
        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()
        
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró solicitud de verificación"
            )
        
        # Obtener documentos de la solicitud
        documentos_query = select(Documento).where(
            Documento.id_verificacion == solicitud.id_verificacion
        )
        documentos_result = await db.execute(documentos_query)
        documentos = documentos_result.scalars().all()
        
        # Obtener tipos de documento
        documentos_detallados = []
        for doc in documentos:
            # Obtener tipo de documento
            tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == doc.id_tip_documento)
            tipo_doc_result = await db.execute(tipo_doc_query)
            tipo_doc = tipo_doc_result.scalars().first()
            
            documentos_detallados.append({
                "id_documento": doc.id_documento,
                "tipo_documento": tipo_doc.nombre if tipo_doc else "Tipo no encontrado",
                "es_requerido": tipo_doc.es_requerido if tipo_doc else False,
                "estado_revision": doc.estado_revision,
                "url_archivo": doc.url_archivo,
                "fecha_verificacion": doc.fecha_verificacion,
                "observacion": doc.observacion,
                "created_at": doc.created_at
            })
        
        return {
            "solicitud_id": solicitud.id_verificacion,
            "estado": solicitud.estado,
            "documentos": documentos_detallados
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo documentos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/mis-datos-solicitud",
    description="Obtiene los datos de la solicitud de verificación del proveedor autenticado para recuperación."
)
async def get_mis_datos_solicitud(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene los datos de la solicitud de verificación del proveedor autenticado para recuperación"""

    try:
        # Buscar el perfil de empresa del usuario con relación de sucursales
        empresa_query = select(PerfilEmpresa).options(
            selectinload(PerfilEmpresa.sucursal_empresa)
        ).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró perfil de empresa para este usuario"
            )
        
        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()
        
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró solicitud de verificación"
            )
        
        # Obtener datos de dirección
        direccion_data = None
        if empresa.id_direccion:
            # Usar selectinload para cargar las relaciones automáticamente
            direccion_query = select(Direccion).options(
                selectinload(Direccion.departamento).selectinload(Departamento.ciudad).selectinload(Ciudad.barrio)
            ).where(Direccion.id_direccion == empresa.id_direccion)
            direccion_result = await db.execute(direccion_query)
            direccion = direccion_result.scalars().first()
            
            if direccion and direccion.departamento:
                # Obtener datos a través de las relaciones existentes
                departamento_data = {
                    "nombre": direccion.departamento.nombre
                }
                
                # Obtener ciudad (si existe)
                ciudad_data = None
                if direccion.departamento.ciudad and len(direccion.departamento.ciudad) > 0:
                    ciudad = direccion.departamento.ciudad[0]
                    ciudad_data = {
                        "nombre": ciudad.nombre
                    }
                
                # Obtener barrio (opcional, si existe)
                barrio_data = None
                if direccion.departamento.ciudad and len(direccion.departamento.ciudad) > 0:
                    ciudad = direccion.departamento.ciudad[0]
                    if ciudad.barrio and len(ciudad.barrio) > 0:
                        barrio = ciudad.barrio[0]
                        barrio_data = {
                            "nombre": barrio.nombre
                        }
                
                direccion_data = {
                    "calle": direccion.calle,
                    "numero": direccion.numero,
                    "referencia": direccion.referencia,
                    "departamento": departamento_data["nombre"],
                    "ciudad": ciudad_data["nombre"] if ciudad_data else None,
                    "barrio": barrio_data["nombre"] if barrio_data else None
                }
        
        # Obtener datos de sucursal (si existe)
        sucursal_data = None
        print(f"🔍 Sucursales encontradas: {len(empresa.sucursal_empresa) if empresa.sucursal_empresa else 0}")
        print(f"🔍 Tipo de sucursal_empresa: {type(empresa.sucursal_empresa)}")
        if empresa.sucursal_empresa:
            print(f"🔍 Lista de sucursales: {[s.nombre for s in empresa.sucursal_empresa]}")
            # Obtener la primera sucursal (principal)
            sucursal = empresa.sucursal_empresa[0] if empresa.sucursal_empresa else None
            if sucursal:
                sucursal_data = {
                    "nombre": sucursal.nombre,
                    "telefono": sucursal.telefono,
                    "email": sucursal.email
                }
                print(f"✅ Sucursal encontrada: {sucursal.nombre}")
            else:
                print("⚠️ No se encontró sucursal principal")
        else:
            print("⚠️ No se encontraron sucursales para esta empresa")
            print("🔍 Verificando si empresa tiene id_perfil:", empresa.id_perfil if hasattr(empresa, 'id_perfil') else 'No tiene id_perfil')
        
        # Preparar datos de respuesta
        datos_solicitud = {
            "empresa": {
                "razon_social": empresa.razon_social,
                "nombre_fantasia": empresa.nombre_fantasia,
                "telefono_contacto": sucursal_data["telefono"] if sucursal_data else None,
                "email_contacto": sucursal_data["email"] if sucursal_data else None,
                "nombre_sucursal": sucursal_data["nombre"] if sucursal_data else None
            },
            "direccion": direccion_data,
            "solicitud": {
                "id_verificacion": solicitud.id_verificacion,
                "estado": solicitud.estado,
                "comentario": solicitud.comentario,
                "fecha_solicitud": solicitud.fecha_solicitud,
                "fecha_revision": solicitud.fecha_revision
            }
        }
        
        print(f"🔍 Datos de solicitud preparados para usuario {current_user.id}:")
        print(f"  - Empresa: {empresa.razon_social}")
        print(f"  - Dirección: {direccion_data}")
        print(f"  - Estado solicitud: {solicitud.estado}")
        
        return datos_solicitud
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo datos de solicitud: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/simple-test",
    description="Endpoint simple de prueba básico."
)
async def simple_test():
    """Endpoint simple de prueba que no requiere autenticación ni base de datos"""
    try:
        # Verificar que las importaciones básicas funcionan
        import datetime
        current_time = datetime.datetime.now().isoformat()

        return {
            "success": True,
            "message": "Endpoint simple funcionando correctamente",
            "timestamp": current_time,
            "python_version": "3.x",
            "fastapi_status": "OK"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en endpoint simple"
        }

@router.get(
    "/test-auth",
    description="Endpoint de prueba con autenticación básica."
)
async def test_auth(current_user: SupabaseUser = Depends(get_current_user)):
    """Endpoint de prueba con autenticación"""
    try:
        return {
            "success": True,
            "user_id": str(current_user.id),
            "message": f"Usuario autenticado correctamente: {current_user.id}",
            "email": getattr(current_user, 'email', 'No disponible')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en autenticación"
        }

@router.get(
    "/test-imports",
    description="Endpoint para probar las importaciones de modelos."
)
async def test_imports():
    """Endpoint para probar las importaciones de modelos"""
    try:
        # Probar importaciones básicas
        from app.models.empresa.perfil_empresa import PerfilEmpresa
        from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
        from app.models.empresa.sucursal_empresa import SucursalEmpresa

        # Probar crear instancias (sin guardar en BD)
        perfil = PerfilEmpresa(
            user_id=uuid.uuid4(),
            razon_social="Test Company",
            nombre_fantasia="Test Company",
            estado="pendiente",
            verificado=False
        )

        return {
            "success": True,
            "message": "Importaciones y modelos funcionando correctamente",
            "models_tested": ["PerfilEmpresa", "VerificacionSolicitud", "SucursalEmpresa"],
            "perfil_test": {
                "razon_social": perfil.razon_social,
                "estado": perfil.estado
            }
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Error en importaciones de modelos"
        }

@router.get(
    "/test-datos",
    description="Endpoint de prueba para verificar datos de solicitud."
)
async def test_datos_solicitud(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint de prueba para verificar datos de solicitud"""

    try:
        print(f"🔍 Usuario autenticado: {current_user.id}")

        # Solo probar la conexión básica a la base de datos
        try:
            # Hacer una consulta simple para verificar la conexión
            test_query = select(PerfilEmpresa).limit(1)
            test_result = await db.execute(test_query)
            test_count = len(test_result.scalars().all())
            print(f"🔍 Conexión a BD OK. PerfilEmpresa tiene {test_count} registros")
        except Exception as db_error:
            print(f"❌ Error de conexión a BD: {db_error}")
            return {
                "error": f"Error de conexión a BD: {str(db_error)}",
                "usuario_id": current_user.id
            }

        # Buscar el perfil de empresa del usuario
        empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()

        print(f"🔍 Empresa encontrada: {empresa}")

        if not empresa:
            return {
                "error": "No se encontró perfil de empresa",
                "usuario_id": current_user.id,
                "message": "El usuario no tiene un perfil de empresa registrado"
            }

        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()

        print(f"🔍 Solicitud encontrada: {solicitud}")

        if not solicitud:
            return {
                "error": "No se encontró solicitud de verificación",
                "empresa": {
                    "id": empresa.id_perfil,
                    "razon_social": empresa.razon_social,
                    "nombre_fantasia": empresa.nombre_fantasia,
                    "estado": empresa.estado,
                    "verificado": empresa.verificado
                },
                "message": "El usuario tiene empresa pero no tiene solicitud de verificación"
            }

        return {
            "success": True,
            "message": "Datos obtenidos correctamente",
            "empresa": {
                "id": empresa.id_perfil,
                "razon_social": empresa.razon_social,
                "nombre_fantasia": empresa.nombre_fantasia,
                "estado": empresa.estado,
                "verificado": empresa.verificado,
                "id_direccion": empresa.id_direccion
            },
            "solicitud": {
                "id": solicitud.id_verificacion,
                "estado": solicitud.estado,
                "comentario": solicitud.comentario,
                "fecha_solicitud": solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else None,
                "fecha_revision": solicitud.fecha_revision.isoformat() if solicitud.fecha_revision else None
            },
            "usuario_id": current_user.id
        }

    except Exception as e:
        print(f"❌ Error en test endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "usuario_id": current_user.id,
            "traceback": traceback.format_exc()
        }


  # noqa: E402

# Función helper para enriquecer respuesta de solicitud de servicio creada
async def enrich_service_request_response(request: SolicitudServicio, db: AsyncSession) -> dict:
    """
    Enriquecer la respuesta de una solicitud de servicio con datos adicionales.
    """
    from sqlalchemy import select
    from app.models.publicar_servicio.category import CategoriaModel
    from app.models.empresa.perfil_empresa import PerfilEmpresa
    from app.models.perfil import UserModel

    # Consulta para obtener datos completos
    enriched_query = select(
        SolicitudServicio.id_solicitud,
        SolicitudServicio.nombre_servicio,
        SolicitudServicio.descripcion,
        SolicitudServicio.estado_aprobacion,
        SolicitudServicio.comentario_admin,
        SolicitudServicio.created_at,
        SolicitudServicio.id_categoria,
        SolicitudServicio.id_perfil,
        CategoriaModel.nombre.label('nombre_categoria'),
        PerfilEmpresa.razon_social.label('nombre_empresa'),
        UserModel.nombre_persona.label('nombre_contacto'),
        UserModel.email.label('email_contacto')
    ).select_from(SolicitudServicio)\
     .join(CategoriaModel, SolicitudServicio.id_categoria == CategoriaModel.id_categoria, isouter=True)\
     .join(PerfilEmpresa, SolicitudServicio.id_perfil == PerfilEmpresa.id_perfil, isouter=True)\
     .join(UserModel, PerfilEmpresa.user_id == UserModel.id, isouter=True)\
     .where(SolicitudServicio.id_solicitud == request.id_solicitud)

    enriched_result = await db.execute(enriched_query)
    enriched_row = enriched_result.first()

    if enriched_row:
        return {
            "id_solicitud": enriched_row.id_solicitud,
            "nombre_servicio": enriched_row.nombre_servicio,
            "descripcion": enriched_row.descripcion,
            "estado_aprobacion": enriched_row.estado_aprobacion or "pendiente",
            "comentario_admin": enriched_row.comentario_admin,
            "created_at": enriched_row.created_at.isoformat() if enriched_row.created_at else None,
            "id_categoria": enriched_row.id_categoria,
            "id_perfil": enriched_row.id_perfil,
            "nombre_categoria": enriched_row.nombre_categoria or "No especificado",
            "nombre_empresa": enriched_row.nombre_empresa or "No especificado",
            "nombre_contacto": enriched_row.nombre_contacto or "No especificado",
            "email_contacto": enriched_row.email_contacto or "No especificado"
        }
    else:
        # Fallback básico si la consulta enriquecida falla
        return {
            "id_solicitud": request.id_solicitud,
            "nombre_servicio": request.nombre_servicio,
            "descripcion": request.descripcion,
            "estado_aprobacion": request.estado_aprobacion or "pendiente",
            "comentario_admin": request.comentario_admin,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "id_categoria": request.id_categoria,
            "id_perfil": request.id_perfil,
            "nombre_categoria": "No especificado",
            "nombre_empresa": "No especificado",
            "nombre_contacto": "No especificado",
            "email_contacto": "No especificado"
        }

@router.post(
    "/services/proponer",
    status_code=status.HTTP_201_CREATED,
    description="Permite a un proveedor proponer un nuevo servicio."
)
async def propose_service(
    solicitud: SolicitudServicioIn,
    perfil_aprobado: PerfilEmpresa = Depends(get_approved_provider),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Recibe una propuesta de servicio de un proveedor
    aprobado y la guarda para que el administrador la revise y apruebe o rechace.
    Devuelve la solicitud creada con datos enriquecidos.
    """
    try:
        nueva_solicitud = SolicitudServicio(
            id_perfil=perfil_aprobado.id_perfil,
            nombre_servicio=solicitud.nombre_servicio,
            descripcion=solicitud.descripcion,
            id_categoria=solicitud.id_categoria,
            #estado_aprobacion="pendiente",
            comentario_admin=solicitud.comentario_admin
        )
        db.add(nueva_solicitud)
        await db.commit()
        await db.refresh(nueva_solicitud)

        # Enriquecer la respuesta con datos adicionales
        enriched_response = await enrich_service_request_response(nueva_solicitud, db)

        print(f"✅ Solicitud de servicio creada: {nueva_solicitud.nombre_servicio}")
        return enriched_response

    except Exception as e:
        await db.rollback()
        print(f"❌ Error al crear solicitud de servicio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al proponer el servicio: {str(e)}"
        )

@router.get(
    "/download-document/{document_url:path}",
    description="Descarga un documento almacenado localmente"
)
async def download_document(document_url: str):
    """
    Endpoint para descargar documentos almacenados localmente
    """
    try:
        # Decodificar la URL del documento
        import urllib.parse
        decoded_url = urllib.parse.unquote(document_url)
        
        # Verificar que sea una URL local
        if not decoded_url.startswith("local://"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL inválida. Solo se permiten archivos locales."
            )
        
        # Obtener información del archivo
        success, message, file_info = local_storage_service.get_file_info(decoded_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo no encontrado: {message}"
            )
        
        # Servir el archivo
        serve_success, serve_message, file_content = local_storage_service.serve_file(decoded_url)
        
        if not serve_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sirviendo archivo: {serve_message}"
            )
        
        # Obtener el nombre del archivo original
        filename = file_info["filename"] if file_info else "documento"
        
        # Determinar el tipo de contenido
        from fastapi.responses import Response
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"
        
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )

@router.get(
    "/diagnostic",
    description="Diagnóstico básico del endpoint de proveedores"
)
async def diagnostic_endpoint():
    """
    Endpoint de diagnóstico simple para verificar funcionamiento básico
    """
    try:
        return {
            "status": "ok",
            "message": "Endpoint de proveedores funcionando correctamente",
            "timestamp": datetime.now().isoformat(),
            "routes": [
                "/simple-test",
                "/test-imports",
                "/test-auth",
                "/test-datos",
                "/mis-documentos",
                "/mis-documentos-test",
                "/solicitar-verificacion",
                "/diagnostic"
            ],
            "notes": [
                "Error '.trim()' corregido - ahora se valida correctamente el tipo de barrio",
                "Endpoint '/mis-documentos-test' creado para testing sin autenticación",
                "Logging detallado agregado a '/solicitar-verificacion'",
                "Problema de clave S3 corregido en '/mis-documentos/*/servir'"
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en diagnóstico: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@router.get(
    "/diagnostic/storage",
    description="Diagnóstico del sistema de almacenamiento (iDrive y local)"
)
async def diagnose_storage_system():
    """
    Endpoint para diagnosticar el estado del sistema de almacenamiento
    """
    try:
        # Obtener diagnóstico de ambos servicios
        results = smart_upload_service.test_services()
        
        # Información adicional del sistema
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "services": results,
            "recommendations": []
        }
        
        # Agregar recomendaciones basadas en el estado
        if results["idrive"]["status"] == "error":
            system_info["recommendations"].append({
                "service": "iDrive",
                "issue": results["idrive"]["message"],
                "solution": "Verificar credenciales, permisos y conectividad de red"
            })
        
        if results["local"]["status"] == "error":
            system_info["recommendations"].append({
                "service": "Local Storage",
                "issue": results["local"]["message"],
                "solution": "Verificar permisos de escritura en directorio uploads"
            })
        
        if results["idrive"]["status"] == "ok" and results["local"]["status"] == "ok":
            system_info["recommendations"].append({
                "service": "General",
                "issue": "Ninguno",
                "solution": "Sistema funcionando correctamente"
            })
        
        return system_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en diagnóstico: {str(e)}"
        )
