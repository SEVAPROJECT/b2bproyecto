#autenticacion supabase
# app/api/v1/routers/auth.py
import uuid
from sqlalchemy import UUID, select, text
from sqlalchemy.orm import selectinload
from app.schemas.auth import SignInIn, SignUpIn, SignUpSuccess, TokenOut, RefreshTokenIn, EmailOnlyIn
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.dependencies.auth_user import get_current_user  # dependencia que valida el JWT
from app.api.v1.dependencies.database_supabase import get_async_db  # dependencia que proporciona la sesión de DB
from app.supabase.auth_service import supabase_auth  # cliente Supabase inicializado
from typing import Any, Dict, Union
from app.schemas.user import UserProfileAndRolesOut
from app.schemas.auth_user import SupabaseUser
from app.utils.errores import handle_supabase_auth_error  # Importa la función para manejar errores de Supabase
from supabase import AuthApiError  # Importa la excepción de error de Supabase
from sqlalchemy.ext.asyncio import AsyncSession 
from app.models.usuario_rol import UsuarioRolModel  
from app.models.rol import RolModel  
from app.models.perfil import UserModel
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from fastapi import File, UploadFile
import os
import uuid
from datetime import datetime

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Endpoints de autenticación ---

@router.post(
    "/signup",
    response_model=Union[TokenOut, SignUpSuccess],
    status_code=status.HTTP_201_CREATED,
    description="Crea un usuario en Supabase Auth. El perfil y rol se crean automáticamente via trigger."
)
async def sign_up(data: SignUpIn, db: AsyncSession = Depends(get_async_db)) -> Union[TokenOut, SignUpSuccess]:
    try:
        logger.info(f"Iniciando registro para usuario: {data.email}")
        
        # --- Paso 1: Crear usuario en Supabase Auth con metadata ---
        # La metadata se enviará al trigger para crear automáticamente el perfil y asignar el rol "Cliente"
        signup_data = {
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "nombre_persona": data.nombre_persona,
                    "nombre_empresa": data.nombre_empresa,
                    "ruc": data.ruc
                }
            }
        }
        
        logger.info(f"Enviando datos a Supabase Auth: {signup_data}")
        signup_response = supabase_auth.auth.sign_up(signup_data)

        if not signup_response.user:
            handle_supabase_auth_error("Respuesta de Supabase incompleta (no hay user)")

        id_user = str(signup_response.user.id)
        logger.info(f"Usuario creado en Supabase Auth con ID: {id_user}")

        # --- Paso 2: Verificar que el trigger funcionó correctamente ---
        # Esperamos un momento para que el trigger se ejecute
        import asyncio
        await asyncio.sleep(2)  # Aumentamos el tiempo de espera

        # Verificar que el perfil se creó con manejo de errores de conexión
        try:
            logger.info(f"Verificando si el perfil se creó para el usuario: {id_user}")
            result = await db.execute(select(UserModel).filter(UserModel.id == id_user))
            user_profile = result.scalars().first()

            if not user_profile:
                logger.error(f"El perfil no se creó para el usuario: {id_user}")
                # Intentar crear el perfil manualmente como fallback
                try:
                    logger.info("Intentando crear perfil manualmente como fallback")
                    new_profile = UserModel(
                        id=id_user,
                        nombre_persona=data.nombre_persona,
                        nombre_empresa=data.nombre_empresa,
                        ruc=data.ruc,
                        estado="ACTIVO"
                    )
                    db.add(new_profile)
                    await db.commit()
                    logger.info("Perfil creado manualmente exitosamente")
                except SQLAlchemyError as e:
                    logger.error(f"Error al crear perfil manualmente: {e}")
                    await db.rollback()
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Error: El perfil del usuario no se creó automáticamente. Error del trigger: {str(e)}"
                    )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al verificar perfil: {e}")
            # Intentar recrear la conexión
            try:
                await db.close()
                # Aquí deberías obtener una nueva sesión, pero por ahora usamos fallback
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error de conexión a la base de datos: {str(e)}"
                )
            except Exception as reconnect_error:
                logger.error(f"Error al intentar reconectar: {reconnect_error}")
                raise HTTPException(
                    status_code=500, 
                    detail="Error de conexión a la base de datos. Inténtalo de nuevo."
                )

        # Verificar que el rol "Cliente" se asignó con manejo de errores
        try:
            logger.info(f"Verificando si el rol 'Cliente' se asignó para el usuario: {id_user}")
            result = await db.execute(
                select(UsuarioRolModel)
                .join(RolModel)
                .filter(
                    UsuarioRolModel.id_usuario == id_user,
                    RolModel.nombre == "Cliente"
                )
            )
            user_role = result.scalars().first()

            if not user_role:
                logger.error(f"El rol 'Cliente' no se asignó para el usuario: {id_user}")
                # Intentar asignar el rol manualmente como fallback
                try:
                    logger.info("Intentando asignar rol manualmente como fallback")
                    result = await db.execute(select(RolModel).filter(RolModel.nombre == "Cliente"))
                    cliente_rol = result.scalars().first()
                    
                    if cliente_rol:
                        new_user_role = UsuarioRolModel(
                            id_usuario=id_user,
                            id_rol=cliente_rol.id
                        )
                        db.add(new_user_role)
                        await db.commit()
                        logger.info("Rol asignado manualmente exitosamente")
                    else:
                        logger.error("Rol 'Cliente' no encontrado en la base de datos")
                        raise HTTPException(
                            status_code=500, 
                            detail="Error: El rol 'Cliente' no existe en la base de datos"
                        )
                except SQLAlchemyError as e:
                    logger.error(f"Error al asignar rol manualmente: {e}")
                    await db.rollback()
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Error: El rol 'Cliente' no se asignó automáticamente. Error del trigger: {str(e)}"
                    )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al verificar rol: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error de conexión al verificar roles: {str(e)}"
            )

        logger.info(f"Registro completado exitosamente para usuario: {id_user}")

        # --- Manejo de confirmación de email ---
        if not signup_response.session:
            return SignUpSuccess(
                message="¡Registro exitoso! Te enviamos un correo para confirmar tu cuenta. Revisa tu bandeja de entrada.",
                email=data.email,
                nombre_persona=data.nombre_persona,
                nombre_empresa=data.nombre_empresa,
                ruc=data.ruc,
            )

        return TokenOut(
            access_token=signup_response.session.access_token,
            refresh_token=signup_response.session.refresh_token,
            expires_in=signup_response.session.expires_in,
        )

    except AuthApiError as e:
        logger.error(f"Error de Supabase Auth: {e}")
        handle_supabase_auth_error(e)
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de base de datos: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inesperado al registrar el usuario: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado al registrar el usuario: {str(e)}"
        )


#para probar el endpoint desde postman http://localhost:8000/auth/signin
@router.post("/signin", response_model=TokenOut,
            status_code=status.HTTP_200_OK,
            description="Autentica un usuario con email y contraseña y devuelve sus tokens de acceso y refresh.")
async def sign_in(data: SignInIn, db: AsyncSession = Depends(get_async_db)) -> TokenOut:
    """
    Autentica un usuario con email y contraseña y devuelve sus tokens.
    """
    #Dict[str, Any] es solo una anotación de tipo, no es necesario para la implementación
    #pero ayuda a entender que supabase_auth.sign_in devuelve un diccionario con los datos de la sesión
    #Supabase Auth utiliza el método sign_in para autenticar usuarios

    try:
        # PASO 1: Verificar estado del usuario en la base de datos ANTES de autenticar
        user_id = None
        user_estado = None

        # Buscar el usuario por email en la tabla public.users primero
        try:
            from sqlalchemy import text
            email_query = text("SELECT id, estado FROM users WHERE id IN (SELECT id FROM auth.users WHERE email = :email)")
            result = await db.execute(email_query, {"email": data.email})
            user_row = result.first()

            if user_row:
                user_id = str(user_row.id)
                user_estado = user_row.estado
                print(f"🔍 Usuario encontrado: ID={user_id}, Estado={user_estado}")

                # Verificar estado del usuario ANTES de autenticar
                if user_estado != "ACTIVO":
                    print(f"🚫 Usuario {user_id} tiene estado {user_estado} - DENEGANDO ACCESO")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Tu cuenta está inactiva. Por favor, contacta al administrador en b2bseva.notificaciones@gmail.com para más detalles."
                    )
            else:
                print(f"⚠️ Usuario con email {data.email} no encontrado en tabla users")

        except Exception as db_error:
            print(f"⚠️ Error consultando base de datos: {str(db_error)}")
            # Si hay error en la consulta, permitir continuar (fallback)

        # PASO 2: Si el estado es ACTIVO (o no se pudo verificar), proceder con autenticación
        print("✅ Estado verificado, procediendo con autenticación en Supabase")

        signin_response = supabase_auth.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if signin_response.user is None or not signin_response.session:
           handle_supabase_auth_error("Supabase response incomplete")

        # PASO 3: Verificación adicional por si acaso (doble verificación)
        if user_id and user_estado:
            if user_estado != "ACTIVO":
                # Si por alguna razón llega aquí, invalidar la sesión inmediatamente
                try:
                    supabase_auth.auth.sign_out()
                except:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tu cuenta está inactiva. Por favor, contacta al administrador en b2bseva.notificaciones@gmail.com para más detalles."
                )

        return TokenOut(
            access_token=signin_response.session.access_token,
            refresh_token=signin_response.session.refresh_token,
            expires_in=signin_response.session.expires_in,
        )

    except AuthApiError as e:
        # Llama a la función centralizada que usa el diccionario
        handle_supabase_auth_error(e)
    except HTTPException:
        # Re-lanzar excepciones HTTP (como la de cuenta inactiva)
        raise
    except (KeyError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar los datos de la sesión: La respuesta de Supabase no tiene el formato esperado. Detalles: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ha ocurrido un error inesperado al iniciar sesión: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenOut,
    status_code=status.HTTP_200_OK,
    description="Refresca el JWT usando el refresh_token."
)
async def refresh_token(data: RefreshTokenIn) -> TokenOut:
    """
    Refresca el JWT usando el refresh_token.
    """
    try:
        # Intenta refrescar la sesión usando el refresh_token proporcionado
        refresh_response = supabase_auth.auth.refresh_session({
            "refresh_token": data.refresh_token
        })

        # Supabase Auth lanza AuthApiError si el refresh_token es inválido o expiró.
        # Sin embargo, si la respuesta es exitosa pero la sesión está ausente,
        # lo manejamos como un error interno.
        if refresh_response.session is None:
            # Esto podría ocurrir si la operación no lanzó un AuthApiError pero
            # no se pudo obtener una sesión válida (ej. problema en Supabase, token ya usado).
            handle_supabase_auth_error("Supabase refresh response incomplete")

        # Si la sesión se refrescó exitosamente, devuelve los nuevos tokens
        return TokenOut(
            access_token=refresh_response.session.access_token,
            refresh_token=refresh_response.session.refresh_token,
            expires_in=refresh_response.session.expires_in,
        )
    except AuthApiError as e:
        # Captura errores específicos de la API de autenticación de Supabase.
        # Esto incluirá casos como un refresh_token inválido o expirado.
        handle_supabase_auth_error(e)
    except (KeyError, TypeError) as e:
        # Captura errores si la estructura de la respuesta de Supabase no es la esperada
        # (ej. si el objeto de sesión no contiene 'access_token', 'refresh_token', 'expires_in').
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar los datos del refresh token: La respuesta de Supabase no tiene el formato esperado. Detalles: {e}"
        )
    except Exception as e:
        # Captura cualquier otra excepción inesperada.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ha ocurrido un error inesperado al refrescar el token: {str(e)}"
        )


@router.post("/resend-confirmation-email",
             status_code=status.HTTP_200_OK,
             description="Re-envia un correo de confirmacion para verificar la cuenta.")
async def resend_confirmation_email(data: EmailOnlyIn):
    """
    Re-envia un correo de confirmacion de email para verificar la cuenta del usuario.
    """
    try:
        supabase_auth.auth.resend({
            "type": "signup",
            "email": data.email
        })
        
        return {"message": f"Se ha enviado un nuevo correo de confirmacion a {data.email}. Por favor, revisa tu bandeja de entrada."}

    except AuthApiError as e:
        handle_supabase_auth_error(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ha ocurrido un error inesperado al re-enviar el correo de confirmaci?n: {str(e)}"
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: SupabaseUser = Depends(get_current_user)):
    """
    Revoca el refresh token del usuario (deslogueo) y termina su sesión activa.
    """
    try:
        # Intenta cerrar la sesión del usuario actual.
        # Supabase suele manejar esto invalidando el refresh token.
        # El resultado de sign_out es a menudo None si es exitoso y no hay errores.
        # supabase_auth.sign_out()
        supabase_auth.auth.sign_out()

        # Si la operación fue exitosa y no lanzó una excepción,
        # simplemente devuelve None para un 204 No Content.
        return None
    except AuthApiError as e:
        # Captura errores específicos de la API de Supabase Auth durante el deslogueo.
        # Esto podría incluir problemas si el token ya no es válido,
        # aunque sign_out es bastante tolerante en esos casos.
        handle_supabase_auth_error(e)
    except Exception as e:
        # Captura cualquier otra excepción inesperada.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ha ocurrido un error inesperado al cerrar la sesión: {str(e)}"
        )

   
@router.post("/forgot-password", status_code=status.HTTP_200_OK,
            description="Envía un correo electrónico para restablecer la contraseña.")
async def forgot_password(data: EmailOnlyIn):
    """
    Solicita a Supabase que envíe un correo de recuperación de contraseña.
    """
    try:
        # Supabase típicamente responde con éxito si la solicitud es válida,
            # incluso si el email no existe, para evitar enumeración de usuarios.
            # El método `reset_password_for_email` es el correcto.
        response = supabase_auth.auth.reset_password_for_email(data.email)
        
        # Si no hay error, significa que el correo se envió correctamente
        return {"message": "Te enviamos un correo para restablecer tu contraseña."}
    except Exception as e:
        # Captura cualquier otra excepción inesperada.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ha ocurrido un error inesperado al solicitar el restablecimiento de contraseña: {str(e)}"
        )


@router.get("/me",
            status_code=status.HTTP_200_OK,
            description="Devuelve la información del usuario autenticado.")
async def read_profile(current_user: SupabaseUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_async_db)) -> UserProfileAndRolesOut:
    """
    Devuelve la información del usuario autenticado.
    """

    # 1. Recuperar el perfil del usuario de la base de datos
    # Se utiliza joinedload para cargar los roles de forma eficiente en una sola consulta.
    '''result_profile = await db.execute(
        select(UserModel)
        .options(joinedload(UserModel.roles))
        .where(UserModel.id == UUID(current_user.id))
    )'''

     # 1. Convertir el id de string a UUID de Python
    user_uuid = uuid.UUID(current_user.id)

    # Se utiliza joinedload para cargar los roles de forma eficiente en una sola consulta,
    # incluyendo la relación anidada `rol` para evitar lazy-loading en el contexto async.
    result_profile = await db.execute(
        select(UserModel)
        .options(
            joinedload(UserModel.roles).joinedload(UsuarioRolModel.rol)
        )
        .where(UserModel.id == user_uuid)
    )

    user_profile = result_profile.scalars().first()
    
    if not user_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de usuario no encontrado")

    # 2. Extraer los nombres de los roles de la lista de objetos de rol
    roles_nombres = [rol_asociado.rol.nombre for rol_asociado in user_profile.roles]

    # 3. Construir y devolver la respuesta final
    return UserProfileAndRolesOut(
        id=user_profile.id,
        email=current_user.email, # El email se obtiene de la autenticacion
        nombre_persona=user_profile.nombre_persona,
        nombre_empresa=user_profile.nombre_empresa,
        ruc=user_profile.ruc,
        roles=roles_nombres,
        foto_perfil=user_profile.foto_perfil
    )


@router.get("/verificacion-estado",
            status_code=status.HTTP_200_OK,
            description="Obtiene el estado actual de la solicitud de verificación del usuario autenticado.")
async def get_verificacion_estado(current_user: SupabaseUser = Depends(get_current_user),
                                 db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene el estado de la solicitud de verificación del usuario actual
    """
    try:
        # Convertir el id de string a UUID de Python
        user_uuid = uuid.UUID(current_user.id)
        
        # Buscar el perfil de empresa del usuario
        from app.models.empresa.perfil_empresa import PerfilEmpresa
        from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
        
        empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == user_uuid)
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            return {
                "estado": "none",
                "mensaje": "No se encontró perfil de empresa para este usuario"
            }
        
        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()
        
        if not solicitud:
            return {
                "estado": "none",
                "mensaje": "No se encontró solicitud de verificación"
            }
        
        # Mapear el estado de la base de datos al estado del frontend
        estado_mapping = {
            "pendiente": "pending",
            "aprobada": "approved", 
            "rechazada": "rejected"
        }
        
        estado_frontend = estado_mapping.get(solicitud.estado, "none")
        
        return {
            "estado": estado_frontend,
            "solicitud_id": solicitud.id_verificacion,
            "fecha_solicitud": solicitud.fecha_solicitud,
            "fecha_revision": solicitud.fecha_revision,
            "comentario": solicitud.comentario,
            "estado_empresa": empresa.estado,
            "verificado": empresa.verificado,
            "mensaje": f"Solicitud {solicitud.estado}"
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo estado de verificación: {str(e)}")
        return {
            "estado": "none",
            "mensaje": f"Error al obtener estado: {str(e)}"
        }



@router.put(
    "/profile",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    description="Actualiza el perfil del usuario autenticado"
)
async def update_user_profile(
    profile_data: dict,
    current_user: UserProfileAndRolesOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Actualiza el perfil del usuario autenticado"""
    try:
        print(f"🔍 Actualizando perfil para usuario: {current_user.id}")
        
        # Obtener el usuario de la base de datos
        user_query = select(UserModel).where(UserModel.id == current_user.id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Actualizar campos permitidos
        if "nombre_persona" in profile_data:
            user.nombre_persona = profile_data["nombre_persona"]
            print(f"✅ Nombre actualizado: {user.nombre_persona}")
        
        if "foto_perfil" in profile_data:
            user.foto_perfil = profile_data["foto_perfil"]
            print(f"✅ Foto de perfil actualizada: {user.foto_perfil}")
        
        # Guardar cambios
        await db.commit()
        await db.refresh(user)
        
        print(f"✅ Perfil actualizado exitosamente para usuario: {current_user.id}")
        
        return {
            "success": True,
            "mensaje": "Perfil actualizado exitosamente",
            "data": {
                "id": str(user.id),
                "nombre_persona": user.nombre_persona,
                "foto_perfil": user.foto_perfil
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando perfil: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar perfil: {str(e)}"
        )

@router.post(
    "/upload-profile-photo",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    description="Sube una foto de perfil para el usuario autenticado"
)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: UserProfileAndRolesOut = Depends(get_current_user)
):
    """Sube una foto de perfil para el usuario autenticado"""
    try:
        print(f"🔍 Subiendo foto de perfil para usuario: {current_user.id}")
        
        # Validar tipo de archivo
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser una imagen"
            )
        
        # Validar extensiones permitidas
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos JPG, JPEG y PNG"
            )
        
        # Validar tamaño (5MB máximo)
        file_content = await file.read()
        if len(file_content) > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no puede ser mayor a 5MB"
            )
        
        # Crear directorio de uploads si no existe
        upload_dir = "uploads/profile_photos"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_user.id}_{timestamp}_{file_id}{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Generar URL relativa
        relative_path = f"/uploads/profile_photos/{filename}"
        
        print(f"✅ Foto de perfil guardada: {relative_path}")
        
        return {
            "success": True,
            "mensaje": "Foto de perfil subida exitosamente",
            "image_path": relative_path,
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error subiendo foto de perfil: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir foto de perfil: {str(e)}"
        )


@router.get(
    "/verificacion-datos",
    description="Obtiene los datos completos de verificación del usuario autenticado, incluyendo empresa, sucursal, dirección y documentos."
)
async def get_verificacion_datos(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene los datos completos de verificación del usuario autenticado"""
    
    try:
        print(f"🔍 Obteniendo datos de verificación para usuario: {current_user.id}")
        
        # Importar modelos necesarios
        from app.models.empresa.perfil_empresa import PerfilEmpresa
        from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
        from app.models.empresa.documento import Documento
        from app.models.empresa.tipo_documento import TipoDocumento
        from app.models.empresa.direccion import Direccion
        from app.models.empresa.barrio import Barrio
        from app.models.empresa.ciudad import Ciudad
        from app.models.empresa.departamento import Departamento
        from app.models.empresa.sucursal_empresa import SucursalEmpresa
        from sqlalchemy.orm import selectinload
        
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
        
        print(f"✅ Empresa encontrada: {empresa.razon_social}")
        
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
        
        print(f"✅ Solicitud encontrada: {solicitud.estado}")
        
        # Obtener datos de dirección usando consulta SQL directa
        direccion_data = None
        if empresa.id_direccion:
            # Usar consulta SQL directa para evitar problemas con selectinload
            direccion_query = text("""
                SELECT 
                    d.calle,
                    d.numero,
                    d.referencia,
                    dep.nombre as departamento,
                    c.nombre as ciudad,
                    b.nombre as barrio
                FROM direccion d
                LEFT JOIN departamento dep ON d.id_departamento = dep.id_departamento
                LEFT JOIN ciudad c ON d.id_ciudad = c.id_ciudad
                LEFT JOIN barrio b ON d.id_barrio = b.id_barrio
                WHERE d.id_direccion = :direccion_id
            """)
            
            result = await db.execute(direccion_query, {"direccion_id": empresa.id_direccion})
            direccion = result.fetchone()
            
            if direccion:
                direccion_data = {
                    "calle": direccion.calle,
                    "numero": direccion.numero,
                    "referencia": direccion.referencia,
                    "departamento": direccion.departamento,
                    "ciudad": direccion.ciudad,
                    "barrio": direccion.barrio
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
                print(f"✅ Datos de sucursal: {sucursal_data}")
            else:
                print("⚠️ No se encontró sucursal principal")
        else:
            print("⚠️ No se encontraron sucursales para esta empresa")
            print("🔍 Verificando si empresa tiene id_perfil:", empresa.id_perfil if hasattr(empresa, 'id_perfil') else 'No tiene id_perfil')
        
        # Obtener documentos
        documentos_query = select(Documento).options(
            selectinload(Documento.tipo_documento)
        ).where(Documento.id_verificacion == solicitud.id_verificacion)
        documentos_result = await db.execute(documentos_query)
        documentos = documentos_result.scalars().all()
        
        documentos_data = []
        for doc in documentos:
            tipo_doc_nombre = doc.tipo_documento.nombre if doc.tipo_documento else f"Tipo {doc.id_tip_documento}"
            es_requerido = doc.tipo_documento.es_requerido if doc.tipo_documento else False
            documentos_data.append({
                "id_documento": doc.id_documento,
                "tipo_documento": tipo_doc_nombre,
                "es_requerido": es_requerido,
                "estado_revision": doc.estado_revision,
                "url_archivo": doc.url_archivo,
                "fecha_verificacion": doc.fecha_verificacion,
                "observacion": doc.observacion,
                "created_at": doc.created_at
            })
        
        # Preparar datos de respuesta
        empresa_dict = {
            "razon_social": empresa.razon_social,
            "nombre_fantasia": empresa.nombre_fantasia,
            "ruc": "",  # No existe en PerfilEmpresa
            "direccion": direccion_data["calle"] + " " + direccion_data["numero"] if direccion_data else "",
            "referencia": direccion_data["referencia"] if direccion_data else "",
            "departamento": direccion_data["departamento"] if direccion_data else None,
            "ciudad": direccion_data["ciudad"] if direccion_data else None,
            "barrio": direccion_data["barrio"] if direccion_data else None,
            "telefono": sucursal_data["telefono"] if sucursal_data else "",
            "email": sucursal_data["email"] if sucursal_data else "",
            "sitio_web": "",  # No existe en PerfilEmpresa
            "descripcion": "",  # No existe en PerfilEmpresa
            "categoria_empresa": "",  # No existe en PerfilEmpresa
            "estado": empresa.estado,
            "verificado": empresa.verificado,
            "fecha_inicio": empresa.fecha_inicio,
            "fecha_fin": empresa.fecha_fin,
            # Agregar datos de sucursal
            "telefono_contacto": sucursal_data["telefono"] if sucursal_data else None,
            "email_contacto": sucursal_data["email"] if sucursal_data else None,
            "nombre_sucursal": sucursal_data["nombre"] if sucursal_data else None
        }
        
        solicitud_dict = {
            "id_verificacion": solicitud.id_verificacion,
            "estado": solicitud.estado,
            "fecha_solicitud": solicitud.fecha_solicitud,
            "fecha_revision": solicitud.fecha_revision,
            "comentario": solicitud.comentario,
            "created_at": solicitud.created_at
        }
        
        response_data = {
            "success": True,
            "empresa": empresa_dict,
            "solicitud": solicitud_dict,
            "documentos": documentos_data
        }
        
        print(f"✅ Datos de verificación preparados para usuario {current_user.id}")
        print(f"  - Empresa: {empresa.razon_social}")
        print(f"  - Sucursal: {sucursal_data['nombre'] if sucursal_data else 'No encontrada'}")
        print(f"  - Documentos: {len(documentos_data)}")
        print(f"🔍 Datos de empresa_dict que se enviarán:")
        print(f"  - nombre_sucursal: {empresa_dict.get('nombre_sucursal')}")
        print(f"  - telefono_contacto: {empresa_dict.get('telefono_contacto')}")
        print(f"  - email_contacto: {empresa_dict.get('email_contacto')}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo datos de verificación: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/debug-sucursal",
    description="Endpoint de debug para verificar datos de sucursal."
)
async def debug_sucursal(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint de debug para verificar datos de sucursal"""
    
    try:
        print(f"🔍 DEBUG: Verificando sucursales para usuario: {current_user.id}")
        
        # Importar modelos necesarios
        from app.models.empresa.perfil_empresa import PerfilEmpresa
        from app.models.empresa.sucursal_empresa import SucursalEmpresa
        from sqlalchemy.orm import selectinload
        
        # Buscar el perfil de empresa del usuario
        empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            return {
                "error": "No se encontró perfil de empresa",
                "usuario_id": current_user.id
            }
        
        print(f"✅ Empresa encontrada: {empresa.razon_social} (ID: {empresa.id_perfil})")
        
        # Buscar sucursales directamente
        sucursales_query = select(SucursalEmpresa).where(SucursalEmpresa.id_perfil == empresa.id_perfil)
        sucursales_result = await db.execute(sucursales_query)
        sucursales = sucursales_result.scalars().all()
        
        print(f"🔍 Sucursales encontradas directamente: {len(sucursales)}")
        for sucursal in sucursales:
            print(f"  - {sucursal.nombre} (ID: {sucursal.id_sucursal})")
        
        # Buscar con relación
        empresa_con_sucursales_query = select(PerfilEmpresa).options(
            selectinload(PerfilEmpresa.sucursal_empresa)
        ).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        empresa_con_sucursales_result = await db.execute(empresa_con_sucursales_query)
        empresa_con_sucursales = empresa_con_sucursales_result.scalars().first()
        
        sucursales_relacion = empresa_con_sucursales.sucursal_empresa if empresa_con_sucursales else []
        print(f"🔍 Sucursales encontradas por relación: {len(sucursales_relacion)}")
        
        return {
            "usuario_id": current_user.id,
            "empresa": {
                "id_perfil": empresa.id_perfil,
                "razon_social": empresa.razon_social,
                "nombre_fantasia": empresa.nombre_fantasia
            },
            "sucursales_directas": [
                {
                    "id_sucursal": s.id_sucursal,
                    "nombre": s.nombre,
                    "telefono": s.telefono,
                    "email": s.email,
                    "es_principal": s.es_principal
                } for s in sucursales
            ],
            "sucursales_relacion": [
                {
                    "id_sucursal": s.id_sucursal,
                    "nombre": s.nombre,
                    "telefono": s.telefono,
                    "email": s.email,
                    "es_principal": s.es_principal
                } for s in sucursales_relacion
            ]
        }
        
    except Exception as e:
        print(f"❌ Error en debug sucursal: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "usuario_id": current_user.id
        }
