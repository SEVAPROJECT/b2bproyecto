#!/usr/bin/env python3
"""
Script para probar búsqueda en Weaviate
"""
import os
import asyncio
from app.services.weaviate_service import weaviate_service

async def test_weaviate_search():
    """Probar búsqueda en Weaviate"""
    print("🔍 Probando búsqueda en Weaviate...")
    
    try:
        # Probar búsqueda simple
        print("\n1. Búsqueda simple...")
        resultados = weaviate_service.search_servicios("servicio", limit=5)
        print(f"📊 Resultados: {len(resultados)}")
        
        for i, resultado in enumerate(resultados, 1):
            print(f"  {i}. {resultado.get('nombre', 'Sin nombre')} - {resultado.get('empresa', 'Sin empresa')}")
        
        # Probar búsqueda por categoría
        print("\n2. Búsqueda por categoría...")
        resultados_cat = weaviate_service.search_servicios("tecnologia", limit=3)
        print(f"📊 Resultados por categoría: {len(resultados_cat)}")
        
        # Probar búsqueda por empresa
        print("\n3. Búsqueda por empresa...")
        resultados_emp = weaviate_service.search_servicios("empresa", limit=3)
        print(f"📊 Resultados por empresa: {len(resultados_emp)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {str(e)}")
        return False

async def test_weaviate_data():
    """Probar acceso a datos indexados"""
    print("\n🔍 Probando acceso a datos...")
    
    try:
        # Obtener estadísticas
        stats = weaviate_service.get_stats()
        print(f"📊 Estadísticas: {stats}")
        
        # Probar obtener servicio por ID
        print("\n4. Buscar servicio por ID...")
        servicio = weaviate_service.get_servicio_by_id(1)
        if servicio:
            print(f"✅ Servicio encontrado: {servicio.get('nombre', 'Sin nombre')}")
        else:
            print("❌ Servicio no encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al acceder a datos: {str(e)}")
        return False

async def main():
    """Función principal"""
    print("🚀 Probando funcionalidades de Weaviate...")
    print("=" * 60)
    
    # Probar búsqueda
    search_ok = await test_weaviate_search()
    
    # Probar acceso a datos
    data_ok = await test_weaviate_data()
    
    print("\n" + "=" * 60)
    print("RESUMEN:")
    print(f"✅ Búsqueda: {'OK' if search_ok else 'ERROR'}")
    print(f"✅ Datos: {'OK' if data_ok else 'ERROR'}")
    
    if search_ok and data_ok:
        print("\n🎉 ¡Todas las funcionalidades están funcionando!")
    else:
        print("\n⚠️  Algunas funcionalidades tienen problemas")

if __name__ == "__main__":
    asyncio.run(main())
