#!/usr/bin/env python3
"""
Script directo para ejecutar la migración sin dependencias externas.
Configuración hardcodeada para simplicidad.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Configuración directa de la base de datos
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "postgres",
    "user": "postgres",
    "password": "postgres"
}

DATABASE_URL = f"postgresql+asyncpg://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

async def run_migration():
    """Ejecuta la migración para agregar id_categoria a solicitud_servicio"""
    print("🔗 Configuración de conexión:")
    print(f"   Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"   Base de datos: {DB_CONFIG['database']}")
    print(f"   Usuario: {DB_CONFIG['user']}")
    print("   Password: ****")
    print()

    engine = create_async_engine(DATABASE_URL, echo=True)

    migration_sql = """
    -- Migración para agregar la columna id_categoria a la tabla solicitud_servicio
    ALTER TABLE solicitud_servicio ADD COLUMN IF NOT EXISTS id_categoria BIGINT;

    -- Agregar la restricción de clave foránea (solo si no existe)
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'solicitud_servicio_id_categoria_fkey'
        ) THEN
            ALTER TABLE solicitud_servicio
            ADD CONSTRAINT solicitud_servicio_id_categoria_fkey
            FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)
            ON DELETE SET NULL;
        END IF;
    END $$;

    -- Crear un índice para mejorar el rendimiento (solo si no existe)
    CREATE INDEX IF NOT EXISTS idx_solicitud_servicio_id_categoria
    ON solicitud_servicio(id_categoria);

    -- Agregar un comentario a la columna
    COMMENT ON COLUMN solicitud_servicio.id_categoria IS 'Referencia a la categoría del servicio solicitado';
    """

    try:
        async with engine.begin() as conn:
            print("🚀 Ejecutando migración...")
            await conn.execute(text(migration_sql))
            print("✅ Migración completada exitosamente!")
            print("🎉 La columna id_categoria ha sido agregada a solicitud_servicio")
            print()
            print("📋 Resumen de cambios:")
            print("   ✅ Columna 'id_categoria' agregada")
            print("   ✅ Clave foránea configurada")
            print("   ✅ Índice creado para rendimiento")
            print("   ✅ Comentario agregado")

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        print()
        print("💡 Verificaciones necesarias:")
        print("   1. PostgreSQL debe estar ejecutándose")
        print("   2. La base de datos 'postgres' debe existir")
        print("   3. Credenciales correctas (usuario: postgres, password: postgres)")
        print("   4. Puerto 5432 debe estar disponible")
        print()
        print("🔧 Si PostgreSQL no está ejecutándose:")
        print("   - En Windows: Inicia el servicio PostgreSQL desde servicios")
        print("   - O ejecuta: pg_ctl start -D \"C:\\Program Files\\PostgreSQL\\XX\\data\"")
        print()
        print("🗄️ Si necesitas cambiar la configuración:")
        print("   - Edita las variables DB_CONFIG en este archivo")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🔄 MIGRACIÓN DE BASE DE DATOS - SOLICITUD_SERVICIO")
    print("=" * 50)
    print("📝 Esta migración agregará la columna id_categoria faltante")
    print("🔗 Se conectará a PostgreSQL local en localhost:5432")
    print()

    try:
        asyncio.run(run_migration())
        print()
        print("🎯 ¡MIGRACIÓN COMPLETADA CON ÉXITO!")
        print("   Ahora puedes usar el sistema sin errores de base de datos.")
    except KeyboardInterrupt:
        print("\n⚠️  Migración cancelada por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        print("\n🔍 Revisa la configuración de PostgreSQL y vuelve a intentar.")
        exit(1)
