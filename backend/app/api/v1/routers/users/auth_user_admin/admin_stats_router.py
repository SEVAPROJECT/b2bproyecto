# admin_stats_router.py
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func 
from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_admin_user, get_current_user
from app.models.perfil import UserModel
from app.models.publicar_servicio.category import CategoriaModel
from app.models.servicio.service import ServicioModel
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
from app.schemas.user import UserProfileAndRolesOut
from app.services.direct_db_service import direct_db_service



router = APIRouter(prefix="/admin/stats", tags=["admin-stats"])

# ========================================
# ENDPOINTS DE ESTADÍSTICAS Y CONTADORES
# ========================================

@router.get("/test")
async def test_endpoint():
    """Endpoint de prueba para verificar que el router funciona"""
    return {"message": "Admin stats router funcionando correctamente", "status": "ok"}


@router.get(
    "/users/count",
    description="Obtiene la cantidad total de usuarios de la plataforma"
)
async def get_all_users(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene el total de usuarios de la plataforma"""
    try:
       # 1. func.count(): Es una función de SQLAlchemy que se traduce a COUNT(*) en SQL.
        # 2. select(...): Construye la sentencia SELECT COUNT(*).
        # 3. select_from(...): Le dice a la consulta de qué tabla debe hacer el conteo.
        total_count_query = select(func.count()).select_from(UserModel)
        
        # 4. await db.execute(...): Ejecuta la consulta de forma asíncrona.
        total_count_result = await db.execute(total_count_query)
        
        # 5. .scalar(): Un método de SQLAlchemy que recupera un solo valor de la consulta.
        #    Esto es mucho más eficiente que .all() o .first() para este caso.
        total_users = total_count_result.scalar()
        
        return {
            "total_users": total_users,
            "message": "Cantidad de usuarios obtenida exitosamente"
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo cantidad de usuarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo cantidad de usuarios: {str(e)}"
        )

@router.get(
    "categories/count",
    description="Obtiene la cantidad total de categorías de la plataforma"
)
async def get_all_categories(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene el total de categorías de la plataforma"""
    try:
        
        total_count_query = select(func.count()).select_from(CategoriaModel)
        total_count_result = await db.execute(total_count_query)
        total_categories = total_count_result.scalar()
        
        return {
            "total_categories": total_categories,
            "message": "Cantidad de categorías obtenida exitosamente"
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo cantidad de categorías: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo cantidad de categorías: {str(e)}"
        )

@router.get(
    "services/count",
    description="Obtiene la cantidad total de servicios de la plataforma"
)
async def get_all_services(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene el total de servicios de la plataforma"""
    try:
        
        total_count_query = select(func.count()).select_from(ServicioModel)
        total_count_result = await db.execute(total_count_query)
        total_services = total_count_result.scalar()
        
        return {
            "total_services": total_services,
            "message": "Cantidad de servicios obtenida exitosamente"
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo cantidad de servicios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo cantidad de servicios: {str(e)}"
        )


@router.get(
    "providers/count",
    description="Obtiene la cantidad total de proveedores de la plataforma"
)
async def get_all_providers(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene el total de proveedores de la plataforma"""
    try:
        
        total_count_query = select(func.count()).select_from(PerfilEmpresa)
        total_count_result = await db.execute(total_count_query)
        total_providers = total_count_result.scalar()
        
        return {
            "total_providers": total_providers,
            "message": "Cantidad de proveedores obtenida exitosamente"
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo cantidad de proveedores: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo cantidad de proveedores: {str(e)}"
        )

@router.get(
    "/dashboard/stats",
    description="Obtiene todas las estadísticas del dashboard en una sola llamada optimizada con cache Redis"
)
async def get_dashboard_stats(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene todas las estadísticas del dashboard con cache Redis profesional"""
    try:
        import time
        start_time = time.time()
        
        # Clave de cache única para estadísticas del dashboard
        #cache_key_str = cache_key("dashboard", "stats")
        
        # Intentar obtener del cache Redis
        '''
        cached_result = await redis_cache.get(cache_key_str)
        if cached_result is not None:
            end_time = time.time()
            cache_time = (end_time - start_time) * 1000
            print(f"🚀 Cache hit - Tiempo: {cache_time:.2f}ms")
            return cached_result
        
        print(f"🔍 Cache miss - Consultando base de datos...")'''
        
        # OPTIMIZACIÓN: Usar una sola consulta SQL con subconsultas para máximo rendimiento
        # Usar direct_db_service para evitar problemas con PgBouncer
        conn = await direct_db_service.get_connection()
        try:
            stats_query = """
                SELECT 
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM categoria) as total_categories,
                    (SELECT COUNT(*) FROM servicio) as total_services,
                    (SELECT COUNT(*) FROM perfil_empresa) as total_providers,
                    (SELECT COUNT(*) FROM verificacion_solicitud) as total_verification_requests,
                    (SELECT COUNT(*) FROM verificacion_solicitud WHERE estado = 'aprobada') as approved_requests
            """
            
            stats_row = await conn.fetchrow(stats_query)
            
            # Extraer resultados de la consulta única
            total_users = stats_row['total_users'] or 0
            total_categories = stats_row['total_categories'] or 0
            total_services = stats_row['total_services'] or 0
            total_providers = stats_row['total_providers'] or 0
            total_verification_requests = stats_row['total_verification_requests'] or 0
            approved_requests = stats_row['approved_requests'] or 0
            
            # Calcular tasa de verificación
            verification_rate = 0
            if total_verification_requests > 0:
                verification_rate = round((approved_requests / total_verification_requests) * 100)
            
            # Preparar respuesta
            response_data = {
                "total_users": total_users,
                "total_categories": total_categories,
                "total_services": total_services,
                "total_providers": total_providers,
                "total_verification_requests": total_verification_requests,
                "approved_requests": approved_requests,
                "verification_rate": verification_rate,
                "message": "Estadísticas del dashboard obtenidas exitosamente",
                "cached": False,
                "cache_ttl": 300
            }
            
            # Guardar en cache Redis por 5 minutos (300 segundos)
            #await redis_cache.set(cache_key_str, response_data, ttl=300)
            
            end_time = time.time()
            query_time = (end_time - start_time) * 1000
            print(f"⏱️ Tiempo total de consultas: {query_time:.2f}ms")
            print(f"📊 Resultados: usuarios={total_users}, categorías={total_categories}, servicios={total_services}")
            print("💾 Datos guardados en cache Redis por 5 minutos")
            
            return response_data
        finally:
            await direct_db_service.pool.release(conn)
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas del dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas del dashboard: {e}"
        )

@router.post(
    "/cache/clear",
    description="Limpia el cache de estadísticas (solo para administradores)"
)
async def clear_dashboard_cache(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user)
):
    """Limpia el cache de estadísticas del dashboard"""
    try:
        # Limpiar cache por patrón
        deleted_keys = await redis_cache.clear_pattern("dashboard:*")
        
        return {
            "message": "Cache limpiado exitosamente",
            "deleted_keys": deleted_keys,
            "cleared_by": admin_user.name
        }
        
    except Exception as e:
        print(f"❌ Error limpiando cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error limpiando cache: {str(e)}"
        )