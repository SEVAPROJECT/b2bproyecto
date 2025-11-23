#!/usr/bin/env python3
"""
Script para agregar el rol de proveedor a un usuario verificado
"""

import asyncio
import asyncpg

async def fix_user_provider_role():
    """Agrega el rol de proveedor a un usuario verificado"""
    
    DATABASE_URL = "postgresql://postgres:postgres@localhost:54322/postgres"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Información del usuario
        user_uuid = "ee26dfbe-f1bd-4e5c-ba98-c0dfe61dcb4a"
        user_email = "david.perez@gmail.com"
        
        print(f"🔧 Solucionando rol de proveedor para: {user_email}")
        print(f"🆔 UUID: {user_uuid}")
        print("=" * 60)
        
        # 1. Verificar que el usuario existe
        print("1️⃣ Verificando usuario...")
        user_query = """
            SELECT id, email
            FROM auth.users 
            WHERE id = $1
        """
        user = await conn.fetchrow(user_query, user_uuid)
        
        if not user:
            print(f"❌ Usuario no encontrado con UUID: {user_uuid}")
            return
        
        print(f"✅ Usuario encontrado: {user['email']}")
        
        # 2. Verificar que el perfil está verificado
        print("\n2️⃣ Verificando perfil de empresa...")
        empresa_query = """
            SELECT id_perfil, user_id, razon_social, estado, verificado
            FROM public.perfil_empresa 
            WHERE user_id = $1
        """
        empresa = await conn.fetchrow(empresa_query, user_uuid)
        
        if not empresa:
            print("❌ No se encontró perfil de empresa")
            return
        
        if not (empresa['estado'] == 'verificado' and empresa['verificado']):
            print(f"❌ El perfil no está verificado - Estado: {empresa['estado']}, Verificado: {empresa['verificado']}")
            return
        
        print(f"✅ Perfil verificado: {empresa['razon_social']}")
        
        # 3. Buscar el rol de proveedor
        print("\n3️⃣ Buscando rol de proveedor...")
        provider_role_query = """
            SELECT id, nombre
            FROM public.rol
            WHERE nombre ILIKE '%proveedor%'
        """
        provider_role = await conn.fetchrow(provider_role_query)
        
        if not provider_role:
            print("❌ No se encontró rol de proveedor en el sistema")
            return
        
        print(f"✅ Rol de proveedor encontrado: {provider_role['nombre']} (ID: {provider_role['id']})")
        
        # 4. Verificar si ya tiene el rol de proveedor
        print("\n4️⃣ Verificando roles actuales...")
        current_roles_query = """
            SELECT ur.id_usuario, ur.id_rol, r.nombre as rol_nombre
            FROM public.usuario_rol ur
            JOIN public.rol r ON ur.id_rol = r.id
            WHERE ur.id_usuario = $1
        """
        current_roles = await conn.fetch(current_roles_query, user_uuid)
        
        print(f"✅ Roles actuales ({len(current_roles)}):")
        for role in current_roles:
            print(f"   - {role['rol_nombre']} (ID: {role['id_rol']})")
        
        # Verificar si ya tiene rol de proveedor
        has_provider_role = any(role['id_rol'] == provider_role['id'] for role in current_roles)
        
        if has_provider_role:
            print("✅ El usuario ya tiene el rol de proveedor")
            return
        
        # 5. Agregar el rol de proveedor
        print("\n5️⃣ Agregando rol de proveedor...")
        
        # Verificar que no existe ya la relación
        existing_role_query = """
            SELECT id_usuario, id_rol
            FROM public.usuario_rol
            WHERE id_usuario = $1 AND id_rol = $2
        """
        existing_role = await conn.fetchrow(existing_role_query, user_uuid, provider_role['id'])
        
        if existing_role:
            print("✅ El rol de proveedor ya está asignado")
            return
        
        # Insertar el rol de proveedor
        insert_role_query = """
            INSERT INTO public.usuario_rol (id_usuario, id_rol, created_at)
            VALUES ($1, $2, NOW())
        """
        
        await conn.execute(insert_role_query, user_uuid, provider_role['id'])
        print("✅ Rol de proveedor agregado exitosamente")
        
        # 6. Verificar el resultado
        print("\n6️⃣ Verificando resultado...")
        updated_roles = await conn.fetch(current_roles_query, user_uuid)
        
        print(f"✅ Roles actualizados ({len(updated_roles)}):")
        for role in updated_roles:
            print(f"   - {role['rol_nombre']} (ID: {role['id_rol']})")
        
        # Determinar rol principal
        role_names = [role['rol_nombre'] for role in updated_roles]
        normalized_roles = [rol.lower().strip() for rol in role_names]
        
        if any(admin_role in normalized_roles for admin_role in ["admin", "administrador", "administrator"]):
            rol_principal = "admin"
        elif any(provider_role in normalized_roles for provider_role in ["provider", "proveedor", "proveedores"]):
            rol_principal = "provider"
        elif any(client_role in normalized_roles for client_role in ["client", "cliente"]):
            rol_principal = "client"
        else:
            rol_principal = "client"
        
        print(f"✅ Rol principal actualizado: {rol_principal}")
        
        print("\n" + "=" * 60)
        print("🎉 SOLUCIÓN COMPLETADA:")
        print(f"   - Usuario: {user['email']}")
        print(f"   - Empresa: {empresa['razon_social']}")
        print(f"   - Estado: {empresa['estado']}")
        print(f"   - Verificado: {empresa['verificado']}")
        print(f"   - Roles: {role_names}")
        print(f"   - Rol principal: {rol_principal}")
        print()
        print("✅ El usuario ahora debería aparecer como proveedor en el frontend")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error durante la solución: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_user_provider_role())
