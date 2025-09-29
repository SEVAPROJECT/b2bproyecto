#!/usr/bin/env python3
"""
Script para asignar rol 'Cliente' a usuarios que no tienen roles
"""
import asyncio
import sys
import os
import asyncpg
from datetime import datetime

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import DATABASE_URL

async def assign_roles_to_users():
    """Asignar rol 'Cliente' a usuarios que no tienen roles"""
    print("🔧 Asignando roles a usuarios sin roles...")
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
        
        # Verificar que existe el rol 'Cliente'
        cliente_role = await conn.fetchrow("""
            SELECT id, nombre FROM rol WHERE nombre = 'Cliente'
        """)
        
        if not cliente_role:
            print("❌ Error: El rol 'Cliente' no existe en la base de datos!")
            print("💡 Primero debes crear el rol 'Cliente' en la tabla 'rol'")
            await conn.close()
            return False
        
        print(f"✅ Rol 'Cliente' encontrado: ID {cliente_role['id']}")
        
        # Identificar usuarios sin roles
        users_without_roles = await conn.fetch("""
            SELECT u.id, u.nombre_persona, u.nombre_empresa
            FROM users u
            LEFT JOIN usuario_rol ur ON u.id = ur.id_usuario
            WHERE ur.id_usuario IS NULL
            ORDER BY u.created_at DESC
        """)
        
        print(f"👥 Usuarios sin roles encontrados: {len(users_without_roles)}")
        
        if len(users_without_roles) == 0:
            print("✅ No hay usuarios sin roles. ¡Todo está correcto!")
            await conn.close()
            return True
        
        # Mostrar usuarios que recibirán el rol
        print("\n📋 Usuarios que recibirán el rol 'Cliente':")
        for user in users_without_roles:
            print(f"  - {user['nombre_persona']} ({user['nombre_empresa']}) - ID: {user['id']}")
        
        # Asignar rol 'Cliente' a todos los usuarios sin roles
        print(f"\n🔧 Asignando rol 'Cliente' a {len(users_without_roles)} usuarios...")
        
        assigned_count = 0
        cliente_role_id = cliente_role['id']
        
        for user in users_without_roles:
            user_id = user['id']
            user_name = user['nombre_persona']
            
            try:
                # Verificar que el usuario no tenga ya el rol
                existing_role = await conn.fetchrow("""
                    SELECT id_usuario FROM usuario_rol 
                    WHERE id_usuario = $1 AND id_rol = $2
                """, user_id, cliente_role_id)
                
                if existing_role:
                    print(f"  ⚠️  {user_name} ya tiene el rol 'Cliente'")
                    continue
                
                # Asignar el rol
                await conn.execute("""
                    INSERT INTO usuario_rol (id_usuario, id_rol, created_at)
                    VALUES ($1, $2, NOW())
                """, user_id, cliente_role_id)
                
                assigned_count += 1
                print(f"  ✅ Rol asignado a: {user_name}")
                
            except Exception as e:
                print(f"  ❌ Error asignando rol a {user_name}: {e}")
        
        print(f"\n🎉 Asignación completada!")
        print(f"📊 Roles asignados: {assigned_count}/{len(users_without_roles)}")
        
        # Verificar que no quedan usuarios sin roles
        remaining_users = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM users u
            LEFT JOIN usuario_rol ur ON u.id = ur.id_usuario
            WHERE ur.id_usuario IS NULL
        """)
        
        remaining_count = remaining_users[0]['count']
        if remaining_count == 0:
            print("✅ ¡Perfecto! Todos los usuarios ahora tienen roles asignados.")
        else:
            print(f"⚠️  Aún quedan {remaining_count} usuarios sin roles.")
        
        # Mostrar estadísticas finales
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        users_with_roles_count = await conn.fetchval("""
            SELECT COUNT(DISTINCT u.id) 
            FROM users u
            INNER JOIN usuario_rol ur ON u.id = ur.id_usuario
        """)
        
        print(f"\n📈 Estadísticas finales:")
        print(f"  - Total de usuarios: {total_users}")
        print(f"  - Usuarios con roles: {users_with_roles_count}")
        print(f"  - Usuarios sin roles: {remaining_count}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error durante la asignación: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Script para asignar roles a usuarios sin roles")
    print("=" * 50)
    
    success = asyncio.run(assign_roles_to_users())
    if success:
        print("\n🎉 ¡Asignación completada exitosamente!")
    else:
        print("\n❌ Error durante la asignación.")

