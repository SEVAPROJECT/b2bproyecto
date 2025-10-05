#!/usr/bin/env python3
"""
Script para probar la conexión a Weaviate después de las correcciones
"""
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_weaviate_connection():
    """Probar la conexión a Weaviate con las correcciones aplicadas"""
    print("🧪 Probando conexión a Weaviate...")
    print("=" * 50)
    
    # Verificar variables de entorno
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    
    print(f"🔗 WEAVIATE_URL: {weaviate_url or 'No configurada'}")
    print(f"🔑 WEAVIATE_API_KEY: {'Configurada' if weaviate_api_key else 'No configurada'}")
    
    if not weaviate_url:
        print("❌ WEAVIATE_URL no está configurada")
        print("💡 Configura WEAVIATE_URL en Railway o como variable de entorno")
        return False
    
    try:
        # Importar el servicio de Weaviate
        from app.services.weaviate_service import weaviate_service
        
        print("\n🔍 Probando inicialización del servicio...")
        
        # Verificar si el cliente se inicializó correctamente
        if weaviate_service.client is None:
            print("❌ El cliente de Weaviate no se pudo inicializar")
            return False
        
        print("✅ Cliente de Weaviate inicializado correctamente")
        
        # Probar conexión
        print("\n🔍 Probando conexión a Weaviate...")
        if weaviate_service.client.is_ready():
            print("✅ Conexión a Weaviate exitosa")
        else:
            print("❌ No se pudo conectar a Weaviate")
            return False
        
        # Obtener estadísticas
        print("\n📊 Obteniendo estadísticas...")
        stats = weaviate_service.get_stats()
        print(f"📈 Estadísticas: {stats}")
        
        if "error" in stats:
            print(f"❌ Error en estadísticas: {stats['error']}")
            return False
        
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """Probar configuración de variables de entorno"""
    print("\n🔧 Verificando variables de entorno...")
    print("=" * 30)
    
    # Variables importantes
    important_vars = [
        "WEAVIATE_URL",
        "WEAVIATE_API_KEY", 
        "OLLAMA_ENDPOINT",
        "OLLAMA_MODEL"
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            # Ocultar API keys por seguridad
            if "KEY" in var or "SECRET" in var:
                display_value = "***" if value else "No configurada"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: No configurada")
    
    print("\n💡 Si alguna variable está faltando, configúrala en Railway")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de Weaviate...")
    
    # Probar variables de entorno
    test_environment_variables()
    
    # Probar conexión
    success = test_weaviate_connection()
    
    if success:
        print("\n🎉 ¡Todas las pruebas pasaron! Weaviate está funcionando correctamente.")
        sys.exit(0)
    else:
        print("\n❌ Algunas pruebas fallaron. Revisa la configuración.")
        sys.exit(1)
