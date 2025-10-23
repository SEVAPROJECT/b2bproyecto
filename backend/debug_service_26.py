#!/usr/bin/env python3
"""
Script para debuggear específicamente el servicio ID 26
"""
import requests
import json

def debug_service_26():
    """Debuggear el servicio ID 26 específicamente"""
    print("🔍 Debuggeando servicio ID 26...")
    
    weaviate_url = "https://weaviate-production-0af4.up.railway.app"
    
    try:
        # Obtener todos los servicios
        response = requests.get(f"{weaviate_url}/v1/objects", params={
            'class': 'Servicios',
            'limit': 100
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            objects = data.get('objects', [])
            
            print(f"📊 Total de servicios en Weaviate: {len(objects)}")
            
            # Buscar específicamente el servicio ID 26
            servicio_26 = None
            for obj in objects:
                properties = obj.get('properties', {})
                if properties.get('id_servicio') == 26:
                    servicio_26 = obj
                    break
            
            if servicio_26:
                print("\n✅ Servicio ID 26 encontrado:")
                properties = servicio_26.get('properties', {})
                
                print(f"  ID: {properties.get('id_servicio')}")
                print(f"  Nombre: '{properties.get('nombre')}'")
                print(f"  Descripción: '{properties.get('descripcion')}'")
                print(f"  Categoría: '{properties.get('categoria')}'")
                print(f"  Empresa: '{properties.get('empresa')}'")
                print(f"  Precio: {properties.get('precio')}")
                print(f"  Estado: {properties.get('estado')}")
                print(f"  Ubicación: '{properties.get('ubicacion')}'")
                
                # Verificar si contiene "desarrollo"
                nombre = properties.get('nombre', '').lower()
                descripcion = properties.get('descripcion', '').lower()
                
                print(f"\n🔍 Análisis de búsqueda:")
                print(f"  'desarrollo' en nombre: {'desarrollo' in nombre}")
                print(f"  'desarrollo' en descripción: {'desarrollo' in descripcion}")
                
                # Verificar caracteres especiales
                print(f"\n🔍 Análisis de caracteres:")
                print(f"  Nombre (bytes): {nombre.encode('utf-8')}")
                print(f"  Descripción (bytes): {descripcion.encode('utf-8')}")
                
                # Verificar si hay campos adicionales
                print(f"\n🔍 Todos los campos:")
                for key, value in properties.items():
                    print(f"  {key}: {repr(value)}")
                    
            else:
                print("❌ Servicio ID 26 NO encontrado en Weaviate")
                
                # Mostrar todos los IDs disponibles
                ids = [obj.get('properties', {}).get('id_servicio') for obj in objects]
                print(f"📋 IDs disponibles: {sorted(ids)}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_service_26()
