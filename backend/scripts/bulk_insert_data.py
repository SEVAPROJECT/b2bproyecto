#!/usr/bin/env python3
"""
Script para insertar datos masivamente en la base de datos.

Uso:
    python scripts/bulk_insert_data.py
"""

import sys
import os
import asyncio
import json
from datetime import datetime, date, time
from typing import List, Dict, Any

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

async def bulk_insert_departamentos(departamentos: List[Dict[str, Any]]):
    """Inserta departamentos masivamente."""
    conn = await direct_db_service.get_connection()
    try:
        async with conn.transaction():
            for dept in departamentos:
                await conn.execute(
                    "INSERT INTO departamento (nombre) VALUES ($1) ON CONFLICT DO NOTHING",
                    dept['nombre']
                )
        print(f"✅ Insertados {len(departamentos)} departamentos")
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def bulk_insert_ciudades(ciudades: List[Dict[str, Any]]):
    """Inserta ciudades masivamente."""
    conn = await direct_db_service.get_connection()
    try:
        async with conn.transaction():
            for ciudad in ciudades:
                # Obtener id_departamento
                dept_row = await conn.fetchrow(
                    "SELECT id_departamento FROM departamento WHERE nombre = $1",
                    ciudad['departamento']
                )
                if not dept_row:
                    print(f"⚠️  Departamento '{ciudad['departamento']}' no encontrado, saltando ciudad '{ciudad['nombre']}'")
                    continue
                
                await conn.execute(
                    "INSERT INTO ciudad (nombre, id_departamento) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    ciudad['nombre'],
                    dept_row['id_departamento']
                )
        print(f"✅ Insertadas {len(ciudades)} ciudades")
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def bulk_insert_barrios(barrios: List[Dict[str, Any]]):
    """Inserta barrios masivamente."""
    conn = await direct_db_service.get_connection()
    try:
        async with conn.transaction():
            for barrio in barrios:
                # Obtener id_ciudad
                ciudad_row = await conn.fetchrow(
                    "SELECT id_ciudad FROM ciudad WHERE nombre = $1",
                    barrio['ciudad']
                )
                if not ciudad_row:
                    print(f"⚠️  Ciudad '{barrio['ciudad']}' no encontrada, saltando barrio '{barrio['nombre']}'")
                    continue
                
                await conn.execute(
                    "INSERT INTO barrio (nombre, id_ciudad) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    barrio['nombre'],
                    ciudad_row['id_ciudad']
                )
        print(f"✅ Insertados {len(barrios)} barrios")
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def bulk_insert_categorias(categorias: List[Dict[str, Any]]):
    """Inserta categorías masivamente."""
    conn = await direct_db_service.get_connection()
    try:
        async with conn.transaction():
            for cat in categorias:
                await conn.execute(
                    "INSERT INTO categoria (nombre, estado) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    cat['nombre'],
                    cat.get('estado', True)
                )
        print(f"✅ Insertadas {len(categorias)} categorías")
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def bulk_insert_tipos_documento(tipos: List[Dict[str, Any]]):
    """Inserta tipos de documento masivamente."""
    conn = await direct_db_service.get_connection()
    try:
        async with conn.transaction():
            for tipo in tipos:
                # estado_documento parece ser un string, no boolean
                await conn.execute(
                    """
                    INSERT INTO tipo_documento (tipo_documento, es_requerido, estado_documento) 
                    VALUES ($1, $2, $3) 
                    ON CONFLICT DO NOTHING
                    """,
                    tipo['nombre'],
                    tipo.get('es_requerido', True),
                    tipo.get('estado_documento', 'ACTIVO')  # String, no boolean
                )
        print(f"✅ Insertados {len(tipos)} tipos de documento")
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def load_data_from_json(file_path: str):
    """Carga datos desde un archivo JSON y los inserta."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'departamentos' in data:
        await bulk_insert_departamentos(data['departamentos'])
    
    if 'ciudades' in data:
        await bulk_insert_ciudades(data['ciudades'])
    
    if 'barrios' in data:
        await bulk_insert_barrios(data['barrios'])
    
    if 'categorias' in data:
        await bulk_insert_categorias(data['categorias'])
    
    if 'tipos_documento' in data:
        await bulk_insert_tipos_documento(data['tipos_documento'])

async def main():
    """Función principal."""
    print("🚀 Iniciando inserción masiva de datos...\n")
    
    # Ejemplo de datos (puedes cargar desde un archivo JSON)
    sample_data = {
        'departamentos': [
            {'nombre': 'Central'},
            {'nombre': 'Asunción'},
            {'nombre': 'Alto Paraná'},
            {'nombre': 'Itapúa'},
        ],
        'categorias': [
            {'nombre': 'Catering', 'estado': True},
            {'nombre': 'Transporte', 'estado': True},
            {'nombre': 'Salud', 'estado': True},
            {'nombre': 'Educación', 'estado': True},
        ],
        'tipos_documento': [
            {'nombre': 'Constancia de RUC', 'es_requerido': True},
            {'nombre': 'Cédula MiPymes', 'es_requerido': True},
            {'nombre': 'Certificado de Cumplimiento Tributario', 'es_requerido': True},
            {'nombre': 'Certificados del Rubro', 'es_requerido': True},
        ]
    }
    
    # Si existe un archivo JSON, usarlo
    json_file = "sample_data.json"
    if os.path.exists(json_file):
        print(f"📂 Cargando datos desde: {json_file}")
        await load_data_from_json(json_file)
    else:
        print("📝 Usando datos de ejemplo (crea 'sample_data.json' para datos personalizados)")
        await bulk_insert_departamentos(sample_data['departamentos'])
        await bulk_insert_categorias(sample_data['categorias'])
        await bulk_insert_tipos_documento(sample_data['tipos_documento'])
    
    print("\n✅ Inserción masiva completada")

if __name__ == "__main__":
    asyncio.run(main())

