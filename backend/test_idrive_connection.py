#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión a iDrive2
"""

import asyncio
import os
from io import BytesIO
from app.core.config import IDRIVE_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, IDRIVE_BUCKET_NAME
from app.idrive.idrive_service import idrive_s3_client

async def test_idrive_connection():
    """Prueba la conexión a iDrive2"""
    
    print("🔍 Verificando configuración de iDrive2...")
    
    # Verificar variables de entorno
    print(f"IDRIVE_ENDPOINT_URL: {'✅ Configurado' if IDRIVE_ENDPOINT_URL else '❌ No configurado'}")
    print(f"AWS_ACCESS_KEY_ID: {'✅ Configurado' if AWS_ACCESS_KEY_ID else '❌ No configurado'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'✅ Configurado' if AWS_SECRET_ACCESS_KEY else '❌ No configurado'}")
    print(f"IDRIVE_BUCKET_NAME: {'✅ Configurado' if IDRIVE_BUCKET_NAME else '❌ No configurado'}")
    
    if not all([IDRIVE_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, IDRIVE_BUCKET_NAME]):
        print("❌ Faltan variables de entorno para iDrive2")
        return False
    
    try:
        print("\n🚀 Probando conexión a iDrive2...")
        
        # Crear un archivo de prueba en memoria
        test_content = b"Este es un archivo de prueba para verificar la conexion a iDrive2"
        test_file = BytesIO(test_content)
        
        # Nombre del archivo de prueba
        test_key = "test/connection_test.txt"
        
        # Intentar subir el archivo
        idrive_s3_client.upload_fileobj(
            test_file,
            IDRIVE_BUCKET_NAME,
            test_key,
            ExtraArgs={"ACL": "public-read"}
        )
        
        print("✅ Archivo subido exitosamente a iDrive2")
        
        # Construir la URL del archivo
        file_url = f"{IDRIVE_ENDPOINT_URL}/{IDRIVE_BUCKET_NAME}/{test_key}"
        print(f"📁 URL del archivo: {file_url}")
        
        # Intentar listar objetos en el bucket
        response = idrive_s3_client.list_objects_v2(
            Bucket=IDRIVE_BUCKET_NAME,
            MaxKeys=5
        )
        
        print(f"📋 Objetos en el bucket: {len(response.get('Contents', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al conectar con iDrive2: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando prueba de conexión a iDrive2...")
    result = asyncio.run(test_idrive_connection())
    
    if result:
        print("\n🎉 ¡Conexión a iDrive2 exitosa!")
    else:
        print("\n💥 Error en la conexión a iDrive2")
