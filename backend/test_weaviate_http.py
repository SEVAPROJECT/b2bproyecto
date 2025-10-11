#!/usr/bin/env python3
"""
Script para probar Weaviate usando HTTP directo
"""
import requests
import json

def test_weaviate_http():
    """Probar Weaviate usando HTTP directo"""
    print("🔍 Probando Weaviate con HTTP directo...")
    
    weaviate_url = "https://weaviate-production-0af4.up.railway.app"
    
    try:
        # 1. Probar endpoint de meta
        print("1️⃣ Probando endpoint /v1/meta...")
        response = requests.get(f"{weaviate_url}/v1/meta", timeout=10)
        
        if response.status_code == 200:
            print("✅ Meta endpoint funcionando")
            meta = response.json()
            print(f"📊 Módulos disponibles: {list(meta.get('modules', {}).keys())}")
        else:
            print(f"❌ Error en meta: {response.status_code}")
            return False
        
        # 2. Probar endpoint de schema
        print("\n2️⃣ Probando endpoint /v1/schema...")
        response = requests.get(f"{weaviate_url}/v1/schema", timeout=10)
        
        if response.status_code == 200:
            print("✅ Schema endpoint funcionando")
            schema = response.json()
            classes = list(schema.get('classes', []))
            print(f"📋 Clases disponibles: {[cls.get('class') for cls in classes]}")
        else:
            print(f"❌ Error en schema: {response.status_code}")
        
        # 3. Probar búsqueda si hay clases
        if classes:
            class_name = classes[0]['class']
            print(f"\n3️⃣ Probando búsqueda en clase '{class_name}'...")
            
            search_url = f"{weaviate_url}/v1/objects"
            params = {
                'class': class_name,
                'limit': 5
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                print("✅ Búsqueda funcionando")
                results = response.json()
                objects = results.get('objects', [])
                print(f"📊 Objetos encontrados: {len(objects)}")
                
                for i, obj in enumerate(objects[:3], 1):
                    properties = obj.get('properties', {})
                    print(f"  {i}. {properties.get('nombre', 'Sin nombre')} - {properties.get('empresa', 'Sin empresa')}")
            else:
                print(f"❌ Error en búsqueda: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_weaviate_http()