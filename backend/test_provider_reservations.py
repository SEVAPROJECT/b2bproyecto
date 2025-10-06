#!/usr/bin/env python3
"""
Script para probar el nuevo endpoint de reservas para proveedores
"""
import asyncio
import aiohttp
import json
import os
from typing import Dict, Any

async def test_provider_reservations():
    """Probar el endpoint de reservas para proveedores"""
    print("🧪 Probando endpoint de reservas para proveedores...")
    print("=" * 60)
    
    # Configuración
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    endpoint = f"{base_url}/api/v1/reservas/reservas-proveedor"
    
    # Token de autenticación (necesitarás reemplazar con un token válido)
    auth_token = os.getenv("PROVIDER_AUTH_TOKEN", "your-auth-token-here")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"🔗 URL del endpoint: {endpoint}")
    print(f"🔑 Token configurado: {'Sí' if auth_token != 'your-auth-token-here' else 'No (usar PROVIDER_AUTH_TOKEN)'}")
    
    # Parámetros de prueba
    test_params = [
        {},  # Sin filtros
        {"limit": 5, "offset": 0},  # Paginación básica
        {"estado": "pendiente"},  # Filtro por estado
        {"search": "servicio"},  # Búsqueda general
        {"nombre_servicio": "consultoría"},  # Filtro por nombre de servicio
        {"nombre_cliente": "Juan"},  # Filtro por nombre de cliente
        {"fecha_desde": "2024-01-01", "fecha_hasta": "2024-12-31"},  # Filtro por fechas
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, params in enumerate(test_params, 1):
            print(f"\n📋 Prueba {i}: {params}")
            print("-" * 40)
            
            try:
                async with session.get(endpoint, headers=headers, params=params) as response:
                    print(f"📊 Status Code: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Respuesta exitosa:")
                        print(f"   📊 Total de reservas: {data.get('pagination', {}).get('total', 0)}")
                        print(f"   📄 Página actual: {data.get('pagination', {}).get('page', 1)}")
                        print(f"   🏢 Proveedor: {data.get('proveedor', {}).get('nombre_empresa', 'N/A')}")
                        print(f"   📋 Reservas encontradas: {len(data.get('reservas', []))}")
                        
                        # Mostrar detalles de las primeras 2 reservas
                        reservas = data.get('reservas', [])
                        for j, reserva in enumerate(reservas[:2]):
                            print(f"   📝 Reserva {j+1}:")
                            print(f"      🆔 ID: {reserva.get('id_reserva')}")
                            print(f"      🛍️ Servicio: {reserva.get('nombre_servicio')}")
                            print(f"      👤 Cliente: {reserva.get('nombre_cliente')}")
                            print(f"      📅 Fecha: {reserva.get('fecha')}")
                            print(f"      ⏰ Hora: {reserva.get('hora_inicio')} - {reserva.get('hora_fin')}")
                            print(f"      📊 Estado: {reserva.get('estado')}")
                        
                    elif response.status == 403:
                        error_data = await response.json()
                        print(f"❌ Acceso denegado: {error_data.get('detail', 'No tienes permisos de proveedor')}")
                        
                    elif response.status == 401:
                        print(f"❌ No autenticado: Token inválido o expirado")
                        
                    else:
                        error_data = await response.json()
                        print(f"❌ Error {response.status}: {error_data.get('detail', 'Error desconocido')}")
                        
            except Exception as e:
                print(f"❌ Error en la petición: {str(e)}")
    
    print(f"\n🎉 Pruebas completadas")
    print("=" * 60)

async def test_endpoint_availability():
    """Probar si el endpoint está disponible"""
    print("🔍 Verificando disponibilidad del endpoint...")
    
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    health_endpoint = f"{base_url}/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_endpoint) as response:
                if response.status == 200:
                    print("✅ Servidor está funcionando")
                    return True
                else:
                    print(f"❌ Servidor no responde correctamente: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {str(e)}")
        return False

def print_usage_instructions():
    """Mostrar instrucciones de uso"""
    print("\n📖 INSTRUCCIONES DE USO:")
    print("=" * 40)
    print("1. Configura las variables de entorno:")
    print("   export API_BASE_URL='https://tu-backend.railway.app'")
    print("   export PROVIDER_AUTH_TOKEN='tu-token-de-proveedor'")
    print()
    print("2. Obtén un token de autenticación de un proveedor verificado")
    print()
    print("3. Ejecuta el script:")
    print("   python test_provider_reservations.py")
    print()
    print("4. Endpoints disponibles:")
    print("   GET /api/v1/reservas/mis-reservas          # Para clientes")
    print("   GET /api/v1/reservas/reservas-proveedor    # Para proveedores")
    print()
    print("5. Parámetros de filtrado para proveedores:")
    print("   - search: búsqueda general")
    print("   - nombre_servicio: filtrar por servicio")
    print("   - nombre_cliente: filtrar por cliente")
    print("   - fecha_desde/fecha_hasta: rango de fechas")
    print("   - estado: pendiente, confirmada, cancelada")
    print("   - limit/offset: paginación")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del endpoint de reservas para proveedores...")
    
    # Verificar disponibilidad del servidor
    if asyncio.run(test_endpoint_availability()):
        # Ejecutar pruebas
        asyncio.run(test_provider_reservations())
    else:
        print("❌ No se puede conectar al servidor. Verifica la configuración.")
    
    # Mostrar instrucciones
    print_usage_instructions()
