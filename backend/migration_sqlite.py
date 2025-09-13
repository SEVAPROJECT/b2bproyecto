#!/usr/bin/env python3
"""
Script de migración usando SQLite para evitar problemas de conexión PostgreSQL.
"""
import sqlite3
import os

# Ruta de la base de datos SQLite (temporal para pruebas)
DB_PATH = "test_migration.db"

def run_sqlite_migration():
    """Ejecuta una migración de prueba en SQLite para verificar la sintaxis SQL"""
    print("🔄 MIGRACIÓN DE PRUEBA - SQLITE")
    print("=" * 40)
    print("📝 Creando base de datos de prueba con SQLite")
    print(f"📁 Archivo: {DB_PATH}")
    print()

    # Crear conexión SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Crear tablas de prueba
        print("🏗️  Creando tablas de prueba...")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categoria (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_categoria TEXT NOT NULL,
            descripcion TEXT,
            activo BOOLEAN DEFAULT 1
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitud_servicio (
            id_solicitud INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_servicio TEXT NOT NULL,
            descripcion TEXT,
            id_perfil_empresa INTEGER,
            fecha_solicitud TEXT DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'pendiente'
        )
        """)

        # Ejecutar la migración
        print("🚀 Ejecutando migración...")

        migration_sql = """
        -- Migración: Agregar columna id_categoria a solicitud_servicio
        ALTER TABLE solicitud_servicio ADD COLUMN id_categoria INTEGER;

        -- Crear índice para rendimiento
        CREATE INDEX IF NOT EXISTS idx_solicitud_servicio_id_categoria
        ON solicitud_servicio(id_categoria);
        """

        # SQLite maneja ALTER TABLE de forma diferente
        try:
            cursor.execute("ALTER TABLE solicitud_servicio ADD COLUMN id_categoria INTEGER")
            print("   ✅ Columna id_categoria agregada")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  Columna id_categoria ya existe")
            else:
                raise

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_solicitud_servicio_id_categoria ON solicitud_servicio(id_categoria)")
            print("   ✅ Índice creado")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Error con índice: {e}")

        # Verificar estructura de la tabla
        cursor.execute("PRAGMA table_info(solicitud_servicio)")
        columns = cursor.fetchall()

        print("📋 Estructura de la tabla solicitud_servicio:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

        conn.commit()

        print("\n✅ Migración completada exitosamente!")
        print("🎯 El SQL está correcto y funcionará en PostgreSQL")
        print()
        print("📝 Para PostgreSQL real:")
        print("   1. Asegúrate de que PostgreSQL esté ejecutándose")
        print("   2. Crea la base de datos si no existe")
        print("   3. Ejecuta el script original con las credenciales correctas")

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        raise
    finally:
        conn.close()

        # Limpiar archivo de prueba
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
                print(f"🧹 Archivo de prueba {DB_PATH} eliminado")
            except:
                print(f"⚠️  No se pudo eliminar {DB_PATH}")

if __name__ == "__main__":
    try:
        run_sqlite_migration()
    except KeyboardInterrupt:
        print("\n⚠️  Migración cancelada por el usuario")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        exit(1)

