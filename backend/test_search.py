#!/usr/bin/env python3
"""
Script para probar la búsqueda en Weaviate
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.weaviate_service import weaviate_service

def main():
    print("🔍 Probando búsqueda en Weaviate...")
    
    try:
        # Probar búsqueda
        results = weaviate_service.search_servicios('marketing', limit=5)
        print(f"📊 Resultados encontrados: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. {result.get('nombre', 'Sin nombre')}")
            
        if not results:
            print("❌ No se encontraron resultados")
            print("💡 Posibles causas:")
            print("   - Los servicios no se vectorizaron correctamente")
            print("   - Ollama no está funcionando")
            print("   - Problema con la configuración de Weaviate")
            
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")

if __name__ == "__main__":
    main()
