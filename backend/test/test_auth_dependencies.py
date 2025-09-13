#!/usr/bin/env python3
"""
Pruebas unitarias para las dependencias de autenticación
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# Importar las dependencias a probar
from app.api.v1.dependencies.auth_user import get_current_user, get_admin_user
from app.schemas.auth_user import SupabaseUser
from app.schemas.user import UserProfileAndRolesOut
from app.models.perfil import UserModel
from app.models.rol import RolModel
from app.models.usuario_rol import UsuarioRolModel


class TestGetCurrentUser:
    """Pruebas para la dependencia get_current_user"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock para las credenciales HTTP"""
        mock_creds = Mock()
        mock_creds.credentials = "valid_jwt_token"
        return mock_creds
    
    @pytest.fixture
    def mock_supabase_auth(self):
        """Mock para el cliente de Supabase Auth"""
        with patch('app.api.v1.dependencies.auth_user.supabase_auth') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_credentials, mock_supabase_auth):
        """Prueba obtención exitosa del usuario actual"""
        # Configurar mock de Supabase
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.email = "test@example.com"
        
        mock_response = Mock()
        mock_response.user = mock_user
        
        mock_supabase_auth.auth.get_user.return_value = mock_response
        
        # Ejecutar dependencia
        result = await get_current_user(mock_credentials)
        
        # Verificar resultado
        assert isinstance(result, SupabaseUser)
        assert result.id == mock_user.id
        assert result.email == mock_user.email
        
        # Verificar que se llamó a Supabase
        mock_supabase_auth.auth.get_user.assert_called_once_with("valid_jwt_token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Prueba sin credenciales"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)
        
        assert exc_info.value.status_code == 401
        assert "No se proporcionó un token de autorización" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_credentials, mock_supabase_auth):
        """Prueba con token inválido"""
        from supabase import AuthApiError
        
        # Configurar mock para lanzar error
        mock_supabase_auth.auth.get_user.side_effect = AuthApiError("Invalid token")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "Token inválido o expirado" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_user_data(self, mock_credentials, mock_supabase_auth):
        """Prueba cuando Supabase no devuelve datos de usuario"""
        # Configurar mock sin datos de usuario
        mock_response = Mock()
        mock_response.user = None
        
        mock_supabase_auth.auth.get_user.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "Token inválido o expirado" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_unexpected_error(self, mock_credentials, mock_supabase_auth):
        """Prueba error inesperado"""
        # Configurar mock para lanzar error inesperado
        mock_supabase_auth.auth.get_user.side_effect = Exception("Unexpected error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)
        
        assert exc_info.value.status_code == 500
        assert "Error inesperado" in str(exc_info.value.detail)


class TestGetAdminUser:
    """Pruebas para la dependencia get_admin_user"""
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock para el usuario actual"""
        return SupabaseUser(
            id=str(uuid.uuid4()),
            email="admin@example.com"
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock para la sesión de base de datos"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_get_admin_user_success(self, mock_current_user, mock_db_session):
        """Prueba obtención exitosa de usuario admin"""
        # Configurar mock del perfil de usuario
        mock_user_profile = Mock(spec=UserModel)
        mock_user_profile.id = uuid.uuid4()
        mock_user_profile.nombre_persona = "Admin User"
        mock_user_profile.nombre_empresa = "Admin Company"
        
        # Configurar mock de roles
        mock_rol = Mock(spec=RolModel)
        mock_rol.nombre = "admin"
        
        mock_usuario_rol = Mock(spec=UsuarioRolModel)
        mock_usuario_rol.rol = mock_rol
        
        mock_user_profile.roles = [mock_usuario_rol]
        
        # Configurar mock de la sesión de DB
        mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_user_profile
        
        # Ejecutar dependencia
        result = await get_admin_user(mock_current_user, mock_db_session)
        
        # Verificar resultado
        assert isinstance(result, UserProfileAndRolesOut)
        assert result.id == mock_user_profile.id
        assert result.email == mock_current_user.email
        assert result.nombre_persona == mock_user_profile.nombre_persona
        assert result.nombre_empresa == mock_user_profile.nombre_empresa
        assert "admin" in result.roles
    
    @pytest.mark.asyncio
    async def test_get_admin_user_no_profile(self, mock_current_user, mock_db_session):
        """Prueba cuando no se encuentra el perfil de usuario"""
        # Configurar mock para no encontrar perfil
        mock_db_session.execute.return_value.scalars.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_user(mock_current_user, mock_db_session)
        
        assert exc_info.value.status_code == 404
        assert "Perfil de usuario no encontrado" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_admin_user_not_admin(self, mock_current_user, mock_db_session):
        """Prueba cuando el usuario no tiene rol de admin"""
        # Configurar mock del perfil de usuario sin rol admin
        mock_user_profile = Mock(spec=UserModel)
        mock_user_profile.id = uuid.uuid4()
        mock_user_profile.nombre_persona = "Regular User"
        mock_user_profile.nombre_empresa = "Regular Company"
        
        # Configurar mock de roles (solo cliente)
        mock_rol = Mock(spec=RolModel)
        mock_rol.nombre = "Cliente"
        
        mock_usuario_rol = Mock(spec=UsuarioRolModel)
        mock_usuario_rol.rol = mock_rol
        
        mock_user_profile.roles = [mock_usuario_rol]
        
        # Configurar mock de la sesión de DB
        mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_user_profile
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_user(mock_current_user, mock_db_session)
        
        assert exc_info.value.status_code == 403
        assert "No tienes permisos de administrador" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_admin_user_multiple_roles(self, mock_current_user, mock_db_session):
        """Prueba usuario con múltiples roles incluyendo admin"""
        # Configurar mock del perfil de usuario
        mock_user_profile = Mock(spec=UserModel)
        mock_user_profile.id = uuid.uuid4()
        mock_user_profile.nombre_persona = "Multi Role User"
        mock_user_profile.nombre_empresa = "Multi Role Company"
        
        # Configurar mock de roles múltiples
        mock_rol_admin = Mock(spec=RolModel)
        mock_rol_admin.nombre = "admin"
        
        mock_rol_cliente = Mock(spec=RolModel)
        mock_rol_cliente.nombre = "Cliente"
        
        mock_usuario_rol_admin = Mock(spec=UsuarioRolModel)
        mock_usuario_rol_admin.rol = mock_rol_admin
        
        mock_usuario_rol_cliente = Mock(spec=UsuarioRolModel)
        mock_usuario_rol_cliente.rol = mock_rol_cliente
        
        mock_user_profile.roles = [mock_usuario_rol_admin, mock_usuario_rol_cliente]
        
        # Configurar mock de la sesión de DB
        mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_user_profile
        
        # Ejecutar dependencia
        result = await get_admin_user(mock_current_user, mock_db_session)
        
        # Verificar resultado
        assert isinstance(result, UserProfileAndRolesOut)
        assert "admin" in result.roles
        assert "Cliente" in result.roles
        assert len(result.roles) == 2


class TestAuthDependenciesIntegration:
    """Pruebas de integración para las dependencias de autenticación"""
    
    @pytest.mark.asyncio
    async def test_full_auth_flow(self):
        """Prueba el flujo completo de autenticación"""
        # Esta prueba simula el flujo completo desde token hasta verificación de admin
        # Es una prueba de integración que combina ambas dependencias
        
        # Mock de credenciales
        mock_creds = Mock()
        mock_creds.credentials = "valid_admin_token"
        
        # Mock de Supabase
        with patch('app.api.v1.dependencies.auth_user.supabase_auth') as mock_supabase:
            mock_user = Mock()
            mock_user.id = str(uuid.uuid4())
            mock_user.email = "admin@example.com"
            
            mock_response = Mock()
            mock_response.user = mock_user
            
            mock_supabase.auth.get_user.return_value = mock_response
            
            # Mock de sesión de DB
            with patch('app.api.v1.dependencies.database_supabase.get_async_db') as mock_get_db:
                mock_session = AsyncMock(spec=AsyncSession)
                mock_get_db.return_value = mock_session
                
                # Mock del perfil de usuario admin
                mock_user_profile = Mock(spec=UserModel)
                mock_user_profile.id = uuid.uuid4()
                mock_user_profile.nombre_persona = "Admin User"
                mock_user_profile.nombre_empresa = "Admin Company"
                
                mock_rol = Mock(spec=RolModel)
                mock_rol.nombre = "admin"
                
                mock_usuario_rol = Mock(spec=UsuarioRolModel)
                mock_usuario_rol.rol = mock_rol
                
                mock_user_profile.roles = [mock_usuario_rol]
                
                mock_session.execute.return_value.scalars.return_value.first.return_value = mock_user_profile
                
                # Ejecutar get_current_user
                current_user = await get_current_user(mock_creds)
                assert current_user.email == "admin@example.com"
                
                # Ejecutar get_admin_user
                admin_user = await get_admin_user(current_user, mock_session)
                assert "admin" in admin_user.roles
                assert admin_user.email == "admin@example.com"


# Configuración de pytest para tests asíncronos
pytest_plugins = ['pytest_asyncio']
