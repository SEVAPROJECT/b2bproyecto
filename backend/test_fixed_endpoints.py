#!/usr/bin/env python3
"""
Script para probar que los endpoints corregidos funcionan.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def test_fixed_queries():
    """Probar las consultas corregidas"""
    print("🧪 PRUEBA DE CONSULTAS CORREGIDAS")
    print("=" * 35)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Probar consulta del endpoint de administrador
            print("1. Probando consulta de solicitudes pendientes...")
            query_admin = """
            SELECT
                ss.id_solicitud,
                ss.nombre_servicio,
                ss.descripcion,
                ss.estado_aprobacion,
                c.nombre as nombre_categoria,
                pe.razon_social as nombre_empresa,
                u.nombre_persona as nombre_contacto
            FROM solicitud_servicio ss
            LEFT JOIN categoria c ON ss.id_categoria = c.id_categoria
            LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
            LEFT JOIN users u ON pe.user_id = u.id
            WHERE ss.estado_aprobacion = 'pendiente'
            LIMIT 3
            """

            result = conn.execute(text(query_admin))
            rows = result.fetchall()

            print(f"✅ Consulta ejecutada. {len(rows)} resultados encontrados.")

            if rows:
                for i, row in enumerate(rows, 1):
                    print(f"\n📋 Solicitud {i}:")
                    print(f"   • Servicio: {row.nombre_servicio}")
                    print(f"   • Categoría: {row.nombre_categoria or 'No especificado'}")
                    print(f"   • Empresa: {row.nombre_empresa or 'No especificado'}")
                    print(f"   • Contacto: {row.nombre_contacto or 'No especificado'}")

            # Verificar estructura de tablas
            print("\n2. Verificando estructura de tablas...")

            # Verificar perfil_empresa
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'perfil_empresa' AND column_name = 'id_perfil'"))
            if result.fetchone():
                print("✅ Tabla perfil_empresa tiene columna 'id_perfil'")
            else:
                print("❌ Tabla perfil_empresa NO tiene columna 'id_perfil'")

            # Verificar solicitud_servicio
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'solicitud_servicio' AND column_name = 'id_perfil'"))
            if result.fetchone():
                print("✅ Tabla solicitud_servicio tiene columna 'id_perfil'")
            else:
                print("❌ Tabla solicitud_servicio NO tiene columna 'id_perfil'")

            # Verificar datos de ejemplo
            print("\n3. Verificando datos de ejemplo...")
            result = conn.execute(text("SELECT COUNT(*) FROM solicitud_servicio WHERE estado_aprobacion = 'pendiente'"))
            pending_count = result.scalar()
            print(f"📊 Solicitudes pendientes: {pending_count}")

            result = conn.execute(text("SELECT COUNT(*) FROM perfil_empresa"))
            perfil_count = result.scalar()
            print(f"📊 Perfiles de empresa: {perfil_count}")

            result = conn.execute(text("SELECT COUNT(*) FROM categoria"))
            categoria_count = result.scalar()
            print(f"📊 Categorías: {categoria_count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    test_fixed_queries()

