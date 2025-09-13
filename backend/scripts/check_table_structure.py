#!/usr/bin/env python3
"""
Script para verificar la estructura de las tablas
"""

import asyncio
import asyncpg

async def check_table_structure():
    """Verifica la estructura de las tablas relevantes"""
    
    DATABASE_URL = "postgresql://postgres:postgres@localhost:54322/postgres"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🔍 Verificando estructura de tablas...")
        print("=" * 60)
        
        # Verificar estructura de perfil_empresa
        print("1️⃣ Estructura de perfil_empresa:")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'perfil_empresa' 
            ORDER BY ordinal_position
        """)
        
        for row in result:
            print(f"   - {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        print("\n2️⃣ Estructura de usuario_rol:")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'usuario_rol' 
            ORDER BY ordinal_position
        """)
        
        for row in result:
            print(f"   - {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        print("\n3️⃣ Estructura de rol:")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'rol' 
            ORDER BY ordinal_position
        """)
        
        for row in result:
            print(f"   - {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())
