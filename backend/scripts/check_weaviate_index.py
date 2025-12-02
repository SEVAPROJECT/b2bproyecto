#!/usr/bin/env python3
"""
Script para verificar cuántos servicios están indexados en Weaviate
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.weaviate_service import weaviate_service

def check_index():
    """Verificar el índice de Weaviate"""
    print("🔍 Verificando índice de Weaviate...\n")
    
    if not weaviate_service.connected:
        print("❌ Weaviate no está conectado")
        return
    
    # Probar búsqueda vacía para obtener todos los objetos
    print("📊 Buscando todos los servicios indexados...")
    all_results = weaviate_service.search_servicios("", limit=1000)
    print(f"✅ Servicios encontrados en Weaviate: {len(all_results)}")
    
    # Probar búsqueda específica
    print("\n🔍 Probando búsqueda 'desarrollo'...")
    desarrollo_results = weaviate_service.search_servicios("desarrollo", limit=100)
    print(f"✅ Resultados para 'desarrollo': {len(desarrollo_results)}")
    
    if desarrollo_results:
        print("\n📋 Primeros 5 resultados:")
        for i, result in enumerate(desarrollo_results[:5], 1):
            print(f"  {i}. {result.get('nombre', 'Sin nombre')} - {result.get('empresa', 'Sin empresa')}")
    
    # Probar búsqueda 'catering'
    print("\n🔍 Probando búsqueda 'catering'...")
    catering_results = weaviate_service.search_servicios("catering", limit=100)
    print(f"✅ Resultados para 'catering': {len(catering_results)}")

if __name__ == "__main__":
    check_index()



