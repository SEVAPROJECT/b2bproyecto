#!/usr/bin/env python3
"""
Script para probar la integración completa de Weaviate
"""
import os
import asyncio
from app.services.weaviate_service import weaviate_service

async def test_weaviate_integration():
    """Probar la integración completa de Weaviate"""
    print("🚀 Probando integración completa de Weaviate...")
    print("=" * 60)
    
    # Configurar variables de entorno
    os.environ['WEAVIATE_URL'] = 'https://weaviate-production-0af4.up.railway.app'
    os.environ['WEAVIATE_API_KEY'] = ''
    
    try:
        # 1. Verificar conexión
        print("1️⃣ Verificando conexión...")
        stats = weaviate_service.get_stats()
        print(f"   📊 Estado: {stats}")
        
        if "error" in stats:
            print("   ❌ Error en la conexión")
            return False
        
        print("   ✅ Conexión exitosa")
        
        # 2. Indexar servicios
        print("\n2️⃣ Indexando servicios...")
        success = await weaviate_service.index_servicios(limit=3)
        
        if success:
            print("   ✅ Indexación exitosa")
        else:
            print("   ❌ Error en la indexación")
            return False
        
        # 3. Probar búsqueda
        print("\n3️⃣ Probando búsqueda...")
        resultados = weaviate_service.search_servicios("servicio", limit=3)
        print(f"   📊 Resultados encontrados: {len(resultados)}")
        
        for i, resultado in enumerate(resultados, 1):
            print(f"   {i}. {resultado.get('nombre', 'Sin nombre')} - {resultado.get('empresa', 'Sin empresa')}")
        
        # 4. Probar búsqueda semántica
        print("\n4️⃣ Probando búsqueda semántica...")
        resultados_semanticos = weaviate_service.search_servicios("tecnologia", limit=2)
        print(f"   📊 Resultados semánticos: {len(resultados_semanticos)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la integración: {str(e)}")
        return False

async def main():
    """Función principal"""
    print("🔧 Configurando entorno...")
    
    success = await test_weaviate_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡Integración de Weaviate completada exitosamente!")
        print("💡 El botón 'Buscar con IA' en el frontend debería funcionar ahora")
    else:
        print("❌ Error en la integración de Weaviate")
        print("💡 Revisa la configuración y conexión")

if __name__ == "__main__":
    asyncio.run(main())
