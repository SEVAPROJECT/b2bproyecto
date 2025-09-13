#!/usr/bin/env python3
"""
Script para verificar las variables de entorno de iDrive2
"""

import os
from dotenv import load_dotenv

def check_idrive_variables():
    """Verifica las variables de entorno de iDrive2"""
    
    print("🔍 Verificando variables de entorno de iDrive2...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Variables a verificar (múltiples opciones)
    variables = {
        'IDRIVE_ENDPOINT_URL': os.getenv('IDRIVE_ENDPOINT_URL'),
        'IDRIVE_BUCKET_NAME': os.getenv('IDRIVE_BUCKET_NAME'),
        # Credenciales - múltiples opciones
        'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'IDRIVE_ACCESS_KEY': os.getenv('IDRIVE_ACCESS_KEY'),
        'IDRIVE_SECRET_KEY': os.getenv('IDRIVE_SECRET_KEY'),
        'ACCESS_KEY_ID': os.getenv('ACCESS_KEY_ID'),
        'SECRET_ACCESS_KEY': os.getenv('SECRET_ACCESS_KEY')
    }
    
    print("\n📋 Estado de las variables:")
    for var_name, var_value in variables.items():
        if var_value:
            # Mostrar solo los primeros y últimos caracteres por seguridad
            if var_name == 'AWS_SECRET_ACCESS_KEY':
                display_value = f"{var_value[:4]}...{var_value[-4:]}" if len(var_value) > 8 else "***"
            else:
                display_value = var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: No configurada")
    
    # Verificar formato de Access Key (buscar en todas las opciones)
    access_key = (variables['AWS_ACCESS_KEY_ID'] or 
                 variables['IDRIVE_ACCESS_KEY'] or 
                 variables['ACCESS_KEY_ID'])
    
    if access_key:
        print(f"\n🔑 Formato de Access Key:")
        print(f"   Longitud: {len(access_key)} caracteres")
        print(f"   Comienza con: {access_key[:4]}")
        
        # Verificar si parece una Access Key válida
        if len(access_key) < 10:
            print("   ⚠️  La Access Key parece muy corta")
        elif not access_key.isalnum():
            print("   ⚠️  La Access Key contiene caracteres especiales")
        else:
            print("   ✅ Formato de Access Key parece correcto")
    
    # Verificar endpoint
    endpoint = variables['IDRIVE_ENDPOINT_URL']
    if endpoint:
        print(f"\n🌐 Endpoint de iDrive2:")
        print(f"   URL: {endpoint}")
        if not endpoint.startswith('http'):
            print("   ⚠️  El endpoint debe comenzar con http:// o https://")
        else:
            print("   ✅ Formato de endpoint correcto")
    
    # Recomendaciones
    print(f"\n💡 Recomendaciones:")
    if not all(variables.values()):
        print("   - Completa todas las variables en el archivo .env")
        print("   - Verifica que no haya espacios extra en las variables")
    else:
        print("   - Todas las variables están configuradas")
        print("   - Verifica que las credenciales sean de iDrive2, no de AWS")

if __name__ == "__main__":
    check_idrive_variables()
