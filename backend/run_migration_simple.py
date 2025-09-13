#!/usr/bin/env python3
"""
Script simplificado para ejecutar la migración que agrega la columna id_categoria a solicitud_servicio
Sin depender de variables de entorno complejas.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# URL de base de datos local (ajusta según tu configuración)
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"

async def run_migration():
    """Ejecuta la migración para agregar id_categoria a solicitud_servicio"""
    print(f"🔗 Conectando a: {DATABASE_URL.replace(':postgres@', ':****@')}")

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

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        print("💡 Asegúrate de que:")
        print("   - PostgreSQL esté ejecutándose en localhost:54322")
        print("   - La base de datos 'postgres' existe")
        print("   - Las credenciales son correctas (usuario: postgres, password: postgres)")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🔄 Iniciando migración simplificada de base de datos...")
    print("📝 Esta migración agregará la columna id_categoria a solicitud_servicio")
    print()

    try:
        asyncio.run(run_migration())
    except KeyboardInterrupt:
        print("\n⚠️  Migración cancelada por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        exit(1)

