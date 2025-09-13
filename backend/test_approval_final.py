#!/usr/bin/env python3
"""
Script final para probar que la aprobación de solicitudes funciona.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def test_approval_setup():
    """Probar que todo esté listo para la aprobación"""
    print("🧪 PRUEBA FINAL - APROBACIÓN DE SOLICITUDES")
    print("=" * 50)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # 1. Verificar que hay monedas
            print("🔍 1. Verificando monedas...")
            result = conn.execute(text("SELECT COUNT(*) FROM moneda"))
            moneda_count = result.scalar()

            if moneda_count == 0:
                print("❌ No hay monedas en la base de datos")
                print("💡 Ejecuta: python setup_currencies.py")
                return False

            result = conn.execute(text("SELECT id_moneda, codigo_iso_moneda, nombre FROM moneda LIMIT 3"))
            monedas = result.fetchall()
            print(f"✅ {moneda_count} monedas encontradas:")
            for moneda in monedas:
                print(f"   • {moneda[1]} ({moneda[2]}) - ID: {moneda[0]}")

            # 2. Verificar que hay solicitudes pendientes
            print("\n🔍 2. Verificando solicitudes pendientes...")
            result = conn.execute(text("SELECT COUNT(*) FROM solicitud_servicio WHERE estado_aprobacion = 'pendiente'"))
            pending_count = result.scalar()

            if pending_count == 0:
                print("⚠️  No hay solicitudes pendientes")
                print("💡 Un proveedor debe crear una solicitud primero")
                return True  # No es error, solo no hay qué aprobar

            result = conn.execute(text("SELECT id_solicitud, nombre_servicio FROM solicitud_servicio WHERE estado_aprobacion = 'pendiente' LIMIT 3"))
            solicitudes = result.fetchall()
            print(f"✅ {pending_count} solicitudes pendientes:")
            for solicitud in solicitudes:
                print(f"   • ID {solicitud[0]}: {solicitud[1]}")

            # 3. Probar la consulta que usa el endpoint
            print("\n🔍 3. Probando consulta del endpoint...")
            result = conn.execute(text("SELECT id_moneda, codigo_iso_moneda FROM moneda ORDER BY codigo_iso_moneda LIMIT 1"))
            test_row = result.first()

            if test_row:
                print(f"✅ Consulta funciona correctamente")
                print(f"   Moneda que se usará: {test_row[1]} (ID: {test_row[0]})")
            else:
                print("❌ Error en la consulta del endpoint")
                return False

        print("\n🎉 ¡TODO ESTÁ LISTO!")
        print("✅ El endpoint de aprobación debería funcionar correctamente")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    success = test_approval_setup()
    if not success:
        print("\n❌ Hay problemas que resolver antes de que funcione la aprobación")
    else:
        print("\n🚀 ¡Puedes probar la aprobación de solicitudes!")

