# app/api/v1/routers/providers/utils.py
"""
Utilidades compartidas para el módulo de proveedores (Capa de Presentación).

NOTA: Las validaciones de negocio se movieron a la Capa de Lógica de Negocio (Services).
Este archivo se mantiene para utilidades específicas de la capa de presentación si son necesarias.
"""

# Las funciones de validación se movieron a VerificationService en la capa de servicios
# para seguir el principio de Arquitectura de Capas:
# - Router (Presentación): Solo maneja HTTP, valida formato básico (FastAPI lo hace automáticamente)
# - Service (Negocio): Contiene todas las validaciones de negocio y lógica
# - Repository (Datos): Solo acceso a datos

