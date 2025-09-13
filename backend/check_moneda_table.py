#!/usr/bin/env python3
"""
Script para verificar la estructura real de la tabla moneda.
"""
import asyncio
from sqlalchemy import create_engine, text, inspect

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def check_moneda_table():
    """Verificar la estructura de la tabla moneda"""
    print("🔍 Verificando estructura de la tabla 'moneda'...")

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)

        # Verificar si la tabla existe
        if not inspector.has_table('moneda'):
            print("❌ La tabla 'moneda' no existe")
            return

        # Obtener columnas de la tabla
        columns = inspector.get_columns('moneda')
        print("📋 Columnas encontradas en la tabla 'moneda':")
        print("-" * 50)

        for col in columns:
            print(f"• {col['name']}: {col['type']} (nullable: {col['nullable']})")

        # Verificar si existe la columna 'estado'
        column_names = [col['name'] for col in columns]
        if 'estado' in column_names:
            print("✅ La columna 'estado' existe")
        else:
            print("❌ La columna 'estado' NO existe")
            print("💡 Necesitas agregar esta columna o corregir el modelo")

        # Verificar datos en la tabla
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM moneda"))
            count = result.scalar()
            print(f"📊 Registros en la tabla: {count}")

            if count > 0:
                result = conn.execute(text("SELECT id_moneda, codigo_iso_moneda, nombre FROM moneda LIMIT 3"))
                rows = result.fetchall()
                print("📋 Primeros registros:")
                for row in rows:
                    print(f"   • ID: {row[0]}, Código: {row[1]}, Nombre: {row[2]}")

    except Exception as e:
        print(f"❌ Error al verificar la tabla: {e}")

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    check_moneda_table()

