# app/core/errors.py

from fastapi import HTTPException, status
from gotrue.errors import AuthApiError

# Diccionario que mapea un patrón de mensaje de error de Supabase a una HTTPException
SUPABASE_AUTH_ERROR_MAP = {
    "Invalid login credentials": HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de inicio de sesión inválidas. Verifica tu email y contraseña."
    ),
    "Email not confirmed": HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tu email no ha sido confirmado. Por favor, revisa tu bandeja de entrada."
    ),
    "User already registered": HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Ya existe una cuenta con este email."
    ),
    "Email already registered": HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Este email ya está registrado."
    ),
    "Password should be at least 6 characters": HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="La contraseña debe tener al menos 6 caracteres."
    ),
    # Error para el caso de respuesta incompleta/nula
    "Supabase response incomplete": HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o respuesta de autenticación incompleta. Revisa tu email y contraseña."
    ),
    # Errores específicos para refresh_session
    "Invalid Refresh Token": HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="El token de refresco proporcionado es inválido o no reconocido. Por favor, vuelve a iniciar sesión."
    ),
    "Refresh Token Expired": HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="El token de refresco ha expirado. Por favor, vuelve a iniciar sesión."
    ),
    "Supabase refresh response incomplete": HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Error interno si no se obtiene sesión
        detail="Error inesperado al refrescar la sesión. Inténtalo de nuevo o vuelve a iniciar sesión."
    ),
}

def handle_supabase_auth_error(error: AuthApiError | str): # Ahora acepta AuthApiError o un string
    """
    Traduce al espanhol los errores comunes de Supabase Auth o estados de respuesta inesperados
    a HTTPException de FastAPI usando un mapeo basado en diccionario.
    """
    if isinstance(error, AuthApiError):
        error_message = error.message
    else: # Si es un string, asumimos que es nuestro mensaje sentinel
        error_message = error

    # Itera sobre el diccionario para encontrar una coincidencia en el mensaje de error
    for message_pattern, http_exception in SUPABASE_AUTH_ERROR_MAP.items():
        if message_pattern in error_message: # Usamos error_message aquí
            raise http_exception
    
    # Si no se encuentra ninguna coincidencia para un AuthApiError, o si el string no coincide
    final_detail = f"Error inesperado de autenticación de Supabase: {error_message}" \
        if isinstance(error, AuthApiError) else f"Error interno: {error_message}"

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=final_detail
    )  
