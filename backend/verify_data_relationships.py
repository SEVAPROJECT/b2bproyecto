#!/usr/bin/env python3
"""
Script para verificar las relaciones de datos entre tablas.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def verify_relationships():
    """Verificar que las relaciones entre tablas estén correctas"""
    print("🔍 VERIFICACIÓN DE RELACIONES DE DATOS")
    print("=" * 45)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Verificar solicitudes y sus relaciones
            print("📋 Verificando solicitudes y sus relaciones...")

            query = """
            SELECT
                ss.id_solicitud,
                ss.nombre_servicio,
                ss.id_categoria,
                c.nombre as categoria_nombre,
                ss.id_perfil,
                pe.razon_social,
                pe.user_id,
                u.nombre_persona
            FROM solicitud_servicio ss
            LEFT JOIN categoria c ON ss.id_categoria = c.id_categoria
            LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil_empresa
            LEFT JOIN users u ON pe.user_id = u.id
            WHERE ss.estado_aprobacion = 'pendiente'
            LIMIT 10
            """

            result = conn.execute(text(query))
            rows = result.fetchall()

            if not rows:
                print("⚠️  No hay solicitudes pendientes")
                return

            print(f"✅ Encontradas {len(rows)} solicitudes:")
            print("-" * 80)

            for row in rows:
                print(f"ID: {row.id_solicitud}")
                print(f"   Servicio: {row.nombre_servicio}")

                # Verificar categoría
                if row.id_categoria and row.categoria_nombre:
                    print(f"   ✅ Categoría: {row.categoria_nombre}")
                else:
                    print(f"   ❌ Categoría: ID {row.id_categoria} - Nombre: {row.categoria_nombre}")

                # Verificar empresa
                if row.id_perfil and row.razon_social:
                    print(f"   ✅ Empresa: {row.razon_social}")
                else:
                    print(f"   ❌ Empresa: ID {row.id_perfil} - Nombre: {row.razon_social}")

                # Verificar usuario/contacto
                if row.user_id and row.nombre_persona:
                    print(f"   ✅ Contacto: {row.nombre_persona}")
                else:
                    print(f"   ❌ Contacto: UserID {row.user_id} - Nombre: {row.nombre_persona}")

                print()

            # Verificar estadísticas generales
            print("📊 Estadísticas de relaciones:")

            # Solicitudes sin categoría
            result = conn.execute(text("""
                SELECT COUNT(*) FROM solicitud_servicio
                WHERE estado_aprobacion = 'pendiente' AND id_categoria IS NULL
            """))
            sin_categoria = result.scalar()

            # Solicitudes sin perfil de empresa
            result = conn.execute(text("""
                SELECT COUNT(*) FROM solicitud_servicio
                WHERE estado_aprobacion = 'pendiente' AND id_perfil IS NULL
            """))
            sin_perfil = result.scalar()

            # Perfiles sin usuario
            result = conn.execute(text("""
                SELECT COUNT(*) FROM perfil_empresa
                WHERE user_id IS NULL
            """))
            perfiles_sin_usuario = result.scalar()

            print(f"   • Solicitudes sin categoría: {sin_categoria}")
            print(f"   • Solicitudes sin perfil: {sin_perfil}")
            print(f"   • Perfiles sin usuario: {perfiles_sin_usuario}")

            if sin_categoria == 0 and sin_perfil == 0 and perfiles_sin_usuario == 0:
                print("🎉 ¡Todas las relaciones están correctas!")
            else:
                print("⚠️  Hay problemas de integridad referencial")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    verify_relationships()

