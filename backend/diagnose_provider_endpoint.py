#!/usr/bin/env python3
"""
Diagnóstico específico para el endpoint de "Mis Solicitudes" del proveedor.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def diagnose_provider_endpoint():
    """Diagnosticar problemas con el endpoint del proveedor"""
    print("🔍 DIAGNÓSTICO - ENDPOINT PROVEEDOR")
    print("=" * 35)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            print("1. Verificando estructura de tablas...")

            # Verificar tabla perfil_empresa
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'perfil_empresa'
                ORDER BY ordinal_position
            """))

            columns = result.fetchall()
            print("📋 Columnas en perfil_empresa:")
            for col in columns:
                print(f"   • {col[0]}: {col[1]}")

            # Verificar que existe user_id
            user_id_exists = any(col[0] == 'user_id' for col in columns)
            if user_id_exists:
                print("✅ Columna 'user_id' existe")
            else:
                print("❌ Columna 'user_id' NO existe")

            print("\n2. Verificando datos de ejemplo...")

            # Verificar perfiles de empresa
            result = conn.execute(text("""
                SELECT pe.id_perfil, pe.razon_social, pe.user_id, u.nombre_persona
                FROM perfil_empresa pe
                LEFT JOIN users u ON pe.user_id = u.id
                LIMIT 5
            """))

            perfiles = result.fetchall()
            print(f"📋 Perfiles encontrados: {len(perfiles)}")
            for perfil in perfiles:
                print(f"   • ID {perfil[0]}: {perfil[1]} (usuario: {perfil[2]}) - {perfil[3] or 'Sin usuario'}")

            print("\n3. Verificando solicitudes de servicios...")

            # Verificar solicitudes
            result = conn.execute(text("""
                SELECT ss.id_solicitud, ss.nombre_servicio, ss.id_perfil, pe.razon_social
                FROM solicitud_servicio ss
                LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
                WHERE ss.estado_aprobacion = 'pendiente'
                LIMIT 5
            """))

            solicitudes = result.fetchall()
            print(f"📋 Solicitudes pendientes: {len(solicitudes)}")
            for solicitud in solicitudes:
                print(f"   • ID {solicitud[0]}: {solicitud[1]} (perfil: {solicitud[2]}) - {solicitud[3] or 'Sin empresa'}")

            print("\n4. Probando consulta del endpoint corregida...")

            # Simular la consulta que haría el endpoint
            result = conn.execute(text("""
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
                WHERE ss.id_perfil = pe.id_perfil
                LIMIT 3
            """))

            test_results = result.fetchall()
            print(f"✅ Consulta ejecutada correctamente. {len(test_results)} resultados.")

            if test_results:
                print("📋 Resultados de prueba:")
                for row in test_results:
                    print(f"   • {row.nombre_servicio}")
                    print(f"     Empresa: {row.nombre_empresa or 'No especificado'}")
                    print(f"     Contacto: {row.nombre_contacto or 'No especificado'}")
                    print(f"     Categoría: {row.nombre_categoria or 'No especificado'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    diagnose_provider_endpoint()

