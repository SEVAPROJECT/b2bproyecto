#!/usr/bin/env python3
"""
Script para verificar el estado de una reserva antes y después del cambio
"""

import requests
import json

def verificar_estado_reserva():
    """
    Verifica el estado de una reserva
    """
    print("🔍 === VERIFICACIÓN DE ESTADO DE RESERVA ===")
    
    # Configuración
    API_BASE_URL = "http://localhost:8000"
    token = input("Ingresa tu token de autenticación: ").strip()
    
    if not token:
        print("❌ Token requerido")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Verificar reservas del proveedor
    print("\n📋 === RESERVAS DEL PROVEEDOR ===")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/reservas/reservas-proveedor", headers=headers)
        if response.status_code == 200:
            data = response.json()
            reservas = data.get('reservas', [])
            print(f"✅ Encontradas {len(reservas)} reservas")
            
            for reserva in reservas:
                print(f"  📝 ID: {reserva.get('id_reserva')} | Estado: {reserva.get('estado')} | Servicio: {reserva.get('servicio_nombre', 'N/A')}")
        else:
            print(f"❌ Error al obtener reservas: {response.status_code}")
            print(f"📊 Respuesta: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Verificar reservas del cliente
    print("\n👤 === RESERVAS DEL CLIENTE ===")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/reservas/mis-reservas", headers=headers)
        if response.status_code == 200:
            data = response.json()
            reservas = data if isinstance(data, list) else data.get('reservas', [])
            print(f"✅ Encontradas {len(reservas)} reservas")
            
            for reserva in reservas:
                print(f"  📝 ID: {reserva.get('id_reserva')} | Estado: {reserva.get('estado')} | Servicio: {reserva.get('servicio', {}).get('nombre', 'N/A')}")
        else:
            print(f"❌ Error al obtener reservas: {response.status_code}")
            print(f"📊 Respuesta: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n🎯 === INSTRUCCIONES ===")
    print("1. Anota el ID de una reserva 'pendiente'")
    print("2. Ve al frontend como proveedor")
    print("3. Haz clic en 'Aceptar' para esa reserva")
    print("4. Ejecuta este script nuevamente para ver el cambio")
    print("5. Ve al frontend como cliente para confirmar el cambio")

if __name__ == "__main__":
    verificar_estado_reserva()
