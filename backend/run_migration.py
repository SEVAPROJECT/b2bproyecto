#!/usr/bin/env python3
"""
Script para ejecutar la migración que agrega la columna id_categoria a solicitud_servicio
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

# Cargar variables de entorno
load_dotenv()

# Configurar la conexión a la base de datos
DATABASE_URL_LOCAL = os.getenv("DATABASE_URL_LOCAL")
if not DATABASE_URL_LOCAL:
    print("❌ Error: DATABASE_URL_LOCAL no está configurada")
    exit(1)

async def run_migration():
    """Ejecuta la migración para agregar id_categoria a solicitud_servicio"""
    engine = create_async_engine(DATABASE_URL_LOCAL, echo=True)

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
            print("✅ Migración completada exitosamente")

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🔄 Iniciando migración de base de datos...")
    asyncio.run(run_migration())
    print("🎉 Proceso completado")

