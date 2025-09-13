#!/usr/bin/env python3
"""
Script para configurar monedas básicas en la base de datos.
"""
import asyncio
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

# Monedas básicas a configurar
DEFAULT_CURRENCIES = [
    ('PYG', 'Guaraní Paraguayo', '₲'),
    ('USD', 'Dólar Estadounidense', '$'),
    ('EUR', 'Euro', '€'),
    ('BRL', 'Real Brasileño', 'R$'),
]

def setup_currencies():
    """Configurar monedas básicas si no existen"""
    print("💰 CONFIGURACIÓN DE MONEDAS BÁSICAS")
    print("=" * 40)

    try:
        # Crear conexión
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Verificar monedas existentes
            result = conn.execute(text("SELECT codigo_iso_moneda FROM moneda"))
            existing_codes = [row[0] for row in result.fetchall()]

            print(f"📋 Monedas existentes: {existing_codes}")

            # Agregar monedas faltantes
            added_count = 0
            for codigo, nombre, simbolo in DEFAULT_CURRENCIES:
                if codigo not in existing_codes:
                    print(f"📝 Agregando moneda: {codigo} ({nombre})")
                    conn.execute(text("""
                        INSERT INTO moneda (codigo_iso_moneda, nombre, simbolo, created_at)
                        VALUES (:codigo, :nombre, :simbolo, NOW())
                    """), {
                        'codigo': codigo,
                        'nombre': nombre,
                        'simbolo': simbolo
                    })
                    added_count += 1
                else:
                    print(f"✅ Moneda {codigo} ya existe")

            if added_count > 0:
                conn.commit()
                print(f"\n✅ {added_count} monedas agregadas exitosamente")
            else:
                print("\n✅ Todas las monedas básicas ya existen")

            # Mostrar resumen final
            result = conn.execute(text("SELECT id_moneda, codigo_iso_moneda, nombre, simbolo FROM moneda ORDER BY codigo_iso_moneda"))
            final_monedas = result.fetchall()

            print("
📋 Monedas disponibles:"            for moneda in final_monedas:
                print(f"   • {moneda[1]} ({moneda[2]}) - {moneda[3]} (ID: {moneda[0]})")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Posibles soluciones:")
        print("1. Verificar que PostgreSQL esté ejecutándose")
        print("2. Verificar que la tabla 'moneda' existe")
        print("3. Verificar credenciales de conexión")

    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    setup_currencies()
    print("\n🎯 ¡Configuración completada!")
    print("Ahora puedes aprobar solicitudes de servicios sin problemas.")

