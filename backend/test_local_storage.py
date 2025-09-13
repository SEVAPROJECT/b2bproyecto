#!/usr/bin/env python3
"""
Script de prueba para verificar el almacenamiento local
"""

import asyncio
import os
from io import BytesIO
from pathlib import Path

# Simular un archivo UploadFile
class MockUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.content = content
    
    async def read(self):
        return self.content

async def test_local_storage():
    """Prueba el almacenamiento local"""
    
    print("🔍 Verificando almacenamiento local...")
    
    try:
        # Importar la función de almacenamiento local
        from app.api.v1.dependencies.local_storage import upload_file_locally, UPLOAD_DIR
        
        print(f"📁 Directorio de almacenamiento: {UPLOAD_DIR}")
        
        # Crear un archivo de prueba
        test_content = b"Este es un archivo de prueba para verificar el almacenamiento local"
        test_file = MockUploadFile("test_document.pdf", test_content)
        
        print("🚀 Probando subida de archivo...")
        
        # Subir el archivo
        file_url = await upload_file_locally(
            file=test_file,
            user_id="test_user_123",
            file_type="RUC"
        )
        
        print(f"✅ Archivo subido: {file_url}")
        
        # Verificar que el archivo existe
        if file_url.startswith("local://"):
            filename = file_url.replace("local://", "")
            file_path = UPLOAD_DIR / filename
            
            if file_path.exists():
                print(f"✅ Archivo guardado en: {file_path}")
                
                # Leer el contenido para verificar
                with open(file_path, "rb") as f:
                    saved_content = f.read()
                
                if saved_content == test_content:
                    print("✅ Contenido del archivo verificado correctamente")
                else:
                    print("❌ El contenido del archivo no coincide")
            else:
                print("❌ El archivo no se guardó correctamente")
        else:
            print(f"❌ URL inesperada: {file_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando prueba de almacenamiento local...")
    result = asyncio.run(test_local_storage())
    
    if result:
        print("\n🎉 ¡Almacenamiento local funcionando correctamente!")
    else:
        print("\n💥 Error en el almacenamiento local")
