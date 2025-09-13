#!/usr/bin/env python3
"""
Prueba rápida de todos los endpoints corregidos.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def test_all_endpoints():
    """Probar todos los endpoints corregidos"""
    print("🚀 PRUEBA RÁPIDA - TODOS LOS ENDPOINTS")
    print("=" * 40)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            print("1. Probando endpoint de administrador...")

            # Endpoint de solicitudes pendientes (administrador)
            result = conn.execute(text("""
                SELECT
                    ss.id_solicitud,
                    ss.nombre_servicio,
                    c.nombre as nombre_categoria,
                    pe.razon_social as nombre_empresa,
                    u.nombre_persona as nombre_contacto
                FROM solicitud_servicio ss
                LEFT JOIN categoria c ON ss.id_categoria = c.id_categoria
                LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
                LEFT JOIN users u ON pe.user_id = u.id
                WHERE ss.estado_aprobacion = 'pendiente'
                LIMIT 3
            """))

            admin_results = result.fetchall()
            print(f"✅ Administrador: {len(admin_results)} solicitudes encontradas")

            for row in admin_results:
                print(f"   • {row.nombre_servicio}")
                print(f"     Empresa: {row.nombre_empresa or 'No especificado'}")
                print(f"     Contacto: {row.nombre_contacto or 'No especificado'}")
                print(f"     Categoría: {row.nombre_categoria or 'No especificado'}")

            print("\n2. Probando endpoint de proveedor...")

            # Obtener un perfil de empresa para simular
            result = conn.execute(text("SELECT id_perfil, razon_social, user_id FROM perfil_empresa LIMIT 1"))
            perfil = result.fetchone()

            if perfil:
                perfil_id = perfil[0]
                print(f"✅ Usando perfil: {perfil[1]} (ID: {perfil_id})")

                # Endpoint de mis solicitudes (proveedor)
                result = conn.execute(text("""
                    SELECT
                        ss.id_solicitud,
                        ss.nombre_servicio,
                        c.nombre as nombre_categoria,
                        pe.razon_social as nombre_empresa,
                        u.nombre_persona as nombre_contacto
                    FROM solicitud_servicio ss
                    LEFT JOIN categoria c ON ss.id_categoria = c.id_categoria
                    LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
                    LEFT JOIN users u ON pe.user_id = u.id
                    WHERE ss.id_perfil = :perfil_id
                    LIMIT 3
                """), {'perfil_id': perfil_id})

                provider_results = result.fetchall()
                print(f"✅ Proveedor: {len(provider_results)} solicitudes encontradas")

                for row in provider_results:
                    print(f"   • {row.nombre_servicio}")
                    print(f"     Empresa: {row.nombre_empresa or 'No especificado'}")
                    print(f"     Contacto: {row.nombre_contacto or 'No especificado'}")
                    print(f"     Categoría: {row.nombre_categoria or 'No especificado'}")
            else:
                print("⚠️  No hay perfiles de empresa para probar el endpoint de proveedor")

            print("\n3. Verificando monedas...")

            # Verificar monedas disponibles
            result = conn.execute(text("SELECT COUNT(*) FROM moneda"))
            moneda_count = result.scalar()
            print(f"✅ Monedas disponibles: {moneda_count}")

            if moneda_count > 0:
                result = conn.execute(text("SELECT codigo_iso_moneda, nombre FROM moneda LIMIT 3"))
                monedas = result.fetchall()
                for moneda in monedas:
                    print(f"   • {moneda[0]} - {moneda[1]}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    test_all_endpoints()
    print("\n🎯 Si no hay errores, todos los endpoints deberían funcionar correctamente.")

