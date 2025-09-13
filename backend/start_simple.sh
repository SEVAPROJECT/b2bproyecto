#!/bin/bash

# Script de inicio simplificado para la aplicación FastAPI
set -e

echo "🚀 Iniciando SEVA B2B API (versión simplificada)..."

# Verificar que las variables de entorno estén configuradas
if [ -z "$PORT" ]; then
    export PORT=8000
    echo "⚠️  PORT no configurado, usando puerto por defecto: $PORT"
fi

echo "📡 Puerto configurado: $PORT"
echo "🌍 Host: 0.0.0.0"

# Verificar Python
echo "🔍 Verificando Python..."
python --version

# Verificar dependencias básicas
echo "🔍 Verificando dependencias básicas..."
python -c "import fastapi; print('✅ FastAPI OK')"
python -c "import uvicorn; print('✅ Uvicorn OK')"

# Crear directorios necesarios
mkdir -p uploads/services
mkdir -p uploads/profile_photos
mkdir -p uploads/documents
mkdir -p uploads/provider_documents

echo "📁 Directorios de upload creados"

# Iniciar la aplicación simplificada
echo "🎯 Iniciando aplicación simplificada..."
exec python simple_app.py
