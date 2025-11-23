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

# Constantes
WEAVIATE_URL = "https://weaviate-production-0af4.up.railway.app"
WEAVIATE_CLASS_SERVICIOS = "Servicios"
WEAVIATE_LIMIT_DEFAULT = 100
SERVICIO_VERIFICAR_ID = 26

# Funciones helper para reindex_services
def get_weaviate_objects(weaviate_url: str, class_name: str, limit: int = WEAVIATE_LIMIT_DEFAULT, where_clause: dict = None) -> dict:
    """Obtiene objetos de Weaviate"""
    params = {'class': class_name, 'limit': limit}
    if where_clause:
        params['where'] = json.dumps(where_clause)
    
    response = requests.get(f"{weaviate_url}/v1/objects", params=params)
    if response.status_code == 200:
        return response.json()
    return {}

def delete_weaviate_object(weaviate_url: str, obj_id: str) -> bool:
    """Elimina un objeto de Weaviate"""
    delete_response = requests.delete(f"{weaviate_url}/v1/objects/{obj_id}")
    return delete_response.status_code == 204

def clean_existing_services(weaviate_url: str) -> None:
    """Limpia servicios existentes en Weaviate"""
    print("🧹 Limpiando servicios existentes...")
    data = get_weaviate_objects(weaviate_url, WEAVIATE_CLASS_SERVICIOS)
    objects = data.get('objects', [])
    
    for obj in objects:
        obj_id = obj.get('id')
        if obj_id and delete_weaviate_object(weaviate_url, obj_id):
            nombre = obj.get('properties', {}).get('nombre', 'Sin nombre')
            print(f"✅ Eliminado: {nombre}")
    
    print("✅ Servicios existentes eliminados")

async def get_services_from_db(conn) -> list:
    """Obtiene servicios de la base de datos"""
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
    return await conn.fetch(query)

def build_service_data(service: dict) -> dict:
    """Construye los datos del servicio para Weaviate"""
    return {
        "class": WEAVIATE_CLASS_SERVICIOS,
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

def index_service_in_weaviate(weaviate_url: str, service_data: dict, service_name: str, service_id: int) -> bool:
    """Indexa un servicio en Weaviate"""
    response = requests.post(f"{weaviate_url}/v1/objects", json=service_data)
    
    if response.status_code == 201:
        print(f"✅ Indexado: {service_name} (ID: {service_id})")
        return True
    else:
        print(f"❌ Error indexando {service_name}: {response.status_code}")
        return False

def index_all_services(weaviate_url: str, services: list) -> int:
    """Indexa todos los servicios en Weaviate"""
    print("\n🤖 Indexando servicios en Weaviate...")
    indexed_count = 0
    
    for service in services:
        try:
            service_data = build_service_data(service)
            if index_service_in_weaviate(weaviate_url, service_data, service['nombre'], service['id_servicio']):
                indexed_count += 1
        except Exception as e:
            nombre = service.get('nombre', 'servicio')
            print(f"❌ Error indexando {nombre}: {e}")
    
    return indexed_count

def verify_service_by_id(weaviate_url: str, service_id: int) -> None:
    """Verifica si un servicio específico existe en Weaviate"""
    print(f"\n🔍 Verificando servicio ID {service_id}...")
    where_clause = {
        "path": ["id_servicio"],
        "operator": "Equal",
        "valueInt": service_id
    }
    
    data = get_weaviate_objects(weaviate_url, WEAVIATE_CLASS_SERVICIOS, where_clause=where_clause)
    objects = data.get('objects', [])
    
    if objects:
        print(f"✅ Servicio ID {service_id} encontrado en Weaviate")
        nombre = objects[0].get('properties', {}).get('nombre')
        print(f"  Nombre: {nombre}")
    else:
        print(f"❌ Servicio ID {service_id} NO encontrado en Weaviate")

async def reindex_services():
    """Re-indexar todos los servicios en Weaviate"""
    print("🔍 Re-indexando servicios en Weaviate...")
    
    try:
        # 1. Limpiar servicios existentes
        clean_existing_services(WEAVIATE_URL)
        
        # 2. Obtener servicios de la base de datos
        print("\n📊 Obteniendo servicios de la base de datos...")
        conn = await direct_db_service.get_connection()
        
        try:
            services = await get_services_from_db(conn)
            print(f"📊 Servicios encontrados: {len(services)}")
            
            # 3. Indexar todos los servicios
            indexed_count = index_all_services(WEAVIATE_URL, services)
            print(f"\n🎉 Re-indexación completada: {indexed_count} servicios indexados")
            
            # 4. Verificar el servicio específico
            verify_service_by_id(WEAVIATE_URL, SERVICIO_VERIFICAR_ID)
            
            return True
        finally:
            await direct_db_service.pool.release(conn)
        
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
