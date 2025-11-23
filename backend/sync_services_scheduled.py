#!/usr/bin/env python3
"""
Script para sincronización programada de servicios con Weaviate
Se puede ejecutar con cron job o task scheduler
"""
import sys
import os
import asyncio
import requests
import json
from datetime import datetime
from typing import Tuple
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.direct_db_service import direct_db_service

# Constantes
WEAVIATE_URL = "https://weaviate-production-0af4.up.railway.app"
WEAVIATE_CLASS_SERVICIOS = "Servicios"
WEAVIATE_LIMIT_DEFAULT = 1000

# Funciones helper para sync_services_scheduled
async def get_services_from_db(conn) -> list:
    """Obtiene servicios de la base de datos"""
    query = """
        SELECT 
            s.id_servicio,
            s.nombre,
            s.descripcion,
            s.precio,
            s.estado,
            s.updated_at,
            c.nombre as categoria,
            pe.nombre_fantasia as empresa
        FROM servicio s
        LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
        LEFT JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
        WHERE s.estado = true
        ORDER BY s.updated_at DESC
    """
    return await conn.fetch(query)

def get_weaviate_services(weaviate_url: str) -> Tuple[bool, list]:
    """Obtiene servicios actuales en Weaviate"""
    response = requests.get(f"{weaviate_url}/v1/objects", params={
        'class': WEAVIATE_CLASS_SERVICIOS,
        'limit': WEAVIATE_LIMIT_DEFAULT
    })
    
    if response.status_code != 200:
        print(f"❌ Error obteniendo servicios de Weaviate: {response.status_code}")
        return False, []
    
    weaviate_data = response.json()
    weaviate_services = weaviate_data.get('objects', [])
    return True, weaviate_services

def identify_sync_needs(db_services: list, weaviate_services: list) -> Tuple[set, set]:
    """Identifica servicios que necesitan sincronización"""
    db_service_ids = {service['id_servicio'] for service in db_services}
    weaviate_service_ids = {obj.get('properties', {}).get('id_servicio') for obj in weaviate_services}
    
    # Servicios a agregar/actualizar
    to_sync = db_service_ids - weaviate_service_ids
    # Servicios a eliminar
    to_remove = weaviate_service_ids - db_service_ids
    
    return to_sync, to_remove

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

def sync_service_to_weaviate(weaviate_url: str, service_data: dict, service_name: str, service_id: int) -> bool:
    """Sincroniza un servicio en Weaviate"""
    response = requests.post(f"{weaviate_url}/v1/objects", json=service_data)
    
    if response.status_code == 201:
        print(f"✅ Sincronizado: {service_name} (ID: {service_id})")
        return True
    else:
        print(f"❌ Error sincronizando {service_name}: {response.status_code}")
        return False

def sync_all_services(weaviate_url: str, services: list, to_sync: set) -> int:
    """Sincroniza todos los servicios que necesitan actualización"""
    synced_count = 0
    
    for service in services:
        if service['id_servicio'] in to_sync:
            try:
                service_data = build_service_data(service)
                if sync_service_to_weaviate(weaviate_url, service_data, service['nombre'], service['id_servicio']):
                    synced_count += 1
            except Exception as e:
                print(f"❌ Error sincronizando {service['nombre']}: {str(e)}")
    
    return synced_count

def remove_obsolete_services(weaviate_url: str, weaviate_services: list, to_remove: set) -> int:
    """Elimina servicios obsoletos de Weaviate"""
    removed_count = 0
    
    for obj in weaviate_services:
        service_id = obj.get('properties', {}).get('id_servicio')
        if service_id in to_remove:
            try:
                obj_id = obj.get('id')
                if obj_id:
                    response = requests.delete(f"{weaviate_url}/v1/objects/{obj_id}")
                    if response.status_code == 204:
                        removed_count += 1
                        nombre = obj.get('properties', {}).get('nombre')
                        print(f"🗑️ Eliminado: {nombre} (ID: {service_id})")
            except Exception as e:
                print(f"❌ Error eliminando servicio {service_id}: {str(e)}")
    
    return removed_count

async def sync_services_scheduled():
    """Sincronización programada de servicios"""
    print(f"🔄 Iniciando sincronización programada - {datetime.now()}")
    
    try:
        # 1. Obtener servicios de la base de datos
        conn = await direct_db_service.get_connection()
        
        try:
            services = await get_services_from_db(conn)
            print(f"📊 Servicios encontrados en BD: {len(services)}")
        finally:
            await direct_db_service.pool.release(conn)
        
        # 2. Obtener servicios actuales en Weaviate
        success, weaviate_services = get_weaviate_services(WEAVIATE_URL)
        if not success:
            return False
        
        print(f"📊 Servicios en Weaviate: {len(weaviate_services)}")
        
        # 3. Identificar servicios que necesitan sincronización
        to_sync, to_remove = identify_sync_needs(services, weaviate_services)
        print(f"🔄 Servicios a sincronizar: {len(to_sync)}")
        print(f"🗑️ Servicios a eliminar: {len(to_remove)}")
        
        # 4. Sincronizar servicios
        synced_count = sync_all_services(WEAVIATE_URL, services, to_sync)
        
        # 5. Eliminar servicios obsoletos
        removed_count = remove_obsolete_services(WEAVIATE_URL, weaviate_services, to_remove)
        
        print("\n🎉 Sincronización completada:")
        print(f"  ✅ Servicios sincronizados: {synced_count}")
        print(f"  🗑️ Servicios eliminados: {removed_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en sincronización: {str(e)}")
        return False

async def main():
    """Función principal"""
    print("🚀 Sincronización programada de servicios con Weaviate")
    print("=" * 60)
    
    success = await sync_services_scheduled()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡Sincronización completada exitosamente!")
    else:
        print("❌ Error en la sincronización")

if __name__ == "__main__":
    asyncio.run(main())
