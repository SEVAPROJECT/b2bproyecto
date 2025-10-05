#!/usr/bin/env python3
"""
Script para verificar si los servicios tienen vectores en Weaviate
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.weaviate_service import weaviate_service

def main():
    print("🔍 Verificando vectores en Weaviate...")
    
    try:
        if not weaviate_service.client:
            print("❌ No hay conexión a Weaviate")
            return
            
        # Obtener la colección
        collection = weaviate_service.client.collections.get("Servicios")
        
        # Obtener algunos objetos
        objects = collection.query.fetch_objects(limit=3)
        
        print(f"📊 Objetos en la colección: {len(objects.objects)}")
        
        for i, obj in enumerate(objects.objects):
            print(f"\n🔍 Objeto {i+1}:")
            print(f"  - ID: {obj.uuid}")
            print(f"  - Nombre: {obj.properties.get('nombre', 'Sin nombre')}")
            print(f"  - Tiene vector: {obj.vector is not None}")
            if obj.vector:
                print(f"  - Dimensión del vector: {len(obj.vector)}")
            else:
                print("  - ❌ NO TIENE VECTOR")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
