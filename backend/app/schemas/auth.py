# app/api/schemas/auth.py

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re

class SignUpIn(BaseModel):

    """
    Validación de datos de entrada para el registro y autenticación,
    antes de enviar a Supabase Auth.
    Esta clase utiliza Pydantic para validar los datos de entrada.
    """

    email: EmailStr
    password: str
    nombre_persona: str
    nombre_empresa: str
    ruc: Optional[str] = None 

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8 or len(v) > 64:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula. Intentente de nuevo.")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una letra minúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("La contraseña debe contener al menos un carácter especial")
        return v
    
    @field_validator("ruc")
    @classmethod
    def validate_ruc(cls, v):
        if v is None or v == "":
            return v  # RUC es opcional
        # Validar formato de RUC paraguayo: 8 dígitos seguidos de un guión y un dígito verificador
        if not re.match(r'^\d{8}-\d$', v):
            raise ValueError("El RUC debe tener el formato: 12345678-9 (8 dígitos, guión, 1 dígito verificador)")
        return v

class SignInIn(BaseModel):
    """
    Modelo de entrada para el inicio de sesión.
    Este modelo se utiliza para validar los datos de entrada al iniciar sesión.
    """
    email: EmailStr
    password: str
 
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8 or len(v) > 64:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula. Intentente de nuevo.")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una letra minúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("La contraseña debe contener al menos un carácter especial")
        return v



class TokenOut(BaseModel):
    """
    Modelo de respuesta, lo que la API devuelve al frontend,
    cuando el usuario se registra o inicia sesión exitosamente.
    Este modelo se utiliza para enviar los tokens de acceso y actualización al usuario.
    """
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"

class SignUpSuccess(BaseModel):
    """
    Modelo de respuesta, lo que la API devuelve al frontend,
    cuando el usuario se registra exitosamente pero necesita confirmar su correo.
    Este modelo se utiliza para enviar un mensaje de éxito al usuario.
    """
    message: str
    email: str
    nombre_persona: str
    nombre_empresa: str
    ruc: Optional[str] = None

class RefreshTokenIn(BaseModel):
    """
    Modelo para la entrada de refresco del endpoint /refresh.
    esto es lo que la API espera recibir del frontend
    """
    refresh_token: str
   
class EmailOnlyIn(BaseModel):
    """
    Modelo de entrada que representa solo una dirección de correo electrónico.
    Usado en endpoints como /forgot-password o /resend-confirmation-email.
    """
    email: EmailStr
