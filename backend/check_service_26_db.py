#!/usr/bin/env python3
"""
Script para verificar el servicio ID 26 en la base de datos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.direct_db_service import direct_db_service
import asyncio

async def check_service_26():
    """Verificar el servicio ID 26 en la base de datos"""
    print("🔍 Verificando servicio ID 26 en la base de datos...")
    
    try:
        conn = await direct_db_service.get_connection()
        
        query = """
            SELECT 
                s.id_servicio,
                s.nombre,
                s.descripcion,
                s.precio,
                s.estado,
                c.nombre as categoria,
                pe.nombre_fantasia as empresa
            FROM servicio s
            LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
            LEFT JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            WHERE s.id_servicio = 26
        """
        
        result = await conn.fetchrow(query)
        
        if result:
            print("✅ Servicio ID 26 encontrado en la base de datos:")
            print(f"  ID: {result['id_servicio']}")
            print(f"  Nombre: '{result['nombre']}'")
            print(f"  Descripción: '{result['descripcion']}'")
            print(f"  Precio: {result['precio']}")
            print(f"  Estado: {result['estado']}")
            print(f"  Categoría: '{result['categoria']}'")
            print(f"  Empresa: '{result['empresa']}'")
            
            # Verificar si contiene "desarrollo"
            nombre = result['nombre'].lower() if result['nombre'] else ''
            descripcion = result['descripcion'].lower() if result['descripcion'] else ''
            
            print(f"\n🔍 Análisis de búsqueda:")
            print(f"  'desarrollo' en nombre: {'desarrollo' in nombre}")
            print(f"  'desarrollo' en descripción: {'desarrollo' in descripcion}")
            
            # Verificar si el estado es activo
            print(f"\n🔍 Estado del servicio:")
            print(f"  Estado: {result['estado']}")
            print(f"  ¿Está activo?: {result['estado'] == True}")
            
        else:
            print("❌ Servicio ID 26 NO encontrado en la base de datos")
        
        await direct_db_service.pool.release(conn)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_service_26())
