#!/usr/bin/env python3
"""
Script para corregir la tabla moneda agregando la columna faltante.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

async def fix_moneda_table():
    """Agregar la columna estado a la tabla moneda si no existe"""
    print("🔧 Corrigiendo tabla 'moneda'...")

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Verificar si la columna existe
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'moneda' AND column_name = 'estado'
            """))

            if result.fetchone():
                print("✅ La columna 'estado' ya existe")
                return

            # Agregar la columna estado
            print("📝 Agregando columna 'estado'...")
            conn.execute(text("""
                ALTER TABLE moneda ADD COLUMN estado BOOLEAN DEFAULT true
            """))

            # Confirmar los cambios
            conn.commit()

            print("✅ Columna 'estado' agregada exitosamente")
            print("📋 Verificando la estructura final...")

            # Verificar la estructura final
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'moneda'
                ORDER BY ordinal_position
            """))

            columns = result.fetchall()
            print("📋 Estructura final de la tabla 'moneda':")
            for col in columns:
                print(f"   • {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")

    except Exception as e:
        print(f"❌ Error al corregir la tabla: {e}")

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_moneda_table())

