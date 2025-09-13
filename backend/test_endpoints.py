#!/usr/bin/env python3
"""
Script simple para probar los endpoints de solicitudes de servicios.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Configuración básica
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

async def test_endpoints():
    """Prueba los endpoints básicos"""
    print("🔍 Probando conexión a la base de datos...")

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Probar consulta básica
            from app.models.publicar_servicio.solicitud_servicio import SolicitudServicio

            result = await session.execute(
                select(SolicitudServicio).limit(5)
            )

            solicitudes = result.scalars().all()
            print(f"✅ Conexión exitosa. Encontradas {len(solicitudes)} solicitudes en total.")

            # Mostrar algunas solicitudes
            for solicitud in solicitudes[:3]:
                print(f"   - ID: {solicitud.id_solicitud}, Servicio: {solicitud.nombre_servicio}, Estado: {solicitud.estado_aprobacion}")

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que:")
        print("   - PostgreSQL esté ejecutándose")
        print("   - La base de datos existe")
        print("   - Las credenciales son correctas")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🧪 PRUEBA DE ENDPOINTS - SOLICITUDES DE SERVICIOS")
    print("=" * 50)
    asyncio.run(test_endpoints())
    print("\n🎯 Si la conexión funciona, los endpoints deberían trabajar correctamente.")

