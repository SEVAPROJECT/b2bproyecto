#!/usr/bin/env python3
"""
Script rápido para probar que los comentarios de rechazo se guardan correctamente.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def test_reject_comment():
    """Probar que los comentarios de rechazo se guardan"""
    print("🧪 PRUEBA DE COMENTARIOS DE RECHAZO")
    print("=" * 35)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Buscar una solicitud pendiente para probar
            result = conn.execute(text("""
                SELECT id_solicitud, nombre_servicio FROM solicitud_servicio
                WHERE estado_aprobacion = 'pendiente'
                LIMIT 1
            """))

            request = result.fetchone()

            if not request:
                print("❌ No hay solicitudes pendientes para probar")
                print("💡 Crea una solicitud primero")
                return

            request_id = request[0]
            service_name = request[1]

            print(f"✅ Solicitud encontrada: {service_name} (ID: {request_id})")

            # Probar rechazo con comentario
            test_comment = "Comentario de prueba: Servicio temporalmente no disponible"

            print(f"📝 Rechazando con comentario: {test_comment}")

            conn.execute(text("""
                UPDATE solicitud_servicio
                SET estado_aprobacion = 'rechazada',
                    comentario_admin = :comment
                WHERE id_solicitud = :request_id
            """), {
                'comment': test_comment,
                'request_id': request_id
            })

            conn.commit()

            # Verificar que se guardó
            result = conn.execute(text("""
                SELECT estado_aprobacion, comentario_admin FROM solicitud_servicio
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            updated = result.fetchone()

            if updated:
                print("✅ Estado actualizado:")
                print(f"   • Estado: {updated[0]}")
                print(f"   • Comentario: {updated[1] or 'Sin comentario'}")

                if updated[1] == test_comment:
                    print("🎉 ¡Comentario guardado correctamente!")
                    print("💡 El proveedor debería poder ver este comentario")
                else:
                    print("❌ El comentario no se guardó correctamente")
            else:
                print("❌ No se pudo verificar la actualización")

            # Limpiar la prueba (volver a pendiente)
            print("\n🧹 Limpiando prueba...")
            conn.execute(text("""
                UPDATE solicitud_servicio
                SET estado_aprobacion = 'pendiente',
                    comentario_admin = NULL
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            conn.commit()
            print("✅ Solicitud vuelta a estado pendiente")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    test_reject_comment()
    print("\n💡 Si la prueba funcionó, el comentario debería aparecer")
    print("   en 'Mis Solicitudes' cuando veas las solicitudes rechazadas.")

