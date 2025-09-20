#!/usr/bin/env python3
"""
Aplicación FastAPI simplificada para testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Crear aplicación FastAPI
app = FastAPI(
    title="SEVA B2B API - Simple",
    description="API simplificada para testing",
    version="1.0.0"
)

# Configurar CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint raíz
@app.get("/")
def read_root():
    return {
        "message": "SEVA B2B API está funcionando",
        "status": "ok",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API is running",
        "version": "1.0.0"
    }

# Endpoint de información del sistema
@app.get("/info")
def system_info():
    return {
        "python_version": os.sys.version,
        "port": os.getenv("PORT", "8000"),
        "environment": os.getenv("NODE_ENV", "development")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

