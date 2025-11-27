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
from typing import Any, Dict, Union, Optional
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
from fastapi.responses import JSONResponse
from app.services.supabase_storage_service import supabase_storage_service

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

from app.models.empresa.sucursal_empresa import SucursalEmpresa
from app.services.supabase_storage_service import supabase_storage_service

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Constantes ---
ESTADO_ACTIVO = "ACTIVO"
TOKEN_TYPE_BEARER = "bearer"
COOKIE_SAMESITE_LAX = "lax"
DOMAIN_LOCALHOST = "localhost"
COOKIE_REFRESH_TOKEN = "refresh_token"
EMAIL_ADMIN = "b2bseva.notificaciones@gmail.com"
MSG_SUPABASE_RESPONSE_INCOMPLETE = "Supabase response incomplete"
MSG_USUARIO_NO_ENCONTRADO = "Usuario no encontrado"
MSG_PERFIL_USUARIO_NO_ENCONTRADO = "Perfil de usuario no encontrado"
MSG_NO_ENCONTRADO_PERFIL_EMPRESA = "No se encontró perfil de empresa para este usuario"
MSG_NO_ENCONTRADA_SOLICITUD_VERIFICACION = "No se encontró solicitud de verificación"
MSG_ERROR_INTERNO_SERVIDOR = "Error interno del servidor"
ERROR_EMAIL_RATE_LIMIT = "email rate limit exceeded"
ERROR_SENDING_CONFIRMATION_EMAIL = "error sending confirmation email"
ESTADO_NONE = "none"
ESTADO_PENDIENTE = "pendiente"
ESTADO_APROBADA = "aprobada"
ESTADO_RECHAZADA = "rechazada"
ESTADO_PENDING = "pending"
ESTADO_APPROVED = "approved"
ESTADO_REJECTED = "rejected"
TYPE_SIGNUP = "signup"
MSG_ARCHIVO_DEBE_SER_IMAGEN = "El archivo debe ser una imagen"
MSG_SOLO_PERMITEN_ARCHIVOS_IMAGEN = "Solo se permiten archivos JPG, JPEG y PNG"
MSG_ARCHIVO_SUPERA_TAMANO = "El archivo no puede ser mayor a 5MB"
MSG_ERROR_SUBIR_IMAGEN_STORAGE = "Error al subir la imagen a Supabase Storage"
MSG_URL_IMAGEN_NO_VALIDA = "URL de imagen no válida para eliminación"
MSG_ERROR_ELIMINAR_FOTO_BUCKET = "Error al eliminar la foto de perfil del bucket"
MSG_FOTO_ELIMINADA_EXITOSA = "Foto de perfil eliminada exitosamente del bucket de Supabase Storage."
MSG_CUENTA_INACTIVA = "Tu cuenta está inactiva. Por favor, contacta al administrador en b2bseva.notificaciones@gmail.com para más detalles."
MSG_LIMITE_ENVIO_EMAILS_REGISTRO = "Has alcanzado el límite de envío de emails. Por favor, espera 1 hora antes de intentar registrarte nuevamente. Si necesitas ayuda inmediata, contacta a b2bseva.notificaciones@gmail.com"
MSG_LIMITE_ENVIO_EMAILS_CONFIRMACION = "Has alcanzado el límite de envío de emails. Por favor, espera 1 hora antes de solicitar un nuevo correo de confirmación. Si necesitas ayuda inmediata, contacta a b2bseva.notificaciones@gmail.com"
MSG_ERROR_ENVIAR_EMAIL_CONFIRMACION = "No se pudo enviar el email de confirmación. El usuario puede haberse creado correctamente. Por favor, intenta iniciar sesión o contacta al administrador en b2bseva.notificaciones@gmail.com si el problema persiste."
MSG_ERROR_CREAR_USUARIO_EMAIL = "No se pudo crear el usuario ni enviar el email de confirmación debido a un problema con la configuración de email del servidor. Por favor, intenta nuevamente más tarde o contacta al administrador en b2bseva.notificaciones@gmail.com"
MSG_ERROR_CREAR_USUARIO = "No se pudo crear el usuario. Por favor, intenta nuevamente o contacta al administrador en b2bseva.notificaciones@gmail.com"
MSG_CONTACTO_ADMIN = f"Para ayuda inmediata: {EMAIL_ADMIN}"  # Se mantiene f-string porque se usa directamente

# --- Endpoints de autenticación ---

# Funciones helper para sign_up
def check_rate_limit(email: str) -> None:
    """Verifica el rate limit antes de proceder con el registro"""
    if not email_rate_limit_service.can_send_email(email):
        remaining_attempts = email_rate_limit_service.get_remaining_attempts(email)
        next_attempt_time = email_rate_limit_service.get_next_attempt_time(email)
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Has alcanzado el límite de intentos de registro. Intentos restantes: {remaining_attempts}. Próximo intento disponible: {next_attempt_time.strftime('%H:%M') if next_attempt_time else 'N/A'}. Contacta a {EMAIL_ADMIN} para ayuda inmediata."
        )

def build_signup_data(data: SignUpIn) -> dict:
    """Construye los datos para el signup en Supabase Auth"""
    return {
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

def create_user_in_supabase(signup_data: dict) -> tuple[Any, str, bool]:
    """Crea el usuario en Supabase Auth y retorna la respuesta, id_user y si hubo error de email
    
    Nota: Esta función es síncrona porque supabase_auth.auth.sign_up() es una llamada síncrona.
    """
    signup_response = None
    id_user = None
    email_sent_error = False
    
    try:
        signup_response = supabase_auth.auth.sign_up(signup_data)
        
        if not signup_response.user:
            handle_supabase_auth_error("Respuesta de Supabase incompleta (no hay user)")
        
        id_user = str(signup_response.user.id)
        logger.info(f"Usuario creado en Supabase Auth con ID: {id_user}")
        
        return signup_response, id_user, email_sent_error
        
    except AuthApiError as e:
        error_message = str(e).lower()
        
        # Si es error de envío de email, verificar si el usuario se creó
        if ERROR_SENDING_CONFIRMATION_EMAIL in error_message:
            logger.warning("⚠️ Error al enviar email de confirmación, verificando si el usuario se creó...")
            email_sent_error = True
            
            id_user = verify_user_created_despite_email_error(signup_data["email"])
            return signup_response, id_user, email_sent_error
        else:
            # Otro tipo de error de AuthApiError, re-lanzar para manejo general
            raise

# Funciones helper para verify_user_created_despite_email_error
def verify_supabase_admin_configured() -> bool:
    """Verifica si supabase_admin está configurado"""
    if not supabase_admin:
        logger.error("❌ No se puede verificar usuario: supabase_admin no está configurado")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_ENVIAR_EMAIL_CONFIRMACION
        )
    return True

def find_user_by_email(auth_users, email: str):
    """Busca un usuario por email en la lista de usuarios"""
    if not auth_users:
        return None
    
    email_lower = email.lower()
    for auth_user in auth_users:
        if auth_user.email and auth_user.email.lower() == email_lower:
            return auth_user
    return None

def process_found_user(found_user) -> str:
    """Procesa un usuario encontrado y retorna su ID"""
    id_user = str(found_user.id)
    logger.info(f"✅ Usuario encontrado a pesar del error de email: {id_user}")
    logger.warning("⚠️ El usuario se creó correctamente, pero no se pudo enviar el email de confirmación")
    return id_user

def handle_user_not_found():
    """Maneja el caso cuando el usuario no se encuentra"""
    logger.error("❌ Usuario no encontrado después del error de email")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=MSG_ERROR_CREAR_USUARIO_EMAIL
    )

def verify_user_created_despite_email_error(email: str) -> str:
    """Verifica si el usuario se creó a pesar del error de email"""
    try:
        # Verificar que supabase_admin esté configurado
        verify_supabase_admin_configured()
        
        # Obtener todos los usuarios y buscar por email
        auth_users = supabase_admin.auth.admin.list_users()
        
        # Buscar el usuario por email
        found_user = find_user_by_email(auth_users, email)
        
        if found_user:
            return process_found_user(found_user)
        else:
            handle_user_not_found()
            
    except HTTPException:
        raise
    except Exception as verify_error:
        logger.error(f"❌ Error verificando usuario después del error de email: {verify_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo enviar el email de confirmación. El usuario puede haberse creado correctamente. Por favor, intenta iniciar sesión o contacta al administrador en b2bseva.notificaciones@gmail.com si el problema persiste."
        )

async def verify_user_profile_with_retries(id_user: str, max_retries: int = 3, retry_delay: float = 0.5) -> Optional[dict]:
    """Verifica el perfil del usuario con reintentos"""
    logger.info("⏳ Esperando que el trigger se ejecute...")
    await asyncio.sleep(1.0)  # Dar tiempo al trigger
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Verificando perfil para usuario {id_user} (intento {attempt + 1}/{max_retries})")
            
            user_profile_data = await direct_db_service.check_user_profile(id_user)
            
            if user_profile_data:
                logger.info(f"✅ Perfil encontrado en intento {attempt + 1}")
                return user_profile_data
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
            await asyncio.sleep(retry_delay * (1.2 ** attempt))
            logger.info(f"⏳ Esperando {retry_delay * (1.2 ** attempt):.1f}s antes del siguiente intento...")
    
    return None

async def create_user_profile_manually(id_user: str, data: SignUpIn) -> dict:
    """Crea el perfil del usuario manualmente si el trigger no lo hizo"""
    logger.warning("⚠️ Trigger no creó el perfil, creando manualmente...")
    
    try:
        await direct_db_service.create_user_profile(
            user_id=id_user,
            nombre_persona=data.nombre_persona,
            nombre_empresa=data.nombre_empresa,
            ruc=data.ruc
        )
        
        logger.info("✅ Perfil creado manualmente")
        return {
            "id": id_user,
            "nombre_persona": data.nombre_persona,
            "nombre_empresa": data.nombre_empresa,
            "ruc": data.ruc,
            "estado": ESTADO_ACTIVO
        }
        
    except Exception as e:
        logger.error(f"❌ Error creando perfil manualmente: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error: No se pudo crear el perfil del usuario. Error: {str(e)}"
        )

def build_signup_success_response(data: SignUpIn, email_sent_error: bool) -> SignUpSuccess:
    """Construye la respuesta de éxito del signup"""
    message = "¡Registro exitoso! 📧 "
    if email_sent_error:
        message += f"⚠️ No se pudo enviar el correo de confirmación automáticamente. Por favor, intenta iniciar sesión con tus credenciales. Si tienes problemas, contacta a {EMAIL_ADMIN} para ayuda."
    else:
        message += "Hemos enviado un correo de confirmación a tu dirección de email. Por favor, revisa tu bandeja de entrada y haz clic en el enlace para activar tu cuenta. Si no encuentras el correo, revisa también tu carpeta de spam."
    
    return SignUpSuccess(
        message=message,
        email=data.email,
        nombre_persona=data.nombre_persona,
        nombre_empresa=data.nombre_empresa,
        ruc=data.ruc,
        instructions="1. Revisa tu bandeja de entrada\n2. Busca el correo de confirmación\n3. Haz clic en el enlace del correo\n4. Si no encuentras el correo, revisa la carpeta de spam" if not email_sent_error else f"1. Intenta iniciar sesión con tus credenciales\n2. Si tienes problemas, contacta a {EMAIL_ADMIN}",
        next_steps="Una vez confirmado tu email, podrás iniciar sesión en la plataforma" if not email_sent_error else "Intenta iniciar sesión ahora mismo con tus credenciales"
    )

def build_token_response(signup_response: Any) -> dict:
    """Construye la respuesta con el token"""
    return {
        "access_token": signup_response.session.access_token,
        "expires_in": signup_response.session.expires_in,
        "token_type": TOKEN_TYPE_BEARER
    }

def configure_refresh_token_cookie(response: JSONResponse, refresh_token: str) -> None:
    """Configura la cookie de refresh token"""
    logger.info(f"🍪 Estableciendo cookie refresh_token: {refresh_token[:20]}...")
    
    # Detectar entorno para configurar cookies
    is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    response.set_cookie(
        key=COOKIE_REFRESH_TOKEN, 
        value=refresh_token,
        httponly=True,
        secure=is_production,  # True en producción (HTTPS), False en desarrollo (HTTP)
        samesite=COOKIE_SAMESITE_LAX,
        max_age=7 * 24 * 60 * 60,  # 7 días
        path="/",
        domain=None if is_production else DOMAIN_LOCALHOST  # None en producción, "localhost" en desarrollo
    )
    
    logger.info("✅ Cookies HttpOnly establecidas correctamente")

@router.post(
    "/signup",
    response_model=Union[TokenOut, SignUpSuccess],
    status_code=status.HTTP_201_CREATED,
    description="Crea un usuario en Supabase Auth. El perfil y rol se crean automáticamente via trigger."
)
async def sign_up(data: SignUpIn) -> Union[TokenOut, SignUpSuccess]:
    try:
        logger.info(f"Iniciando registro para usuario: {data.email}")
        
        # Verificar rate limit antes de proceder
        check_rate_limit(data.email)
        
        # Construir datos de signup
        signup_data = build_signup_data(data)
        logger.info(f"Enviando datos a Supabase Auth: {signup_data}")
        
        # Crear usuario en Supabase Auth
        signup_response, id_user, email_sent_error = create_user_in_supabase(signup_data)
        
        # Validar que id_user existe antes de continuar
        if not id_user:
            logger.error("❌ No se pudo crear el usuario: id_user es None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=MSG_ERROR_CREAR_USUARIO
            )
        
        # Registrar intento de envío de email (solo si no hubo error)
        if not email_sent_error:
            email_rate_limit_service.record_email_attempt(data.email)

        # Verificar perfil del usuario con reintentos
        user_profile = await verify_user_profile_with_retries(id_user)
        
        # Si no se encontró el perfil, crear manualmente
        if not user_profile:
            user_profile = await create_user_profile_manually(id_user, data)
        
        # Confiar en el trigger para el rol
        logger.info("✅ Perfil verificado. El trigger asignará el rol automáticamente.")
        logger.info("💡 No verificamos el rol para evitar bloquear el trigger.")
        logger.info(f"Registro completado exitosamente para usuario: {id_user}")

        # Manejo de confirmación de email
        if email_sent_error or not signup_response or not signup_response.session:
            return build_signup_success_response(data, email_sent_error)

        # Crear respuesta con token
        token_data = build_token_response(signup_response)
        response = JSONResponse(content=token_data)
        
        # Configurar cookie de refresh token
        configure_refresh_token_cookie(response, signup_response.session.refresh_token)

        return response

    except AuthApiError as e:
        logger.error(f"Error de Supabase Auth: {e}")
        error_message = str(e).lower()
        
        # Manejar específicamente el rate limit de emails
        if ERROR_EMAIL_RATE_LIMIT in error_message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=MSG_LIMITE_ENVIO_EMAILS_REGISTRO
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


# Funciones helper para sign_in
async def verify_user_status_in_db(email: str) -> tuple[Optional[str], Optional[str]]:
    """Verifica el estado del usuario en la base de datos"""
    try:
        print("🔍 Obteniendo conexión de la base de datos...")
        
        # Usar direct_db_service para evitar problemas con PgBouncer
        conn = await direct_db_service.get_connection()
        print("🔍 Conexión obtenida, ejecutando consulta...")
        try:
            # Consulta simplificada para evitar problemas de rendimiento
            user_result = await conn.fetchrow("""
                SELECT u.id, u.estado 
                FROM users u 
                JOIN auth.users au ON u.id = au.id 
                WHERE au.email = $1
            """, email)
            print(f"🔍 Consulta ejecutada, resultado: {user_result}")

            if user_result:
                user_id = str(user_result['id'])
                user_estado = user_result['estado']
                print(f"🔍 Usuario encontrado: ID={user_id}, Estado={user_estado}")

                # Verificar estado del usuario ANTES de autenticar
                if user_estado != ESTADO_ACTIVO:
                    print(f"🚫 Usuario {user_id} tiene estado {user_estado} - DENEGANDO ACCESO")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=MSG_CUENTA_INACTIVA
                    )
                return user_id, user_estado
            else:
                print(f"⚠️ Usuario con email {email} no encontrado en tabla users")
                return None, None
        finally:
            await direct_db_service.pool.release(conn)

    except HTTPException:
        raise  # Re-lanzar HTTPException para mantener el comportamiento
    except Exception as db_error:
        print(f"⚠️ Error consultando base de datos: {str(db_error)}")
        # Si hay error en la consulta, permitir continuar (fallback)
        return None, None

def authenticate_with_supabase(email: str, password: str) -> Any:
    """Autentica el usuario en Supabase Auth"""
    print("✅ Estado verificado, procediendo con autenticación en Supabase")
    print(f"🔍 Llamando a Supabase Auth con email: {email}")
    signin_response = supabase_auth.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    print(f"🔍 Respuesta de Supabase recibida: {signin_response}")
    
    if signin_response.user is None or not signin_response.session:
        handle_supabase_auth_error(MSG_SUPABASE_RESPONSE_INCOMPLETE)
    
    return signin_response

def verify_user_status_after_auth(user_id: Optional[str], user_estado: Optional[str]) -> None:
    """Verificación adicional del estado del usuario después de la autenticación"""
    if user_id and user_estado and user_estado != ESTADO_ACTIVO:
        # Si por alguna razón llega aquí, invalidar la sesión inmediatamente
        try:
            supabase_auth.auth.sign_out()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MSG_CUENTA_INACTIVA
        )

def build_signin_token_response(signin_response: Any) -> dict:
    """Construye la respuesta con el token de signin"""
    return {
        "access_token": signin_response.session.access_token,
        "expires_in": signin_response.session.expires_in,
        "token_type": TOKEN_TYPE_BEARER
    }

def build_signin_response(signin_response: Any) -> JSONResponse:
    """Construye la respuesta completa de signin con cookies"""
    token_data = build_signin_token_response(signin_response)
    response = JSONResponse(content=token_data)
    
    # Configurar cookie de refresh token
    print(f"🍪 Estableciendo cookie refresh_token: {signin_response.session.refresh_token[:20]}...")
    configure_refresh_token_cookie(response, signin_response.session.refresh_token)
    print("✅ Cookies HttpOnly establecidas correctamente")
    
    return response

@router.post("/signin", response_model=TokenOut,
            status_code=status.HTTP_200_OK,
            description="Autentica un usuario con email y contraseña y devuelve sus tokens de acceso y refresh.")
async def sign_in(data: SignInIn, db: AsyncSession = Depends(get_async_db)) -> JSONResponse:
    """
    Autentica un usuario con email y contraseña y devuelve sus tokens.
    """
    try:
        print(f"🔍 LOGIN ENDPOINT INICIADO - Email: {data.email}")
        
        # Verificar estado del usuario en la base de datos
        user_id, user_estado = await verify_user_status_in_db(data.email)
        
        # Autenticación en Supabase Auth
        signin_response = authenticate_with_supabase(data.email, data.password)
        
        # Verificación adicional del estado (doble verificación)
        verify_user_status_after_auth(user_id, user_estado)

        # Construir y retornar respuesta
        return build_signin_response(signin_response)

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
            detail=MSG_PERFIL_USUARIO_NO_ENCONTRADO
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
            "type": TYPE_SIGNUP,
            "email": data.email
        })
        
        return {
            "message": f"📧 Se ha enviado un nuevo correo de confirmación a {data.email}. Por favor, revisa tu bandeja de entrada y haz clic en el enlace para activar tu cuenta. Si no encuentras el correo, revisa también tu carpeta de spam.",
            "email": data.email,
            "instructions": "1. Revisa tu bandeja de entrada\n2. Busca el correo de confirmación\n3. Haz clic en el enlace del correo\n4. Si no encuentras el correo, revisa la carpeta de spam"
        }

    except AuthApiError as e:
        # Manejar específicamente el rate limit de emails
        if ERROR_EMAIL_RATE_LIMIT in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=MSG_LIMITE_ENVIO_EMAILS_CONFIRMACION
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
                detail=MSG_USUARIO_NO_ENCONTRADO
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
        "contact": MSG_CONTACTO_ADMIN
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

#ACTUALMENTE NO SE USA   
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
        #response = supabase_auth.auth.reset_password_for_email(data.email)
        
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
                    "estado": ESTADO_NONE,
                    "mensaje": MSG_NO_ENCONTRADO_PERFIL_EMPRESA
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
                    "estado": ESTADO_NONE,
                    "mensaje": MSG_NO_ENCONTRADA_SOLICITUD_VERIFICACION
                }
            
            # Mapear el estado de la base de datos al estado del frontend
            estado_mapping = {
                ESTADO_PENDIENTE: ESTADO_PENDING,
                ESTADO_APROBADA: ESTADO_APPROVED, 
                ESTADO_RECHAZADA: ESTADO_REJECTED
            }
            
            estado_frontend = estado_mapping.get(solicitud_result['estado'], ESTADO_NONE)
        
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
                detail=MSG_USUARIO_NO_ENCONTRADO
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
                detail=MSG_ARCHIVO_DEBE_SER_IMAGEN
            )
        
        # Validar extensiones permitidas
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_SOLO_PERMITEN_ARCHIVOS_IMAGEN
            )
        
        # Validar tamaño (5MB máximo)
        file_content = await file.read()
        if len(file_content) > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_ARCHIVO_SUPERA_TAMANO
            )
        
        
        # Subir imagen a Supabase Storage en la carpeta perfiles/
        success, public_url = await supabase_storage_service.upload_profile_image(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type
        )
        
        if not success or not public_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=MSG_ERROR_SUBIR_IMAGEN_STORAGE
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
        
        # Verificar que la URL es de Supabase Storage
        if not image_url or not image_url.startswith('https://') or 'supabase.co' not in image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_URL_IMAGEN_NO_VALIDA
            )
        
        # Extraer el nombre del archivo de la URL
        file_name = os.path.basename(image_url.split('?')[0])  # Remover query parameters
        
        # Eliminar imagen del bucket
        success = await supabase_storage_service.delete_image(image_url)
        
        if success:
            print(f"✅ Foto de perfil eliminada exitosamente del bucket: {file_name}")
            return {
                "message": MSG_FOTO_ELIMINADA_EXITOSA,
                "deleted_file": file_name
            }
        else:
            print(f"❌ Error eliminando foto de perfil del bucket: {file_name}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=MSG_ERROR_ELIMINAR_FOTO_BUCKET
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en delete_profile_photo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la foto de perfil: {str(e)}"
        )


# Constantes para mensajes de error
MSG_NO_ENCONTRADO_PERFIL_EMPRESA = "No se encontró perfil de empresa para este usuario"
MSG_NO_ENCONTRADA_SOLICITUD_VERIFICACION = "No se encontró solicitud de verificación"

# Funciones helper para get_verificacion_datos
async def get_empresa_profile(user_id: str) -> dict:
    """
    Obtiene el perfil de empresa del usuario.
    Usa direct_db_service para evitar problemas con PgBouncer.
    Retorna un diccionario con los datos de la empresa.
    """
    conn = None
    try:
        conn = await direct_db_service.get_connection()
        
        empresa_query = """
            SELECT 
                pe.id_perfil,
                pe.razon_social,
                pe.nombre_fantasia,
                pe.estado,
                pe.verificado,
                pe.fecha_inicio,
                pe.fecha_fin,
                pe.id_direccion,
                pe.user_id
            FROM perfil_empresa pe
            WHERE pe.user_id = $1
            LIMIT 1
        """
        empresa_row = await conn.fetchrow(empresa_query, user_id)
        
        if not empresa_row:
            print(f"⚠️ No se encontró perfil de empresa para usuario {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_NO_ENCONTRADO_PERFIL_EMPRESA
            )
        
        empresa_dict = dict(empresa_row)
        print(f"✅ Empresa encontrada: {empresa_dict['razon_social']}")
        return empresa_dict
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_latest_verification_request(id_perfil: int) -> Optional[dict]:
    """
    Obtiene la solicitud de verificación más reciente.
    Usa direct_db_service para evitar problemas con PgBouncer.
    Retorna un diccionario con los datos de la solicitud o None si no existe.
    """
    conn = None
    try:
        conn = await direct_db_service.get_connection()
        
        solicitud_query = """
            SELECT 
                id_verificacion,
                id_perfil,
                estado,
                fecha_solicitud,
                fecha_revision,
                comentario,
                created_at
            FROM verificacion_solicitud
            WHERE id_perfil = $1
            ORDER BY created_at DESC
            LIMIT 1
        """
        solicitud_row = await conn.fetchrow(solicitud_query, id_perfil)
        
        if not solicitud_row:
            print(f"⚠️ No se encontró solicitud de verificación para perfil {id_perfil}")
            return None
        
        solicitud_dict = dict(solicitud_row)
        print(f"✅ Solicitud encontrada: {solicitud_dict['estado']}")
        return solicitud_dict
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_direccion_data(id_direccion: Optional[int]) -> Optional[dict]:
    """
    Obtiene los datos de dirección.
    Usa direct_db_service para evitar problemas con PgBouncer.
    """
    if not id_direccion:
        return None
    
    conn = None
    try:
        conn = await direct_db_service.get_connection()
        
        direccion_query = """
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
            WHERE d.id_direccion = $1
        """
        
        direccion_row = await conn.fetchrow(direccion_query, id_direccion)
        
        if not direccion_row:
            return None
        
        return dict(direccion_row)
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_sucursal_data(id_perfil: int) -> Optional[dict]:
    """
    Obtiene los datos de la sucursal principal.
    Usa direct_db_service para evitar problemas con PgBouncer.
    """
    conn = None
    try:
        conn = await direct_db_service.get_connection()
        
        sucursal_query = """
            SELECT nombre, telefono, email
            FROM sucursal_empresa
            WHERE id_perfil = $1
            ORDER BY created_at ASC
            LIMIT 1
        """
        sucursal_row = await conn.fetchrow(sucursal_query, id_perfil)
        
        if not sucursal_row:
            print("⚠️ No se encontraron sucursales para esta empresa")
            return None
        
        sucursal_data = dict(sucursal_row)
        print(f"✅ Sucursal encontrada: {sucursal_data['nombre']}")
        print(f"✅ Datos de sucursal: {sucursal_data}")
        return sucursal_data
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_documentos_data(id_verificacion: int) -> list[dict]:
    """
    Obtiene los documentos de la solicitud de verificación.
    Usa direct_db_service para evitar problemas con PgBouncer.
    """
    conn = None
    try:
        conn = await direct_db_service.get_connection()
        
        documentos_query = """
            SELECT 
                d.id_documento,
                d.id_verificacion,
                d.id_tip_documento,
                d.estado_revision,
                d.url_archivo,
                d.fecha_verificacion,
                d.observacion,
                d.created_at,
                td.nombre as tipo_documento_nombre,
                td.es_requerido
            FROM documento d
            LEFT JOIN tipo_documento td ON d.id_tip_documento = td.id_tip_documento
            WHERE d.id_verificacion = $1
            ORDER BY d.created_at ASC
        """
        documentos_rows = await conn.fetch(documentos_query, id_verificacion)
        
        documentos_data = []
        for row in documentos_rows:
            tipo_doc_nombre = row['tipo_documento_nombre'] if row['tipo_documento_nombre'] else f"Tipo {row['id_tip_documento']}"
            es_requerido = row['es_requerido'] if row['es_requerido'] is not None else False
            documentos_data.append({
                "id_documento": row['id_documento'],
                "tipo_documento": tipo_doc_nombre,
                "es_requerido": es_requerido,
                "estado_revision": row['estado_revision'],
                "url_archivo": row['url_archivo'],
                "fecha_verificacion": row['fecha_verificacion'],
                "observacion": row['observacion'],
                "created_at": row['created_at']
            })
        
        return documentos_data
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

def build_empresa_dict(empresa: dict, direccion_data: Optional[dict], sucursal_data: Optional[dict]) -> dict:
    """Construye el diccionario de datos de empresa"""
    return {
        "razon_social": empresa["razon_social"],
        "nombre_fantasia": empresa["nombre_fantasia"],
        "ruc": "",  # No existe en PerfilEmpresa
        "direccion": direccion_data["calle"] + " " + direccion_data["numero"] if direccion_data and direccion_data.get("calle") and direccion_data.get("numero") else "",
        "referencia": direccion_data["referencia"] if direccion_data else "",
        "departamento": direccion_data["departamento"] if direccion_data else None,
        "ciudad": direccion_data["ciudad"] if direccion_data else None,
        "barrio": direccion_data["barrio"] if direccion_data else None,
        "telefono": sucursal_data["telefono"] if sucursal_data else "",
        "email": sucursal_data["email"] if sucursal_data else "",
        "sitio_web": "",  # No existe en PerfilEmpresa
        "descripcion": "",  # No existe en PerfilEmpresa
        "categoria_empresa": "",  # No existe en PerfilEmpresa
        "estado": empresa["estado"],
        "verificado": empresa["verificado"],
        "fecha_inicio": empresa["fecha_inicio"],
        "fecha_fin": empresa["fecha_fin"],
        # Agregar datos de sucursal
        "telefono_contacto": sucursal_data["telefono"] if sucursal_data else None,
        "email_contacto": sucursal_data["email"] if sucursal_data else None,
        "nombre_sucursal": sucursal_data["nombre"] if sucursal_data else None
    }

def build_solicitud_dict(solicitud: Optional[dict]) -> dict:
    """Construye el diccionario de datos de solicitud"""
    if not solicitud:
        return {
            "id_verificacion": None,
            "estado": None,
            "fecha_solicitud": None,
            "fecha_revision": None,
            "comentario": None,
            "created_at": None
        }
    return {
        "id_verificacion": solicitud["id_verificacion"],
        "estado": solicitud["estado"],
        "fecha_solicitud": solicitud["fecha_solicitud"],
        "fecha_revision": solicitud["fecha_revision"],
        "comentario": solicitud["comentario"],
        "created_at": solicitud["created_at"]
    }

def build_verificacion_response(empresa_dict: dict, solicitud_dict: dict, documentos_data: list[dict]) -> dict:
    """Construye la respuesta completa de verificación"""
    return {
        "success": True,
        "empresa": empresa_dict,
        "solicitud": solicitud_dict,
        "documentos": documentos_data
    }

@router.get(
    "/verificacion-datos",
    description="Obtiene los datos completos de verificación del usuario autenticado, incluyendo empresa, sucursal, dirección y documentos."
)
async def get_verificacion_datos(
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Obtiene los datos completos de verificación del usuario autenticado.
    Usa direct_db_service para evitar problemas con PgBouncer.
    """
    try:
        print(f"🔍 Obteniendo datos de verificación para usuario: {current_user.id}")
        
        # Obtener perfil de empresa
        empresa = await get_empresa_profile(current_user.id)
        
        # Obtener solicitud de verificación más reciente (puede ser None)
        solicitud = await get_latest_verification_request(empresa["id_perfil"])
        
        # Obtener datos de dirección
        direccion_data = await get_direccion_data(empresa.get("id_direccion"))
        
        # Obtener datos de sucursal
        sucursal_data = await get_sucursal_data(empresa["id_perfil"])
        
        # Obtener documentos (solo si hay solicitud)
        documentos_data = []
        if solicitud:
            documentos_data = await get_documentos_data(solicitud["id_verificacion"])
        
        # Construir diccionarios de respuesta
        empresa_dict = build_empresa_dict(empresa, direccion_data, sucursal_data)
        solicitud_dict = build_solicitud_dict(solicitud) if solicitud else {}
        response_data = build_verificacion_response(empresa_dict, solicitud_dict, documentos_data)
        
        print(f"✅ Datos de verificación preparados para usuario {current_user.id}")
        print(f"  - Empresa: {empresa['razon_social']}")
        print(f"  - Sucursal: {sucursal_data['nombre'] if sucursal_data else 'No encontrada'}")
        print(f"  - Documentos: {len(documentos_data)}")
        print("🔍 Datos de empresa_dict que se enviarán:")
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
            detail=MSG_ERROR_INTERNO_SERVIDOR
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
        
        # Buscar el perfil de empresa del usuario
        empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            return {
                "error": MSG_NO_ENCONTRADO_PERFIL_EMPRESA,
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
