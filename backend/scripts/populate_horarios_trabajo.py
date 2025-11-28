#!/usr/bin/env python3
"""
Script para insertar horarios de trabajo para proveedores que no los tienen.
Crea horarios estándar: Lunes a Viernes, 9:00 AM - 5:00 PM

Uso:
    python scripts/populate_horarios_trabajo.py
"""

import sys
import os
import asyncio
from datetime import time
from typing import List, Dict, Any

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

# Horarios estándar: Lunes a Viernes (0-4), 9:00 AM - 5:00 PM
HORARIOS_ESTANDAR = [
    {"dia_semana": 0, "hora_inicio": time(9, 0), "hora_fin": time(17, 0), "activo": True},  # Lunes
    {"dia_semana": 1, "hora_inicio": time(9, 0), "hora_fin": time(17, 0), "activo": True},  # Martes
    {"dia_semana": 2, "hora_inicio": time(9, 0), "hora_fin": time(17, 0), "activo": True},  # Miércoles
    {"dia_semana": 3, "hora_inicio": time(9, 0), "hora_fin": time(17, 0), "activo": True},  # Jueves
    {"dia_semana": 4, "hora_inicio": time(9, 0), "hora_fin": time(17, 0), "activo": True},  # Viernes
]

async def get_proveedores_sin_horarios() -> List[Dict[str, Any]]:
    """Obtiene proveedores que no tienen horarios de trabajo configurados"""
    conn = await direct_db_service.get_connection()
    
    try:
        query = """
            SELECT DISTINCT pe.id_perfil, pe.razon_social, pe.nombre_fantasia
            FROM perfil_empresa pe
            WHERE pe.estado = 'ACTIVO' 
            AND pe.verificado = true
            AND pe.id_perfil NOT IN (
                SELECT DISTINCT id_proveedor 
                FROM horario_trabajo
            )
            ORDER BY pe.id_perfil
        """
        
        proveedores = await conn.fetch(query)
        return [dict(prov) for prov in proveedores]
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_proveedores_con_horarios() -> List[int]:
    """Obtiene IDs de proveedores que ya tienen horarios"""
    conn = await direct_db_service.get_connection()
    
    try:
        query = """
            SELECT DISTINCT id_proveedor
            FROM horario_trabajo
        """
        
        proveedores = await conn.fetch(query)
        return [row['id_proveedor'] for row in proveedores]
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def insert_horarios_proveedor(conn, id_proveedor: int) -> int:
    """Inserta los horarios estándar para un proveedor"""
    horarios_insertados = 0
    
    for horario in HORARIOS_ESTANDAR:
        # Verificar si ya existe
        check_query = """
            SELECT id_horario 
            FROM horario_trabajo 
            WHERE id_proveedor = $1 AND dia_semana = $2
        """
        existe = await conn.fetchrow(check_query, id_proveedor, horario["dia_semana"])
        
        if not existe:
            insert_query = """
                INSERT INTO horario_trabajo (
                    id_proveedor, 
                    dia_semana, 
                    hora_inicio, 
                    hora_fin, 
                    activo
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id_horario
            """
            
            await conn.execute(
                insert_query,
                id_proveedor,
                horario["dia_semana"],
                horario["hora_inicio"],
                horario["hora_fin"],
                horario["activo"]
            )
            horarios_insertados += 1
    
    return horarios_insertados

async def populate_horarios_trabajo():
    """Inserta horarios de trabajo para proveedores que no los tienen"""
    print("🚀 Iniciando población de horarios de trabajo...\n")
    
    # Verificar estado actual
    print("📊 Verificando estado actual...")
    proveedores_con_horarios = await get_proveedores_con_horarios()
    print(f"📊 Proveedores con horarios: {len(proveedores_con_horarios)}")
    
    proveedores_sin_horarios = await get_proveedores_sin_horarios()
    total_sin_horarios = len(proveedores_sin_horarios)
    print(f"📊 Proveedores sin horarios: {total_sin_horarios}\n")
    
    if total_sin_horarios == 0:
        print("✅ Todos los proveedores ya tienen horarios de trabajo configurados")
        return
    
    print(f"📦 Insertando horarios para {total_sin_horarios} proveedores...\n")
    
    conn = await direct_db_service.get_connection()
    
    try:
        total_horarios_insertados = 0
        
        async with conn.transaction():
            for i, proveedor in enumerate(proveedores_sin_horarios, 1):
                id_proveedor = proveedor['id_perfil']
                nombre = proveedor.get('nombre_fantasia', proveedor.get('razon_social', 'N/A'))
                
                print(f"📦 Procesando proveedor {i}/{total_sin_horarios}: {nombre} (ID: {id_proveedor})...")
                
                horarios_insertados = await insert_horarios_proveedor(conn, id_proveedor)
                total_horarios_insertados += horarios_insertados
                
                print(f"  ✅ {horarios_insertados} horarios insertados")
        
        # Resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN")
        print("=" * 60)
        print(f"✅ Proveedores procesados: {total_sin_horarios}")
        print(f"📊 Total horarios insertados: {total_horarios_insertados}")
        print(f"📅 Horarios por proveedor: {len(HORARIOS_ESTANDAR)} días (Lunes a Viernes)")
        print(f"⏰ Horario: 9:00 AM - 5:00 PM")
        print()
        
        # Verificar
        total_horarios = await conn.fetchrow("SELECT COUNT(*) as total FROM horario_trabajo")
        print(f"✅ Verificación: {total_horarios['total']} horarios en total en la base de datos")
        
    except Exception as e:
        print(f"❌ Error durante la población: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

if __name__ == "__main__":
    asyncio.run(populate_horarios_trabajo())

