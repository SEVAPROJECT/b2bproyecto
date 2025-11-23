#logica de autenticacion/validacion de token (jwt, auth0, etc)
#una dependencia para validar el token JWT en cada request
from fastapi import Depends, HTTPException, status, Request
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

# Dependencia para validar el token JWT desde cookies o headers
def get_current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
    ) -> SupabaseUser:
    """
    Dependencia que valida el token JWT desde cookies o headers y retorna los datos del usuario autenticado.
    """
    # Intentar obtener token desde cookies primero
    token = request.cookies.get("access_token")
    print(f"🍪 Token desde cookies: {token[:20] + '...' if token else 'None'}")
    
    # Si no hay token en cookies, usar el token del header
    if not token and credentials:
        token = credentials.credentials
        print(f"🔑 Token desde header: {token[:20] + '...' if token else 'None'}")
    
    if not token:
        print("❌ No se encontró token en cookies ni headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó un token de autorización"
        )
    

    try:
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
    current_user: SupabaseUser = Depends(get_current_user)
) -> UserProfileAndRolesOut:
    """
    Dependencia que asegura que el usuario autenticado es un administrador.
    Usa DirectDBService para evitar problemas con prepared statements.
    """
    try:
        print(f"🔍 DEBUG: get_admin_user iniciado para usuario: {current_user.id}")
        print(f"🔍 DEBUG: Email del usuario: {current_user.email}")
        
        # Usar DirectDBService para evitar problemas con prepared statements
        from app.services.direct_db_service import direct_db_service
        
        print(f"🔍 DEBUG: Convirtiendo ID a UUID: {current_user.id}")
        user_uuid = str(current_user.id)
        print(f"🔍 DEBUG: UUID convertido: {user_uuid}")
        print("🔍 DEBUG: Ejecutando consulta de base de datos...")
        
        # Obtener perfil con roles usando DirectDBService
        user_data = await direct_db_service.get_user_profile_with_roles(user_uuid)
        print(f"🔍 DEBUG: Perfil encontrado: {user_data is not None}")
        
        if not user_data:
            print(f"❌ DEBUG: Perfil de usuario no encontrado para UUID: {user_uuid}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Perfil de usuario no encontrado"
            )
        
        # Extraer los nombres de los roles
        roles_data = user_data.get('roles', [])
        roles_nombres = [rol.get('nombre') for rol in roles_data if rol.get('nombre')]
        print(f"🔍 DEBUG: Roles encontrados: {roles_nombres}")
        
        # Verificar si tiene rol de admin (solución para mayúsculas/minúsculas)
        roles_lower = [rol.lower() for rol in roles_nombres]
        print(f"🔍 DEBUG: Roles en minúsculas: {roles_lower}")
        
        if "admin" not in roles_lower and "administrador" not in roles_lower:
            print("❌ DEBUG: Usuario no tiene permisos de administrador")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos de administrador"
            )
        
        print("✅ DEBUG: Usuario administrador validado exitosamente")
        return UserProfileAndRolesOut(
            id=user_data['id'],
            email=current_user.email,
            nombre_persona=user_data.get('nombre_persona', ''),
            nombre_empresa=user_data.get('nombre_empresa', ''),
            roles=roles_nombres
        )
        
    except Exception as e:
        print(f"❌ DEBUG: Error en get_admin_user: {str(e)}")
        import traceback
        print("Traceback completo:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validando administrador: {str(e)}"
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