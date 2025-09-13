#!/usr/bin/env python3
"""
Script para corregir la tabla tipo_tarifa_servicio agregando la columna descripcion faltante
"""

import asyncpg
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def fix_tipo_tarifa_servicio_table():
    """Agrega la columna descripcion faltante a la tabla tipo_tarifa_servicio"""

    # Configuración de la base de datos
    DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_LOCAL')

    if not DATABASE_URL:
        print("❌ No se encontró DATABASE_URL en las variables de entorno")
        return

    try:
        print("🔧 Conectando a la base de datos...")
        conn = await asyncpg.connect(DATABASE_URL)

        # Verificar si la columna descripcion existe
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'tipo_tarifa_servicio'
                AND column_name = 'descripcion'
            )
        """)

        if result:
            print("✅ La columna 'descripcion' ya existe en la tabla tipo_tarifa_servicio")
        else:
            print("📝 Agregando columna 'descripcion' a la tabla tipo_tarifa_servicio...")

            # Agregar la columna descripcion
            await conn.execute("""
                ALTER TABLE tipo_tarifa_servicio
                ADD COLUMN descripcion VARCHAR(200) NOT NULL DEFAULT 'Sin descripción'
            """)

            print("✅ Columna 'descripcion' agregada exitosamente")

        # Verificar si hay datos en la tabla y actualizar descripciones por defecto
        count = await conn.fetchval("SELECT COUNT(*) FROM tipo_tarifa_servicio")

        if count == 0:
            print("📝 Insertando tipos de tarifa por defecto...")

            await conn.executemany("""
                INSERT INTO tipo_tarifa_servicio (nombre, descripcion, estado)
                VALUES ($1, $2, $3)
            """, [
                ('Por hora', 'Tarifa calculada por hora de trabajo', True),
                ('Por día', 'Tarifa calculada por día de trabajo', True),
                ('Por proyecto', 'Tarifa fija por proyecto completo', True),
                ('Por semana', 'Tarifa calculada por semana de trabajo', True),
                ('Por mes', 'Tarifa calculada por mes de trabajo', True)
            ])

            print("✅ Tipos de tarifa por defecto insertados")
        else:
            print(f"✅ La tabla ya tiene {count} registros")

        await conn.close()
        print("🎉 Operación completada exitosamente!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(fix_tipo_tarifa_servicio_table())

