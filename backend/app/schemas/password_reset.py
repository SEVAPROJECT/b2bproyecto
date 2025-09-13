"""
Esquemas para restablecimiento de contraseña
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class PasswordResetRequest(BaseModel):
    """Esquema para solicitar restablecimiento de contraseña"""
    email: EmailStr = Field(..., description="Email del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com"
            }
        }

class PasswordResetCodeVerify(BaseModel):
    """Esquema para verificar código de restablecimiento"""
    email: EmailStr = Field(..., description="Email del usuario")
    code: str = Field(..., min_length=4, max_length=4, description="Código de 4 dígitos")
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('El código debe contener solo números')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com",
                "code": "1234"
            }
        }

class PasswordResetNewPassword(BaseModel):
    """Esquema para establecer nueva contraseña"""
    email: EmailStr = Field(..., description="Email del usuario")
    code: Optional[str] = Field(None, min_length=4, max_length=4, description="Código de 4 dígitos (opcional si ya fue verificado)")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")
    confirm_password: str = Field(..., min_length=8, description="Confirmación de nueva contraseña")
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError('El código debe contener solo números')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com",
                "code": "1234",
                "new_password": "NuevaPassword123",
                "confirm_password": "NuevaPassword123"
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
                "message": "Código enviado exitosamente",
                "expires_in_seconds": 60
            }
        }
