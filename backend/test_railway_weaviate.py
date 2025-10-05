#!/usr/bin/env python3
"""
Script para probar la conexión con Weaviate en Railway
"""
import os
import requests
import json

def test_weaviate_connection():
    """Probar conexión directa a Weaviate"""
    print("🔍 Probando conexión directa a Weaviate...")
    
    # Obtener URL de Weaviate
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    print(f"🌐 URL de Weaviate: {weaviate_url}")
    
    try:
        # Probar endpoint de meta
        meta_url = f"{weaviate_url}/v1/meta"
        print(f"🔗 Probando: {meta_url}")
        
        response = requests.get(meta_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Conexión exitosa a Weaviate")
            meta_data = response.json()
            print(f"📊 Versión: {meta_data.get('version', 'Unknown')}")
            print(f"📊 Hostname: {meta_data.get('hostname', 'Unknown')}")
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a Weaviate")
        print("💡 Verifica que la URL sea correcta y que el servicio esté ejecutándose")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_weaviate_schema():
    """Probar acceso al esquema de Weaviate"""
    print("\n🔍 Probando acceso al esquema...")
    
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    try:
        schema_url = f"{weaviate_url}/v1/schema"
        response = requests.get(schema_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Acceso al esquema exitoso")
            schema_data = response.json()
            classes = schema_data.get("classes", [])
            print(f"📊 Clases existentes: {len(classes)}")
            
            for cls in classes:
                print(f"  - {cls.get('class', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Error al acceder al esquema: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar esquema: {str(e)}")
        return False

def test_weaviate_modules():
    """Probar módulos disponibles en Weaviate"""
    print("\n🔍 Probando módulos disponibles...")
    
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    try:
        modules_url = f"{weaviate_url}/v1/modules"
        response = requests.get(modules_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Módulos accesibles")
            modules_data = response.json()
            
            # Mostrar módulos disponibles
            for module_name, module_info in modules_data.items():
                print(f"  📦 {module_name}: {module_info.get('status', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Error al acceder a módulos: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar módulos: {str(e)}")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 Probando conexión con Weaviate en Railway...")
    print("=" * 60)
    
    # Verificar variables de entorno
    weaviate_url = os.getenv("WEAVIATE_URL")
    if not weaviate_url:
        print("❌ Variable WEAVIATE_URL no configurada")
        print("💡 Configura WEAVIATE_URL en Railway o como variable de entorno")
        print("💡 Ejemplo: export WEAVIATE_URL=https://tu-weaviate.railway.app")
        return
    
    # Pruebas
    connection_ok = test_weaviate_connection()
    schema_ok = test_weaviate_schema() if connection_ok else False
    modules_ok = test_weaviate_modules() if connection_ok else False
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS:")
    print(f"✅ Conexión: {'OK' if connection_ok else 'ERROR'}")
    print(f"✅ Esquema: {'OK' if schema_ok else 'ERROR'}")
    print(f"✅ Módulos: {'OK' if modules_ok else 'ERROR'}")
    
    if connection_ok and schema_ok and modules_ok:
        print("\n🎉 ¡Weaviate está funcionando correctamente!")
        print("💡 Puedes proceder con la indexación de servicios")
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        print("💡 Revisa la configuración de Weaviate en Railway")

if __name__ == "__main__":
    main()
