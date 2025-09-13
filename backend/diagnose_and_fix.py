#!/usr/bin/env python3
"""
Script de diagnóstico y solución rápida para problemas de backend
"""

import os
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def print_header():
    print("🔧 DIAGNÓSTICO Y SOLUCIÓN DE PROBLEMAS - B2B BACKEND")
    print("=" * 60)

def print_step(step_num, title, description=""):
    print(f"\n{step_num}. {title}")
    if description:
        print(f"   {description}")

def check_environment():
    """Verificar configuración del entorno"""
    print_step("1", "VERIFICANDO CONFIGURACIÓN DEL ENTORNO")

    # Verificar variables de entorno
    database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_LOCAL')
    if database_url:
        print("   ✅ DATABASE_URL configurada")
    else:
        print("   ❌ DATABASE_URL no encontrada")
        print("   💡 Asegúrate de tener .env con DATABASE_URL")

    # Verificar archivos importantes
    files_to_check = [
        'app/main.py',
        'app/models/publicar_servicio/tipo_tarifa_servicio.py',
        'app/api/v1/routers/services/provider_services.py'
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} existe")
        else:
            print(f"   ❌ {file_path} no encontrado")

def generate_sql_fix():
    """Generar script SQL para arreglar la base de datos"""
    print_step("2", "SCRIPT SQL PARA ARREGLAR LA BASE DE DATOS")

    sql_script = """
-- Script para arreglar la tabla tipo_tarifa_servicio
-- Ejecuta esto en tu cliente PostgreSQL

-- 1. Verificar si existe la columna descripcion
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tipo_tarifa_servicio'
        AND column_name = 'descripcion'
    ) THEN
        ALTER TABLE tipo_tarifa_servicio
        ADD COLUMN descripcion VARCHAR(200) NOT NULL DEFAULT 'Sin descripción';
        RAISE NOTICE '✅ Columna descripcion agregada';
    ELSE
        RAISE NOTICE '✅ Columna descripcion ya existe';
    END IF;
END $$;

-- 2. Insertar tipos de tarifa por defecto si no existen
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

-- 3. Verificar resultado
SELECT id_tarifa, nombre, descripcion, estado
FROM tipo_tarifa_servicio
ORDER BY id_tarifa;
"""

    print("   📋 Copia y ejecuta este script SQL en tu base de datos:")
    print("   " + "=" * 55)
    print(sql_script)
    print("   " + "=" * 55)

def print_server_commands():
    """Mostrar comandos para iniciar el servidor"""
    print_step("3", "COMANDOS PARA INICIAR EL SERVIDOR")

    commands = [
        ("Navegar al directorio backend", "cd b2bproyecto-main-main/backend"),
        ("Instalar dependencias (si es necesario)", "pip install -r requirements.txt"),
        ("Iniciar servidor con uvicorn", "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"),
        ("O usar script personalizado", "python run_simple.py"),
        ("Verificar CORS", "curl -H 'Origin: http://localhost:5173' -v http://localhost:8000/api/v1/provider/services/options/monedas")
    ]

    for desc, cmd in commands:
        print(f"   📌 {desc}:")
        print(f"      {cmd}")
        print()

def print_frontend_commands():
    """Mostrar comandos para el frontend"""
    print_step("4", "COMANDOS PARA EL FRONTEND")

    commands = [
        ("Navegar al directorio frontend", "cd b2bproyecto-main-main/frontend"),
        ("Instalar dependencias", "npm install"),
        ("Iniciar servidor de desarrollo", "npm run dev"),
        ("Verificar que corre en puerto 5173", "http://localhost:5173")
    ]

    for desc, cmd in commands:
        print(f"   📌 {desc}:")
        print(f"      {cmd}")
        print()

def print_troubleshooting():
    """Mostrar consejos de solución de problemas"""
    print_step("5", "CONSEJOS DE SOLUCIÓN DE PROBLEMAS")

    tips = [
        "Si CORS persiste, verifica que el servidor backend esté corriendo en el puerto 8000",
        "Si hay errores de base de datos, ejecuta el script SQL proporcionado arriba",
        "Si el frontend muestra 'Failed to fetch', verifica que ambos servidores estén corriendo",
        "Revisa la consola del navegador (F12) para errores detallados",
        "Verifica que las variables de entorno estén configuradas correctamente",
        "Si hay errores de importación, ejecuta 'pip install -r requirements.txt' en backend"
    ]

    for i, tip in enumerate(tips, 1):
        print(f"   💡 {i}. {tip}")

def main():
    print_header()
    check_environment()
    generate_sql_fix()
    print_server_commands()
    print_frontend_commands()
    print_troubleshooting()

    print("\n" + "=" * 60)
    print("🎯 RESUMEN DE SOLUCIONES:")
    print("1. ✅ Problema de CORS: Configurado correctamente en main.py")
    print("2. ✅ Problema de columna BD: Script SQL generado arriba")
    print("3. ✅ Endpoint simplificado: Consultas separadas para evitar JOINs complejos")
    print("4. ✅ Endpoint robusto: Manejo de errores y datos por defecto")
    print("=" * 60)

if __name__ == "__main__":
    main()

