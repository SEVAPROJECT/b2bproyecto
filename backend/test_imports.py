#!/usr/bin/env python3
"""
Script de prueba para verificar que las importaciones funcionen correctamente
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    print("🔄 Probando importaciones...")
    
    # Probar importación del main
    print("1. Importando app.main...")
    from app.main import app
    print("✅ app.main importado correctamente")
    
    # Probar importación de startup
    print("2. Importando app.core.startup...")
    from app.core.startup import startup_events, shutdown_events
    print("✅ app.core.startup importado correctamente")
    
    # Probar importación de direct_db_service
    print("3. Importando app.services.direct_db_service...")
    from app.services.direct_db_service import direct_db_service
    print("✅ app.services.direct_db_service importado correctamente")
    
    # Probar importación de config
    print("4. Importando app.core.config...")
    from app.core.config import DATABASE_URL
    print("✅ app.core.config importado correctamente")
    
    print("\n🎉 ¡Todas las importaciones funcionan correctamente!")
    print("✅ La aplicación debería poder iniciar en Railway")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print(f"❌ Tipo de error: {type(e).__name__}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    print(f"❌ Tipo de error: {type(e).__name__}")
    sys.exit(1)
