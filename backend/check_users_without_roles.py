#!/usr/bin/env python3
"""
Script para verificar usuarios sin roles (solo lectura)
"""
import asyncio
import sys
import os
import asyncpg

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import DATABASE_URL

async def check_users_without_roles():
    """Verificar usuarios que no tienen roles asignados (solo lectura)"""
    print("🔍 Verificando usuarios sin roles...")
    print(f"📡 DATABASE_URL: {DATABASE_URL}")
    
    try:
        # Extraer parámetros de conexión
        url_parts = DATABASE_URL.replace('postgresql://', '').split('@')
        user_pass = url_parts[0].split(':')
        user = user_pass[0]
        password = user_pass[1]
        
        host_port_db = url_parts[1].split('/')
        host_port = host_port_db[0].split(':')
        host = host_port[0]
        port = int(host_port[1])
        database = host_port_db[1]
        
        # Conectar directamente
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            statement_cache_size=0,
            command_timeout=30
        )
        
        print("✅ Conexión exitosa!")
        
        # Verificar usuarios sin roles
        users_without_roles = await conn.fetch("""
            SELECT 
                u.id, 
                u.nombre_persona, 
                u.nombre_empresa, 
                u.ruc,
                u.estado,
                u.created_at,
                u.foto_perfil
            FROM users u
            LEFT JOIN usuario_rol ur ON u.id = ur.id_usuario
            WHERE ur.id_usuario IS NULL
            ORDER BY u.created_at DESC
        """)
        
        print(f"\n📊 Usuarios sin roles: {len(users_without_roles)}")
        
        if len(users_without_roles) == 0:
            print("✅ ¡Excelente! No hay usuarios sin roles.")
            await conn.close()
            return True
        
        # Mostrar detalles de usuarios sin roles
        print("\n👥 Usuarios sin roles asignados:")
        print("=" * 80)
        
        for i, user in enumerate(users_without_roles, 1):
            print(f"{i}. ID: {user['id']}")
            print(f"   Nombre: {user['nombre_persona']}")
            print(f"   Empresa: {user['nombre_empresa']}")
            print(f"   RUC: {user['ruc'] or 'N/A'}")
            print(f"   Estado: {user['estado']}")
            print(f"   Creado: {user['created_at']}")
            print(f"   Foto: {'Sí' if user['foto_perfil'] else 'No'}")
            print("-" * 40)
        
        # Verificar usuarios CON roles para comparación
        users_with_roles = await conn.fetch("""
            SELECT 
                u.id, 
                u.nombre_persona, 
                COUNT(ur.id_rol) as role_count,
                STRING_AGG(r.nombre, ', ') as roles
            FROM users u
            INNER JOIN usuario_rol ur ON u.id = ur.id_usuario
            INNER JOIN rol r ON ur.id_rol = r.id
            GROUP BY u.id, u.nombre_persona
            ORDER BY role_count DESC
            LIMIT 5
        """)
        
        print(f"\n✅ Usuarios CON roles (ejemplos): {len(users_with_roles)}")
        for user in users_with_roles:
            print(f"  - {user['nombre_persona']}: {user['role_count']} rol(es) - {user['roles']}")
        
        # Estadísticas generales
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        users_with_roles_count = await conn.fetchval("""
            SELECT COUNT(DISTINCT u.id) 
            FROM users u
            INNER JOIN usuario_rol ur ON u.id = ur.id_usuario
        """)
        
        print(f"\n📈 Estadísticas:")
        print(f"  - Total de usuarios: {total_users}")
        print(f"  - Usuarios con roles: {users_with_roles_count}")
        print(f"  - Usuarios sin roles: {len(users_without_roles)}")
        print(f"  - Porcentaje sin roles: {(len(users_without_roles)/total_users*100):.1f}%")
        
        await conn.close()
        print("\n🎉 Verificación completada!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(check_users_without_roles())
    sys.exit(0 if success else 1)

