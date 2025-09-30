# OPTIMIZACIÓN: Endpoint de usuarios con paginación y búsqueda híbrida
# Este archivo contiene la versión optimizada del endpoint /users

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, func
from typing import List, Optional

from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.perfil import UserModel
from app.models.rol import RolModel
from app.models.usuario_rol import UsuarioRolModel
from app.schemas.user import UserProfileAndRolesOut
from app.api.v1.dependencies.auth_user import get_admin_user

# Función optimizada para obtener usuarios
async def get_users_optimized(
    admin_user: UserProfileAndRolesOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_db),
    search_empresa: str = None,
    search_nombre: str = None,
    page: int = 1,
    limit: int = 100
):
    """Obtiene usuarios con paginación y búsqueda optimizada"""
    try:
        print(f"🔍 DEBUG: Endpoint optimizado - Página: {page}, Límite: {limit}")
        print(f"🔍 DEBUG: Búsqueda empresa: {search_empresa}, nombre: {search_nombre}")

        # OPTIMIZACIÓN 1: Una sola consulta con JOIN para usuarios y roles
        base_query = select(
            UserModel.id,
            UserModel.nombre_persona,
            UserModel.nombre_empresa,
            UserModel.estado,
            UserModel.foto_perfil,
            RolModel.nombre.label('rol_nombre')
        ).select_from(
            UserModel
        ).outerjoin(
            UsuarioRolModel, UserModel.id == UsuarioRolModel.id_usuario
        ).outerjoin(
            RolModel, UsuarioRolModel.id_rol == RolModel.id
        )

        # Aplicar filtros de búsqueda
        if search_empresa and search_empresa.strip():
            search_term = f"%{search_empresa.strip()}%"
            base_query = base_query.where(UserModel.nombre_empresa.ilike(search_term))
            print(f"🔍 DEBUG: Filtro empresa aplicado: {search_term}")

        if search_nombre and search_nombre.strip():
            search_term = f"%{search_nombre.strip()}%"
            base_query = base_query.where(UserModel.nombre_persona.ilike(search_term))
            print(f"🔍 DEBUG: Filtro nombre aplicado: {search_term}")

        # OPTIMIZACIÓN 2: Obtener total de registros para paginación
        count_query = select(func.count(func.distinct(UserModel.id)))
        if search_empresa and search_empresa.strip():
            count_query = count_query.where(UserModel.nombre_empresa.ilike(f"%{search_empresa.strip()}%"))
        if search_nombre and search_nombre.strip():
            count_query = count_query.where(UserModel.nombre_persona.ilike(f"%{search_nombre.strip()}%"))

        total_result = await db.execute(count_query)
        total_users = total_result.scalar()

        # OPTIMIZACIÓN 3: Aplicar paginación
        offset = (page - 1) * limit
        base_query = base_query.offset(offset).limit(limit)

        # Ejecutar consulta optimizada
        result = await db.execute(base_query)
        users_with_roles = result.all()

        print(f"🔍 DEBUG: {len(users_with_roles)} registros obtenidos de {total_users} totales")

        # OPTIMIZACIÓN 4: Obtener todos los emails de Supabase de una vez
        from app.supabase.auth_service import supabase_admin
        auth_users = supabase_admin.auth.admin.list_users()
        emails_dict = {}
        if auth_users and auth_users.users:
            for auth_user in auth_users.users:
                if auth_user.id and auth_user.email:
                    emails_dict[auth_user.id] = {
                        "email": auth_user.email,
                        "ultimo_acceso": auth_user.last_sign_in_at
                    }

        # OPTIMIZACIÓN 5: Procesar resultados agrupados por usuario
        users_dict = {}
        for row in users_with_roles:
            user_id = str(row.id)
            
            if user_id not in users_dict:
                # Crear usuario base
                users_dict[user_id] = {
                    "id": user_id,
                    "nombre_persona": row.nombre_persona,
                    "nombre_empresa": row.nombre_empresa,
                    "foto_perfil": row.foto_perfil,
                    "estado": row.estado or "ACTIVO",
                    "roles": [],
                    "rol_principal": "client",
                    "email": "No disponible",
                    "ultimo_acceso": None
                }

                # Agregar email si existe
                if user_id in emails_dict:
                    users_dict[user_id]["email"] = emails_dict[user_id]["email"]
                    users_dict[user_id]["ultimo_acceso"] = emails_dict[user_id]["ultimo_acceso"]

            # Agregar rol si existe
            if row.rol_nombre:
                users_dict[user_id]["roles"].append(row.rol_nombre)

        # OPTIMIZACIÓN 6: Determinar rol principal para cada usuario
        users_data = []
        for user_id, user_data in users_dict.items():
            roles = user_data["roles"]
            user_data["todos_roles"] = roles.copy()

            # Determinar rol principal
            normalized_roles = [rol.lower().strip() for rol in roles]
            if any(admin_role in normalized_roles for admin_role in ["admin", "administrador", "administrator"]):
                user_data["rol_principal"] = "admin"
            elif any(provider_role in normalized_roles for provider_role in ["provider", "proveedor", "proveedores"]):
                user_data["rol_principal"] = "provider"
            elif any(client_role in normalized_roles for client_role in ["client", "cliente"]):
                user_data["rol_principal"] = "client"
            else:
                user_data["rol_principal"] = "client"

            users_data.append(user_data)

        print(f"🔍 DEBUG: Procesamiento completado, {len(users_data)} usuarios listos")

        return {
            "usuarios": users_data,
            "total": total_users,
            "page": page,
            "limit": limit,
            "total_pages": (total_users + limit - 1) // limit,
            "message": "Usuarios obtenidos exitosamente"
        }

    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo usuarios: {str(e)}"
        )






