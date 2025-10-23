#!/usr/bin/env python3
"""
Script para re-indexar servicios en Weaviate desde Railway
"""
import sys
import os
import asyncio
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.direct_db_service import direct_db_service

async def reindex_services():
    """Re-indexar todos los servicios en Weaviate"""
    print("🔍 Re-indexando servicios en Weaviate...")
    
    weaviate_url = "https://weaviate-production-0af4.up.railway.app"
    
    try:
        # 1. Limpiar servicios existentes
        print("🧹 Limpiando servicios existentes...")
        response = requests.get(f"{weaviate_url}/v1/objects", params={
            'class': 'Servicios',
            'limit': 100
        })
        
        if response.status_code == 200:
            data = response.json()
            objects = data.get('objects', [])
            
            for obj in objects:
                obj_id = obj.get('id')
                if obj_id:
                    delete_response = requests.delete(f"{weaviate_url}/v1/objects/{obj_id}")
                    if delete_response.status_code == 204:
                        print(f"✅ Eliminado: {obj.get('properties', {}).get('nombre', 'Sin nombre')}")
        
        print("✅ Servicios existentes eliminados")
        
        # 2. Obtener servicios de la base de datos
        print("\n📊 Obteniendo servicios de la base de datos...")
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
            WHERE s.estado = true
            ORDER BY s.id_servicio
        """
        
        services = await conn.fetch(query)
        print(f"📊 Servicios encontrados: {len(services)}")
        
        # 3. Indexar cada servicio
        print("\n🤖 Indexando servicios en Weaviate...")
        indexed_count = 0
        
        for service in services:
            try:
                # Preparar datos para Weaviate
                service_data = {
                    "class": "Servicios",
                    "properties": {
                        "id_servicio": service['id_servicio'],
                        "nombre": service['nombre'] or "",
                        "descripcion": service['descripcion'] or "",
                        "precio": float(service['precio']) if service['precio'] else 0.0,
                        "categoria": service['categoria'] or "",
                        "empresa": service['empresa'] or "",
                        "ubicacion": "",
                        "estado": "activo" if service['estado'] else "inactivo"
                    }
                }
                
                # Crear objeto en Weaviate
                response = requests.post(f"{weaviate_url}/v1/objects", json=service_data)
                
                if response.status_code == 201:
                    indexed_count += 1
                    print(f"✅ Indexado: {service['nombre']} (ID: {service['id_servicio']})")
                else:
                    print(f"❌ Error indexando {service['nombre']}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error indexando {service.get('nombre', 'servicio')}: {e}")
        
        await direct_db_service.pool.release(conn)
        
        print(f"\n🎉 Re-indexación completada: {indexed_count} servicios indexados")
        
        # 4. Verificar el servicio ID 26 específicamente
        print("\n🔍 Verificando servicio ID 26...")
        response = requests.get(f"{weaviate_url}/v1/objects", params={
            'class': 'Servicios',
            'where': json.dumps({
                "path": ["id_servicio"],
                "operator": "Equal",
                "valueInt": 26
            })
        })
        
        if response.status_code == 200:
            data = response.json()
            objects = data.get('objects', [])
            if objects:
                print("✅ Servicio ID 26 encontrado en Weaviate")
                print(f"  Nombre: {objects[0].get('properties', {}).get('nombre')}")
            else:
                print("❌ Servicio ID 26 NO encontrado en Weaviate")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en re-indexación: {e}")
        return False

async def main():
    """Función principal"""
    print("🚀 Re-indexando servicios en Weaviate...")
    print("=" * 60)
    
    success = await reindex_services()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡Re-indexación completada exitosamente!")
        print("💡 Ahora el servicio ID 26 debería aparecer en la búsqueda de IA")
    else:
        print("❌ Error en la re-indexación")
        print("💡 Revisa la configuración de Weaviate")

if __name__ == "__main__":
    asyncio.run(main())
