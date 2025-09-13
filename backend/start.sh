#!/bin/bash

# Script de inicio para la aplicación FastAPI
set -e

echo "🚀 Iniciando SEVA B2B API..."

# Verificar que las variables de entorno estén configuradas
if [ -z "$PORT" ]; then
    export PORT=8000
    echo "⚠️  PORT no configurado, usando puerto por defecto: $PORT"
fi

echo "📡 Puerto configurado: $PORT"
echo "🌍 Host: 0.0.0.0"

# Crear directorios necesarios
mkdir -p uploads/services
mkdir -p uploads/profile_photos
mkdir -p uploads/documents
mkdir -p uploads/provider_documents

echo "📁 Directorios de upload creados"

# Verificar que Python puede importar la aplicación
echo "🔍 Verificando importación de la aplicación..."
python test_app.py || {
    echo "❌ Error al verificar la aplicación"
    exit 1
}

# Iniciar la aplicación
echo "🎯 Iniciando uvicorn..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --access-log \
    --log-level info
