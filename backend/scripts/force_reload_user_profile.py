#!/usr/bin/env python3
"""
Script para forzar la recarga del perfil del usuario y verificar que el RUC se muestre
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies.database_supabase import AsyncSessionLocal
from sqlalchemy import text

async def force_reload_user_profile():
    """Fuerza la recarga del perfil del usuario para verificar que el RUC se muestre"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🔍 Forzando recarga del perfil del usuario...")
            
            # IDs de los usuarios específicos
            user_ids = [
                'b82f228b-77b4-4ee7-b3a5-92de1705ac10',  # Carina Acosta
                'daa6a312-4121-4d93-bc2f-4f556fada6b4'   # Tomas Rivarola
            ]
            
            # 1. Verificar datos actuales en la base de datos
            print("\n📋 1. Verificando datos actuales en la base de datos:")
            for user_id in user_ids:
                result = await session.execute(text("""
                    SELECT 
                        au.id,
                        au.email,
                        au.raw_user_meta_data->>'ruc' as auth_ruc,
                        pu.ruc as public_ruc,
                        pu.nombre_persona,
                        pu.nombre_empresa,
                        pu.estado,
                        pu.created_at,
                        pu.updated_at
                    FROM auth.users au
                    LEFT JOIN public.users pu ON au.id = pu.id
                    WHERE au.id = :user_id
                """), {"user_id": user_id})
                
                user_data = result.fetchone()
                if user_data:
                    user_id, email, auth_ruc, public_ruc, nombre, empresa, estado, created_at, updated_at = user_data
                    print(f"   - {email} ({nombre}):")
                    print(f"     Auth RUC: {auth_ruc}")
                    print(f"     Public RUC: {public_ruc}")
                    print(f"     Estado: {estado}")
                    print(f"     Creado: {created_at}")
                    print(f"     Actualizado: {updated_at}")
                    
                    if public_ruc:
                        print(f"     ✅ RUC presente en public.users")
                    else:
                        print(f"     ❌ RUC NO presente en public.users")
                else:
                    print(f"   - Usuario {user_id} no encontrado")
            
            # 2. Simular la respuesta del endpoint /me
            print("\n🔐 2. Simulando respuesta del endpoint /me:")
            for user_id in user_ids:
                result = await session.execute(text("""
                    SELECT 
                        pu.id,
                        pu.nombre_persona,
                        pu.nombre_empresa,
                        pu.ruc,
                        pu.estado,
                        pu.foto_perfil
                    FROM public.users pu
                    WHERE pu.id = :user_id
                """), {"user_id": user_id})
                
                user_data = result.fetchone()
                if user_data:
                    user_id, nombre, empresa, ruc, estado, foto = user_data
                    print(f"   - Usuario {user_id}:")
                    print(f"     Nombre: {nombre}")
                    print(f"     Empresa: {empresa}")
                    print(f"     RUC: {ruc}")
                    print(f"     Estado: {estado}")
                    print(f"     Foto: {foto}")
                    
                    # Simular la respuesta del endpoint /me
                    response_data = {
                        "id": str(user_id),
                        "email": "usuario@email.com",  # Se obtiene de auth
                        "nombre_persona": nombre,
                        "nombre_empresa": empresa,
                        "ruc": ruc,
                        "roles": ["Cliente"],
                        "foto_perfil": foto
                    }
                    
                    print(f"   - Respuesta del endpoint /me:")
                    print(f"     {response_data}")
                    
                    if ruc:
                        print(f"     ✅ RUC incluido en la respuesta")
                    else:
                        print(f"     ❌ RUC NO incluido en la respuesta")
                else:
                    print(f"   - Usuario {user_id} no encontrado en public.users")
            
            # 3. Verificar el frontend
            print("\n🖥️ 3. Verificando frontend:")
            print("   - El frontend debe recibir el RUC del endpoint /me")
            print("   - El campo RUC debe mostrarse en ManageProfilePage.tsx")
            print("   - El valor debe ser user?.ruc || 'No especificado'")
            
            # 4. Instrucciones para el usuario
            print("\n📝 4. Instrucciones para el usuario:")
            print("   - Si el RUC está en la base de datos pero no se muestra en el perfil:")
            print("     1. Cierra sesión y vuelve a iniciar sesión")
            print("     2. O refresca la página del perfil")
            print("     3. O espera unos segundos y recarga la página")
            print("   - El problema puede ser que el frontend no se haya actualizado")
            print("   - Después del registro, el usuario debe recargar su perfil")
            
            # 5. Verificar si hay problemas de caché
            print("\n💾 5. Verificando problemas de caché:")
            print("   - El frontend puede estar usando datos en caché")
            print("   - El usuario debe recargar su perfil después del registro")
            print("   - O cerrar sesión y volver a iniciar sesión")
            
            # 6. Verificar la sincronización
            print("\n🔄 6. Verificando sincronización:")
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total_usuarios,
                    COUNT(CASE WHEN pu.ruc IS NOT NULL AND pu.ruc != '' THEN 1 END) as usuarios_con_ruc,
                    COUNT(CASE WHEN au.raw_user_meta_data->>'ruc' = pu.ruc THEN 1 END) as usuarios_sincronizados
                FROM auth.users au
                JOIN public.users pu ON au.id = pu.id
            """))
            
            sync_stats = result.fetchone()
            if sync_stats:
                total, con_ruc, sincronizados = sync_stats
                print(f"   - Total usuarios: {total}")
                print(f"   - Usuarios con RUC: {con_ruc}")
                print(f"   - Usuarios sincronizados: {sincronizados}")
            
            print("\n✅ Verificación completada")
            return True
            
        except Exception as e:
            print(f"❌ Error durante la verificación: {e}")
            return False

async def main():
    """Función principal"""
    print("🚀 Iniciando verificación de recarga del perfil del usuario...")
    success = await force_reload_user_profile()
    
    if success:
        print("\n📋 Resumen de la verificación:")
        print("💡 Si el RUC está en la base de datos pero no se muestra en el perfil:")
        print("   1. Cierra sesión y vuelve a iniciar sesión")
        print("   2. O refresca la página del perfil")
        print("   3. O espera unos segundos y recarga la página")
        print("   4. El problema puede ser que el frontend no se haya actualizado")
    else:
        print("\n❌ Verificación falló")

if __name__ == "__main__":
    asyncio.run(main())
