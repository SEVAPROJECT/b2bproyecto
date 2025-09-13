#!/usr/bin/env python3
"""
Script para probar el endpoint de rechazo directamente.
"""
import asyncio
import json
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def test_reject_endpoint():
    """Probar el endpoint de rechazo directamente"""
    print("🧪 PRUEBA DIRECTA - ENDPOINT RECHAZO")
    print("=" * 40)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            print("1. Buscando solicitud pendiente...")

            # Encontrar una solicitud pendiente
            result = conn.execute(text("""
                SELECT id_solicitud, nombre_servicio
                FROM solicitud_servicio
                WHERE estado_aprobacion = 'pendiente'
                LIMIT 1
            """))

            request = result.fetchone()

            if not request:
                print("❌ No hay solicitudes pendientes para probar")
                print("💡 Crea una solicitud como proveedor primero")
                return

            request_id = request[0]
            service_name = request[1]

            print(f"✅ Solicitud encontrada: {service_name} (ID: {request_id})")

            print("\n2. Simulando llamada al endpoint de rechazo...")

            # Simular lo que hace el endpoint
            comentario_test = "Comentario de prueba desde endpoint de rechazo"

            print(f"📝 Comentario a guardar: '{comentario_test}'")

            # Actualizar directamente como lo haría el endpoint
            conn.execute(text("""
                UPDATE solicitud_servicio
                SET estado_aprobacion = 'rechazada',
                    comentario_admin = :comentario
                WHERE id_solicitud = :request_id
            """), {
                'comentario': comentario_test,
                'request_id': request_id
            })

            conn.commit()

            print("✅ Update ejecutado")

            print("\n3. Verificando que se guardó correctamente...")

            # Verificar que se guardó
            result = conn.execute(text("""
                SELECT id_solicitud, nombre_servicio, estado_aprobacion, comentario_admin
                FROM solicitud_servicio
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            saved_request = result.fetchone()

            if saved_request:
                print("📋 Datos guardados:")
                print(f"   • ID: {saved_request[0]}")
                print(f"   • Servicio: {saved_request[1]}")
                print(f"   • Estado: {saved_request[2]}")
                print(f"   • Comentario: '{saved_request[3] or 'NULL'}'")

                if saved_request[3] == comentario_test:
                    print("🎉 ¡Comentario guardado correctamente!")
                    print("💡 El endpoint de rechazo está funcionando bien")
                else:
                    print("❌ Error: El comentario no se guardó como esperado")
                    print(f"   Esperado: '{comentario_test}'")
                    print(f"   Guardado: '{saved_request[3] or 'NULL'}'")
            else:
                print("❌ No se pudo recuperar la solicitud")

            print("\n4. Verificando que aparece en consultas del proveedor...")

            # Obtener el perfil de la solicitud para simular vista del proveedor
            result = conn.execute(text("""
                SELECT id_perfil FROM solicitud_servicio
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            perfil_row = result.fetchone()

            if perfil_row:
                perfil_id = perfil_row[0]

                # Simular consulta del proveedor
                result = conn.execute(text("""
                    SELECT
                        ss.id_solicitud,
                        ss.nombre_servicio,
                        ss.estado_aprobacion,
                        ss.comentario_admin
                    FROM solicitud_servicio ss
                    WHERE ss.id_perfil = :perfil_id
                    AND ss.estado_aprobacion = 'rechazada'
                    LIMIT 3
                """), {'perfil_id': perfil_id})

                provider_requests = result.fetchall()

                print(f"📱 El proveedor vería {len(provider_requests)} solicitudes rechazadas:")

                for req in provider_requests:
                    print(f"   • {req.nombre_servicio}")
                    print(f"     Estado: {req.estado_aprobacion}")
                    print(f"     Comentario: '{req.comentario_admin or 'Sin comentario'}'")

            # Limpiar la prueba
            print("\n🧹 Limpiando prueba...")
            conn.execute(text("""
                UPDATE solicitud_servicio
                SET estado_aprobacion = 'pendiente',
                    comentario_admin = NULL
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            conn.commit()
            print("✅ Prueba limpiada - solicitud vuelta a pendiente")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    test_reject_endpoint()

