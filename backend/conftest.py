#!/usr/bin/env python3
"""
Configuración de pytest para el proyecto SEVA B2B
"""
import sys
import os
from pathlib import Path

# Agregar el directorio actual al PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configuración adicional de pytest
import pytest

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configuración automática para todas las pruebas"""
    # Asegurar que el PYTHONPATH esté configurado
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
