#registro/login usando supabase

from supabase import Client, create_client
from sqlalchemy import create_engine
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL
from supabase.lib.client_options import ClientOptions
import httpx

# Configurar timeout para httpx (60 segundos para evitar "read operation timed out")
# El timeout por defecto de httpx es muy corto (5 segundos), lo aumentamos a 60
SUPABASE_HTTP_TIMEOUT = httpx.Timeout(60.0, connect=10.0)  # 60s total, 10s para conectar

# Crear cliente HTTP personalizado con timeout aumentado para Supabase Auth
http_client_auth = httpx.Client(timeout=SUPABASE_HTTP_TIMEOUT)

# Cliente para uso publico/autenticacion de usuarios (con la anon key)
# Solo inicializar si las variables de entorno están configuradas
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        # Intentar crear cliente con http_client personalizado
        supabase_auth: Client = create_client(
            SUPABASE_URL, 
            SUPABASE_ANON_KEY,
            options=ClientOptions(http_client=http_client_auth)
        )
        print("✅ Supabase Auth cliente inicializado correctamente (timeout: 60s)")
    except (TypeError, AttributeError) as e:
        # Si ClientOptions no acepta http_client, crear sin opciones y modificar el cliente httpx directamente
        print(f"⚠️ ClientOptions no acepta http_client ({e}), modificando timeout después de crear cliente")
        supabase_auth: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Modificar el timeout del cliente httpx interno de Supabase de forma más agresiva
        try:
            # Acceder al cliente httpx a través de la estructura interna de gotrue
            # gotrue usa httpx.Client internamente, necesitamos encontrarlo
            if hasattr(supabase_auth, 'auth'):
                auth_obj = supabase_auth.auth
                
                # Ruta 1: auth._client._http_client (estructura común de gotrue)
                if hasattr(auth_obj, '_client'):
                    client_obj = auth_obj._client
                    # Intentar acceder a _http_client
                    if hasattr(client_obj, '_http_client'):
                        http_client = client_obj._http_client
                        http_client.timeout = SUPABASE_HTTP_TIMEOUT
                        print(f"✅ Timeout modificado a {SUPABASE_HTTP_TIMEOUT.read} segundos vía _http_client")
                    # Intentar acceder directamente al timeout
                    elif hasattr(client_obj, 'timeout'):
                        client_obj.timeout = SUPABASE_HTTP_TIMEOUT
                        print(f"✅ Timeout modificado a {SUPABASE_HTTP_TIMEOUT.read} segundos directamente")
                    # Intentar acceder a través de otros atributos comunes
                    elif hasattr(client_obj, 'http_client'):
                        client_obj.http_client.timeout = SUPABASE_HTTP_TIMEOUT
                        print(f"✅ Timeout modificado a {SUPABASE_HTTP_TIMEOUT.read} segundos vía http_client")
                
                # Ruta 2: Buscar en todos los atributos del objeto auth
                if hasattr(auth_obj, '__dict__'):
                    for key, value in auth_obj.__dict__.items():
                        if isinstance(value, httpx.Client):
                            value.timeout = SUPABASE_HTTP_TIMEOUT
                            print(f"✅ Timeout modificado en atributo {key} (httpx.Client encontrado)")
                        elif hasattr(value, 'timeout') and 'http' in key.lower():
                            value.timeout = SUPABASE_HTTP_TIMEOUT
                            print(f"✅ Timeout modificado en atributo {key}")
                
                # Ruta 3: Intentar acceder a través de _transport si existe
                if hasattr(auth_obj, '_client') and hasattr(auth_obj._client, '_transport'):
                    transport = auth_obj._client._transport
                    if hasattr(transport, '_pool'):
                        # El pool puede tener configuración de timeout
                        pass
        except Exception as timeout_error:
            print(f"⚠️ No se pudo modificar timeout directamente: {timeout_error}")
            import traceback
            traceback.print_exc()
        
        print("✅ Supabase Auth cliente inicializado correctamente")
else:
    supabase_auth = None
    print("⚠️ Supabase Auth no configurado - SUPABASE_URL o SUPABASE_ANON_KEY faltantes")

# Crear cliente HTTP personalizado con timeout aumentado para Supabase Admin
http_client_admin = httpx.Client(timeout=SUPABASE_HTTP_TIMEOUT)

# Cliente para tareas administrativas (con la service_role key)
# IMPORTANTE: Para operaciones admin como get_user_by_id, usar SERVICE_ROLE_KEY
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        # Intentar crear cliente con http_client personalizado
        supabase_admin: Client = create_client(
            SUPABASE_URL, 
            SUPABASE_SERVICE_ROLE_KEY,
            options=ClientOptions(http_client=http_client_admin)
        )
        print("✅ Supabase Admin cliente inicializado correctamente (timeout: 60s)")
    except (TypeError, AttributeError) as e:
        # Si ClientOptions no acepta http_client, crear sin opciones y modificar el cliente httpx directamente
        print(f"⚠️ ClientOptions no acepta http_client ({e}), modificando timeout después de crear cliente")
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Modificar el timeout del cliente httpx interno de Supabase de forma más agresiva
        try:
            # Acceder al cliente httpx a través de la estructura interna de gotrue
            # gotrue usa httpx.Client internamente, necesitamos encontrarlo
            if hasattr(supabase_admin, 'auth'):
                auth_obj = supabase_admin.auth
                
                # Ruta 1: auth._client._http_client (estructura común de gotrue)
                if hasattr(auth_obj, '_client'):
                    client_obj = auth_obj._client
                    # Intentar acceder a _http_client
                    if hasattr(client_obj, '_http_client'):
                        http_client = client_obj._http_client
                        http_client.timeout = SUPABASE_HTTP_TIMEOUT
                        print(f"✅ Timeout modificado a {SUPABASE_HTTP_TIMEOUT.read} segundos vía _http_client")
                    # Intentar acceder directamente al timeout
                    elif hasattr(client_obj, 'timeout'):
                        client_obj.timeout = SUPABASE_HTTP_TIMEOUT
                        print(f"✅ Timeout modificado a {SUPABASE_HTTP_TIMEOUT.read} segundos directamente")
                    # Intentar acceder a través de otros atributos comunes
                    elif hasattr(client_obj, 'http_client'):
                        client_obj.http_client.timeout = SUPABASE_HTTP_TIMEOUT
                        print(f"✅ Timeout modificado a {SUPABASE_HTTP_TIMEOUT.read} segundos vía http_client")
                
                # Ruta 2: Buscar en todos los atributos del objeto auth
                if hasattr(auth_obj, '__dict__'):
                    for key, value in auth_obj.__dict__.items():
                        if isinstance(value, httpx.Client):
                            value.timeout = SUPABASE_HTTP_TIMEOUT
                            print(f"✅ Timeout modificado en atributo {key} (httpx.Client encontrado)")
                        elif hasattr(value, 'timeout') and 'http' in key.lower():
                            value.timeout = SUPABASE_HTTP_TIMEOUT
                            print(f"✅ Timeout modificado en atributo {key}")
                
                # Ruta 3: Intentar acceder a través de _transport si existe
                if hasattr(auth_obj, '_client') and hasattr(auth_obj._client, '_transport'):
                    transport = auth_obj._client._transport
                    if hasattr(transport, '_pool'):
                        # El pool puede tener configuración de timeout
                        pass
        except Exception as timeout_error:
            print(f"⚠️ No se pudo modificar timeout directamente: {timeout_error}")
            import traceback
            traceback.print_exc()
        
        print("✅ Supabase Admin cliente inicializado correctamente")
else:
    supabase_admin = None
    print("⚠️ Supabase Admin no configurado - SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY faltantes")

# SQLAlchemy engine para tu base de datos propia
#engine = create_engine(DATABASE_URL, echo=True)

