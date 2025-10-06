#!/usr/bin/env python3
"""
Script para probar el cambio de estado de reservas
"""

import requests
import json
import sys

# Configuración
API_BASE_URL = "http://localhost:8000"
ENDPOINT_ACTUALIZAR_ESTADO = f"{API_BASE_URL}/api/v1/reservas"

def test_cambio_estado_reserva():
    """
    Prueba el cambio de estado de una reserva
    """
    print("🧪 === PRUEBA DE CAMBIO DE ESTADO DE RESERVA ===")
    
    # Token de autenticación (reemplaza con un token válido)
    token = input("Ingresa tu token de autenticación: ").strip()
    
    if not token:
        print("❌ Token requerido")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # ID de reserva a probar
    reserva_id = input("Ingresa el ID de la reserva a probar: ").strip()
    
    if not reserva_id:
        print("❌ ID de reserva requerido")
        return
    
    try:
        reserva_id = int(reserva_id)
    except ValueError:
        print("❌ ID de reserva debe ser un número")
        return
    
    # Estados a probar
    estados_a_probar = [
        {"nuevo_estado": "aprobado", "observacion": "Reserva aprobada por el proveedor"},
        {"nuevo_estado": "concluido", "observacion": "Servicio completado exitosamente"}
    ]
    
    for i, estado_data in enumerate(estados_a_probar, 1):
        print(f"\n🔄 === PRUEBA {i}: Cambiar a '{estado_data['nuevo_estado']}' ===")
        
        # Realizar la petición
        url = f"{ENDPOINT_ACTUALIZAR_ESTADO}/{reserva_id}/estado"
        payload = {
            "nuevo_estado": estado_data["nuevo_estado"],
            "observacion": estado_data["observacion"]
        }
        
        print(f"📤 Enviando petición a: {url}")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.put(url, headers=headers, json=payload, timeout=30)
            
            print(f"📥 Status Code: {response.status_code}")
            print(f"📥 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ ¡Cambio de estado exitoso!")
                try:
                    data = response.json()
                    print(f"📊 Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📊 Respuesta (texto): {response.text}")
            else:
                print(f"❌ Error en la petición")
                try:
                    error_data = response.json()
                    print(f"📊 Error: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📊 Error (texto): {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {str(e)}")
        
        # Pausa entre pruebas
        if i < len(estados_a_probar):
            input("\n⏸️ Presiona Enter para continuar con la siguiente prueba...")
    
    print("\n🎯 === VERIFICACIÓN EN BASE DE DATOS ===")
    print("Para verificar que el cambio se reflejó en la base de datos:")
    print("1. Ve a la página del cliente")
    print("2. Verifica que el estado de la reserva haya cambiado")
    print("3. Revisa los logs del backend para confirmar la actualización")
    
    print("\n✅ Prueba completada")

if __name__ == "__main__":
    test_cambio_estado_reserva()
