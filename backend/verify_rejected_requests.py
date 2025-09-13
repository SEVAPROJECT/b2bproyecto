#!/usr/bin/env python3
"""
Script para verificar que las solicitudes rechazadas guardan el comentario correctamente.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def check_rejected_requests():
    """Verificar solicitudes rechazadas y sus comentarios"""
    print("🔍 VERIFICANDO SOLICITUDES RECHAZADAS")
    print("=" * 40)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Verificar solicitudes rechazadas con comentarios
            result = conn.execute(text("""
                SELECT
                    ss.id_solicitud,
                    ss.nombre_servicio,
                    ss.comentario_admin,
                    ss.estado_aprobacion,
                    pe.razon_social,
                    u.nombre_persona
                FROM solicitud_servicio ss
                LEFT JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
                LEFT JOIN users u ON pe.user_id = u.id
                WHERE ss.estado_aprobacion = 'rechazada'
                ORDER BY ss.id_solicitud DESC
                LIMIT 10
            """))

            rejected_requests = result.fetchall()

            if rejected_requests:
                print(f"✅ Encontradas {len(rejected_requests)} solicitudes rechazadas:")
                print("-" * 80)

                for request in rejected_requests:
                    print(f"ID: {request.id_solicitud}")
                    print(f"   Servicio: {request.nombre_servicio}")
                    print(f"   Empresa: {request.razon_social or 'No especificado'}")
                    print(f"   Contacto: {request.nombre_persona or 'No especificado'}")
                    print(f"   Estado: {request.estado_aprobacion}")
                    if request.comentario_admin:
                        print(f"   ✅ Comentario: {request.comentario_admin}")
                    else:
                        print("   ❌ Sin comentario")
                    print()

                # Verificar que hay solicitudes con comentarios
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM solicitud_servicio
                    WHERE estado_aprobacion = 'rechazada' AND comentario_admin IS NOT NULL
                """))

                with_comments = result.scalar()
                print(f"📊 Solicitudes rechazadas con comentario: {with_comments}")

            else:
                print("⚠️  No hay solicitudes rechazadas")
                print("💡 Rechaza algunas solicitudes con comentarios para probar")

            # Verificar si hay solicitudes pendientes para probar
            result = conn.execute(text("""
                SELECT COUNT(*) FROM solicitud_servicio
                WHERE estado_aprobacion = 'pendiente'
            """))

            pending_count = result.scalar()
            print(f"\n📋 Solicitudes pendientes disponibles: {pending_count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    check_rejected_requests()

