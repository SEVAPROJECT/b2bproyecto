#!/usr/bin/env python3
"""
Script para actualizar automáticamente el uso de DateService.now() a DateService.now()
en todo el proyecto backend
"""
import os
import re
import sys
from pathlib import Path

def update_datetime_usage_in_file(file_path: str) -> bool:
    """
    Actualiza el uso de DateService.now() en un archivo específico
    
    Args:
        file_path: Ruta del archivo a actualizar
        
    Returns:
        bool: True si se realizaron cambios
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Patrón para encontrar DateService.now()
        pattern = r'datetime\.utcnow\(\)'
        
        # Verificar si el archivo contiene el patrón
        if not re.search(pattern, content):
            return False
        
        # Reemplazar DateService.now() con DateService.now()
        content = re.sub(pattern, 'DateService.now()', content)
        
        # Agregar import de DateService si no existe
        if 'DateService.now()' in content and 'from app.services.date_service import DateService' not in content:
            # Buscar la primera línea de import
            lines = content.split('\n')
            import_line_index = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('from ') or line.strip().startswith('import '):
                    import_line_index = i
            
            if import_line_index >= 0:
                # Insertar después de la última línea de import
                lines.insert(import_line_index + 1, 'from app.services.date_service import DateService')
                content = '\n'.join(lines)
            else:
                # Si no hay imports, agregar al principio
                content = 'from app.services.date_service import DateService\n' + content
        
        # Solo escribir si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {str(e)}")
        return False

def find_python_files(directory: str) -> list:
    """
    Encuentra todos los archivos Python en un directorio
    
    Args:
        directory: Directorio a buscar
        
    Returns:
        list: Lista de archivos Python encontrados
    """
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Excluir directorios específicos
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    """Función principal"""
    print("🔄 Iniciando actualización de uso de DateService.now() a DateService.now()...")
    
    # Directorio del proyecto backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Encontrar todos los archivos Python
    python_files = find_python_files(backend_dir)
    
    print(f"📁 Encontrados {len(python_files)} archivos Python")
    
    updated_files = []
    
    for file_path in python_files:
        # Excluir archivos específicos
        if any(exclude in file_path for exclude in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']):
            continue
        
        print(f"🔍 Procesando: {file_path}")
        
        if update_datetime_usage_in_file(file_path):
            updated_files.append(file_path)
            print(f"✅ Actualizado: {file_path}")
        else:
            print(f"ℹ️ Sin cambios: {file_path}")
    
    print(f"\n📊 Resumen:")
    print(f"   Total de archivos procesados: {len(python_files)}")
    print(f"   Archivos actualizados: {len(updated_files)}")
    
    if updated_files:
        print(f"\n✅ Archivos actualizados:")
        for file_path in updated_files:
            print(f"   - {file_path}")
    else:
        print(f"\nℹ️ No se encontraron archivos que requieran actualización")
    
    print(f"\n🎉 Proceso completado!")

if __name__ == "__main__":
    main()
