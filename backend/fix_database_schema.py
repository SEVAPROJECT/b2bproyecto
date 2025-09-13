#!/usr/bin/env python3
"""
Script simple para arreglar el esquema de la base de datos
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_LOCAL')

if not DATABASE_URL:
    print("❌ No se encontró DATABASE_URL")
    DATABASE_URL = input("Ingresa la URL de la base de datos: ")

# Script SQL para ejecutar
sql_script = """
-- Verificar y agregar columna descripcion a tipo_tarifa_servicio si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tipo_tarifa_servicio'
        AND column_name = 'descripcion'
    ) THEN
        ALTER TABLE tipo_tarifa_servicio
        ADD COLUMN descripcion VARCHAR(200) NOT NULL DEFAULT 'Sin descripción';
        RAISE NOTICE 'Columna descripcion agregada a tipo_tarifa_servicio';
    ELSE
        RAISE NOTICE 'La columna descripcion ya existe en tipo_tarifa_servicio';
    END IF;
END $$;

-- Insertar tipos de tarifa por defecto si la tabla está vacía
INSERT INTO tipo_tarifa_servicio (nombre, descripcion, estado)
SELECT * FROM (VALUES
    ('Por hora', 'Tarifa calculada por hora de trabajo', true),
    ('Por día', 'Tarifa calculada por día de trabajo', true),
    ('Por proyecto', 'Tarifa fija por proyecto completo', true),
    ('Por semana', 'Tarifa calculada por semana de trabajo', true),
    ('Por mes', 'Tarifa calculada por mes de trabajo', true)
) AS v(nombre, descripcion, estado)
WHERE NOT EXISTS (
    SELECT 1 FROM tipo_tarifa_servicio
    WHERE nombre = v.nombre
);

-- Verificar estructura de la tabla
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'tipo_tarifa_servicio'
ORDER BY ordinal_position;
"""

print("📝 Script SQL para arreglar la base de datos:")
print("=" * 50)
print(sql_script)
print("=" * 50)

print("\n📋 INSTRUCCIONES:")
print("1. Copia el script SQL de arriba")
print("2. Ejecutalo en tu cliente PostgreSQL (pgAdmin, DBeaver, etc.)")
print("3. O ejecutalo desde línea de comandos:")
print(f"   psql '{DATABASE_URL}' -c \"{sql_script.replace(chr(10), ' ').replace(chr(13), '')}\"")
print("\n4. Después de ejecutar el script, reinicia el servidor backend")
print("\n✅ Esto debería resolver el error de columna faltante")

