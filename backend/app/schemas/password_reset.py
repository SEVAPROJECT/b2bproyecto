"""
Esquemas para restablecimiento de contraseña
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

# Constantes
EMAIL_EJEMPLO = "usuario@ejemplo.com"
CODIGO_EJEMPLO = "1234"
PASSWORD_EJEMPLO = "NuevaPassword123"
MSG_CODIGO_SOLO_NUMEROS = "El código debe contener solo números"
MSG_CONTRASEÑAS_NO_COINCIDEN = "Las contraseñas no coinciden"
MSG_CONTRASEÑA_MIN_8_CARACTERES = "La contraseña debe tener al menos 8 caracteres"
MSG_CONTRASEÑA_REQUIERE_MAYUSCULA = "La contraseña debe contener al menos una letra mayúscula"
MSG_CONTRASEÑA_REQUIERE_MINUSCULA = "La contraseña debe contener al menos una letra minúscula"
MSG_CONTRASEÑA_REQUIERE_NUMERO = "La contraseña debe contener al menos un número"
MSG_CODIGO_ENVIADO_EXITOSAMENTE = "Código enviado exitosamente"
LONGITUD_CODIGO = 4
LONGITUD_MIN_PASSWORD = 8
EXPIRES_IN_SECONDS_EJEMPLO = 60
CAMPO_CODE = "code"
CAMPO_NEW_PASSWORD = "new_password"
CAMPO_CONFIRM_PASSWORD = "confirm_password"

class PasswordResetRequest(BaseModel):
    """Esquema para solicitar restablecimiento de contraseña"""
    email: EmailStr = Field(..., description="Email del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": EMAIL_EJEMPLO
            }
        }

class PasswordResetCodeVerify(BaseModel):
    """Esquema para verificar código de restablecimiento"""
    email: EmailStr = Field(..., description="Email del usuario")
    code: str = Field(..., min_length=LONGITUD_CODIGO, max_length=LONGITUD_CODIGO, description="Código de 4 dígitos")
    
    @validator(CAMPO_CODE)
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError(MSG_CODIGO_SOLO_NUMEROS)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": EMAIL_EJEMPLO,
                "code": CODIGO_EJEMPLO
            }
        }

class PasswordResetNewPassword(BaseModel):
    """Esquema para establecer nueva contraseña"""
    email: EmailStr = Field(..., description="Email del usuario")
    code: Optional[str] = Field(None, min_length=LONGITUD_CODIGO, max_length=LONGITUD_CODIGO, description="Código de 4 dígitos (opcional si ya fue verificado)")
    new_password: str = Field(..., min_length=LONGITUD_MIN_PASSWORD, description="Nueva contraseña")
    confirm_password: str = Field(..., min_length=LONGITUD_MIN_PASSWORD, description="Confirmación de nueva contraseña")
    
    @validator(CAMPO_CODE)
    def validate_code(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError(MSG_CODIGO_SOLO_NUMEROS)
        return v
    
    @validator(CAMPO_CONFIRM_PASSWORD)
    def passwords_match(cls, v, values, **kwargs):
        if CAMPO_NEW_PASSWORD in values and v != values[CAMPO_NEW_PASSWORD]:
            raise ValueError(MSG_CONTRASEÑAS_NO_COINCIDEN)
        return v
    
    @validator(CAMPO_NEW_PASSWORD)
    def validate_password_strength(cls, v):
        if len(v) < LONGITUD_MIN_PASSWORD:
            raise ValueError(MSG_CONTRASEÑA_MIN_8_CARACTERES)
        if not any(c.isupper() for c in v):
            raise ValueError(MSG_CONTRASEÑA_REQUIERE_MAYUSCULA)
        if not any(c.islower() for c in v):
            raise ValueError(MSG_CONTRASEÑA_REQUIERE_MINUSCULA)
        if not any(c.isdigit() for c in v):
            raise ValueError(MSG_CONTRASEÑA_REQUIERE_NUMERO)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": EMAIL_EJEMPLO,
                "code": CODIGO_EJEMPLO,
                "new_password": PASSWORD_EJEMPLO,
                "confirm_password": PASSWORD_EJEMPLO
            }
        }

class PasswordResetResponse(BaseModel):
    """Respuesta para operaciones de restablecimiento"""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    expires_in_seconds: Optional[int] = Field(None, description="Segundos hasta expiración del código")
    remaining_attempts: Optional[int] = Field(None, description="Intentos restantes")
    expired: Optional[bool] = Field(None, description="Indica si el código expiró")
    max_attempts_reached: Optional[bool] = Field(None, description="Indica si se alcanzó el máximo de intentos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": MSG_CODIGO_ENVIADO_EXITOSAMENTE,
                "expires_in_seconds": EXPIRES_IN_SECONDS_EJEMPLO
            }
        }
