from pydantic import BaseModel

class SupabaseUser(BaseModel):
    """
    Modelo de datos de usuario devuelto por Supabase Auth.
    Este modelo se utiliza para validar los datos de usuario devueltos por Supabase Auth.
    Atributos:
        id (str): Identificador único del usuario (UUID).
        email (str): Correo electrónico del usuario. 
                     Nunca se debe devolver la contraseña en este modelo.
    """
    
    id: str
    email: str  # Nunca devolver la contraseña
