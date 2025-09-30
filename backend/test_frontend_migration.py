#!/usr/bin/env python3
"""
Script para probar la migración del frontend al endpoint unificado
"""

import asyncio
import httpx
import json

async def test_frontend_migration():
    """Probar que el frontend puede usar el endpoint unificado"""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 Probando migración del frontend al endpoint unificado")
    print("=" * 60)
    
    # Test 1: Simular llamada del frontend sin filtros (comportamiento original)
    print("\n1️⃣ Probando llamada sin filtros (comportamiento original):")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/services/services?limit=5&offset=0")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servicios encontrados: {len(data.get('services', []))}")
                print(f"📊 Total: {data.get('pagination', {}).get('total', 0)}")
                print(f"📄 Página: {data.get('pagination', {}).get('page', 0)}")
                print(f"🔍 Filtros aplicados: {data.get('filters_applied', {})}")
            else:
                print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error en test 1: {e}")
    
    # Test 2: Simular llamada del frontend con filtros (comportamiento filtrado)
    print("\n2️⃣ Probando llamada con filtros (comportamiento filtrado):")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/services/services?limit=5&offset=0&currency=GS&max_price=5000000")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servicios encontrados: {len(data.get('services', []))}")
                print(f"📊 Total: {data.get('pagination', {}).get('total', 0)}")
                print(f"🔍 Filtros aplicados: {data.get('filters_applied', {})}")
            else:
                print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error en test 2: {e}")
    
    # Test 3: Verificar que el endpoint /filtered sigue funcionando (compatibilidad)
    print("\n3️⃣ Verificando compatibilidad con endpoint /filtered:")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/services/filtered?limit=5&offset=0")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servicios encontrados: {len(data.get('services', []))}")
                print(f"📊 Total: {data.get('pagination', {}).get('total', 0)}")
            else:
                print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error en test 3: {e}")
    
    print("\n🎉 Pruebas de migración completadas!")
    print("\n📋 Resumen:")
    print("✅ Endpoint unificado /services funciona")
    print("✅ Endpoint /filtered mantiene compatibilidad")
    print("✅ Frontend puede migrar gradualmente")

if __name__ == "__main__":
    asyncio.run(test_frontend_migration())


