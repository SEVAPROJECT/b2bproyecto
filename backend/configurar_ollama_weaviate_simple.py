#!/usr/bin/env python3
"""
Script para configurar Ollama + Weaviate en Railway (sin emojis)
"""

import os

def configurar_ollama_weaviate():
    """
    Configura Ollama y Weaviate para Railway
    """
    print("=== CONFIGURACION OLLAMA + WEAVIATE EN RAILWAY ===")
    
    # Variables de entorno necesarias
    variables_necesarias = {
        "WEAVIATE_URL": "http://weaviate:8080",
        "WEAVIATE_API_KEY": "",
        "OLLAMA_URL": "http://ollama:11434",
        "OLLAMA_MODEL": "nomic-embed-text",
        "WEAVIATE_CLASS_NAME": "Servicios"
    }
    
    print("\n=== VARIABLES DE ENTORNO NECESARIAS ===")
    for key, value in variables_necesarias.items():
        print(f"  {key}={value}")
    
    print("\n=== CONFIGURACION EN RAILWAY ===")
    print("1. Ve a tu proyecto en Railway")
    print("2. Ve a 'Variables' en la configuracion")
    print("3. Agrega las siguientes variables:")
    
    for key, value in variables_necesarias.items():
        print(f"   - {key}: {value}")
    
    print("\n=== CONFIGURACION DE OLLAMA ===")
    print("1. En Railway, agrega un servicio Ollama")
    print("2. Usa la imagen: ollama/ollama")
    print("3. Configura el puerto: 11434")
    print("4. Variables de entorno de Ollama:")
    print("   - OLLAMA_HOST=0.0.0.0")
    print("   - OLLAMA_ORIGINS=*")
    
    print("\n=== CONFIGURACION DE WEAVIATE ===")
    print("1. En Railway, agrega un servicio Weaviate")
    print("2. Usa la imagen: semitechnologies/weaviate:latest")
    print("3. Configura el puerto: 8080")
    print("4. Variables de entorno de Weaviate:")
    
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
    
    print("\n=== MODELOS RECOMENDADOS PARA OLLAMA ===")
    modelos = [
        "nomic-embed-text (recomendado)",
        "mxbai-embed-large",
        "snowflake-arctic-embed"
    ]
    
    for modelo in modelos:
        print(f"   - {modelo}")
    
    print("\n=== COMANDOS PARA DESCARGAR MODELOS ===")
    print("En el servicio Ollama, ejecuta:")
    print("  ollama pull nomic-embed-text")
    print("  ollama pull mxbai-embed-large")
    
    print("\n=== VERIFICACION ===")
    print("1. Verifica que Ollama este funcionando:")
    print("   curl http://ollama:11434/api/tags")
    print("2. Verifica que Weaviate este funcionando:")
    print("   curl http://weaviate:8080/v1/meta")
    print("3. Ejecuta el script de prueba:")
    print("   python test_ollama_weaviate_simple.py")
    
    return variables_necesarias

def crear_script_prueba():
    """
    Crea un script de prueba para Ollama + Weaviate
    """
    script_content = '''#!/usr/bin/env python3
"""
Script de prueba para Ollama + Weaviate en Railway (sin emojis)
"""

import os
import requests
import weaviate
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ollama_connection():
    """Prueba la conexion con Ollama"""
    print("=== PRUEBA DE CONEXION OLLAMA ===")
    
    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            print("OK: Ollama esta funcionando")
            models = response.json().get("models", [])
            print(f"Modelos disponibles: {len(models)}")
            for model in models:
                print(f"  - {model.get('name', 'N/A')}")
        else:
            print(f"ERROR: Ollama - {response.status_code}")
    except Exception as e:
        print(f"ERROR: Conexion con Ollama - {str(e)}")

def test_weaviate_connection():
    """Prueba la conexion con Weaviate"""
    print("\\n=== PRUEBA DE CONEXION WEAVIATE ===")
    
    weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    
    try:
        client = weaviate.connect_to_local(host=weaviate_url.replace("http://", ""))
        
        if client.is_ready():
            print("OK: Weaviate esta funcionando")
            cluster_info = client.get_meta()
            print(f"Info del cluster: {cluster_info}")
        else:
            print("ERROR: Weaviate no esta listo")
            
    except Exception as e:
        print(f"ERROR: Conexion con Weaviate - {str(e)}")

def test_integration():
    """Prueba la integracion Ollama + Weaviate"""
    print("\\n=== PRUEBA DE INTEGRACION ===")
    
    try:
        weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        client = weaviate.connect_to_local(host=weaviate_url.replace("http://", ""))
        
        if client.is_ready():
            print("OK: Integracion funcionando")
        else:
            print("ERROR: Weaviate no listo para integracion")
            
    except Exception as e:
        print(f"ERROR: Integracion - {str(e)}")

if __name__ == "__main__":
    print("=== PRUEBA COMPLETA OLLAMA + WEAVIATE ===")
    
    test_ollama_connection()
    test_weaviate_connection()
    test_integration()
    
    print("\\nPrueba completada")
'''
    
    with open("test_ollama_weaviate_simple.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("Script de prueba creado: test_ollama_weaviate_simple.py")

if __name__ == "__main__":
    print("=== CONFIGURACION OLLAMA + WEAVIATE EN RAILWAY ===")
    
    # Configurar variables
    variables = configurar_ollama_weaviate()
    
    # Crear script de prueba
    crear_script_prueba()
    
    print("\\nConfiguracion completada")
    print("\\n=== PROXIMOS PASOS ===")
    print("1. Configura las variables en Railway")
    print("2. Despliega los servicios Ollama y Weaviate")
    print("3. Ejecuta: python test_ollama_weaviate_simple.py")
    print("4. Verifica que todo funcione correctamente")
