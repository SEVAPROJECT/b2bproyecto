#!/usr/bin/env python3
"""
Script para configurar la zona horaria de la base de datos a GMT-3
"""
import sys
import os
import asyncio

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.supabase.db.db_supabase import AsyncSessionLocal
from sqlalchemy import text

async def set_database_timezone():
    """Configura la zona horaria de la base de datos a GMT-3"""
    print("🕐 Configurando zona horaria de la base de datos a GMT-3...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Verificar zona horaria actual
            print("\n🔄 Verificando zona horaria actual")
            result = await db.execute(text("SELECT current_setting('timezone') as current_tz"))
            current_tz = result.scalar()
            print(f"✅ Zona horaria actual: {current_tz}")
            
            # Configurar zona horaria a GMT-3
            print("\n🔄 Configurando zona horaria a GMT-3")
            await db.execute(text("SET timezone = 'America/Argentina/Buenos_Aires'"))  # GMT-3
            await db.commit()
            
            # Verificar que se aplicó el cambio
            result = await db.execute(text("SELECT current_setting('timezone') as new_tz"))
            new_tz = result.scalar()
            print(f"✅ Nueva zona horaria: {new_tz}")
            
            # Verificar fecha actual
            result = await db.execute(text("SELECT now() as current_time"))
            current_time = result.scalar()
            print(f"✅ Fecha actual: {current_time}")
            
            print("\n🎉 Zona horaria configurada exitosamente!")
            print("💡 Nota: Este cambio es temporal para la sesión actual.")
            print("💡 Para hacerlo permanente, necesitas configurarlo en Supabase.")
            
    except Exception as e:
        print(f"❌ Error configurando zona horaria: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(set_database_timezone())
