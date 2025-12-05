#!/usr/bin/env python3
"""
Script para exportar la estructura de las tablas de la base de datos
en formato SQL y JSON para facilitar la inserción masiva de datos.

Uso:
    python scripts/export_table_structure.py
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

async def get_table_structure(table_name: str):
    """Obtiene la estructura de una tabla."""
    conn = await direct_db_service.get_connection()
    try:
        # Obtener columnas de la tabla
        query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position;
        """
        rows = await conn.fetch(query, table_name)
        
        columns = []
        for row in rows:
            columns.append({
                'name': row['column_name'],
                'type': row['data_type'],
                'max_length': row['character_maximum_length'],
                'nullable': row['is_nullable'] == 'YES',
                'default': row['column_default'],
                'position': row['ordinal_position']
            })
        
        return columns
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_all_tables():
    """Obtiene todas las tablas de la base de datos."""
    conn = await direct_db_service.get_connection()
    try:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        rows = await conn.fetch(query)
        return [row['table_name'] for row in rows]
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def export_structure():
    """Exporta la estructura de todas las tablas."""
    print("🔍 Obteniendo lista de tablas...")
    tables = await get_all_tables()
    
    print(f"📊 Encontradas {len(tables)} tablas\n")
    
    structure = {}
    sql_ddl = []
    
    for table_name in tables:
        print(f"📋 Procesando tabla: {table_name}")
        columns = await get_table_structure(table_name)
        structure[table_name] = columns
        
        # Generar SQL CREATE TABLE básico
        sql_parts = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
        col_defs = []
        for col in columns:
            col_def = f"    {col['name']} {col['type']}"
            if col['max_length']:
                col_def += f"({col['max_length']})"
            if not col['nullable']:
                col_def += " NOT NULL"
            if col['default']:
                col_def += f" DEFAULT {col['default']}"
            col_defs.append(col_def)
        sql_parts.append(",\n".join(col_defs))
        sql_parts.append(");")
        sql_ddl.append("\n".join(sql_parts))
    
    # Guardar en JSON
    json_file = "database_structure.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Estructura guardada en: {json_file}")
    
    # Guardar SQL DDL
    sql_file = "database_structure.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write("-- Estructura de tablas exportada\n")
        f.write(f"-- Fecha: {datetime.now()}\n\n")
        for ddl in sql_ddl:
            f.write(ddl + "\n\n")
    print(f"✅ DDL SQL guardado en: {sql_file}")
    
    # Mostrar resumen
    print("\n📊 Resumen de tablas:")
    for table_name, columns in structure.items():
        print(f"  - {table_name}: {len(columns)} columnas")

if __name__ == "__main__":
    asyncio.run(export_structure())




