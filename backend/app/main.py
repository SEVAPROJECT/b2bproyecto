from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Importar routers con manejo de errores
try:
    from app.api.v1.routers.users.auth_user import auth
    print("✅ Router de autenticación importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de autenticación: {e}")
    auth = None

try:
    from app.api.v1.routers.users.auth_user_admin.admin_router import router as auth_admin_router
    print("✅ Router de admin importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de admin: {e}")
    auth_admin_router = None

try:
    from app.api.v1.routers.locations import locations
    print("✅ Router de ubicaciones importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de ubicaciones: {e}")
    locations = None

try:
    from app.api.v1.routers.providers import providers
    print("✅ Router de proveedores importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de proveedores: {e}")
    providers = None

try:
    from app.api.v1.routers.services.categorie_service import router as categories_router
    print("✅ Router de categorías importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de categorías: {e}")
    categories_router = None

try:
    from app.api.v1.routers.services.services import router as services_router
    print("✅ Router de servicios importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de servicios: {e}")
    services_router = None

try:
    from app.api.v1.routers.services.service_requests import router as service_requests_router
    print("✅ Router de solicitudes de servicios importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de solicitudes: {e}")
    service_requests_router = None

try:
    from app.api.v1.routers.services.category_requests import router as category_requests_router
    print("✅ Router de solicitudes de categorías importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de solicitudes de categorías: {e}")
    category_requests_router = None

try:
    from app.api.v1.routers.services.additional_endpoints import router as additional_router
    print("✅ Router adicional importado")
except ImportError as e:
    print(f"⚠️  Error al importar router adicional: {e}")
    additional_router = None

try:
    from app.api.v1.routers.services.provider_services import router as provider_services_router
    print("✅ Router de servicios de proveedores importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de servicios de proveedores: {e}")
    provider_services_router = None

try:
    from app.api.v1.routers.auth.password_reset import router as password_reset_router
    print("✅ Router de reset de contraseña importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de reset de contraseña: {e}")
    password_reset_router = None

try:
    from app.api.v1.routers.auth.supabase_password_reset import router as supabase_password_reset_router
    print("✅ Router de reset de contraseña de Supabase importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de reset de contraseña de Supabase: {e}")
    supabase_password_reset_router = None

try:
    from app.api.v1.routers.auth.direct_password_reset import router as direct_password_reset_router
    print("✅ Router de reset directo de contraseña importado")
except ImportError as e:
    print(f"⚠️  Error al importar router de reset directo de contraseña: {e}")
    direct_password_reset_router = None

# Instancia de la aplicación de FastAPI
app = FastAPI(
    title="SEVA B2B API",
    description="API para la plataforma B2B SEVA Empresas",
    version="1.0.0"
)

# Configurar CORS para permitir comunicación con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:5173",  # Vite dev server (alternativo)
        "http://127.0.0.1:3000",  # React dev server (alternativo)
        "https://*.railway.app",  # Railway URLs
        "https://*.vercel.app",   # Vercel URLs
        "https://*.netlify.app",  # Netlify URLs
        "*"  # Temporalmente para testing - REMOVER EN PRODUCCIÓN
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Crear directorio uploads si no existe
os.makedirs("uploads/services", exist_ok=True)
os.makedirs("uploads/profile_photos", exist_ok=True)

# Servir archivos estáticos (imágenes)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Incluir routers solo si se importaron correctamente
if auth:
    app.include_router(auth.router, prefix="/api/v1")
    print("✅ Router de autenticación incluido")

if auth_admin_router:
    app.include_router(auth_admin_router, prefix="/api/v1")
    print("✅ Router de admin incluido")

if providers:
    app.include_router(providers.router, prefix="/api/v1")
    print("✅ Router de proveedores incluido")

if locations:
    app.include_router(locations.router, prefix="/api/v1")
    print("✅ Router de ubicaciones incluido")

if categories_router:
    app.include_router(categories_router, prefix="/api/v1")
    print("✅ Router de categorías incluido")

if services_router:
    app.include_router(services_router, prefix="/api/v1")
    print("✅ Router de servicios incluido")

if service_requests_router:
    app.include_router(service_requests_router, prefix="/api/v1")
    print("✅ Router de solicitudes de servicios incluido")

if category_requests_router:
    app.include_router(category_requests_router, prefix="/api/v1")
    print("✅ Router de solicitudes de categorías incluido")

if provider_services_router:
    app.include_router(provider_services_router, prefix="/api/v1")
    print("✅ Router de servicios de proveedores incluido")

if additional_router:
    app.include_router(additional_router, prefix="/api/v1")
    print("✅ Router adicional incluido")

if password_reset_router:
    app.include_router(password_reset_router, prefix="/api/v1")
    print("✅ Router de reset de contraseña incluido")

if supabase_password_reset_router:
    app.include_router(supabase_password_reset_router, prefix="/api/v1")
    print("✅ Router de reset de contraseña de Supabase incluido")

if direct_password_reset_router:
    app.include_router(direct_password_reset_router, prefix="/api/v1")
    print("✅ Router de reset directo de contraseña incluido") 

# endpoint (una ruta) para la URL raíz ("/")
@app.get("/")
def read_root():
    return {
        "Hello": "World", 
        "message": "SEVA B2B API está funcionando", 
        "status": "ok",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "message": "API is running", 
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Endpoint de diagnóstico
@app.get("/diagnostic")
def diagnostic():
    import os
    return {
        "status": "ok",
        "port": os.getenv("PORT", "8000"),
        "environment": os.getenv("NODE_ENV", "development"),
        "supabase_configured": bool(os.getenv("SUPABASE_URL")),
        "idrive_configured": bool(os.getenv("AWS_ACCESS_KEY_ID")),
        "message": "Backend funcionando correctamente"
    }