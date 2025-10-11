#!/usr/bin/env python3
"""
Script para debuggear todos los servicios en Weaviate
"""
import requests
import json

def debug_weaviate_services():
    """Obtener todos los servicios de Weaviate para debug"""
    print("🔍 Obteniendo todos los servicios de Weaviate...")
    
    weaviate_url = "https://weaviate-production-0af4.up.railway.app"
    
    try:
        # Obtener todos los objetos
        response = requests.get(f"{weaviate_url}/v1/objects", params={
            'class': 'Servicios',
            'limit': 50
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            objects = data.get('objects', [])
            
            print(f"📊 Total de objetos en Weaviate: {len(objects)}")
            print("\n📋 Lista de servicios:")
            
            for i, obj in enumerate(objects, 1):
                properties = obj.get('properties', {})
                nombre = properties.get('nombre', 'Sin nombre')
                descripcion = properties.get('descripcion', 'Sin descripción')
                empresa = properties.get('empresa', 'Sin empresa')
                
                print(f"\n{i}. {nombre}")
                print(f"   Empresa: {empresa}")
                print(f"   Descripción: {descripcion[:100]}...")
                
                # Buscar "desarrollo" en el nombre
                if 'desarrollo' in nombre.lower():
                    print("   ✅ CONTIENE 'desarrollo' en el nombre")
                else:
                    print("   ❌ NO contiene 'desarrollo' en el nombre")
            
            return objects
        else:
            print(f"❌ Error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    debug_weaviate_services()
