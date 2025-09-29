#!/usr/bin/env python3
"""
Script para eliminar usuarios sin roles asignados
"""
import asyncio
import sys
import os
import asyncpg
from datetime import datetime

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import DATABASE_URL

async def cleanup_users_without_roles():
    """Eliminar usuarios que no tienen roles asignados"""
    print("🧹 Limpiando usuarios sin roles...")
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
        
        # Primero, identificar usuarios sin roles
        users_without_roles = await conn.fetch("""
            SELECT u.id, u.nombre_persona, u.nombre_empresa, u.created_at
            FROM users u
            LEFT JOIN usuario_rol ur ON u.id = ur.id_usuario
            WHERE ur.id_usuario IS NULL
            ORDER BY u.created_at DESC
        """)
        
        print(f"👥 Usuarios sin roles encontrados: {len(users_without_roles)}")
        
        if len(users_without_roles) == 0:
            print("✅ No hay usuarios sin roles. Base de datos limpia!")
            await conn.close()
            return True
        
        # Mostrar usuarios que serán eliminados
        print("\n📋 Usuarios que serán eliminados:")
        for user in users_without_roles:
            print(f"  - {user['id']}: {user['nombre_persona']} ({user['nombre_empresa']}) - {user['created_at']}")
        
        # Confirmar eliminación
        print(f"\n⚠️  ADVERTENCIA: Se eliminarán {len(users_without_roles)} usuarios sin roles.")
        print("💡 Esto incluye:")
        print("   - Perfiles de usuarios en la tabla 'users'")
        print("   - Datos relacionados (direcciones, documentos, etc.)")
        print("   - NO se eliminarán usuarios de Supabase Auth")
        
        # Crear backup antes de eliminar
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_users_without_roles_{backup_timestamp}.sql"
        
        print(f"\n💾 Creando backup en: {backup_file}")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup de usuarios sin roles - {datetime.now()}\n")
            f.write(f"-- Total de usuarios: {len(users_without_roles)}\n\n")
            
            for user in users_without_roles:
                f.write(f"-- Usuario: {user['nombre_persona']} ({user['nombre_empresa']})\n")
                f.write(f"-- ID: {user['id']}\n")
                f.write(f"-- Creado: {user['created_at']}\n")
                f.write(f"INSERT INTO users (id, nombre_persona, nombre_empresa, ruc, estado, created_at) VALUES ('{user['id']}', '{user['nombre_persona']}', '{user['nombre_empresa']}', NULL, 'ACTIVO', '{user['created_at']}');\n\n")
        
        print(f"✅ Backup creado: {backup_file}")
        
        # Eliminar usuarios sin roles
        print("\n🗑️  Eliminando usuarios sin roles...")
        
        # Eliminar en orden para respetar foreign keys
        deleted_count = 0
        
        for user in users_without_roles:
            user_id = user['id']
            user_name = user['nombre_persona']
            
            try:
                # Eliminar datos relacionados primero
                await conn.execute("""
                    DELETE FROM direccion WHERE id_usuario = $1
                """, user_id)
                
                await conn.execute("""
                    DELETE FROM documento WHERE id_usuario = $1
                """, user_id)
                
                await conn.execute("""
                    DELETE FROM perfil_empresa WHERE id_usuario = $1
                """, user_id)
                
                # Eliminar el usuario principal
                await conn.execute("""
                    DELETE FROM users WHERE id = $1
                """, user_id)
                
                deleted_count += 1
                print(f"  ✅ Eliminado: {user_name} ({user_id})")
                
            except Exception as e:
                print(f"  ❌ Error eliminando {user_name}: {e}")
        
        print(f"\n🎉 Limpieza completada!")
        print(f"📊 Usuarios eliminados: {deleted_count}/{len(users_without_roles)}")
        print(f"💾 Backup guardado en: {backup_file}")
        
        # Verificar que no quedan usuarios sin roles
        remaining_users = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM users u
            LEFT JOIN usuario_rol ur ON u.id = ur.id_usuario
            WHERE ur.id_usuario IS NULL
        """)
        
        remaining_count = remaining_users[0]['count']
        if remaining_count == 0:
            print("✅ ¡Base de datos completamente limpia! No quedan usuarios sin roles.")
        else:
            print(f"⚠️  Aún quedan {remaining_count} usuarios sin roles.")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Script de limpieza de usuarios sin roles")
    print("=" * 50)
    
    # Preguntar confirmación
    print("\n⚠️  ADVERTENCIA: Este script eliminará TODOS los usuarios que no tengan roles asignados.")
    print("💡 Se creará un backup antes de eliminar.")
    print("🔒 Los usuarios de Supabase Auth NO serán eliminados.")
    
    confirm = input("\n¿Continuar? (escribe 'SI' para confirmar): ")
    
    if confirm.upper() == 'SI':
        success = asyncio.run(cleanup_users_without_roles())
        if success:
            print("\n🎉 ¡Limpieza completada exitosamente!")
        else:
            print("\n❌ Error durante la limpieza.")
    else:
        print("\n❌ Operación cancelada por el usuario.")

