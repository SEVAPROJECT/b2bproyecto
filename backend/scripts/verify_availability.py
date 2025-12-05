#!/usr/bin/env python3
"""
Script para verificar que las disponibilidades se insertaron correctamente
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

async def verify():
    conn = await direct_db_service.get_connection()
    
    try:
        # Contar total
        total = await conn.fetchrow("SELECT COUNT(*) as total FROM disponibilidad")
        print(f"📊 Total disponibilidades: {total['total']}")
        
        # Contar por servicio
        por_servicio = await conn.fetchrow("""
            SELECT COUNT(DISTINCT id_servicio) as total 
            FROM disponibilidad
        """)
        print(f"📊 Servicios con disponibilidad: {por_servicio['total']}")
        
        # Ejemplo de disponibilidad
        ejemplo = await conn.fetchrow("""
            SELECT 
                id_servicio,
                fecha_inicio,
                fecha_fin,
                disponible
            FROM disponibilidad
            WHERE disponible = true
            ORDER BY fecha_inicio ASC
            LIMIT 1
        """)
        
        if ejemplo:
            print(f"\n📋 Ejemplo de disponibilidad:")
            print(f"  Servicio ID: {ejemplo['id_servicio']}")
            print(f"  Fecha inicio: {ejemplo['fecha_inicio']}")
            print(f"  Fecha fin: {ejemplo['fecha_fin']}")
            print(f"  Disponible: {ejemplo['disponible']}")
        
        # Verificar un servicio específico
        servicio_ejemplo = await conn.fetchrow("""
            SELECT id_servicio FROM servicio WHERE estado = true LIMIT 1
        """)
        
        if servicio_ejemplo:
            servicio_id = servicio_ejemplo['id_servicio']
            count = await conn.fetchrow("""
                SELECT COUNT(*) as total 
                FROM disponibilidad 
                WHERE id_servicio = $1 AND disponible = true
            """, servicio_id)
            print(f"\n📊 Disponibilidades para servicio ID {servicio_id}: {count['total']}")
            
    finally:
        await direct_db_service.pool.release(conn)

if __name__ == "__main__":
    asyncio.run(verify())




