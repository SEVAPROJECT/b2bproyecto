#logica de autenticacion/validacion de token (jwt, auth0, etc)
#una dependencia para validar el token JWT en cada request
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import AuthApiError
from app.schemas.user import UserProfileAndRolesOut
from app.supabase.auth_service import supabase_auth  # Importa el cliente Supabase inicializado
from app.schemas.auth_user import SupabaseUser  # 
from gotrue.types import User  # Importa el tipo User de gotrue
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.empresa.perfil_empresa import PerfilEmpresa
import logging
import uuid

# Configurar logging
logger = logging.getLogger(__name__)

security = HTTPBearer()

# Dependencia para validar el token JWT y obtener los datos del usuario autenticado
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> SupabaseUser:
    """
    Dependencia que valida el token JWT y retorna los datos del usuario autenticado.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó un token de autorización"
        )
    token = credentials.credentials
    #user_data = supabase_auth.auth.get_user(token).get("data")

    # Manejando el objeto UserResponse en lugar de un diccionario

    '''if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

    return SupabaseUser(
        id=user_data.get("id"),
        email=user_data.get("email")
    )'''

    try:
        # Verificar si Supabase está configurado
        if not supabase_auth:
            logger.warning("⚠️ Supabase no configurado - autenticación no disponible")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de autenticación no disponible. Supabase no está configurado."
            )
        
        logger.info(f"🔍 Validando token: {token[:20]}...")
        
        # Obtenemos la respuesta completa del cliente de Supabase
        user_response = supabase_auth.auth.get_user(token)
        logger.info(f"🔍 Respuesta de Supabase recibida: {user_response}")
        
        # Accedemos al objeto 'user' que está anidado en la respuesta
        user_data = user_response.user
        logger.info(f"🔍 Datos de usuario: {user_data}")
        
        if not user_data:
            # Si no hay datos de usuario, es un token inválido
            logger.error("❌ No se encontraron datos de usuario en la respuesta")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )

        # Si el usuario es válido, creamos y devolvemos nuestro esquema Pydantic
        logger.info(f"✅ Usuario autenticado exitosamente: {user_data.email}")
        return SupabaseUser(
            id=user_data.id,
            email=user_data.email
        )
    except AuthApiError as e:
        # Capturamos la excepción específica de la librería para un token inválido
        logger.error(f"❌ Error de autenticación de Supabase: {e}")

        # Si es un error de token expirado, dar mensaje más específico
        error_msg = str(e).lower()
        if "expired" in error_msg or "invalid" in error_msg:
            logger.warning("⚠️ Token expirado detectado - puede requerir renovación")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado. Por favor, refresca la página e inicia sesión nuevamente."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: {str(e)}"
            )
    except Exception as e:
        # Captura cualquier otra excepción inesperada
        logger.error(f"❌ Error inesperado al validar el token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al validar el token: {str(e)}"
        )
    

async def get_admin_user(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> UserProfileAndRolesOut:
    """
    Dependencia que asegura que el usuario autenticado es un administrador.
    """
    from app.models.perfil import UserModel
    from app.models.usuario_rol import UsuarioRolModel
    from app.models.rol import RolModel
    from sqlalchemy.orm import joinedload
    import uuid
    
    # Obtener el perfil del usuario con sus roles
    user_uuid = uuid.UUID(current_user.id)
    result_profile = await db.execute(
        select(UserModel)
        .options(
            joinedload(UserModel.roles).joinedload(UsuarioRolModel.rol)
        )
        .where(UserModel.id == user_uuid)
    )
    
    user_profile = result_profile.scalars().first()
    
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Perfil de usuario no encontrado"
        )
    
    # Extraer los nombres de los roles
    roles_nombres = [rol_asociado.rol.nombre for rol_asociado in user_profile.roles]
    
    # Verificar si tiene rol de admin (solución para mayúsculas/minúsculas)
    roles_lower = [rol.lower() for rol in roles_nombres]
    if "admin" not in roles_lower and "administrador" not in roles_lower:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    
    return UserProfileAndRolesOut(
        id=user_profile.id,
        email=current_user.email,
        nombre_persona=user_profile.nombre_persona,
        nombre_empresa=user_profile.nombre_empresa,
        roles=roles_nombres
    )

async def get_approved_provider(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Dependencia que verifica si el usuario autenticado es un proveedor aprobado.
    """
    try:
        query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        perfil = await db.execute(query)
        perfil_empresa = perfil.scalars().first()

        if not perfil_empresa or not perfil_empresa.verificado:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes un perfil de proveedor aprobado para publicar servicios."
            )

        return perfil_empresa
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar el estado del proveedor: {str(e)}"
        )