#!/usr/bin/env python3
"""
Script para insertar RUCs genéricos en todos los usuarios que no posean RUC en la tabla public.users
"""
import asyncio
import random
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies.database_supabase import AsyncSessionLocal
from sqlalchemy import text

def generate_generic_ruc():
    """
    Genera un RUC genérico válido para Paraguay
    Formato: 8 dígitos seguidos de un guión y un dígito verificador
    """
    # Generar 8 dígitos aleatorios
    digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    
    # Calcular dígito verificador (algoritmo simplificado para Paraguay)
    # En la realidad, el dígito verificador se calcula con un algoritmo específico
    # Aquí usamos un dígito aleatorio para simplicidad
    check_digit = random.randint(0, 9)
    
    return f"{digits}-{check_digit}"

async def insert_generic_ruc_for_users():
    """Inserta RUCs genéricos en todos los usuarios que no posean RUC"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🔍 Insertando RUCs genéricos en usuarios sin RUC...")
            
            # 1. Verificar usuarios sin RUC
            print("\n📋 1. Verificando usuarios sin RUC:")
            result = await session.execute(text("""
                SELECT 
                    pu.id,
                    pu.nombre_persona,
                    pu.nombre_empresa,
                    pu.ruc,
                    au.email
                FROM public.users pu
                LEFT JOIN auth.users au ON pu.id = au.id
                WHERE pu.ruc IS NULL OR pu.ruc = ''
                ORDER BY pu.created_at
            """))
            
            users_without_ruc = result.fetchall()
            
            if not users_without_ruc:
                print("   ✅ Todos los usuarios ya tienen RUC asignado")
                return True
            
            print(f"   📊 Encontrados {len(users_without_ruc)} usuarios sin RUC:")
            for user in users_without_ruc:
                user_id, nombre, empresa, ruc, email = user
                print(f"     - {email} ({nombre}) - Empresa: {empresa}")
            
            # 2. Generar RUCs genéricos únicos
            print("\n🔢 2. Generando RUCs genéricos únicos:")
            used_rucs = set()
            generic_rucs = []
            
            for user in users_without_ruc:
                while True:
                    generic_ruc = generate_generic_ruc()
                    if generic_ruc not in used_rucs:
                        used_rucs.add(generic_ruc)
                        generic_rucs.append(generic_ruc)
                        break
            
            print(f"   📊 Generados {len(generic_rucs)} RUCs genéricos únicos:")
            for i, ruc in enumerate(generic_rucs):
                user_id, nombre, empresa, _, email = users_without_ruc[i]
                print(f"     - {email} ({nombre}): {ruc}")
            
            # 3. Insertar RUCs genéricos
            print("\n💾 3. Insertando RUCs genéricos en la base de datos:")
            updated_count = 0
            
            for i, user in enumerate(users_without_ruc):
                user_id, nombre, empresa, _, email = user
                generic_ruc = generic_rucs[i]
                
                try:
                    await session.execute(text("""
                        UPDATE public.users 
                        SET ruc = :ruc
                        WHERE id = :user_id
                    """), {"ruc": generic_ruc, "user_id": user_id})
                    
                    updated_count += 1
                    print(f"   ✅ {email} ({nombre}): RUC {generic_ruc} asignado")
                    
                except Exception as e:
                    print(f"   ❌ Error actualizando {email}: {e}")
            
            # 4. Confirmar cambios
            await session.commit()
            print(f"\n✅ {updated_count} usuarios actualizados con RUCs genéricos")
            
            # 5. Verificar resultados
            print("\n🔍 4. Verificando resultados:")
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total_usuarios,
                    COUNT(CASE WHEN ruc IS NOT NULL AND ruc != '' THEN 1 END) as usuarios_con_ruc,
                    COUNT(CASE WHEN ruc IS NULL OR ruc = '' THEN 1 END) as usuarios_sin_ruc
                FROM public.users
            """))
            
            stats = result.fetchone()
            if stats:
                total, con_ruc, sin_ruc = stats
                print(f"   📊 Estadísticas finales:")
                print(f"     - Total usuarios: {total}")
                print(f"     - Usuarios con RUC: {con_ruc}")
                print(f"     - Usuarios sin RUC: {sin_ruc}")
                
                if sin_ruc == 0:
                    print(f"     ✅ Todos los usuarios ahora tienen RUC")
                else:
                    print(f"     ⚠️  Aún hay {sin_ruc} usuarios sin RUC")
            
            # 6. Mostrar algunos ejemplos de RUCs asignados
            print("\n📋 5. Ejemplos de RUCs asignados:")
            result = await session.execute(text("""
                SELECT 
                    pu.nombre_persona,
                    pu.nombre_empresa,
                    pu.ruc,
                    au.email
                FROM public.users pu
                LEFT JOIN auth.users au ON pu.id = au.id
                WHERE pu.ruc IS NOT NULL AND pu.ruc != ''
                ORDER BY pu.updated_at DESC
                LIMIT 5
            """))
            
            examples = result.fetchall()
            for example in examples:
                nombre, empresa, ruc, email = example
                print(f"   - {email} ({nombre}): {ruc}")
            
            print("\n✅ Script completado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
            await session.rollback()
            return False

async def main():
    """Función principal"""
    print("🚀 Iniciando inserción de RUCs genéricos para usuarios sin RUC...")
    print("⚠️  ADVERTENCIA: Este script asignará RUCs genéricos a usuarios que no tienen RUC")
    print("💡 Los RUCs generados son válidos en formato pero no son RUCs reales")
    
    # Confirmar ejecución
    confirm = input("\n¿Deseas continuar? (s/n): ").lower().strip()
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Operación cancelada por el usuario")
        return
    
    success = await insert_generic_ruc_for_users()
    
    if success:
        print("\n📋 Resumen de la operación:")
        print("✅ RUCs genéricos asignados exitosamente")
        print("💡 Los usuarios ahora pueden ver su RUC en el perfil")
        print("🔧 Para ver los cambios, los usuarios deben recargar su perfil")
    else:
        print("\n❌ Operación falló")

if __name__ == "__main__":
    asyncio.run(main())
