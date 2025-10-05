#!/usr/bin/env python3
"""
Script para indexar servicios en Weaviate
"""
import os
import asyncio
from app.services.weaviate_service import weaviate_service

async def index_services_in_weaviate():
    """Indexar servicios en Weaviate"""
    print("🔍 Indexando servicios en Weaviate...")
    
    # Configurar variables de entorno
    os.environ['WEAVIATE_URL'] = 'https://weaviate-production-0af4.up.railway.app'
    os.environ['WEAVIATE_API_KEY'] = ''
    
    try:
        # Indexar servicios
        success = await weaviate_service.index_servicios(limit=10)
        
        if success:
            print("✅ Servicios indexados exitosamente")
            
            # Probar búsqueda
            print("\n🔍 Probando búsqueda...")
            resultados = weaviate_service.search_servicios("", limit=5)
            print(f"📊 Servicios en Weaviate: {len(resultados)}")
            
            for i, resultado in enumerate(resultados, 1):
                print(f"  {i}. {resultado.get('nombre', 'Sin nombre')} - {resultado.get('empresa', 'Sin empresa')}")
            
            return True
        else:
            print("❌ Error al indexar servicios")
            return False
            
    except Exception as e:
        print(f"❌ Error en indexación: {str(e)}")
        return False

async def main():
    """Función principal"""
    print("🚀 Indexando servicios en Weaviate...")
    print("=" * 50)
    
    success = await index_services_in_weaviate()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Servicios indexados exitosamente!")
        print("💡 Ahora puedes probar la búsqueda con IA en el frontend")
    else:
        print("❌ Error en la indexación")
        print("💡 Revisa la configuración de Weaviate")

if __name__ == "__main__":
    asyncio.run(main())
