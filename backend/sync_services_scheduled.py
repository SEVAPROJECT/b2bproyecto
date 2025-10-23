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
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.direct_db_service import direct_db_service

async def sync_services_scheduled():
    """Sincronización programada de servicios"""
    print(f"🔄 Iniciando sincronización programada - {datetime.now()}")
    
    weaviate_url = "https://weaviate-production-0af4.up.railway.app"
    
    try:
        # 1. Obtener servicios de la base de datos
        conn = await direct_db_service.get_connection()
        
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
        
        services = await conn.fetch(query)
        await direct_db_service.pool.release(conn)
        
        print(f"📊 Servicios encontrados en BD: {len(services)}")
        
        # 2. Obtener servicios actuales en Weaviate
        response = requests.get(f"{weaviate_url}/v1/objects", params={
            'class': 'Servicios',
            'limit': 1000
        })
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo servicios de Weaviate: {response.status_code}")
            return False
        
        weaviate_data = response.json()
        weaviate_services = weaviate_data.get('objects', [])
        
        print(f"📊 Servicios en Weaviate: {len(weaviate_services)}")
        
        # 3. Identificar servicios que necesitan sincronización
        db_service_ids = {service['id_servicio'] for service in services}
        weaviate_service_ids = {obj.get('properties', {}).get('id_servicio') for obj in weaviate_services}
        
        # Servicios a agregar/actualizar
        to_sync = db_service_ids - weaviate_service_ids
        # Servicios a eliminar
        to_remove = weaviate_service_ids - db_service_ids
        
        print(f"🔄 Servicios a sincronizar: {len(to_sync)}")
        print(f"🗑️ Servicios a eliminar: {len(to_remove)}")
        
        # 4. Sincronizar servicios
        synced_count = 0
        for service in services:
            if service['id_servicio'] in to_sync:
                try:
                    # Crear/actualizar en Weaviate
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
                    
                    response = requests.post(f"{weaviate_url}/v1/objects", json=service_data)
                    
                    if response.status_code == 201:
                        synced_count += 1
                        print(f"✅ Sincronizado: {service['nombre']} (ID: {service['id_servicio']})")
                    else:
                        print(f"❌ Error sincronizando {service['nombre']}: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error sincronizando {service['nombre']}: {str(e)}")
        
        # 5. Eliminar servicios obsoletos
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
                            print(f"🗑️ Eliminado: {obj.get('properties', {}).get('nombre')} (ID: {service_id})")
                except Exception as e:
                    print(f"❌ Error eliminando servicio {service_id}: {str(e)}")
        
        print(f"\n🎉 Sincronización completada:")
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
