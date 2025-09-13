#!/usr/bin/env python3
"""
Solución rápida: Agregar una moneda básica si no existe ninguna.
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def quick_fix():
    """Agregar una moneda básica rápidamente"""
    print("🚀 SOLUCIÓN RÁPIDA - AGREGAR MONEDA BÁSICA")

    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Verificar si hay monedas
            result = conn.execute(text("SELECT COUNT(*) FROM moneda"))
            count = result.scalar()

            if count > 0:
                print("✅ Ya hay monedas en la base de datos")
                result = conn.execute(text("SELECT codigo_iso_moneda, nombre FROM moneda LIMIT 5"))
                monedas = result.fetchall()
                print("Monedas existentes:")
                for moneda in monedas:
                    print(f"   • {moneda[0]} - {moneda[1]}")
                return

            # Agregar una moneda básica
            print("📝 Agregando moneda básica (USD)...")
            conn.execute(text("""
                INSERT INTO moneda (codigo_iso_moneda, nombre, simbolo, created_at)
                VALUES ('USD', 'Dólar Estadounidense', '$', NOW())
            """))

            conn.commit()
            print("✅ Moneda USD agregada exitosamente")
            print("🎯 Ahora puedes aprobar solicitudes sin problemas")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    quick_fix()

