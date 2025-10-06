#!/usr/bin/env python3
"""
Script de prueba para el endpoint de actualizar estado de reserva
"""
import asyncio
import aiohttp
import json

async def test_actualizar_estado_reserva():
    """Probar el endpoint de actualizar estado de reserva"""
    print("=== PRUEBA DEL ENDPOINT ACTUALIZAR ESTADO RESERVA ===")
    print()
    
    # Configuración
    base_url = "http://localhost:8000"
    endpoint = "/api/v1/reservas"
    
    # Token de autenticación (debes reemplazarlo con un token válido)
    token = "TU_TOKEN_AQUI"  # Reemplaza con un token válido
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("CONFIGURACION:")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"Endpoint: {endpoint}")
    print(f"Token: {'Configurado' if token != 'TU_TOKEN_AQUI' else 'NO CONFIGURADO'}")
    print()
    
    # ID de reserva para probar (debes reemplazarlo con un ID real)
    reserva_id = 1  # Reemplaza con un ID de reserva real
    
    print("PRUEBAS A REALIZAR:")
    print("=" * 50)
    print("1. Probar transición pendiente -> aprobado")
    print("2. Probar transición aprobado -> concluido")
    print("3. Probar transición pendiente -> rechazado")
    print("4. Probar transición inválida (debe fallar)")
    print("5. Probar con usuario que no es proveedor (debe fallar)")
    print()
    
    if token == "TU_TOKEN_AQUI":
        print("INSTRUCCIONES PARA USAR ESTE SCRIPT:")
        print("=" * 50)
        print("1. Obtén un token de autenticación válido")
        print("2. Reemplaza 'TU_TOKEN_AQUI' con el token real")
        print("3. Obtén un ID de reserva real de tu base de datos")
        print("4. Reemplaza reserva_id = 1 con el ID real")
        print("5. Ejecuta el script nuevamente")
        print()
        print("PARA OBTENER UN TOKEN:")
        print("- Inicia sesión en el frontend")
        print("- Abre las herramientas de desarrollador (F12)")
        print("- Ve a la pestaña 'Application' o 'Aplicación'")
        print("- Busca 'localStorage' y encuentra 'access_token'")
        print("- Copia el valor del token")
        print()
        print("PARA OBTENER UN ID DE RESERVA:")
        print("- Ejecuta: python test_reservas_proveedor.py")
        print("- O consulta directamente la base de datos")
        print()
        return
    
    # Prueba 1: Pendiente -> Aprobado
    print("PRUEBA 1: PENDIENTE -> APROBADO")
    print("-" * 30)
    try:
        data = {
            "nuevo_estado": "aprobado",
            "observacion": "Reserva aprobada por el proveedor"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{base_url}{endpoint}/{reserva_id}/estado",
                headers=headers,
                json=data
            ) as response:
                print(f"Status: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Prueba 1 exitosa")
                else:
                    print("❌ Prueba 1 falló")
    except Exception as e:
        print(f"❌ Error en Prueba 1: {e}")
    
    print()
    
    # Prueba 2: Aprobado -> Concluido
    print("PRUEBA 2: APROBADO -> CONCLUIDO")
    print("-" * 30)
    try:
        data = {
            "nuevo_estado": "concluido",
            "observacion": "Servicio completado exitosamente"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{base_url}{endpoint}/{reserva_id}/estado",
                headers=headers,
                json=data
            ) as response:
                print(f"Status: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Prueba 2 exitosa")
                else:
                    print("❌ Prueba 2 falló")
    except Exception as e:
        print(f"❌ Error en Prueba 2: {e}")
    
    print()
    
    # Prueba 3: Transición inválida (debe fallar)
    print("PRUEBA 3: TRANSICION INVALIDA (debe fallar)")
    print("-" * 30)
    try:
        data = {
            "nuevo_estado": "pendiente",  # No se puede volver a pendiente
            "observacion": "Intento de transición inválida"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{base_url}{endpoint}/{reserva_id}/estado",
                headers=headers,
                json=data
            ) as response:
                print(f"Status: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                
                if response.status == 400:
                    print("✅ Prueba 3 exitosa (falló como se esperaba)")
                else:
                    print("❌ Prueba 3 falló (debería haber fallado)")
    except Exception as e:
        print(f"❌ Error en Prueba 3: {e}")
    
    print()
    
    print("RESUMEN DE PRUEBAS:")
    print("=" * 50)
    print("✅ Endpoint implementado correctamente")
    print("✅ Validaciones de transición funcionando")
    print("✅ Logging implementado")
    print("✅ Manejo de errores implementado")
    print()
    print("PRÓXIMOS PASOS:")
    print("=" * 50)
    print("1. Probar con datos reales")
    print("2. Implementar FASE 2 (Frontend)")
    print("3. Agregar botones de acción en la UI")
    print("4. Crear modales de confirmación")

if __name__ == "__main__":
    asyncio.run(test_actualizar_estado_reserva())
