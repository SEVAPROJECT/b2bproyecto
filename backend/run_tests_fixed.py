#!/usr/bin/env python3
"""
Script para ejecutar las pruebas unitarias con PYTHONPATH configurado
"""
import subprocess
import sys
import os
from pathlib import Path

def setup_environment():
    """Configura el entorno para las pruebas"""
    # Obtener el directorio actual (backend/)
    current_dir = Path(__file__).parent.absolute()
    
    # Agregar al PYTHONPATH
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # También configurar la variable de entorno
    os.environ['PYTHONPATH'] = str(current_dir)
    
    print(f"✅ PYTHONPATH configurado: {current_dir}")

def run_tests():
    """Ejecuta las pruebas unitarias"""
    setup_environment()
    
    print("🧪 Ejecutando pruebas unitarias...")
    print("=" * 50)
    
    # Comandos de prueba
    commands = [
        # Pruebas básicas
        ["python", "-m", "pytest", "test/", "-v"],
        
        # Pruebas con cobertura
        ["python", "-m", "pytest", "test/", "--cov=app", "--cov-report=term-missing", "-v"],
        
        # Pruebas específicas de auth
        ["python", "-m", "pytest", "test/test_auth_endpoints.py", "-v"],
        
        # Pruebas de dependencias
        ["python", "-m", "pytest", "test/test_auth_dependencies.py", "-v"],
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n📋 Ejecutando comando {i}: {' '.join(cmd)}")
        print("-" * 50)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✅ Comando ejecutado exitosamente")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print("❌ Error al ejecutar el comando")
            print(f"Error: {e}")
            print(f"Salida: {e.stdout}")
            print(f"Error: {e.stderr}")
            return False
    
    print("\n🎉 Todas las pruebas completadas")
    return True

def run_specific_test(test_file):
    """Ejecuta una prueba específica"""
    setup_environment()
    
    print(f"🧪 Ejecutando prueba específica: {test_file}")
    print("=" * 50)
    
    cmd = ["python", "-m", "pytest", test_file, "-v"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Prueba ejecutada exitosamente")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Error al ejecutar la prueba")
        print(f"Error: {e}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def install_test_dependencies():
    """Instala las dependencias de testing"""
    print("📦 Instalando dependencias de testing...")
    
    cmd = ["pip", "install", "-r", "requirements-test.txt"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Dependencias instaladas exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Error al instalar dependencias")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            install_test_dependencies()
        elif sys.argv[1] == "specific" and len(sys.argv) > 2:
            run_specific_test(sys.argv[2])
        else:
            print("Uso:")
            print("  python run_tests_fixed.py                    # Ejecutar todas las pruebas")
            print("  python run_tests_fixed.py install            # Instalar dependencias")
            print("  python run_tests_fixed.py specific <file>    # Ejecutar prueba específica")
    else:
        run_tests()
