#!/usr/bin/env python3
"""
Script para probar Weaviate usando HTTP directo
"""
import os
import urllib.request
import json

def test_weaviate_http():
    """Probar conexión HTTP directa a Weaviate"""
    print("🔍 Probando conexión HTTP directa a Weaviate...")
    
    # Obtener URL
    weaviate_url = os.getenv("WEAVIATE_URL")
    if not weaviate_url:
        print("❌ Variable WEAVIATE_URL no configurada")
        return False
    
    print(f"🌐 URL: {weaviate_url}")
    
    try:
        # Probar endpoint de meta
        meta_url = f"{weaviate_url}/v1/meta"
        print(f"🔗 Probando: {meta_url}")
        
        request = urllib.request.Request(meta_url)
        request.add_header('User-Agent', 'Python-Weaviate-Test')
        
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print("✅ Conexión HTTP exitosa!")
                print(f"📊 Versión: {data.get('version', 'Unknown')}")
                print(f"📊 Hostname: {data.get('hostname', 'Unknown')}")
                return True
            else:
                print(f"❌ Error HTTP: {response.status}")
                return False
                
    except urllib.error.URLError as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_weaviate_schema_http():
    """Probar esquema via HTTP"""
    print("\n🔍 Probando esquema via HTTP...")
    
    weaviate_url = os.getenv("WEAVIATE_URL")
    
    try:
        schema_url = f"{weaviate_url}/v1/schema"
        request = urllib.request.Request(schema_url)
        request.add_header('User-Agent', 'Python-Weaviate-Test')
        
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                classes = data.get('classes', [])
                print(f"✅ Esquema accesible! Clases: {len(classes)}")
                
                for cls in classes:
                    print(f"  - {cls.get('class', 'Unknown')}")
                
                return True
            else:
                print(f"❌ Error HTTP: {response.status}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Probando Weaviate via HTTP...")
    print("=" * 50)
    
    # Probar conexión básica
    connection_ok = test_weaviate_http()
    
    # Probar esquema si la conexión es exitosa
    schema_ok = False
    if connection_ok:
        schema_ok = test_weaviate_schema_http()
    
    print("\n" + "=" * 50)
    print("RESUMEN:")
    print(f"✅ Conexión HTTP: {'OK' if connection_ok else 'ERROR'}")
    print(f"✅ Esquema: {'OK' if schema_ok else 'ERROR'}")
    
    if connection_ok and schema_ok:
        print("\n🎉 ¡Weaviate está funcionando correctamente!")
    else:
        print("\n❌ Error en la conexión a Weaviate")
