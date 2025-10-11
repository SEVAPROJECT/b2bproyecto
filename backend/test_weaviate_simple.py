#!/usr/bin/env python3
"""
Script simple para probar conexión con Weaviate en Railway
"""
import weaviate
import os

def test_weaviate_connection():
    """Probar conexión directa con Weaviate"""
    print("🔍 Probando conexión directa con Weaviate...")
    
    try:
        # URL de Railway
        weaviate_url = "https://weaviate-production-0af4.up.railway.app"
        
        print(f"🔗 Conectando a: {weaviate_url}")
        
        # Conexión directa sin autenticación
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=None  # Sin autenticación
        )
        
        print("✅ Conexión exitosa!")
        
        # Verificar que está listo
        if client.is_ready():
            print("✅ Weaviate está listo")
            
            # Obtener información del cluster
            meta = client.get_meta()
            print(f"📊 Información del cluster: {meta}")
            
            # Listar clases
            classes = client.get_schema()
            print(f"📋 Clases disponibles: {list(classes.keys())}")
            
            return True
        else:
            print("❌ Weaviate no está listo")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    test_weaviate_connection()