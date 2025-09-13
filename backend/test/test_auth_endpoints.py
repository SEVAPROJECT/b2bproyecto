#!/usr/bin/env python3
"""
Pruebas unitarias para los endpoints de autenticación
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import uuid
import json

# Importar la aplicación y dependencias
from app.main import app
from app.api.v1.routers.users.auth_user import auth
from app.schemas.auth import SignUpIn, SignInIn, TokenOut, EmailOnlyIn
from app.schemas.user import UserProfileAndRolesOut
from app.models.perfil import UserModel
from app.models.rol import RolModel
from app.models.usuario_rol import UsuarioRolModel

# Cliente de prueba
client = TestClient(app)


class TestAuthEndpoints:
    """Clase para probar los endpoints de autenticación"""
    
    @pytest.fixture
    def mock_supabase_auth(self):
        """Mock para el cliente de Supabase Auth"""
        with patch('app.api.v1.routers.users.auth_user.supabase_auth') as mock:
            yield mock
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock para la sesión de base de datos"""
        with patch('app.api.v1.dependencies.database_supabase.get_async_db') as mock:
            mock_session = AsyncMock(spec=AsyncSession)
            mock.return_value = mock_session
            yield mock_session
    
    @pytest.fixture
    def sample_user_data(self):
        """Datos de ejemplo para un usuario"""
        return {
            "email": "test@example.com",
            "password": "testpassword123",
            "nombre_persona": "Juan Pérez",
            "nombre_empresa": "Empresa Test S.A."
        }
    
    @pytest.fixture
    def sample_signin_data(self):
        """Datos de ejemplo para login"""
        return {
            "email": "test@example.com",
            "password": "testpassword123"
        }
    
    @pytest.fixture
    def mock_user_response(self):
        """Mock de respuesta de usuario de Supabase"""
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.email = "test@example.com"
        
        mock_session = Mock()
        mock_session.access_token = "mock_access_token"
        mock_session.refresh_token = "mock_refresh_token"
        mock_session.expires_in = 3600
        
        mock_response = Mock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        
        return mock_response

    def test_signup_success(self, mock_supabase_auth, mock_db_session, sample_user_data, mock_user_response):
        """Prueba registro exitoso de usuario"""
        # Configurar mocks
        mock_supabase_auth.auth.sign_up.return_value = mock_user_response
        
        # Mock del perfil de usuario
        mock_user_profile = Mock(spec=UserModel)
        mock_user_profile.id = uuid.uuid4()
        mock_user_profile.nombre_persona = sample_user_data["nombre_persona"]
        mock_user_profile.nombre_empresa = sample_user_data["nombre_empresa"]
        mock_user_profile.roles = []
        
        mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_user_profile
        
        # Realizar request
        response = client.post("/api/v1/auth/signup", json=sample_user_data)
        
        # Verificar respuesta
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["access_token"] == "mock_access_token"
        
        # Verificar que se llamó a Supabase
        mock_supabase_auth.auth.sign_up.assert_called_once()
        call_args = mock_supabase_auth.auth.sign_up.call_args[0][0]
        assert call_args["email"] == sample_user_data["email"]
        assert call_args["password"] == sample_user_data["password"]
        assert call_args["options"]["data"]["nombre_persona"] == sample_user_data["nombre_persona"]
        assert call_args["options"]["data"]["nombre_empresa"] == sample_user_data["nombre_empresa"]

    def test_signup_without_session(self, mock_supabase_auth, sample_user_data):
        """Prueba registro cuando no hay sesión (confirmación de email requerida)"""
        # Configurar mock sin sesión
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(uuid.uuid4())
        mock_user_response.session = None
        
        mock_supabase_auth.auth.sign_up.return_value = mock_user_response
        
        # Realizar request
        response = client.post("/api/v1/auth/signup", json=sample_user_data)
        
        # Verificar respuesta
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "email" in data
        assert data["email"] == sample_user_data["email"]
        assert "Te enviamos un correo para confirmar tu cuenta" in data["message"]

    def test_signup_invalid_data(self):
        """Prueba registro con datos inválidos"""
        invalid_data = {
            "email": "invalid-email",
            "password": "123",  # Contraseña muy corta
            "nombre_persona": "",
            "nombre_empresa": ""
        }
        
        response = client.post("/api/v1/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_signup_supabase_error(self, mock_supabase_auth, sample_user_data):
        """Prueba registro con error de Supabase"""
        from supabase import AuthApiError
        
        # Configurar mock para lanzar error
        mock_supabase_auth.auth.sign_up.side_effect = AuthApiError("Email already registered")
        
        response = client.post("/api/v1/auth/signup", json=sample_user_data)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_signin_success(self, mock_supabase_auth, sample_signin_data, mock_user_response):
        """Prueba login exitoso"""
        # Configurar mock
        mock_supabase_auth.auth.sign_in_with_password.return_value = mock_user_response
        
        # Realizar request
        response = client.post("/api/v1/auth/signin", json=sample_signin_data)
        
        # Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["access_token"] == "mock_access_token"
        
        # Verificar que se llamó a Supabase
        mock_supabase_auth.auth.sign_in_with_password.assert_called_once_with({
            "email": sample_signin_data["email"],
            "password": sample_signin_data["password"]
        })

    def test_signin_invalid_credentials(self, mock_supabase_auth, sample_signin_data):
        """Prueba login con credenciales inválidas"""
        from supabase import AuthApiError
        
        # Configurar mock para lanzar error
        mock_supabase_auth.auth.sign_in_with_password.side_effect = AuthApiError("Invalid login credentials")
        
        response = client.post("/api/v1/auth/signin", json=sample_signin_data)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_signin_invalid_data(self):
        """Prueba login con datos inválidos"""
        invalid_data = {
            "email": "invalid-email",
            "password": ""
        }
        
        response = client.post("/api/v1/auth/signin", json=invalid_data)
        assert response.status_code == 422

    def test_refresh_token_success(self, mock_supabase_auth):
        """Prueba refresh de token exitoso"""
        # Configurar mock
        mock_session = Mock()
        mock_session.access_token = "new_access_token"
        mock_session.refresh_token = "new_refresh_token"
        mock_session.expires_in = 3600
        
        mock_supabase_auth.auth.refresh_session.return_value = mock_session
        
        refresh_data = {"refresh_token": "old_refresh_token"}
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["access_token"] == "new_access_token"

    def test_refresh_token_invalid(self, mock_supabase_auth):
        """Prueba refresh de token inválido"""
        from supabase import AuthApiError
        
        mock_supabase_auth.auth.refresh_session.side_effect = AuthApiError("Invalid refresh token")
        
        refresh_data = {"refresh_token": "invalid_token"}
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 400

    def test_forgot_password_success(self, mock_supabase_auth):
        """Prueba recuperación de contraseña exitosa"""
        # Configurar mock
        mock_supabase_auth.auth.reset_password_email.return_value = None
        
        email_data = {"email": "test@example.com"}
        
        response = client.post("/api/v1/auth/forgot-password", json=email_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verificar que se llamó a Supabase
        mock_supabase_auth.auth.reset_password_email.assert_called_once_with(email_data["email"])

    def test_forgot_password_invalid_email(self, mock_supabase_auth):
        """Prueba recuperación de contraseña con email inválido"""
        from supabase import AuthApiError
        
        mock_supabase_auth.auth.reset_password_email.side_effect = AuthApiError("User not found")
        
        email_data = {"email": "nonexistent@example.com"}
        
        response = client.post("/api/v1/auth/forgot-password", json=email_data)
        assert response.status_code == 400

    @patch('app.api.v1.routers.users.auth_user.supabase_auth')
    @patch('app.api.v1.dependencies.database_supabase.get_async_db')
    def test_get_profile_success(self, mock_get_db, mock_supabase_auth):
        """Prueba obtención de perfil de usuario exitosa"""
        # Configurar mocks
        mock_session = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_session
        
        # Mock del usuario autenticado
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.email = "test@example.com"
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        mock_supabase_auth.auth.get_user.return_value = mock_user_response
        
        # Mock del perfil de usuario
        mock_user_profile = Mock(spec=UserModel)
        mock_user_profile.id = uuid.uuid4()
        mock_user_profile.nombre_persona = "Juan Pérez"
        mock_user_profile.nombre_empresa = "Empresa Test"
        
        # Mock de roles
        mock_rol = Mock(spec=RolModel)
        mock_rol.nombre = "Cliente"
        
        mock_usuario_rol = Mock(spec=UsuarioRolModel)
        mock_usuario_rol.rol = mock_rol
        
        mock_user_profile.roles = [mock_usuario_rol]
        
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_user_profile
        
        # Realizar request con token
        headers = {"Authorization": "Bearer valid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "nombre_persona" in data
        assert "nombre_empresa" in data
        assert "roles" in data
        assert data["email"] == "test@example.com"
        assert data["nombre_persona"] == "Juan Pérez"
        assert "Cliente" in data["roles"]

    def test_get_profile_no_token(self):
        """Prueba obtención de perfil sin token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @patch('app.api.v1.routers.users.auth_user.supabase_auth')
    def test_get_profile_invalid_token(self, mock_supabase_auth):
        """Prueba obtención de perfil con token inválido"""
        from supabase import AuthApiError
        
        mock_supabase_auth.auth.get_user.side_effect = AuthApiError("Invalid token")
        
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401

    def test_signout_success(self, mock_supabase_auth):
        """Prueba logout exitoso"""
        # Configurar mock
        mock_supabase_auth.auth.sign_out.return_value = None
        
        response = client.post("/api/v1/auth/signout")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Sesión cerrada exitosamente" in data["message"]
        
        # Verificar que se llamó a Supabase
        mock_supabase_auth.auth.sign_out.assert_called_once()

    def test_signout_error(self, mock_supabase_auth):
        """Prueba logout con error"""
        from supabase import AuthApiError
        
        mock_supabase_auth.auth.sign_out.side_effect = AuthApiError("Sign out error")
        
        response = client.post("/api/v1/auth/signout")
        assert response.status_code == 400


class TestAuthValidation:
    """Clase para probar validaciones de esquemas"""
    
    def test_signup_schema_validation(self):
        """Prueba validación del esquema de registro"""
        # Datos válidos
        valid_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "nombre_persona": "Juan Pérez",
            "nombre_empresa": "Empresa Test S.A."
        }
        
        signup_in = SignUpIn(**valid_data)
        assert signup_in.email == valid_data["email"]
        assert signup_in.password == valid_data["password"]
        assert signup_in.nombre_persona == valid_data["nombre_persona"]
        assert signup_in.nombre_empresa == valid_data["nombre_empresa"]
    
    def test_signin_schema_validation(self):
        """Prueba validación del esquema de login"""
        valid_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        signin_in = SignInIn(**valid_data)
        assert signin_in.email == valid_data["email"]
        assert signin_in.password == valid_data["password"]
    
    def test_email_only_schema_validation(self):
        """Prueba validación del esquema de email"""
        valid_data = {"email": "test@example.com"}
        
        email_in = EmailOnlyIn(**valid_data)
        assert email_in.email == valid_data["email"]
    
    def test_token_out_schema_validation(self):
        """Prueba validación del esquema de token"""
        valid_data = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600
        }
        
        token_out = TokenOut(**valid_data)
        assert token_out.access_token == valid_data["access_token"]
        assert token_out.refresh_token == valid_data["refresh_token"]
        assert token_out.expires_in == valid_data["expires_in"]


class TestAuthErrorHandling:
    """Clase para probar manejo de errores"""
    
    def test_handle_supabase_auth_error(self):
        """Prueba manejo de errores de Supabase Auth"""
        from app.utils.errores import handle_supabase_auth_error
        from supabase import AuthApiError
        
        # Probar con error conocido
        error = AuthApiError("Email already registered")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_supabase_auth_error(error)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    def test_handle_unknown_error(self):
        """Prueba manejo de errores desconocidos"""
        from app.utils.errores import handle_supabase_auth_error
        
        # Probar con error desconocido
        error = Exception("Unknown error")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_supabase_auth_error(error)
        
        assert exc_info.value.status_code == 500
        assert "Error inesperado" in str(exc_info.value.detail)


# Configuración de pytest
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configuración automática para todas las pruebas"""
    # Aquí puedes agregar configuración global si es necesario
    pass


if __name__ == "__main__":
    # Ejecutar las pruebas
    pytest.main([__file__, "-v"])
