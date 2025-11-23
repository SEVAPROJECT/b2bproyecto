#!/bin/bash

# Script de inicio para la aplicación FastAPI
set -e

echo "🚀 Iniciando SEVA B2B API..."

# Verificar que las variables de entorno estén configuradas
if [[ -z "$PORT" ]]; then
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

# Verificar Python y dependencias básicas
echo "🔍 Verificando Python..."
python --version

echo "🔍 Verificando dependencias básicas..."
python -c "import sys; print(f'Python path: {sys.path}')"

# Intentar importar la aplicación paso a paso
echo "🔍 Verificando importación de FastAPI..."
python -c "import fastapi; print('✅ FastAPI OK')" || {
    echo "❌ Error con FastAPI" >&2
    exit 1
}

echo "🔍 Verificando importación de Uvicorn..."
python -c "import uvicorn; print('✅ Uvicorn OK')" || {
    echo "❌ Error con Uvicorn" >&2
    exit 1
}

echo "🔍 Verificando importación de la aplicación..."
python -c "from app.main import app; print('✅ App importada OK')" || {
    echo "❌ Error al importar la aplicación" >&2
    echo "🔍 Listando archivos en app/" >&2
    ls -la app/ >&2
    echo "🔍 Listando archivos en app/main.py" >&2
    ls -la app/main.py >&2 || echo "main.py no encontrado" >&2
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
