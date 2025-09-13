#!/usr/bin/env python3
"""
Script para probar el endpoint de rechazo vía API HTTP.
"""
import requests
import json
from sqlalchemy import create_engine, text

# Configuración
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"
BASE_URL = "http://localhost:8000"

def test_reject_via_api():
    """Probar el endpoint de rechazo vía HTTP"""
    print("🌐 PRUEBA API - ENDPOINT RECHAZO")
    print("=" * 35)

    try:
        # Crear conexión a BD
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            print("1. Preparando solicitud de prueba...")

            # Buscar una solicitud pendiente
            result = conn.execute(text("""
                SELECT id_solicitud, nombre_servicio
                FROM solicitud_servicio
                WHERE estado_aprobacion = 'pendiente'
                LIMIT 1
            """))

            request = result.fetchone()

            if not request:
                print("❌ No hay solicitudes pendientes")
                return

            request_id = request[0]
            service_name = request[1]

            print(f"✅ Solicitud: {service_name} (ID: {request_id})")

            print("\n2. Probando endpoint HTTP...")

            # Datos del request
            comentario_test = "Comentario de prueba vía API - Servicio no disponible temporalmente"

            payload = {
                "comentario_admin": comentario_test
            }

            print(f"📤 Enviando: {json.dumps(payload, indent=2)}")

            try:
                # Hacer la llamada HTTP (sin autenticación para prueba)
                response = requests.put(
                    f"{BASE_URL}/api/v1/service-requests/{request_id}/reject",
                    json=payload,
                    timeout=10
                )

                print(f"📥 Respuesta: {response.status_code}")

                if response.status_code == 200:
                    print("✅ Endpoint respondió correctamente")
                    response_data = response.json()
                    print(f"   Mensaje: {response_data.get('message', 'Sin mensaje')}")
                elif response.status_code == 401:
                    print("⚠️  Endpoint requiere autenticación (esto es normal)")
                    print("💡 En el frontend real funcionará con el token")
                else:
                    print(f"❌ Error en endpoint: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Respuesta: {response.text}")

            except requests.exceptions.ConnectionError:
                print("❌ No se puede conectar al servidor")
                print("💡 Asegúrate de que el servidor esté ejecutándose")
                print("   python server_quick_fix.py")
                return
            except Exception as e:
                print(f"❌ Error HTTP: {e}")
                return

            print("\n3. Verificando en base de datos...")

            # Verificar si se guardó en BD
            result = conn.execute(text("""
                SELECT estado_aprobacion, comentario_admin
                FROM solicitud_servicio
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            saved = result.fetchone()

            if saved:
                print("📋 Estado en BD después del request:")
                print(f"   • Estado: {saved[0]}")
                print(f"   • Comentario: '{saved[1] or 'NULL'}'")

                if saved[0] == 'rechazada' and saved[1] == comentario_test:
                    print("🎉 ¡El endpoint está funcionando correctamente!")
                elif saved[0] == 'rechazada' and saved[1] != comentario_test:
                    print("⚠️  Solicitud rechazada pero comentario no guardado")
                    print("💡 Puede ser por falta de autenticación en la prueba")
                else:
                    print("❌ Solicitud no fue rechazada")
            else:
                print("❌ No se pudo verificar en BD")

            # Limpiar si se modificó
            if saved and saved[0] == 'rechazada':
                print("\n🧹 Limpiando cambios de prueba...")
                conn.execute(text("""
                    UPDATE solicitud_servicio
                    SET estado_aprobacion = 'pendiente',
                        comentario_admin = NULL
                    WHERE id_solicitud = :request_id
                """), {'request_id': request_id})
                conn.commit()
                print("✅ Cambios limpiados")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    test_reject_via_api()

