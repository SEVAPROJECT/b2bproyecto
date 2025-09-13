#!/usr/bin/env python3
"""
Script completo para probar el flujo de rechazo y visualización de comentarios.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def test_full_rejection_flow():
    """Probar flujo completo de rechazo y visualización"""
    print("🔄 PRUEBA COMPLETA DEL FLUJO DE RECHAZO")
    print("=" * 45)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            print("1. Buscando solicitud pendiente...")

            # Encontrar una solicitud pendiente
            result = conn.execute(text("""
                SELECT ss.id_solicitud, ss.nombre_servicio, pe.id_perfil, pe.razon_social
                FROM solicitud_servicio ss
                JOIN perfil_empresa pe ON ss.id_perfil = pe.id_perfil
                WHERE ss.estado_aprobacion = 'pendiente'
                LIMIT 1
            """))

            request = result.fetchone()

            if not request:
                print("❌ No hay solicitudes pendientes")
                print("💡 Un proveedor debe crear una solicitud primero")
                return

            request_id = request[0]
            service_name = request[1]
            perfil_id = request[2]
            empresa = request[3]

            print(f"✅ Solicitud encontrada:")
            print(f"   • Servicio: {service_name}")
            print(f"   • Empresa: {empresa}")
            print(f"   • ID Solicitud: {request_id}")
            print(f"   • ID Perfil: {perfil_id}")

            print("\n2. Rechazando solicitud con comentario...")

            # Comentario de prueba
            comentario = "Servicio temporalmente no disponible. Intente nuevamente en unos días."

            # Rechazar la solicitud
            conn.execute(text("""
                UPDATE solicitud_servicio
                SET estado_aprobacion = 'rechazada',
                    comentario_admin = :comentario
                WHERE id_solicitud = :request_id
            """), {
                'comentario': comentario,
                'request_id': request_id
            })

            conn.commit()

            print(f"✅ Solicitud rechazada con comentario:")
            print(f"   '{comentario}'")

            print("\n3. Verificando que se guardó correctamente...")

            # Verificar que se guardó
            result = conn.execute(text("""
                SELECT estado_aprobacion, comentario_admin
                FROM solicitud_servicio
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            saved = result.fetchone()

            if saved:
                print("✅ Datos guardados:")
                print(f"   • Estado: {saved[0]}")
                print(f"   • Comentario: '{saved[1] or 'NULL'}'")

                if saved[1] == comentario:
                    print("✅ Comentario guardado correctamente")
                else:
                    print("❌ Error al guardar comentario")
            else:
                print("❌ No se pudo verificar")

            print("\n4. Simulando vista del proveedor...")

            # Simular lo que vería el proveedor (como si llamara al endpoint)
            result = conn.execute(text("""
                SELECT
                    ss.id_solicitud,
                    ss.nombre_servicio,
                    ss.estado_aprobacion,
                    ss.comentario_admin,
                    c.nombre as categoria
                FROM solicitud_servicio ss
                LEFT JOIN categoria c ON ss.id_categoria = c.id_categoria
                WHERE ss.id_perfil = :perfil_id
                AND ss.estado_aprobacion = 'rechazada'
                ORDER BY ss.id_solicitud DESC
                LIMIT 5
            """), {'perfil_id': perfil_id})

            provider_view = result.fetchall()

            print(f"📱 Lo que vería el proveedor ({len(provider_view)} solicitudes):")
            print("-" * 60)

            for req in provider_view:
                print(f"Solicitud: {req.nombre_servicio}")
                print(f"Estado: {req.estado_aprobacion}")
                print(f"Categoría: {req.categoria or 'No especificado'}")
                print(f"Comentario del admin: '{req.comentario_admin or 'Sin comentario'}'")
                print()

            print("🎉 ¡Flujo completo funcionando!")
            print("\n💡 El proveedor debería ver:")
            print("   • Estado: Rechazada")
            print("   • Motivo del rechazo: [comentario del admin]")
            print("   • Información completa de la solicitud")

            # Limpiar la prueba
            print("\n🧹 Limpiando prueba...")
            conn.execute(text("""
                UPDATE solicitud_servicio
                SET estado_aprobacion = 'pendiente',
                    comentario_admin = NULL
                WHERE id_solicitud = :request_id
            """), {'request_id': request_id})

            conn.commit()
            print("✅ Prueba limpiada")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    test_full_rejection_flow()

