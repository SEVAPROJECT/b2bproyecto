#!/usr/bin/env python3
"""Script rápido para insertar categorías faltantes."""
import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.direct_db_service import direct_db_service

async def insert_categories():
    conn = await direct_db_service.get_connection()
    try:
        await conn.execute("INSERT INTO categoria (nombre, estado) VALUES ('Eventos', true) ON CONFLICT DO NOTHING")
        await conn.execute("INSERT INTO categoria (nombre, estado) VALUES ('Limpieza', true) ON CONFLICT DO NOTHING")
        print("✅ Categorías Eventos y Limpieza insertadas")
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

if __name__ == "__main__":
    asyncio.run(insert_categories())



