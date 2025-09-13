#!/usr/bin/env python3
"""
Script para corregir problemas de integridad referencial en los datos.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def fix_data_integrity():
    """Corregir problemas de integridad referencial"""
    print("🔧 CORRIENDO INTEGRIDAD REFERENCIAL")
    print("=" * 35)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            print("1. Verificando solicitudes sin perfil válido...")

            # Encontrar solicitudes con id_perfil que no existe en perfil_empresa
            result = conn.execute(text("""
                SELECT ss.id_solicitud, ss.nombre_servicio, ss.id_perfil
                FROM solicitud_servicio ss
                LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
                WHERE ss.id_perfil IS NOT NULL AND pe.id_perfil IS NULL
                AND ss.estado_aprobacion = 'pendiente'
            """))

            invalid_requests = result.fetchall()

            if invalid_requests:
                print(f"❌ Encontradas {len(invalid_requests)} solicitudes con perfil inválido:")
                for req in invalid_requests:
                    print(f"   • ID {req.id_solicitud}: {req.nombre_servicio} (perfil: {req.id_perfil})")

                # Corregir asignando un perfil válido o null
                print("\n🔧 Corrigiendo solicitudes...")
                conn.execute(text("""
                    UPDATE solicitud_servicio
                    SET id_perfil = NULL
                    WHERE id_perfil IS NOT NULL
                    AND id_perfil NOT IN (SELECT id_perfil FROM perfil_empresa)
                """))

                print("✅ Solicitudes corregidas")
            else:
                print("✅ Todas las solicitudes tienen perfiles válidos")

            print("\n2. Verificando solicitudes sin categoría válida...")

            # Encontrar solicitudes con id_categoria que no existe
            result = conn.execute(text("""
                SELECT ss.id_solicitud, ss.nombre_servicio, ss.id_categoria
                FROM solicitud_servicio ss
                LEFT JOIN categoria c ON ss.id_categoria = c.id_categoria
                WHERE ss.id_categoria IS NOT NULL AND c.id_categoria IS NULL
                AND ss.estado_aprobacion = 'pendiente'
            """))

            invalid_categories = result.fetchall()

            if invalid_categories:
                print(f"❌ Encontradas {len(invalid_categories)} solicitudes con categoría inválida:")
                for req in invalid_categories:
                    print(f"   • ID {req.id_solicitud}: {req.nombre_servicio} (categoría: {req.id_categoria})")

                # Corregir asignando null
                print("\n🔧 Corrigiendo categorías...")
                conn.execute(text("""
                    UPDATE solicitud_servicio
                    SET id_categoria = NULL
                    WHERE id_categoria IS NOT NULL
                    AND id_categoria NOT IN (SELECT id_categoria FROM categoria)
                """))

                print("✅ Categorías corregidas")
            else:
                print("✅ Todas las solicitudes tienen categorías válidas")

            print("\n3. Verificando perfiles sin usuario válido...")

            # Encontrar perfiles con user_id que no existe
            result = conn.execute(text("""
                SELECT pe.id_perfil, pe.razon_social, pe.user_id
                FROM perfil_empresa pe
                LEFT JOIN users u ON pe.user_id = u.id
                WHERE pe.user_id IS NOT NULL AND u.id IS NULL
            """))

            invalid_users = result.fetchall()

            if invalid_users:
                print(f"❌ Encontrados {len(invalid_users)} perfiles con usuario inválido:")
                for perfil in invalid_users:
                    print(f"   • ID {perfil.id_perfil}: {perfil.razon_social} (usuario: {perfil.user_id})")

                # Para estos casos, mejor dejarlos como NULL ya que no podemos crear usuarios
                print("\n⚠️  No se pueden corregir automáticamente los perfiles sin usuario")
                print("   Los joins devolverán NULL para el nombre_contacto")
            else:
                print("✅ Todos los perfiles tienen usuarios válidos")

            # Confirmar cambios
            conn.commit()

            print("\n4. Verificación final...")
            result = conn.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM solicitud_servicio WHERE estado_aprobacion = 'pendiente') as solicitudes,
                    (SELECT COUNT(*) FROM perfil_empresa) as perfiles,
                    (SELECT COUNT(*) FROM categoria) as categorias,
                    (SELECT COUNT(*) FROM users) as usuarios
            """))

            stats = result.fetchone()
            print("📊 Estadísticas finales:")
            print(f"   • Solicitudes pendientes: {stats.solicitudes}")
            print(f"   • Perfiles de empresa: {stats.perfiles}")
            print(f"   • Categorías: {stats.categorias}")
            print(f"   • Usuarios: {stats.usuarios}")

            print("\n🎉 ¡Integridad referencial verificada y corregida!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    fix_data_integrity()

