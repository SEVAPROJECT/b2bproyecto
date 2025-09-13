#!/usr/bin/env python3
"""
Script para debuggear el problema de guardado de comentarios de rechazo.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def debug_rejection():
    """Debug del proceso de rechazo"""
    print("🐛 DEBUG - PROCESO DE RECHAZO")
    print("=" * 35)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            print("1. Verificando estructura de la tabla...")

            # Verificar que la columna comentario_admin existe
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'solicitud_servicio'
                AND column_name = 'comentario_admin'
            """))

            column_info = result.fetchone()

            if column_info:
                print("✅ Columna comentario_admin existe:")
                print(f"   • Tipo: {column_info[1]}")
                print(f"   • Nullable: {column_info[2]}")
            else:
                print("❌ Columna comentario_admin NO existe")
                return

            print("\n2. Verificando solicitudes recientes...")

            # Ver solicitudes recientes y su estado de comentario
            result = conn.execute(text("""
                SELECT
                    id_solicitud,
                    nombre_servicio,
                    estado_aprobacion,
                    comentario_admin,
                    created_at
                FROM solicitud_servicio
                ORDER BY created_at DESC
                LIMIT 10
            """))

            requests = result.fetchall()

            print(f"📋 Últimas {len(requests)} solicitudes:")
            print("-" * 80)

            for req in requests:
                print(f"ID: {req[0]}")
                print(f"   Servicio: {req[1]}")
                print(f"   Estado: {req[2]}")
                print(f"   Comentario: '{req[3] or 'NULL'}'")
                print(f"   Creado: {req[4]}")
                print()

            print("3. Buscando solicitudes rechazadas con comentarios...")

            # Ver específicamente las rechazadas
            result = conn.execute(text("""
                SELECT
                    id_solicitud,
                    nombre_servicio,
                    comentario_admin,
                    created_at
                FROM solicitud_servicio
                WHERE estado_aprobacion = 'rechazada'
                AND comentario_admin IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 5
            """))

            rejected_with_comments = result.fetchall()

            if rejected_with_comments:
                print(f"✅ {len(rejected_with_comments)} solicitudes rechazadas con comentarios:")
                for req in rejected_with_comments:
                    print(f"   • ID {req[0]}: {req[1]}")
                    print(f"     Comentario: '{req[2]}'")
            else:
                print("⚠️  No hay solicitudes rechazadas con comentarios")
                print("💡 Esto confirma que los comentarios no se están guardando")

            print("\n4. Simulando un rechazo con comentario...")

            # Buscar una solicitud pendiente para probar
            result = conn.execute(text("""
                SELECT id_solicitud, nombre_servicio
                FROM solicitud_servicio
                WHERE estado_aprobacion = 'pendiente'
                LIMIT 1
            """))

            test_request = result.fetchone()

            if test_request:
                test_id = test_request[0]
                test_name = test_request[1]
                test_comment = "Comentario de prueba - Debug del sistema"

                print(f"📝 Probando con solicitud: {test_name} (ID: {test_id})")
                print(f"💬 Comentario: '{test_comment}'")

                # Simular el rechazo
                conn.execute(text("""
                    UPDATE solicitud_servicio
                    SET estado_aprobacion = 'rechazada',
                        comentario_admin = :comment
                    WHERE id_solicitud = :request_id
                """), {
                    'comment': test_comment,
                    'request_id': test_id
                })

                conn.commit()

                # Verificar que se guardó
                result = conn.execute(text("""
                    SELECT estado_aprobacion, comentario_admin
                    FROM solicitud_servicio
                    WHERE id_solicitud = :request_id
                """), {'request_id': test_id})

                saved = result.fetchone()

                if saved:
                    print("✅ Resultado después del update:")
                    print(f"   • Estado: {saved[0]}")
                    print(f"   • Comentario: '{saved[1] or 'NULL'}'")

                    if saved[1] == test_comment:
                        print("🎉 ¡El guardado funciona correctamente!")
                        print("💡 El problema debe estar en el endpoint API")
                    else:
                        print("❌ El comentario no se guardó correctamente")
                else:
                    print("❌ No se pudo verificar el guardado")

                # Limpiar la prueba
                print("\n🧹 Limpiando prueba...")
                conn.execute(text("""
                    UPDATE solicitud_servicio
                    SET estado_aprobacion = 'pendiente',
                        comentario_admin = NULL
                    WHERE id_solicitud = :request_id
                """), {'request_id': test_id})

                conn.commit()
                print("✅ Prueba limpiada")

            else:
                print("⚠️  No hay solicitudes pendientes para probar")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    debug_rejection()

