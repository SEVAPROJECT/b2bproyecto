#!/usr/bin/env python3
"""
Script para probar múltiples queries de búsqueda
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.weaviate_service import weaviate_service

def test_query(query):
    print(f"\n🔍 Probando búsqueda: '{query}'")
    try:
        results = weaviate_service.search_servicios(query, limit=10)
        print(f"📊 Resultados: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.get('nombre', 'Sin nombre')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🧪 Probando múltiples queries de búsqueda...")
    
    # Probar diferentes queries
    queries = [
        "desarrollo",
        "marketing", 
        "seo",
        "email",
        "tecnologia",
        "",  # Sin query
        "xyz"  # Query que no existe
    ]
    
    for query in queries:
        test_query(query)

if __name__ == "__main__":
    main()
