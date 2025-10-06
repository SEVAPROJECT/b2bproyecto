#!/usr/bin/env python3
"""
Script para probar la integración del frontend con el endpoint de reservas-proveedor
"""
import asyncio
import aiohttp
import json
import os

async def test_frontend_integration():
    """Probar la integración del frontend con el endpoint correcto"""
    print("=== PRUEBA DE INTEGRACION FRONTEND ===")
    print()
    
    # Configuración
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Endpoints a probar
    endpoints = {
        "endpoint_correcto": f"{base_url}/api/v1/reservas/reservas-proveedor",
        "endpoint_incorrecto": f"{base_url}/api/v1/reservas/proveedor",
        "endpoint_diagnostico": f"{base_url}/api/v1/reservas/diagnostico-usuario"
    }
    
    print("ENDPOINTS A PROBAR:")
    print("=" * 50)
    for nombre, url in endpoints.items():
        print(f"{nombre}: {url}")
    print()
    
    # Token de autenticación
    auth_token = os.getenv("AUTH_TOKEN", "your-auth-token-here")
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"Token configurado: {'Si' if auth_token != 'your-auth-token-here' else 'No (usar AUTH_TOKEN)'}")
    print()
    
    async with aiohttp.ClientSession() as session:
        for nombre, url in endpoints.items():
            print(f"Probando {nombre}...")
            print("-" * 30)
            
            try:
                async with session.get(url, headers=headers) as response:
                    print(f"Status Code: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Exitoso - Datos recibidos")
                        
                        if nombre == "endpoint_diagnostico":
                            print(f"   Usuario: {data.get('usuario', {}).get('email', 'N/A')}")
                            print(f"   Es Proveedor: {data.get('es_proveedor', False)}")
                            print(f"   Es Cliente: {data.get('es_cliente', False)}")
                            print(f"   Endpoints recomendados: {data.get('endpoints_recomendados', [])}")
                        else:
                            reservas = data.get('reservas', [])
                            pagination = data.get('pagination', {})
                            print(f"   Reservas encontradas: {len(reservas)}")
                            print(f"   Total: {pagination.get('total', 0)}")
                            
                    elif response.status == 404:
                        print(f"❌ No encontrado - Endpoint no existe")
                        
                    elif response.status == 401:
                        print(f"❌ No autenticado - Token invalido")
                        
                    elif response.status == 403:
                        error_data = await response.json()
                        print(f"❌ Acceso denegado - {error_data.get('detail', 'Sin permisos')}")
                        
                    else:
                        error_data = await response.json()
                        print(f"❌ Error {response.status} - {error_data.get('detail', 'Error desconocido')}")
                        
            except Exception as e:
                print(f"❌ Error en la peticion: {str(e)}")
            
            print()
    
    print("RESUMEN DE LA CORRECCION:")
    print("=" * 50)
    print("✅ Frontend corregido: /api/v1/reservas/reservas-proveedor")
    print("❌ Frontend anterior: /api/v1/reservas/proveedor (no existe)")
    print()
    print("PROXIMOS PASOS:")
    print("1. Reinicia el frontend para aplicar los cambios")
    print("2. Prueba la funcionalidad de reservas para proveedores")
    print("3. Verifica que aparezcan las reservas correctamente")

if __name__ == "__main__":
    asyncio.run(test_frontend_integration())
