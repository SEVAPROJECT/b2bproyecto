#!/usr/bin/env python3
"""
Script para indexar servicios en Weaviate
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.direct_db_service import direct_db_service
from app.services.weaviate_service import weaviate_service

async def main():
    print("🔍 Verificando servicios en la base de datos...")
    
    try:
        # Obtener conexión a la base de datos
        conn = await direct_db_service.get_connection()
        
        # Consulta SQL para obtener servicios
        query = """
            SELECT 
                s.id_servicio, s.nombre, s.descripcion, s.precio,
                pe.razon_social as empresa,
                d.nombre as departamento, c.nombre as ciudad
            FROM servicio s
            JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            LEFT JOIN direccion dir ON pe.id_direccion = dir.id_direccion
            LEFT JOIN departamento d ON dir.id_departamento = d.id_departamento
            LEFT JOIN ciudad c ON dir.id_ciudad = c.id_ciudad
            WHERE s.estado = true AND pe.verificado = true
            LIMIT 10
        """
        
        services = await conn.fetch(query)
        print(f"📊 Servicios encontrados en BD: {len(services)}")
        
        if not services:
            print("❌ No hay servicios en la base de datos")
            return
            
        # Mostrar algunos servicios
        for i, service in enumerate(services[:3]):
            print(f"  - {service.get('nombre', 'Sin nombre')}")
            
        print("\n🤖 Indexando servicios en Weaviate...")
        
        # Indexar servicios en Weaviate
        indexed_count = 0
        for service in services:
            try:
                # Preparar datos para Weaviate
                service_data = {
                    'id_servicio': service.get('id_servicio'),
                    'nombre': service.get('nombre', ''),
                    'descripcion': service.get('descripcion', ''),
                    'categoria': 'General',  # Valor por defecto
                    'empresa': service.get('empresa', ''),
                    'precio': service.get('precio', 0),
                    'estado': True  # Agregar campo estado requerido
                }
                
                # Indexar en Weaviate
                weaviate_service._index_servicio(service_data)
                indexed_count += 1
                print(f"✅ Indexado: {service_data['nombre']}")
                
            except Exception as e:
                print(f"❌ Error indexando {service.get('nombre', 'servicio')}: {e}")
                
        print(f"\n🎉 Indexación completada: {indexed_count} servicios indexados")
        
        # Probar búsqueda
        print("\n🔍 Probando búsqueda...")
        results = weaviate_service.search_servicios('marketing', limit=5)
        print(f"📊 Resultados de búsqueda: {len(results)} servicios encontrados")
        
        for result in results:
            print(f"  - {result.get('nombre', 'Sin nombre')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cerrar conexión
        if 'conn' in locals():
            await direct_db_service.pool.release(conn)

if __name__ == "__main__":
    asyncio.run(main())
