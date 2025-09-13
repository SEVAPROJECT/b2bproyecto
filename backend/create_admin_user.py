#!/usr/bin/env python3
"""
Script para crear un usuario administrador en la base de datos
"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies.database_supabase import AsyncSessionLocal
from app.models.perfil import UserModel
from app.models.rol import RolModel
from app.models.usuario_rol import UsuarioRolModel
from sqlalchemy.future import select
from sqlalchemy import insert

async def create_admin_user():
    """Crea un usuario administrador"""
    
    # Datos del administrador
    admin_email = "admin@seva.com"
    admin_nombre_persona = "Administrador"
    admin_nombre_empresa = "SEVA B2B"
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Verificar si el usuario ya existe
            result = await session.execute(
                select(UserModel).where(UserModel.email == admin_email)
            )
            existing_user = result.scalars().first()
            
            if existing_user:
                print(f"❌ El usuario {admin_email} ya existe")
                return
            
            # 2. Crear el usuario
            admin_user_id = str(uuid.uuid4())
            admin_user = UserModel(
                id=admin_user_id,
                email=admin_email,
                nombre_persona=admin_nombre_persona,
                nombre_empresa=admin_nombre_empresa
            )
            
            session.add(admin_user)
            await session.flush()  # Para obtener el ID
            
            # 3. Buscar el rol de administrador
            result = await session.execute(
                select(RolModel).where(RolModel.nombre == "admin")
            )
            admin_role = result.scalars().first()
            
            if not admin_role:
                print("❌ El rol 'admin' no existe en la base de datos")
                print("💡 Ejecuta primero el script para crear roles básicos")
                return
            
            # 4. Asignar el rol de administrador al usuario
            usuario_rol = UsuarioRolModel(
                id_usuario=admin_user_id,
                id_rol=admin_role.id_rol
            )
            
            session.add(usuario_rol)
            await session.commit()
            
            print(f"✅ Usuario administrador creado exitosamente:")
            print(f"   Email: {admin_email}")
            print(f"   Nombre: {admin_nombre_persona}")
            print(f"   Empresa: {admin_nombre_empresa}")
            print(f"   ID: {admin_user_id}")
            print(f"   Rol: {admin_role.nombre}")
            print("\n🔑 Ahora puedes registrarte en el frontend con estos datos:")
            print(f"   Email: {admin_email}")
            print("   Contraseña: (la que elijas al registrarte)")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error al crear usuario administrador: {e}")
            raise

async def create_basic_roles():
    """Crea los roles básicos si no existen"""
    
    async with AsyncSessionLocal() as session:
        try:
            # Roles básicos
            basic_roles = [
                {"nombre": "admin", "descripcion": "Administrador del sistema"},
                {"nombre": "provider", "descripcion": "Proveedor de servicios"},
                {"nombre": "client", "descripcion": "Cliente de la plataforma"}
            ]
            
            for role_data in basic_roles:
                # Verificar si el rol ya existe
                result = await session.execute(
                    select(RolModel).where(RolModel.nombre == role_data["nombre"])
                )
                existing_role = result.scalars().first()
                
                if not existing_role:
                    # Crear el rol
                    new_role = RolModel(**role_data)
                    session.add(new_role)
                    print(f"✅ Rol '{role_data['nombre']}' creado")
                else:
                    print(f"ℹ️  Rol '{role_data['nombre']}' ya existe")
            
            await session.commit()
            print("✅ Roles básicos verificados/creados")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error al crear roles básicos: {e}")
            raise

async def main():
    """Función principal"""
    print("🚀 Iniciando creación de usuario administrador...")
    print("=" * 50)
    
    # 1. Crear roles básicos
    print("\n📋 Paso 1: Verificando roles básicos...")
    await create_basic_roles()
    
    # 2. Crear usuario administrador
    print("\n👤 Paso 2: Creando usuario administrador...")
    await create_admin_user()
    
    print("\n🎉 Proceso completado!")

if __name__ == "__main__":
    asyncio.run(main())
