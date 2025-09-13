#!/usr/bin/env python3
"""
Script para verificar y agregar monedas necesarias.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def check_and_add_currencies():
    """Verificar monedas existentes y agregar PYG si no existe"""
    print("🔍 Verificando monedas en la base de datos...")

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Verificar monedas existentes
            result = conn.execute(text("SELECT id_moneda, codigo_iso_moneda, nombre, simbolo FROM moneda"))
            monedas = result.fetchall()

            print(f"📋 Monedas encontradas: {len(monedas)}")
            for moneda in monedas:
                print(f"   • {moneda[1]} ({moneda[2]}) - ID: {moneda[0]}")

            # Verificar si existe PYG
            pyg_exists = any(moneda[1] == 'PYG' for moneda in monedas)

            if pyg_exists:
                print("✅ La moneda PYG ya existe")
                return

            # Agregar moneda PYG
            print("📝 Agregando moneda PYG...")
            conn.execute(text("""
                INSERT INTO moneda (codigo_iso_moneda, nombre, simbolo, created_at)
                VALUES ('PYG', 'Guaraní Paraguayo', '₲', NOW())
            """))

            # Confirmar
            conn.commit()

            print("✅ Moneda PYG agregada exitosamente")
            print("📋 Moneda agregada:")
            print("   • PYG (Guaraní Paraguayo) - ₲")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    print("💰 VERIFICACIÓN Y AGREGADO DE MONEDAS")
    print("=" * 40)
    check_and_add_currencies()
    print("\n🎯 Ahora el endpoint de aprobación debería funcionar correctamente.")

