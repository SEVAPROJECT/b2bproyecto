#!/usr/bin/env python3
"""
Script básico para probar Weaviate sin dependencias complejas
"""
import os
import weaviate

def test_weaviate_basic():
    """Probar conexión básica a Weaviate"""
    print("🔍 Probando conexión básica a Weaviate...")
    
    # Obtener URL
    weaviate_url = os.getenv("WEAVIATE_URL")
    if not weaviate_url:
        print("❌ Variable WEAVIATE_URL no configurada")
        print("💡 Configura: set WEAVIATE_URL=https://tu-weaviate.railway.app")
        return False
    
    print(f"🌐 URL: {weaviate_url}")
    
    try:
        # Crear cliente con la versión correcta
        client = weaviate.connect_to_local(
            host=weaviate_url.replace("https://", "").replace("http://", ""),
            port=443 if weaviate_url.startswith("https") else 80,
            grpc_port=50051
        )
        
        # Verificar conexión
        if client.is_ready():
            print("✅ Conexión exitosa!")
            
            # Obtener información básica
            meta = client.get_meta()
            print(f"📊 Versión: {meta.get('version', 'Unknown')}")
            print(f"📊 Hostname: {meta.get('hostname', 'Unknown')}")
            
            # Verificar esquema
            schema = client.schema.get()
            classes = schema.get('classes', [])
            print(f"📊 Clases existentes: {len(classes)}")
            
            for cls in classes:
                print(f"  - {cls.get('class', 'Unknown')}")
            
            return True
        else:
            print("❌ Weaviate no está listo")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Probando conexión básica a Weaviate...")
    print("=" * 50)
    
    success = test_weaviate_basic()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Conexión exitosa!")
    else:
        print("❌ Error en la conexión")
