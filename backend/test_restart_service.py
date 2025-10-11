#!/usr/bin/env python3
"""
Script para reiniciar el servicio de Weaviate
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Forzar recarga del módulo
if 'app.services.weaviate_service' in sys.modules:
    del sys.modules['app.services.weaviate_service']

# Importar de nuevo
from app.services.weaviate_service import weaviate_service

def main():
    print("🔄 Reiniciando servicio de Weaviate...")
    
    # Verificar URL actual
    print(f"🔗 URL actual: {weaviate_service.base_url}")
    print(f"🔗 Conectado: {weaviate_service.connected}")
    
    # Probar búsqueda
    print("\n🔍 Probando búsqueda...")
    results = weaviate_service.search_servicios('desarrollo', limit=5)
    print(f"📊 Resultados: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('nombre', 'Sin nombre')}")

if __name__ == "__main__":
    main()
