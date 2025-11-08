#autenticacion supabase
# app/api/v1/routers/auth.py
import uuid
from sqlalchemy import UUID, select, text
from sqlalchemy.orm import selectinload
from app.schemas.auth import SignInIn, SignUpIn, SignUpSuccess, TokenOut, RefreshTokenIn, EmailOnlyIn
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.dependencies.auth_user import get_current_user  # dependencia que valida el JWT
from app.api.v1.dependencies.database_supabase import get_async_db  # dependencia que proporciona la sesión de DB
from app.services.rate_limit_service import email_rate_limit_service
from app.services.direct_db_service import direct_db_service
from app.supabase.auth_service import supabase_auth, supabase_admin  # cliente Supabase inicializado
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
import asyncio
from app.services.direct_db_service import direct_db_service
from fastapi.responses import JSONResponse

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
async def sign_up(data: SignUpIn) -> Union[TokenOut, SignUpSuccess]:
    try:
        logger.info(f"Iniciando registro para usuario: {data.email}")
        
        # --- Verificar rate limit antes de proceder ---
        if not email_rate_limit_service.can_send_email(data.email):
            remaining_attempts = email_rate_limit_service.get_remaining_attempts(data.email)
            next_attempt_time = email_rate_limit_service.get_next_attempt_time(data.email)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Has alcanzado el límite de intentos de registro. Intentos restantes: {remaining_attempts}. Próximo intento disponible: {next_attempt_time.strftime('%H:%M') if next_attempt_time else 'N/A'}. Contacta a b2bseva.notificaciones@gmail.com para ayuda inmediata."
            )
        
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
        
        signup_response = None
        id_user = None
        email_sent_error = False
        
        try:
            signup_response = supabase_auth.auth.sign_up(signup_data)
            
            if not signup_response.user:
                handle_supabase_auth_error("Respuesta de Supabase incompleta (no hay user)")
            
            id_user = str(signup_response.user.id)
            logger.info(f"Usuario creado en Supabase Auth con ID: {id_user}")
            
        except AuthApiError as e:
            error_message = str(e).lower()
            
            # Si es error de envío de email, verificar si el usuario se creó
            if "error sending confirmation email" in error_message:
                logger.warning("⚠️ Error al enviar email de confirmación, verificando si el usuario se creó...")
                email_sent_error = True
                
                # Intentar verificar si el usuario se creó a pesar del error usando list_users()
                try:
                    if supabase_admin:
                        # Obtener todos los usuarios y buscar por email
                        auth_users = supabase_admin.auth.admin.list_users()
                        
                        # Buscar el usuario por email
                        found_user = None
                        if auth_users:
                            for auth_user in auth_users:
                                if auth_user.email and auth_user.email.lower() == data.email.lower():
                                    found_user = auth_user
                                    break
                        
                        if found_user:
                            id_user = str(found_user.id)
                            logger.info(f"✅ Usuario encontrado a pesar del error de email: {id_user}")
                            logger.warning("⚠️ El usuario se creó correctamente, pero no se pudo enviar el email de confirmación")
                        else:
                            logger.error("❌ Usuario no encontrado después del error de email")
                            # Nota: El usuario puede haberse creado en auth.users pero aún no estar visible
                            # debido a la naturaleza asíncrona. Es mejor asumir que no se creó.
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="No se pudo crear el usuario ni enviar el email de confirmación debido a un problema con la configuración de email del servidor. Por favor, intenta nuevamente más tarde o contacta al administrador en b2bseva.notificaciones@gmail.com"
                            )
                    else:
                        logger.error("❌ No se puede verificar usuario: supabase_admin no está configurado")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="No se pudo enviar el email de confirmación. El usuario puede haberse creado correctamente. Por favor, intenta iniciar sesión o contacta al administrador en b2bseva.notificaciones@gmail.com si el problema persiste."
                        )
                except HTTPException:
                    # Re-lanzar HTTPException tal cual
                    raise
                except Exception as verify_error:
                    logger.error(f"❌ Error verificando usuario después del error de email: {verify_error}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="No se pudo enviar el email de confirmación. El usuario puede haberse creado correctamente. Por favor, intenta iniciar sesión o contacta al administrador en b2bseva.notificaciones@gmail.com si el problema persiste."
                    )
            else:
                # Otro tipo de error de AuthApiError, re-lanzar para manejo general
                raise
        
        # Validar que id_user existe antes de continuar
        # Si id_user es None, significa que hubo un error que impidió crear el usuario
        if not id_user:
            logger.error("❌ No se pudo crear el usuario: id_user es None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo crear el usuario. Por favor, intenta nuevamente o contacta al administrador en b2bseva.notificaciones@gmail.com"
            )
        
        # Registrar intento de envío de email (solo si no hubo error)
        if not email_sent_error:
            email_rate_limit_service.record_email_attempt(data.email)

        # --- Paso 2: Verificar solo el perfil usando direct_db_service ---
        # Usar direct_db_service.get_connection() para evitar problemas con PgBouncer
        logger.info("⏳ Esperando que el trigger se ejecute...")
        await asyncio.sleep(1.0)  # Dar tiempo al trigger
        
        user_profile = None
        max_retries = 3  # Solo 3 intentos para el perfil
        retry_delay = 0.5  # Retry rápido
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Verificando perfil para usuario {id_user} (intento {attempt + 1}/{max_retries})")
                
                # Usar servicio directo para verificar solo el perfil (usa get_connection internamente)
                user_profile_data = await direct_db_service.check_user_profile(id_user)
                
                if user_profile_data:
                    logger.info(f"✅ Perfil encontrado en intento {attempt + 1}")
                    user_profile = user_profile_data
                    break
                else:
                    logger.warning(f"⚠️ Perfil no encontrado en intento {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"❌ Error en intento {attempt + 1}: {e}")
                
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Error de conexión a la base de datos: {str(e)}"
                    )
            
            # Esperar antes del siguiente intento
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (1.2 ** attempt))  # 0.5s, 0.6s
                logger.info(f"⏳ Esperando {retry_delay * (1.2 ** attempt):.1f}s antes del siguiente intento...")

        # Si no se encontró el perfil, crear manualmente usando direct_db_service
        if not user_profile:
            logger.warning("⚠️ Trigger no creó el perfil, creando manualmente...")
            
            try:
                # Usar direct_db_service.create_user_profile que usa get_connection internamente
                await direct_db_service.create_user_profile(
                    user_id=id_user,
                    nombre_persona=data.nombre_persona,
                    nombre_empresa=data.nombre_empresa,
                    ruc=data.ruc
                )
                
                logger.info("✅ Perfil creado manualmente")
                user_profile = {
                    "id": id_user,
                    "nombre_persona": data.nombre_persona,
                    "nombre_empresa": data.nombre_empresa,
                    "ruc": data.ruc,
                    "estado": "ACTIVO"
                }
                
            except Exception as e:
                logger.error(f"❌ Error creando perfil manualmente: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error: No se pudo crear el perfil del usuario. Error: {str(e)}"
                )
        
        # --- Paso 3: Confiar en el trigger para el rol ---
        logger.info("✅ Perfil verificado. El trigger asignará el rol automáticamente.")
        logger.info("💡 No verificamos el rol para evitar bloquear el trigger.")

        logger.info(f"Registro completado exitosamente para usuario: {id_user}")

        # --- Manejo de confirmación de email ---
        # Si hubo error al enviar el email o no hay sesión (usuario no confirmado)
        if email_sent_error or not signup_response or not signup_response.session:
            message = "¡Registro exitoso! 📧 "
            if email_sent_error:
                message += "⚠️ No se pudo enviar el correo de confirmación automáticamente. Por favor, intenta iniciar sesión con tus credenciales. Si tienes problemas, contacta a b2bseva.notificaciones@gmail.com para ayuda."
            else:
                message += "Hemos enviado un correo de confirmación a tu dirección de email. Por favor, revisa tu bandeja de entrada y haz clic en el enlace para activar tu cuenta. Si no encuentras el correo, revisa también tu carpeta de spam."
            
            return SignUpSuccess(
                message=message,
                email=data.email,
                nombre_persona=data.nombre_persona,
                nombre_empresa=data.nombre_empresa,
                ruc=data.ruc,
                instructions="1. Revisa tu bandeja de entrada\n2. Busca el correo de confirmación\n3. Haz clic en el enlace del correo\n4. Si no encuentras el correo, revisa la carpeta de spam" if not email_sent_error else "1. Intenta iniciar sesión con tus credenciales\n2. Si tienes problemas, contacta a b2bseva.notificaciones@gmail.com",
                next_steps="Una vez confirmado tu email, podrás iniciar sesión en la plataforma" if not email_sent_error else "Intenta iniciar sesión ahora mismo con tus credenciales"
            )

        # Crear respuesta JSON (consistente con signin)
        token_data = {
            "access_token": signup_response.session.access_token,
            "expires_in": signup_response.session.expires_in,
            "token_type": "bearer"
        }

        response = JSONResponse(content=token_data)

        # Configurar SOLO refresh_token en cookie HttpOnly (consistente con signin)
        logger.info(f"🍪 Estableciendo cookie refresh_token: {signup_response.session.refresh_token[:20]}...")
        
        # Detectar entorno para configurar cookies
        import os
        is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None
        
        response.set_cookie(
            key="refresh_token", 
            value=signup_response.session.refresh_token,
            httponly=True,
            secure=False,  # True en producción (Railway), False en desarrollo
            samesite="lax",
            max_age=7 * 24 * 60 * 60,  # 7 días
            path="/",
            domain=None if is_production else "localhost"  # None en producción, "localhost" en desarrollo
        )
        
        logger.info("✅ Cookies HttpOnly establecidas correctamente")

        return response

    except AuthApiError as e:
        logger.error(f"Error de Supabase Auth: {e}")
        error_message = str(e).lower()
        
        # Manejar específicamente el rate limit de emails
        if "email rate limit exceeded" in error_message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Has alcanzado el límite de envío de emails. Por favor, espera 1 hora antes de intentar registrarte nuevamente. Si necesitas ayuda inmediata, contacta a b2bseva.notificaciones@gmail.com"
            )
        
        # Este bloque ya no se ejecutará para "error sending confirmation email"
        # porque ahora lo manejamos antes del try-except general
        
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


@router.post("/signin", response_model=TokenOut,
            status_code=status.HTTP_200_OK,
            description="Autentica un usuario con email y contraseña y devuelve sus tokens de acceso y refresh.")
async def sign_in(data: SignInIn, db: AsyncSession = Depends(get_async_db)) -> JSONResponse:
    """
    Autentica un usuario con email y contraseña y devuelve sus tokens.
    """
    try:
        print(f"🔍 LOGIN ENDPOINT INICIADO - Email: {data.email}")
        
        # PASO 1: Verificar estado del usuario en la base de datos
        try:
            print(f"🔍 Obteniendo conexión de la base de datos...")
            
            # Usar direct_db_service para evitar problemas con PgBouncer
            conn = await direct_db_service.get_connection()
            print(f"🔍 Conexión obtenida, ejecutando consulta...")
            try:
                # Consulta simplificada para evitar problemas de rendimiento
                user_result = await conn.fetchrow("""
                    SELECT u.id, u.estado 
                    FROM users u 
                    JOIN auth.users au ON u.id = au.id 
                    WHERE au.email = $1
                """, data.email)
                print(f"🔍 Consulta ejecutada, resultado: {user_result}")

                if user_result:
                    user_id = str(user_result['id'])
                    user_estado = user_result['estado']
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
            finally:
                await direct_db_service.pool.release(conn)

        except HTTPException:
            raise  # Re-lanzar HTTPException para mantener el comportamiento
        except Exception as db_error:
            print(f"⚠️ Error consultando base de datos: {str(db_error)}")
            # Si hay error en la consulta, permitir continuar (fallback)

        # PASO 2: Autenticación en Supabase Auth
        print("✅ Estado verificado, procediendo con autenticación en Supabase")
        print(f"🔍 Llamando a Supabase Auth con email: {data.email}")
        signin_response = supabase_auth.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })
        print(f"🔍 Respuesta de Supabase recibida: {signin_response}")
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

        # Crear respuesta JSON
        token_data = {
            "access_token": signin_response.session.access_token,
            "expires_in": signin_response.session.expires_in,
            "token_type": "bearer"
        }

        response = JSONResponse(content=token_data)

        # Configurar SOLO refresh_token en cookie HttpOnly
        print(f"🍪 Estableciendo cookie refresh_token: {signin_response.session.refresh_token[:20]}...")
        
        # Detectar entorno para configurar cookies
        import os
        is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None
        
        response.set_cookie(
            key="refresh_token", 
            value=signin_response.session.refresh_token,
            httponly=True,
            secure=False,  # True en producción (Railway), False en desarrollo
            samesite="lax",
            max_age=7 * 24 * 60 * 60,  # 7 días
            path="/",
            domain=None if is_production else "localhost"  # None en producción, "localhost" en desarrollo
        )
        
        print("✅ Cookies HttpOnly establecidas correctamente")

        return response

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


@router.get("/me",
            status_code=status.HTTP_200_OK,
            description="Devuelve la información del usuario autenticado.")
async def read_profile(current_user: SupabaseUser = Depends(get_current_user),
                       db: AsyncSession = Depends(get_async_db)) -> UserProfileAndRolesOut:
    """
    Devuelve la información del usuario autenticado.
    """

    # 1. Convertir el id de string a UUID de Python
    user_uuid = uuid.UUID(current_user.id)

    # Usar servicio directo para evitar problemas con PgBouncer
    logger.info(f"🔍 Endpoint /me - Buscando perfil para usuario: {str(user_uuid)}")
    user_profile_data = await direct_db_service.get_user_profile_with_roles(str(user_uuid))
    logger.info(f"📊 Endpoint /me - Resultado del servicio: {user_profile_data is not None}")
    
    if not user_profile_data:
        logger.error(f"❌ Endpoint /me - Perfil no encontrado para usuario: {str(user_uuid)}")
        raise HTTPException(
            status_code=404,
            detail="Perfil de usuario no encontrado"
        )
    
    logger.info(f"✅ Endpoint /me - Perfil encontrado para usuario: {str(user_uuid)}")
    
    # Extraer los nombres de los roles
    # Los roles vienen como JSON string desde la consulta optimizada
    import json
    if isinstance(user_profile_data['roles'], str):
        roles_data = json.loads(user_profile_data['roles'])
    else:
        roles_data = user_profile_data['roles']
    
    roles_nombres = [role['nombre'] for role in roles_data]

    # Construir y devolver la respuesta final
    return UserProfileAndRolesOut(
        id=user_profile_data['id'],
        email=current_user.email, # El email se obtiene de la autenticacion
        nombre_persona=user_profile_data['nombre_persona'],
        nombre_empresa=user_profile_data['nombre_empresa'],
        ruc=user_profile_data['ruc'],
        roles=roles_nombres,
        foto_perfil=user_profile_data['foto_perfil']
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
        
        return {
            "message": f"📧 Se ha enviado un nuevo correo de confirmación a {data.email}. Por favor, revisa tu bandeja de entrada y haz clic en el enlace para activar tu cuenta. Si no encuentras el correo, revisa también tu carpeta de spam.",
            "email": data.email,
            "instructions": "1. Revisa tu bandeja de entrada\n2. Busca el correo de confirmación\n3. Haz clic en el enlace del correo\n4. Si no encuentras el correo, revisa la carpeta de spam"
        }

    except AuthApiError as e:
        # Manejar específicamente el rate limit de emails
        if "email rate limit exceeded" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Has alcanzado el límite de envío de emails. Por favor, espera 1 hora antes de solicitar un nuevo correo de confirmación. Si necesitas ayuda inmediata, contacta a b2bseva.notificaciones@gmail.com"
            )
        
        handle_supabase_auth_error(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ha ocurrido un error inesperado al re-enviar el correo de confirmación: {str(e)}"
        )


@router.get("/check-email-confirmation/{email}",
           status_code=status.HTTP_200_OK,
           description="Verifica si el email del usuario está confirmado.")
async def check_email_confirmation(email: str):
    """
    Verifica si el email del usuario está confirmado.
    """
    try:
        # Obtener información del usuario desde Supabase Auth
        user_response = supabase_auth.auth.admin.get_user_by_email(email)
        
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        user = user_response.user
        is_confirmed = user.email_confirmed_at is not None
        
        return {
            "email": email,
            "is_confirmed": is_confirmed,
            "confirmed_at": user.email_confirmed_at,
            "message": "Email confirmado" if is_confirmed else "Email pendiente de confirmación"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar confirmación de email: {str(e)}"
        )


@router.get("/rate-limit-status",
           status_code=status.HTTP_200_OK,
           description="Obtiene información sobre el estado del rate limit de emails.")
async def get_rate_limit_status():
    """
    Obtiene información sobre el estado del rate limit de emails.
    """
    return {
        "message": "Información sobre límites de email",
        "limits": {
            "free_plan": "3 emails por hora por usuario",
            "pro_plan": "30 emails por hora por usuario", 
            "team_plan": "100 emails por hora por usuario"
        },
        "current_status": "Si recibes error 429, has alcanzado el límite",
        "solution": "Espera 1 hora antes de intentar nuevamente",
        "contact": "Para ayuda inmediata: b2bseva.notificaciones@gmail.com"
    }


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




@router.get("/verificacion-estado",
            status_code=status.HTTP_200_OK,
            description="Obtiene el estado actual de la solicitud de verificación del usuario autenticado.")
async def get_verificacion_estado(current_user: SupabaseUser = Depends(get_current_user)):
    """
    Obtiene el estado de la solicitud de verificación del usuario actual
    """
    try:
        from app.services.direct_db_service import direct_db_service
        
        # Convertir el id de string a UUID de Python
        user_uuid = str(current_user.id)
        
        # Usar direct_db_service para evitar problemas con PgBouncer
        conn = await direct_db_service.get_connection()
        try:
        # Buscar el perfil de empresa del usuario
            empresa_result = await conn.fetchrow("""
                SELECT id_perfil, estado, verificado
                FROM perfil_empresa 
                WHERE user_id = $1
            """, user_uuid)
            
            if not empresa_result:
                return {
                    "estado": "none",
                    "mensaje": "No se encontró perfil de empresa para este usuario"
                }
        
            # Buscar la solicitud de verificación más reciente
            solicitud_result = await conn.fetchrow("""
                SELECT 
                    id_verificacion,
                    estado,
                    fecha_solicitud,
                    fecha_revision,
                    comentario
                FROM verificacion_solicitud 
                WHERE id_perfil = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, empresa_result['id_perfil'])
            
            if not solicitud_result:
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
            
            estado_frontend = estado_mapping.get(solicitud_result['estado'], "none")
        
            return {
                "estado": estado_frontend,
                "solicitud_id": solicitud_result['id_verificacion'],
                "fecha_solicitud": solicitud_result['fecha_solicitud'],
                "fecha_revision": solicitud_result['fecha_revision'],
                "comentario": solicitud_result['comentario'],
                "estado_empresa": empresa_result['estado'],
                "verificado": empresa_result['verificado'],
                "mensaje": f"Solicitud {solicitud_result['estado']}"
            }
            
        finally:
            await direct_db_service.pool.release(conn)
        
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
        
        # Usar Supabase Storage para fotos de perfil
        from app.services.supabase_storage_service import supabase_storage_service
        
        # Subir imagen a Supabase Storage en la carpeta perfiles/
        success, public_url = await supabase_storage_service.upload_profile_image(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type
        )
        
        if not success or not public_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al subir la imagen a Supabase Storage"
            )
        
        print(f"✅ Foto de perfil subida exitosamente a Supabase Storage: {public_url}")
        
        # Usar la URL pública de Supabase Storage
        relative_path = public_url
        
        print(f"✅ Foto de perfil guardada: {relative_path}")
        
        return {
            "success": True,
            "mensaje": "Foto de perfil subida exitosamente",
            "image_path": relative_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error subiendo foto de perfil: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir foto de perfil: {str(e)}"
        )

@router.delete("/delete-profile-photo")
async def delete_profile_photo(
    image_url: str,
    current_user: UserProfileAndRolesOut = Depends(get_current_user)
):
    """
    Elimina una foto de perfil del bucket de Supabase Storage.
    """
    try:
        from app.services.supabase_storage_service import supabase_storage_service
        
        # Verificar que la URL es de Supabase Storage
        if not image_url or not image_url.startswith('https://') or 'supabase.co' not in image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL de imagen no válida para eliminación"
            )
        
        # Extraer el nombre del archivo de la URL
        import os
        file_name = os.path.basename(image_url.split('?')[0])  # Remover query parameters
        
        # Eliminar imagen del bucket
        success = await supabase_storage_service.delete_image(image_url)
        
        if success:
            print(f"✅ Foto de perfil eliminada exitosamente del bucket: {file_name}")
            return {
                "message": "Foto de perfil eliminada exitosamente del bucket de Supabase Storage.",
                "deleted_file": file_name
            }
        else:
            print(f"❌ Error eliminando foto de perfil del bucket: {file_name}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar la foto de perfil del bucket"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en delete_profile_photo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la foto de perfil: {str(e)}"
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
