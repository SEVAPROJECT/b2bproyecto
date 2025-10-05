#!/usr/bin/env python3
"""
Script para configurar variables de entorno de Weaviate
"""
import os

def setup_weaviate_environment():
    """Configurar variables de entorno para Weaviate"""
    print("🔧 Configurando variables de entorno para Weaviate...")
    
    # Configurar variables de entorno
    os.environ['WEAVIATE_URL'] = 'https://weaviate-production-0af4.up.railway.app'
    os.environ['WEAVIATE_API_KEY'] = ''  # Vacío para acceso anónimo
    
    print(f"✅ WEAVIATE_URL configurada: {os.environ.get('WEAVIATE_URL')}")
    print(f"✅ WEAVIATE_API_KEY configurada: {'Sí' if os.environ.get('WEAVIATE_API_KEY') else 'No (acceso anónimo)'}")
    
    # Probar conexión
    try:
        from app.services.weaviate_service import weaviate_service
        stats = weaviate_service.get_stats()
        print(f"📊 Estado de Weaviate: {stats}")
        
        if "error" not in stats:
            print("🎉 ¡Weaviate está funcionando correctamente!")
            return True
        else:
            print("❌ Error en la conexión con Weaviate")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar Weaviate: {str(e)}")
        return False

if __name__ == "__main__":
    setup_weaviate_environment()
