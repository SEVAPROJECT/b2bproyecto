#!/usr/bin/env python3
"""
Script para probar el endpoint unificado /services
"""

import asyncio
import httpx
import json

async def test_unified_endpoint():
    """Probar el endpoint unificado /services"""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 Probando endpoint unificado /services")
    print("=" * 50)
    
    # Test 1: Sin filtros (comportamiento original de /with-providers)
    print("\n1️⃣ Probando sin filtros (comportamiento /with-providers):")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/services?limit=5&offset=0")
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
    
    # Test 2: Con filtro de moneda
    print("\n2️⃣ Probando con filtro de moneda (GS):")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/services?limit=5&offset=0&currency=GS")
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
    
    # Test 3: Con filtro de precio
    print("\n3️⃣ Probando con filtro de precio (hasta 5,000,000):")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/services?limit=5&offset=0&currency=GS&max_price=5000000")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servicios encontrados: {len(data.get('services', []))}")
                print(f"📊 Total: {data.get('pagination', {}).get('total', 0)}")
                print(f"🔍 Filtros aplicados: {data.get('filters_applied', {})}")
            else:
                print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error en test 3: {e}")
    
    # Test 4: Con múltiples filtros
    print("\n4️⃣ Probando con múltiples filtros:")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/services?limit=3&offset=0&currency=GS&min_price=100000&max_price=3000000&search=servicio")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servicios encontrados: {len(data.get('services', []))}")
                print(f"📊 Total: {data.get('pagination', {}).get('total', 0)}")
                print(f"🔍 Filtros aplicados: {data.get('filters_applied', {})}")
            else:
                print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error en test 4: {e}")
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    asyncio.run(test_unified_endpoint())
