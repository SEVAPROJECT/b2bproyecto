from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.routers.users.auth_user import auth
from app.api.v1.routers.users.auth_user_admin.admin_router import router as auth_admin_router
from app.api.v1.routers.locations import locations
from app.api.v1.routers.providers import providers
from app.api.v1.routers.services.categorie_service import router as categories_router
from app.api.v1.routers.services.services import router as services_router
from app.api.v1.routers.services.service_requests import router as service_requests_router
from app.api.v1.routers.services.category_requests import router as category_requests_router
from app.api.v1.routers.services.additional_endpoints import router as additional_router
from app.api.v1.routers.services.provider_services import router as provider_services_router
from app.api.v1.routers.auth.password_reset import router as password_reset_router
from app.api.v1.routers.auth.supabase_password_reset import router as supabase_password_reset_router
from app.api.v1.routers.auth.direct_password_reset import router as direct_password_reset_router

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

# Incluir routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth_admin_router, prefix="/api/v1")
app.include_router(providers.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(service_requests_router, prefix="/api/v1")
app.include_router(category_requests_router, prefix="/api/v1")
app.include_router(provider_services_router, prefix="/api/v1")
app.include_router(additional_router, prefix="/api/v1")
app.include_router(password_reset_router, prefix="/api/v1")
app.include_router(supabase_password_reset_router, prefix="/api/v1")
app.include_router(direct_password_reset_router, prefix="/api/v1") 

# endpoint (una ruta) para la URL raíz ("/")
@app.get("/")
def read_root():
    return {"Hello": "World", "message": "SEVA B2B API está funcionando"}