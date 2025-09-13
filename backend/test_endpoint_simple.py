#!/usr/bin/env python3
"""
Script simple para probar el endpoint específico que está fallando.
"""
import asyncio
import os
import sys

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuración básica
os.environ["DATABASE_URL_LOCAL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

async def test_endpoint():
    """Probar el endpoint de solicitudes pendientes"""
    try:
        print("🔍 Probando endpoint de solicitudes pendientes...")

        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.future import select
        from app.models.publicar_servicio.solicitud_servicio import SolicitudServicio

        # Crear conexión
        DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Probar consulta básica
            result = await session.execute(
                select(SolicitudServicio)
                .where(SolicitudServicio.estado_aprobacion == 'pendiente')
            )

            requests = result.scalars().all()
            print(f"✅ Consulta ejecutada correctamente. Encontradas {len(requests)} solicitudes pendientes.")

            # Mostrar algunas solicitudes
            for i, request in enumerate(requests[:3]):
                print(f"   {i+1}. ID: {request.id_solicitud}, Servicio: {request.nombre_servicio}")

        await engine.dispose()
        print("✅ ¡Endpoint funcionando correctamente!")

    except Exception as e:
        print(f"❌ Error en el endpoint: {e}")
        print("Posibles causas:")
        print("1. Base de datos no está ejecutándose")
        print("2. Credenciales incorrectas")
        print("3. Tabla solicitud_servicio no existe")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 PRUEBA DE ENDPOINT - SOLICITUDES PENDIENTES")
    print("=" * 50)
    asyncio.run(test_endpoint())

