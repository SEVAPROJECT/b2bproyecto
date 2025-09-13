# tests/test_auth.py

from fastapi.testclient import TestClient
from supabase import AuthApiError
from ..main import app  # Importa tu aplicación de FastAPI
import pytest
from unittest.mock import patch, MagicMock

# Crea una instancia del cliente de pruebas para tu aplicación
client = TestClient(app)

# Mock de la respuesta exitosa de Supabase para el inicio de sesión
MOCK_SUPABASE_SIGNIN_RESPONSE = {
    "user": {"id": "12345", "email": "test@example.com"},
    "session": {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "expires_in": 3600,
        "token_type": "bearer"
    }
}

# Mock de la respuesta de error de Supabase
MOCK_SUPABASE_ERROR_RESPONSE = {
    "message": "Invalid login credentials"
}

def test_sign_in_success():
    """
    Prueba un inicio de sesión exitoso.
    """
    # Usamos patch para simular la respuesta del cliente de Supabase
    with patch("app.supabase.auth_service.supabase_auth.auth.sign_in_with_password",
               return_value=MagicMock(user=MOCK_SUPABASE_SIGNIN_RESPONSE["user"], 
                                      session=MOCK_SUPABASE_SIGNIN_RESPONSE["session"])):
        
        # Simulamos la petición POST al endpoint
        response = client.post(
            "/api/v1/auth/signin",
            json={"email": "test@example.com", "password": "password123"}
        )
    
    # Verificamos que el código de estado HTTP sea 200 (OK)
    assert response.status_code == 200
    # Verificamos que la respuesta contenga los tokens
    assert "access_token" in response.json()

def test_sign_in_invalid_credentials():
    """
    Prueba un inicio de sesión con credenciales inválidas.
    """
    # Usamos patch para simular una excepción de Supabase
    with patch("app.supabase.auth_service.supabase_auth.auth.sign_in_with_password",
               side_effect=AuthApiError(MOCK_SUPABASE_ERROR_RESPONSE, 400)):
        
        # Simulamos la petición POST con credenciales incorrectas
        response = client.post(
            "/api/v1/auth/signin",
            json={"email": "wrong@example.com", "password": "wrongpassword"}
        )
    
    # Verificamos que el código de estado HTTP sea 401 (Unauthorized)
    assert response.status_code == 401
    # Verificamos que el mensaje de error sea el esperado
    assert "Credenciales de inicio de sesión inválidas" in response.json()["detail"]

# Para correr las pruebas, usa el siguiente comando en tu terminal:
# pytest