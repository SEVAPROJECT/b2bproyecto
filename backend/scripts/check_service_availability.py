#!/usr/bin/env python3
"""Script para verificar disponibilidades de un servicio específico"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

async def check_service_availability(servicio_id: int):
    conn = await direct_db_service.get_connection()
    try:
        # Verificar si el servicio existe
        servicio = await conn.fetchrow(
            "SELECT id_servicio, nombre, estado FROM servicio WHERE id_servicio = $1",
            servicio_id
        )
        
        if not servicio:
            print(f"❌ Servicio {servicio_id} no existe")
            return
        
        print(f"✅ Servicio {servicio_id}: {servicio['nombre']} (Estado: {servicio['estado']})\n")
        
        # Contar disponibilidades
        count = await conn.fetchrow(
            """
            SELECT COUNT(*) as total 
            FROM disponibilidad 
            WHERE id_servicio = $1 
            AND disponible = true 
            AND fecha_inicio >= CURRENT_DATE
            AND fecha_inicio <= CURRENT_DATE + INTERVAL '30 days'
            """,
            servicio_id
        )
        
        print(f"📊 Disponibilidades encontradas: {count['total']}\n")
        
        if count['total'] > 0:
            # Obtener ejemplos
            ejemplos = await conn.fetch(
                """
                SELECT fecha_inicio, fecha_fin, disponible, precio_adicional
                FROM disponibilidad 
                WHERE id_servicio = $1 
                AND disponible = true 
                AND fecha_inicio >= CURRENT_DATE
                AND fecha_inicio <= CURRENT_DATE + INTERVAL '30 days'
                ORDER BY fecha_inicio ASC
                LIMIT 10
                """,
                servicio_id
            )
            
            print("📋 Primeros 10 ejemplos:")
            for i, ej in enumerate(ejemplos, 1):
                print(f"  {i}. {ej['fecha_inicio']} - {ej['fecha_fin']} (Disponible: {ej['disponible']})")
        else:
            print("⚠️  No hay disponibilidades para este servicio")
            
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Verificar disponibilidades de un servicio")
    parser.add_argument("--servicio", type=int, default=786, help="ID del servicio")
    args = parser.parse_args()
    asyncio.run(check_service_availability(args.servicio))



