#!/usr/bin/env python3
"""
Script simple para probar Weaviate sin dependencias externas
"""
import os
import sys
import asyncio
from app.services.weaviate_service import weaviate_service

async def test_weaviate_simple():
    """Probar Weaviate con el servicio integrado"""
    print("🔍 Probando conexión con Weaviate...")
    print("=" * 50)
    
    # Verificar variables de entorno
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_key = os.getenv("WEAVIATE_API_KEY")
    
    print(f"🌐 WEAVIATE_URL: {weaviate_url or 'No configurada'}")
    print(f"🔑 WEAVIATE_API_KEY: {'Configurada' if weaviate_key else 'No configurada (acceso anónimo)'}")
    
    if not weaviate_url:
        print("\n❌ Variable WEAVIATE_URL no configurada")
        print("💡 Configura la variable de entorno:")
        print("   export WEAVIATE_URL=https://tu-weaviate.railway.app")
        return False
    
    try:
        # Probar conexión
        print("\n🔗 Probando conexión...")
        stats = weaviate_service.get_stats()
        
        if "error" in stats:
            print(f"❌ Error en conexión: {stats['error']}")
            return False
        
        print("✅ Conexión exitosa!")
        print(f"📊 Estado: {stats}")
        
        # Probar indexación (solo 1 servicio para prueba)
        print("\n📦 Probando indexación...")
        success = await weaviate_service.index_servicios(limit=1)
        
        if success:
            print("✅ Indexación exitosa!")
            
            # Probar búsqueda
            print("\n🔍 Probando búsqueda...")
            resultados = weaviate_service.search_servicios("servicio", limit=1)
            
            if resultados:
                print(f"✅ Búsqueda exitosa! Encontrados: {len(resultados)}")
                for resultado in resultados:
                    print(f"  - {resultado.get('nombre', 'Sin nombre')}")
            else:
                print("⚠️  Búsqueda sin resultados")
            
            return True
        else:
            print("❌ Error en indexación")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def main():
    """Función principal"""
    print("🚀 Probando Weaviate con servicio integrado...")
    
    success = await test_weaviate_simple()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Weaviate está funcionando correctamente!")
        print("💡 Puedes proceder con la indexación completa")
    else:
        print("❌ Error en la configuración de Weaviate")
        print("💡 Revisa la URL y configuración")

if __name__ == "__main__":
    asyncio.run(main())
