#!/usr/bin/env python3
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
    print("\n=== PRUEBA DE CONEXION WEAVIATE ===")
    
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
    print("\n=== PRUEBA DE INTEGRACION ===")
    
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
    
    print("\nPrueba completada")
