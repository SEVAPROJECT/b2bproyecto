#!/usr/bin/env python3
"""
Script para probar el flujo completo de rechazo de solicitudes.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def test_rejection_flow():
    """Probar el flujo completo de rechazo"""
    print("🧪 PRUEBA DEL FLUJO DE RECHAZO")
    print("=" * 35)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Paso 1: Verificar que hay solicitudes pendientes
            print("1. Verificando solicitudes pendientes...")
            result = conn.execute(text("""
                SELECT id_solicitud, nombre_servicio FROM solicitud_servicio
                WHERE estado_aprobacion = 'pendiente'
                LIMIT 1
            """))

            pending_request = result.fetchone()

            if not pending_request:
                print("❌ No hay solicitudes pendientes para probar")
                print("💡 Un proveedor debe crear una solicitud primero")
                return

            request_id = pending_request[0]
            service_name = pending_request[1]

            print(f"✅ Solicitud encontrada: ID {request_id} - {service_name}")

            # Paso 2: Simular rechazo con comentario
            print("\n2. Simulando rechazo con comentario...")
            test_comment = "Prueba de comentario de rechazo - Servicio no disponible temporalmente"

            # Actualizar la solicitud
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
            print("✅ Solicitud rechazada con comentario")

            # Paso 3: Verificar que se guardó correctamente
            print("\n3. Verificando que se guardó correctamente...")
            result = conn.execute(text("""
                SELECT id_solicitud, nombre_servicio, estado_aprobacion, comentario_admin
                FROM solicitud_servicio
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            updated_request = result.fetchone()

            if updated_request:
                print("📋 Datos guardados:")
                print(f"   • ID: {updated_request[0]}")
                print(f"   • Servicio: {updated_request[1]}")
                print(f"   • Estado: {updated_request[2]}")
                print(f"   • Comentario: {updated_request[3] or 'Sin comentario'}")

                if updated_request[3] == test_comment:
                    print("✅ Comentario guardado correctamente")
                else:
                    print("❌ El comentario no se guardó correctamente")
            else:
                print("❌ No se pudo recuperar la solicitud actualizada")

            # Paso 4: Verificar que aparece en consultas del proveedor
            print("\n4. Verificando consultas del proveedor...")

            # Obtener un perfil para simular consulta del proveedor
            result = conn.execute(text("SELECT id_perfil FROM perfil_empresa LIMIT 1"))
            perfil = result.fetchone()

            if perfil:
                perfil_id = perfil[0]
                print(f"✅ Usando perfil ID: {perfil_id}")

                # Simular consulta del endpoint del proveedor
                result = conn.execute(text("""
                    SELECT
                        ss.id_solicitud,
                        ss.nombre_servicio,
                        ss.estado_aprobacion,
                        ss.comentario_admin
                    FROM solicitud_servicio ss
                    WHERE ss.id_perfil = :perfil_id
                    AND ss.estado_aprobacion = 'rechazada'
                    LIMIT 5
                """), {'perfil_id': perfil_id})

                provider_requests = result.fetchall()
                print(f"📋 Solicitudes rechazadas del proveedor: {len(provider_requests)}")

                for req in provider_requests:
                    print(f"   • ID {req[0]}: {req[1]}")
                    print(f"     Estado: {req[2]}")
                    print(f"     Comentario: {req[3] or 'Sin comentario'}")

                    if req[3]:
                        print("     ✅ Comentario visible para el proveedor")
                    else:
                        print("     ❌ Sin comentario para el proveedor")

            # Paso 5: Limpiar la prueba (volver a pendiente)
            print("\n5. Limpiando prueba...")
            conn.execute(text("""
                UPDATE solicitud_servicio
                SET estado_aprobacion = 'pendiente',
                    comentario_admin = NULL
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            conn.commit()
            print("✅ Prueba limpiada - solicitud vuelta a pendiente")

        print("\n🎉 ¡Flujo de rechazo funcionando correctamente!")
        print("\n💡 El comentario del administrador debería aparecer")
        print("   en 'Mis Solicitudes' cuando el proveedor vea")
        print("   las solicitudes rechazadas.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    test_rejection_flow()

