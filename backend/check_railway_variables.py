#!/usr/bin/env python3
"""
Script para verificar las variables de entorno de Railway
"""
import os

def check_railway_variables():
    """Verificar variables de entorno disponibles"""
    print("🔍 Verificando variables de entorno de Railway...")
    print("=" * 50)
    
    # Variables comunes de Railway
    railway_vars = [
        "RAILWAY_PUBLIC_DOMAIN",
        "RAILWAY_STATIC_URL", 
        "PUBLIC_URL",
        "WEAVIATE_URL",
        "WEAVIATE_HOST",
        "WEAVIATE_API_KEY",
        "WEAVIATE_KEY"
    ]
    
    found_vars = {}
    
    for var in railway_vars:
        value = os.getenv(var)
        if value:
            found_vars[var] = value
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: No encontrada")
    
    print("\n" + "=" * 50)
    print("RESUMEN:")
    
    if found_vars:
        print("📊 Variables encontradas:")
        for var, value in found_vars.items():
            print(f"  {var} = {value}")
        
        # Sugerir configuración
        weaviate_url = found_vars.get("WEAVIATE_URL") or found_vars.get("PUBLIC_URL") or found_vars.get("RAILWAY_PUBLIC_DOMAIN")
        weaviate_key = found_vars.get("WEAVIATE_API_KEY") or found_vars.get("WEAVIATE_KEY")
        
        print("\n🔧 Configuración sugerida:")
        if weaviate_url:
            print(f"WEAVIATE_URL = {weaviate_url}")
        else:
            print("WEAVIATE_URL = https://tu-weaviate.railway.app")
            
        if weaviate_key:
            print(f"WEAVIATE_API_KEY = {weaviate_key}")
        else:
            print("WEAVIATE_API_KEY = (dejar vacío si no es necesario)")
    else:
        print("❌ No se encontraron variables de Weaviate")
        print("💡 Asegúrate de que el servicio Weaviate esté ejecutándose en Railway")
        print("💡 Verifica que las variables estén configuradas en Railway")

if __name__ == "__main__":
    check_railway_variables()
