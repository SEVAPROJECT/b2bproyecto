from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.startup import startup_events, shutdown_events
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

# Constantes CORS
ORIGIN_LOCALHOST_5173 = "http://localhost:5173"
ORIGIN_LOCALHOST_5174 = "http://localhost:5174"
ORIGIN_LOCALHOST_3000 = "http://localhost:3000"
ORIGIN_127_0_0_1_5173 = "http://127.0.0.1:5173"
ORIGIN_127_0_0_1_5174 = "http://127.0.0.1:5174"
ORIGIN_127_0_0_1_3000 = "http://127.0.0.1:3000"
ORIGIN_RAILWAY = "https://frontend-production-ee3b.up.railway.app"
ORIGIN_VERCEL = "https://seva-frontend.vercel.app"
ORIGIN_NETLIFY = "https://seva-frontend.netlify.app"

# Lista de orígenes permitidos
ALLOWED_ORIGINS = [
    ORIGIN_LOCALHOST_5173,
    ORIGIN_LOCALHOST_5174,
    ORIGIN_LOCALHOST_3000,
    ORIGIN_127_0_0_1_5173,
    ORIGIN_127_0_0_1_5174,
    ORIGIN_127_0_0_1_3000,
    ORIGIN_RAILWAY,
    ORIGIN_VERCEL,
    ORIGIN_NETLIFY,
]

# Constantes para métodos y headers CORS
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
CORS_METHODS_STRING = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
CORS_HEADERS_STRING = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
CORS_HEADERS_LIST = [
    "Accept",
    "Accept-Language",
    "Content-Language",
    "Content-Type",
    "Authorization",
    "X-Requested-With",
    "Origin",
    "Access-Control-Request-Method",
    "Access-Control-Request-Headers",
]

# Constantes para prefijos de API
API_PREFIX_V1 = "/api/v1"
API_PREFIX_CALIFICACION = "/api/v1/calificacion"

# Constantes para rutas y directorios
UPLOADS_PATH = "/uploads"
UPLOADS_DIRECTORY = "uploads"
UPLOADS_SERVICES_DIR = "uploads/services"
UPLOADS_PROFILE_PHOTOS_DIR = "uploads/profile_photos"

# Constantes para mensajes y valores
MSG_ERROR_INTERNO_SERVIDOR = "Error interno del servidor"
MSG_OK = "OK"
CORS_CREDENTIALS_TRUE = "true"
CORS_MAX_AGE = "86400"

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
from app.api.v1.routers.calificacion import router as calificacion_router

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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS_LIST,
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
    
    # Determinar el origen permitido
    cors_origin = origin if origin in ALLOWED_ORIGINS else ORIGIN_LOCALHOST_5174
    
    try:
        response = await call_next(request)
    except Exception as e:
        logging.error(f"Error en request: {str(e)}")
        # Crear respuesta de error con headers CORS
        response = JSONResponse(
            status_code=500,
            content={"detail": MSG_ERROR_INTERNO_SERVIDOR},
            headers={
                "Access-Control-Allow-Origin": cors_origin,
                "Access-Control-Allow-Methods": CORS_METHODS_STRING,
                "Access-Control-Allow-Headers": CORS_HEADERS_STRING,
                "Access-Control-Allow-Credentials": CORS_CREDENTIALS_TRUE,
            }
        )
    
    # Asegurar que los headers CORS estén presentes en todas las respuestas
    if "Access-Control-Allow-Origin" not in response.headers:
        response.headers["Access-Control-Allow-Origin"] = cors_origin
        response.headers["Access-Control-Allow-Methods"] = CORS_METHODS_STRING
        response.headers["Access-Control-Allow-Headers"] = CORS_HEADERS_STRING
        response.headers["Access-Control-Allow-Credentials"] = CORS_CREDENTIALS_TRUE
    
    return response





# Crear directorio uploads si no existe
os.makedirs(UPLOADS_SERVICES_DIR, exist_ok=True)
os.makedirs(UPLOADS_PROFILE_PHOTOS_DIR, exist_ok=True)

# Servir archivos estáticos (imágenes)
app.mount(UPLOADS_PATH, StaticFiles(directory=UPLOADS_DIRECTORY), name=UPLOADS_DIRECTORY)

# Incluir routers directamente

app.include_router(auth.router, prefix=API_PREFIX_V1)
app.include_router(auth_admin_router, prefix=API_PREFIX_V1)
app.include_router(admin_stats_router, prefix=API_PREFIX_V1)
app.include_router(providers.router, prefix=API_PREFIX_V1)
app.include_router(locations.router, prefix=API_PREFIX_V1)
app.include_router(categories_router, prefix=API_PREFIX_V1)
app.include_router(services_router, prefix=API_PREFIX_V1)
app.include_router(service_requests_router, prefix=API_PREFIX_V1)
app.include_router(category_requests_router, prefix=API_PREFIX_V1)
app.include_router(provider_services_router, prefix=API_PREFIX_V1)
app.include_router(additional_router, prefix=API_PREFIX_V1)
app.include_router(password_reset_router, prefix=API_PREFIX_V1)
app.include_router(supabase_password_reset_router, prefix=API_PREFIX_V1)
app.include_router(direct_password_reset_router, prefix=API_PREFIX_V1)
app.include_router(reserva_router, prefix=API_PREFIX_V1)
app.include_router(disponibilidad_router, prefix=API_PREFIX_V1)
app.include_router(disponibilidad_optimizada_router, prefix=API_PREFIX_V1)
app.include_router(horario_trabajo_router, prefix=API_PREFIX_V1)
app.include_router(horarios_disponibles_router, prefix=API_PREFIX_V1)
app.include_router(weaviate_router, prefix=API_PREFIX_V1)
app.include_router(weaviate_test_router, prefix=API_PREFIX_V1)
app.include_router(calificacion_router, prefix=API_PREFIX_CALIFICACION)
app.include_router(test_router, prefix=API_PREFIX_V1)

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
    
    # Determinar el origen permitido
    cors_origin = origin if origin in ALLOWED_ORIGINS else ORIGIN_LOCALHOST_5174
    
    return Response(
        content=MSG_OK,
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Methods": CORS_METHODS_STRING,
            "Access-Control-Allow-Headers": CORS_HEADERS_STRING,
            "Access-Control-Allow-Credentials": CORS_CREDENTIALS_TRUE,
            "Access-Control-Max-Age": CORS_MAX_AGE
        }
    )
