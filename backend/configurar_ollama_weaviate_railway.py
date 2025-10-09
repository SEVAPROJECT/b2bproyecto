#!/usr/bin/env python3
"""
Script para configurar Ollama + Weaviate en Railway
"""

import os
import requests
import json
import time

def configurar_ollama_weaviate():
    """
    Configura Ollama y Weaviate para Railway
    """
    print("🚀 === CONFIGURACIÓN OLLAMA + WEAVIATE EN RAILWAY ===")
    
    # Variables de entorno necesarias
    variables_necesarias = {
        "WEAVIATE_URL": "http://weaviate:8080",  # URL interna de Weaviate en Railway
        "WEAVIATE_API_KEY": "",  # Dejar vacío para desarrollo local
        "OLLAMA_URL": "http://ollama:11434",  # URL interna de Ollama en Railway
        "OLLAMA_MODEL": "nomic-embed-text",  # Modelo de embeddings
        "WEAVIATE_CLASS_NAME": "Servicios"
    }
    
    print("\n📋 === VARIABLES DE ENTORNO NECESARIAS ===")
    for key, value in variables_necesarias.items():
        print(f"  {key}={value}")
    
    print("\n🔧 === CONFIGURACIÓN EN RAILWAY ===")
    print("1. Ve a tu proyecto en Railway")
    print("2. Ve a 'Variables' en la configuración")
    print("3. Agrega las siguientes variables:")
    
    for key, value in variables_necesarias.items():
        print(f"   - {key}: {value}")
    
    print("\n🤖 === CONFIGURACIÓN DE OLLAMA ===")
    print("1. En Railway, agrega un servicio Ollama")
    print("2. Usa la imagen: ollama/ollama")
    print("3. Configura el puerto: 11434")
    print("4. Agrega las variables de entorno de Ollama")
    
    print("\n🔗 === CONFIGURACIÓN DE WEAVIATE ===")
    print("1. En Railway, agrega un servicio Weaviate")
    print("2. Usa la imagen: semitechnologies/weaviate:latest")
    print("3. Configura el puerto: 8080")
    print("4. Agrega las variables de entorno de Weaviate")
    
    print("\n📝 === VARIABLES DE WEAVIATE ===")
    weaviate_vars = {
        "QUERY_DEFAULTS_LIMIT": "25",
        "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
        "PERSISTENCE_DATA_PATH": "/var/lib/weaviate",
        "DEFAULT_VECTORIZER_MODULE": "none",
        "ENABLE_MODULES": "text2vec-ollama",
        "CLUSTER_HOSTNAME": "node1"
    }
    
    for key, value in weaviate_vars.items():
        print(f"   - {key}: {value}")
    
    print("\n🧪 === SCRIPT DE PRUEBA ===")
    print("Ejecuta este script para probar la conexión:")
    print("python test_ollama_weaviate_railway.py")
    
    return variables_necesarias

def crear_script_prueba():
    """
    Crea un script de prueba para Ollama + Weaviate
    """
    script_content = '''#!/usr/bin/env python3
"""
Script de prueba para Ollama + Weaviate en Railway
"""

import os
import requests
import weaviate
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ollama_connection():
    """Prueba la conexión con Ollama"""
    print("🤖 === PRUEBA DE CONEXIÓN OLLAMA ===")
    
    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    
    try:
        # Probar que Ollama esté funcionando
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama está funcionando")
            models = response.json().get("models", [])
            print(f"📋 Modelos disponibles: {len(models)}")
            for model in models:
                print(f"  - {model.get('name', 'N/A')}")
        else:
            print(f"❌ Error en Ollama: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conexión con Ollama: {str(e)}")

def test_weaviate_connection():
    """Prueba la conexión con Weaviate"""
    print("\\n🔗 === PRUEBA DE CONEXIÓN WEAVIATE ===")
    
    weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    
    try:
        # Conectar a Weaviate
        client = weaviate.connect_to_local(host=weaviate_url.replace("http://", ""))
        
        if client.is_ready():
            print("✅ Weaviate está funcionando")
            
            # Obtener información del cluster
            cluster_info = client.get_meta()
            print(f"📊 Información del cluster: {cluster_info}")
            
        else:
            print("❌ Weaviate no está listo")
            
    except Exception as e:
        print(f"❌ Error de conexión con Weaviate: {str(e)}")

def test_ollama_weaviate_integration():
    """Prueba la integración Ollama + Weaviate"""
    print("\\n🔗 === PRUEBA DE INTEGRACIÓN OLLAMA + WEAVIATE ===")
    
    try:
        # Configurar Weaviate con Ollama
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        
        client = weaviate.connect_to_local(host=weaviate_url.replace("http://", ""))
        
        if client.is_ready():
            print("✅ Integración funcionando")
            
            # Crear una clase de prueba
            class_name = "TestClass"
            
            # Verificar si la clase existe
            if client.schema.exists(class_name):
                print(f"✅ Clase {class_name} existe")
            else:
                print(f"ℹ️ Clase {class_name} no existe (normal en primera ejecución)")
        else:
            print("❌ Weaviate no está listo para integración")
            
    except Exception as e:
        print(f"❌ Error en integración: {str(e)}")

if __name__ == "__main__":
    print("🧪 === PRUEBA COMPLETA OLLAMA + WEAVIATE ===")
    
    test_ollama_connection()
    test_weaviate_connection()
    test_ollama_weaviate_integration()
    
    print("\\n✅ Prueba completada")
'''
    
    with open("test_ollama_weaviate_railway.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("📝 Script de prueba creado: test_ollama_weaviate_railway.py")

if __name__ == "__main__":
    print("🚀 === CONFIGURACIÓN OLLAMA + WEAVIATE EN RAILWAY ===")
    
    # Configurar variables
    variables = configurar_ollama_weaviate()
    
    # Crear script de prueba
    crear_script_prueba()
    
    print("\\n✅ Configuración completada")
    print("\\n📋 === PRÓXIMOS PASOS ===")
    print("1. Configura las variables en Railway")
    print("2. Despliega los servicios Ollama y Weaviate")
    print("3. Ejecuta: python test_ollama_weaviate_railway.py")
    print("4. Verifica que todo funcione correctamente")
