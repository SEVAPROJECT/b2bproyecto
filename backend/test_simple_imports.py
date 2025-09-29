#!/usr/bin/env python3
"""
Script de prueba simple para verificar importaciones básicas
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    print("🔄 Probando importaciones básicas...")
    
    # Probar importación de config
    print("1. Importando app.core.config...")
    from app.core.config import DATABASE_URL
    print("✅ app.core.config importado correctamente")
    
    # Probar importación de supabase
    print("2. Importando supabase...")
    from supabase import create_client
    print("✅ supabase importado correctamente")
    
    # Probar importación de auth_service
    print("3. Importando app.supabase.auth_service...")
    from app.supabase.auth_service import supabase_auth, supabase_admin
    print("✅ app.supabase.auth_service importado correctamente")
    
    # Probar importación de direct_db_service
    print("4. Importando app.services.direct_db_service...")
    from app.services.direct_db_service import direct_db_service
    print("✅ app.services.direct_db_service importado correctamente")
    
    print("\n🎉 ¡Todas las importaciones básicas funcionan correctamente!")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print(f"❌ Tipo de error: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    print(f"❌ Tipo de error: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
