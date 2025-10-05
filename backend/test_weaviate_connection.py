#!/usr/bin/env python3
"""
Script para probar la conexión con Weaviate
"""
import asyncio
import os
import sys
from app.services.weaviate_service import weaviate_service

async def test_weaviate_connection():
    """Probar la conexión con Weaviate"""
    print("🔍 Probando conexión con Weaviate...")
    
    try:
        # Verificar variables de entorno
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        print(f"🌐 URL de Weaviate: {weaviate_url}")
        
        # Verificar estado
        stats = weaviate_service.get_stats()
        print(f"📊 Estado: {stats}")
        
        if "error" in stats:
            print("❌ Error en la conexión con Weaviate")
            return False
        
        print("✅ Conexión con Weaviate establecida")
        return True
        
    except Exception as e:
        print(f"❌ Error al probar conexión: {str(e)}")
        return False

async def test_index_servicios():
    """Probar la indexación de servicios"""
    print("\n🔍 Probando indexación de servicios...")
    
    try:
        # Indexar algunos servicios de prueba
        success = await weaviate_service.index_servicios(limit=5)
        
        if success:
            print("✅ Indexación de servicios exitosa")
            return True
        else:
            print("❌ Error en la indexación")
            return False
            
    except Exception as e:
        print(f"❌ Error al indexar servicios: {str(e)}")
        return False

async def test_search():
    """Probar búsqueda semántica"""
    print("\n🔍 Probando búsqueda semántica...")
    
    try:
        # Buscar servicios
        resultados = weaviate_service.search_servicios("servicio", limit=3)
        
        print(f"📊 Resultados encontrados: {len(resultados)}")
        for i, resultado in enumerate(resultados, 1):
            print(f"  {i}. {resultado.get('nombre', 'Sin nombre')} - {resultado.get('empresa', 'Sin empresa')}")
        
        return len(resultados) > 0
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {str(e)}")
        return False

async def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas de Weaviate...")
    print("=" * 50)
    
    # Prueba 1: Conexión
    connection_ok = await test_weaviate_connection()
    
    if not connection_ok:
        print("\n❌ No se puede continuar sin conexión a Weaviate")
        print("💡 Asegúrate de que Weaviate esté ejecutándose y configurado correctamente")
        return
    
    # Prueba 2: Indexación
    index_ok = await test_index_servicios()
    
    # Prueba 3: Búsqueda (solo si la indexación fue exitosa)
    search_ok = False
    if index_ok:
        search_ok = await test_search()
    
    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN DE PRUEBAS:")
    print(f"✅ Conexión: {'OK' if connection_ok else 'ERROR'}")
    print(f"✅ Indexación: {'OK' if index_ok else 'ERROR'}")
    print(f"✅ Búsqueda: {'OK' if search_ok else 'ERROR'}")
    
    if connection_ok and index_ok and search_ok:
        print("\n🎉 ¡Todas las pruebas pasaron! Weaviate está funcionando correctamente.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa la configuración de Weaviate.")

if __name__ == "__main__":
    asyncio.run(main())
