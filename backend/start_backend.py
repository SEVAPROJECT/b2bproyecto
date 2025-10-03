#!/usr/bin/env python3
"""
Script para iniciar el backend local
"""
import subprocess
import sys
import os

def start_backend():
    """Iniciar el backend local"""
    try:
        print("🚀 Iniciando backend local...")
        print("📁 Directorio actual:", os.getcwd())
        
        # Verificar que estamos en el directorio correcto
        if not os.path.exists("app/main.py"):
            print("❌ No se encontró app/main.py")
            print("💡 Asegúrate de estar en el directorio b2bproyecto/backend")
            return False
        
        print("✅ Archivo main.py encontrado")
        
        # Comando para iniciar uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        print(f"🔧 Ejecutando: {' '.join(cmd)}")
        print("🌐 Backend estará disponible en: http://localhost:8000")
        print("📊 Health check: http://localhost:8000/health")
        print("🔍 Endpoint de prueba: http://localhost:8000/api/v1/reservas/mis-reservas-test")
        print("\n⏹️  Presiona Ctrl+C para detener el servidor")
        
        # Ejecutar el comando
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️  Servidor detenido por el usuario")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar el servidor: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = start_backend()
    sys.exit(0 if success else 1)
