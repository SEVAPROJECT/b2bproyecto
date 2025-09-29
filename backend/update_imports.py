#!/usr/bin/env python3
"""
Script para actualizar todas las importaciones de app.supabase a app.supabase_client
"""

import os
import re

def update_imports_in_file(file_path):
    """Actualizar importaciones en un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar todas las importaciones de app.supabase
        updated_content = re.sub(
            r'from app\.supabase\.',
            'from app.supabase_client.',
            content
        )
        
        # Solo escribir si hubo cambios
        if content != updated_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Actualizado: {file_path}")
            return True
        else:
            print(f"ℹ️ Sin cambios: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return False

def find_python_files(directory):
    """Encontrar todos los archivos Python en un directorio"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Función principal"""
    print("🔄 Actualizando importaciones de app.supabase a app.supabase_client...")
    
    # Directorio del proyecto
    project_dir = "app"
    
    # Encontrar todos los archivos Python
    python_files = find_python_files(project_dir)
    
    updated_count = 0
    total_files = len(python_files)
    
    for file_path in python_files:
        if update_imports_in_file(file_path):
            updated_count += 1
    
    print(f"\n📊 Resumen:")
    print(f"   Total de archivos procesados: {total_files}")
    print(f"   Archivos actualizados: {updated_count}")
    print(f"   Archivos sin cambios: {total_files - updated_count}")

if __name__ == "__main__":
    main()
