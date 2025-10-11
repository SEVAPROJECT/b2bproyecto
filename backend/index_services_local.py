#!/usr/bin/env python3
"""
Script para indexar servicios en Weaviate local
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.weaviate_service import weaviate_service
import asyncio

async def index_services():
    """Indexar servicios en Weaviate local"""
    print("🔍 Indexando servicios en Weaviate local...")
    
    try:
        # Indexar servicios
        success = await weaviate_service.index_servicios(limit=20)
        
        if success:
            print("✅ Indexación exitosa")
            
            # Probar búsqueda
            print("\n🔍 Probando búsqueda...")
            results = weaviate_service.search_servicios('desarrollo', limit=5)
            print(f"📊 Resultados: {len(results)}")
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.get('nombre', 'Sin nombre')}")
        else:
            print("❌ Error en la indexación")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(index_services())
