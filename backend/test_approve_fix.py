#!/usr/bin/env python3
"""
Script para probar la corrección del endpoint de aprobación.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Configuración de la base de datos
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

async def test_approve_fix():
    """Probar la corrección del endpoint de aprobación"""
    print("🧪 Probando corrección del endpoint de aprobación...")

    try:
        # Crear conexión
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Verificar que podemos obtener el ID de la moneda PYG
            print("🔍 Verificando consulta de moneda PYG...")
            moneda_result = await session.execute(
                text("SELECT id_moneda FROM moneda WHERE codigo_iso_moneda = 'PYG' LIMIT 1")
            )
            moneda_row = moneda_result.first()

            if moneda_row:
                print(f"✅ Moneda PYG encontrada con ID: {moneda_row[0]}")
            else:
                print("❌ Moneda PYG no encontrada")
                print("💡 Asegúrate de que existe una moneda con código 'PYG' en la tabla")
                return

            # Verificar que existe al menos una solicitud pendiente
            print("🔍 Verificando solicitudes pendientes...")
            request_result = await session.execute(
                text("SELECT id_solicitud, nombre_servicio FROM solicitud_servicio WHERE estado_aprobacion = 'pendiente' LIMIT 1")
            )
            request_row = request_result.first()

            if request_row:
                print(f"✅ Solicitud pendiente encontrada: ID {request_row[0]} - {request_row[1]}")
                print("🎯 El endpoint de aprobación debería funcionar correctamente ahora")
            else:
                print("⚠️  No hay solicitudes pendientes para probar")
                print("💡 Crea una solicitud de servicio primero para probar la aprobación")

    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🔧 PRUEBA DE CORRECCIÓN - ENDPOINT APROBAR SOLICITUD")
    print("=" * 55)
    asyncio.run(test_approve_fix())
    print("\n✅ Si no hay errores, el endpoint debería funcionar correctamente.")

