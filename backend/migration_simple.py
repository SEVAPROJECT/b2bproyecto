#!/usr/bin/env python3
"""
Script simple de migración usando psycopg2 directo.
"""
import psycopg2
import sys

# Configuración de conexión
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "postgres",
    "user": "postgres",
    "password": "postgres"
}

def test_connection():
    """Prueba la conexión a PostgreSQL"""
    try:
        print("🔍 Probando conexión a PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print("✅ Conexión exitosa!")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def run_migration():
    """Ejecuta la migración"""
    try:
        print("🚀 Ejecutando migración...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # SQL de migración
        migration_sql = """
        -- Agregar columna id_categoria
        ALTER TABLE solicitud_servicio ADD COLUMN IF NOT EXISTS id_categoria BIGINT;

        -- Agregar clave foránea
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

        -- Crear índice
        CREATE INDEX IF NOT EXISTS idx_solicitud_servicio_id_categoria
        ON solicitud_servicio(id_categoria);

        -- Agregar comentario
        COMMENT ON COLUMN solicitud_servicio.id_categoria IS 'Referencia a la categoría del servicio solicitado';
        """

        cursor.execute(migration_sql)
        conn.commit()

        print("✅ Migración completada exitosamente!")
        print("🎉 La columna id_categoria ha sido agregada a solicitud_servicio")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

    return True

def main():
    print("🔄 MIGRACIÓN SIMPLE - PostgreSQL")
    print("=" * 35)

    if not test_connection():
        print("\n💡 PostgreSQL no está disponible.")
        print("📝 Soluciones:")
        print("   1. Inicia PostgreSQL desde servicios de Windows")
        print("   2. Ejecuta: pg_ctl start -D \"C:\\Program Files\\PostgreSQL\\XX\\data\"")
        print("   3. O ejecuta el archivo migration_manual.sql manualmente")
        print()
        print("📋 Archivo SQL creado: migration_manual.sql")
        print("   - Ábrelo con pgAdmin o psql")
        print("   - Ejecuta todo el contenido")
        return

    if run_migration():
        print("\n🎯 ¡MIGRACIÓN COMPLETADA!")
        print("   Ahora puedes usar el sistema sin errores.")
    else:
        print("\n❌ La migración falló.")

if __name__ == "__main__":
    main()

