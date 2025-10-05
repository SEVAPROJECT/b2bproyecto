from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.startup import startup_events, shutdown_events
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

# Imports de routers
from app.api.v1.routers.users.auth_user import auth
from app.api.v1.routers.users.auth_user_admin.admin_router import router as auth_admin_router
from app.api.v1.routers.users.auth_user_admin.admin_stats_router import router as admin_stats_router
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
from app.api.v1.routers.reserva_service.reserva import router as reserva_router
from app.api.v1.routers.disponibilidad import router as disponibilidad_router
from app.api.v1.routers.test import router as test_router
from app.api.v1.routers.disponibilidad_optimizada import router as disponibilidad_optimizada_router
from app.api.v1.routers.horario_trabajo import router as horario_trabajo_router
from app.api.v1.routers.horarios_disponibles import router as horarios_disponibles_router
from app.api.v1.routers.weaviate.weaviate import router as weaviate_router
from app.api.v1.routers.weaviate_test import router as weaviate_test_router

# Lifespan handler para reemplazar @app.on_event (deprecado)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_events()
    yield
    # Shutdown
    await shutdown_events()

# Instancia de la aplicación de FastAPI
app = FastAPI(
    title="SEVA B2B API",
    description="API para la plataforma B2B SEVA Empresas",
    version="1.0.0",
    lifespan=lifespan
)


# Configurar CORS para permitir comunicación con el frontend
#es mejor que el middleware CORS esté lo más arriba posible en la pila de middlewares
# de lo contrario, algunas solicitudes podrían no ser manejadas correctamente.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite dev server (puerto alternativo)
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:5173",  # Vite dev server (alternativo)
        "http://127.0.0.1:5174",  # Vite dev server (puerto alternativo)
        "http://127.0.0.1:3000",  # React dev server (alternativo)
        "https://frontend-production-ee3b.up.railway.app",  # Railway deployment
        "https://seva-frontend.vercel.app",  # Vercel deployment
        "https://seva-frontend.netlify.app",  # Netlify deployment
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
)

# Middleware personalizado para asegurar headers CORS en errores
@app.middleware("http")
async def cors_error_handler(request: Request, call_next):
    """
    Middleware para asegurar que los headers CORS se devuelvan incluso en errores.
    """
    # Obtener el origen de la request para configurar CORS dinámicamente
    origin = request.headers.get("origin", "")
    
    # Lista de orígenes permitidos
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "https://frontend-production-ee3b.up.railway.app",
        "https://seva-frontend.vercel.app",
        "https://seva-frontend.netlify.app",
    ]
    
    # Determinar el origen permitido
    cors_origin = origin if origin in allowed_origins else "http://localhost:5174"
    
    try:
        response = await call_next(request)
    except Exception as e:
        logging.error(f"Error en request: {str(e)}")
        # Crear respuesta de error con headers CORS
        response = JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"},
            headers={
                "Access-Control-Allow-Origin": cors_origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    
    # Asegurar que los headers CORS estén presentes en todas las respuestas
    if "Access-Control-Allow-Origin" not in response.headers:
        response.headers["Access-Control-Allow-Origin"] = cors_origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response





# Crear directorio uploads si no existe
os.makedirs("uploads/services", exist_ok=True)
os.makedirs("uploads/profile_photos", exist_ok=True)

# Servir archivos estáticos (imágenes)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Incluir routers directamente

app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth_admin_router, prefix="/api/v1")
app.include_router(admin_stats_router, prefix="/api/v1")
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
app.include_router(reserva_router, prefix="/api/v1")
app.include_router(disponibilidad_router, prefix="/api/v1")
app.include_router(disponibilidad_optimizada_router, prefix="/api/v1")
app.include_router(horario_trabajo_router, prefix="/api/v1")
app.include_router(horarios_disponibles_router, prefix="/api/v1")
app.include_router(weaviate_router, prefix="/api/v1")
app.include_router(weaviate_test_router, prefix="/api/v1")
app.include_router(test_router, prefix="/api/v1")

# endpoint (una ruta) para la URL raíz ("/")
@app.get("/")
def read_root():
    return {"Hello": "World", "message": "SEVA B2B API está funcionando"}

# Health Check endpoint para Railway (evitar cold starts)
@app.get("/health")
async def health_check():
    """
    Health check endpoint para mantener la aplicación activa en Railway.
    Railway usa este endpoint para verificar que la app está funcionando.
    """
    import asyncio
    from datetime import datetime
    from app.services.direct_db_service import direct_db_service
    
    try:
        # Verificar conexión a la base de datos
        db_status = "connected"
        try:
            # Test rápido de conexión
            await asyncio.wait_for(
                direct_db_service.test_connection(), 
                timeout=2.0
            )
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "uptime": "active"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "timestamp": datetime.now().isoformat(),
            "error": str(e)[:100]
        }

# Endpoint específico para manejar peticiones OPTIONS (preflight)
@app.options("/{path:path}")
async def options_handler(path: str, request: Request):
    """
    Maneja peticiones OPTIONS (preflight) para CORS.
    """
    from fastapi import Response
    
    # Obtener el origen de la request
    origin = request.headers.get("origin", "")
    
    # Lista de orígenes permitidos
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "https://frontend-production-ee3b.up.railway.app",
        "https://seva-frontend.vercel.app",
        "https://seva-frontend.netlify.app",
    ]
    
    # Determinar el origen permitido
    cors_origin = origin if origin in allowed_origins else "http://localhost:5174"
    
    return Response(
        content="OK",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400"
        }
    )
