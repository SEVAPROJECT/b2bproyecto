#registro/login usando supabase

from supabase import Client, create_client
from sqlalchemy import create_engine
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL
from supabase.lib.client_options import ClientOptions


#options = ClientOptions(use_ssl=False)

# Cliente para uso publico/autenticacion de usuarios (con la anon key)
# Solo inicializar si las variables de entorno están configuradas
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase_auth: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("✅ Supabase Auth cliente inicializado correctamente")
else:
    supabase_auth = None
    print("⚠️ Supabase Auth no configurado - SUPABASE_URL o SUPABASE_ANON_KEY faltantes")

# Cliente para tareas administrativas (con la service_role key)
# IMPORTANTE: Para operaciones admin como get_user_by_id, usar SERVICE_ROLE_KEY
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print("✅ Supabase Admin cliente inicializado correctamente")
else:
    supabase_admin = None
    print("⚠️ Supabase Admin no configurado - SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY faltantes")

# SQLAlchemy engine para tu base de datos propia
#engine = create_engine(DATABASE_URL, echo=True)

