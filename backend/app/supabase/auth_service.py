#registro/login usando supabase

from supabase import Client, create_client
from sqlalchemy import create_engine
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL
from supabase.lib.client_options import ClientOptions

#options = ClientOptions(use_ssl=False)

# Inicializar clientes de Supabase solo si están configurados
supabase_auth: Client = None
supabase_admin: Client = None

try:
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        # Cliente para uso publico/autenticacion de usuarios (con la anon key)
        supabase_auth = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("✅ Cliente de autenticación de Supabase inicializado")
    else:
        print("⚠️  Supabase no configurado - funciones de autenticación no disponibles")
except Exception as e:
    print(f"❌ Error al inicializar cliente de autenticación de Supabase: {e}")
    supabase_auth = None

try:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        # Cliente para tareas administrativas (con la service_role key)
        # IMPORTANTE: Para operaciones admin como get_user_by_id, usar SERVICE_ROLE_KEY
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("✅ Cliente administrativo de Supabase inicializado")
    else:
        print("⚠️  Supabase Service Role no configurado - funciones administrativas no disponibles")
except Exception as e:
    print(f"❌ Error al inicializar cliente administrativo de Supabase: {e}")
    supabase_admin = None

# SQLAlchemy engine para tu base de datos propia
#engine = create_engine(DATABASE_URL, echo=True)

