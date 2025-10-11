#!/usr/bin/env python3
"""
Script para probar búsqueda específica de 'desarrollo'
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.weaviate_service import weaviate_service

def main():
    print("🔍 Probando búsqueda específica de 'desarrollo'...")
    
    try:
        # Probar búsqueda específica
        results = weaviate_service.search_servicios('desarrollo', limit=10)
        print(f"📊 Resultados encontrados: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.get('nombre', 'Sin nombre')} - {result.get('empresa', 'Sin empresa')}")
            
        if not results:
            print("❌ No se encontraron resultados")
            print("💡 Posibles causas:")
            print("   - El filtro HTTP no está funcionando correctamente")
            print("   - Los datos no contienen la palabra 'desarrollo'")
            
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")

if __name__ == "__main__":
    main()
