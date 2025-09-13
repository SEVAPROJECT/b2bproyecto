#!/usr/bin/env python3
"""
Script para mostrar la estructura de carpetas en iDrive2
"""

def show_folder_structure():
    """Muestra ejemplos de la estructura de carpetas en iDrive2"""
    
    print("📁 Estructura de Carpetas en iDrive2")
    print("=" * 50)
    
    # Ejemplo 1: Con razón social
    print("\n🎯 Ejemplo 1: Con Razón Social")
    print("✅ Ventajas: Fácil identificación para el admin")
    print("📂 Estructura:")
    print("""
idrive2/
├── Empresa_ABC_S.A./
│   ├── RUC/
│   │   └── 123e4567-e89b-12d3-a456-426614174000.pdf
│   ├── Patente_Municipal/
│   │   └── 987fcdeb-51a2-43d1-b789-123456789abc.pdf
│   └── Contrato_Social/
│       └── abc12345-6789-def0-ghij-klmnopqrstuv.pdf
├── Comercial_XYZ_Ltda./
│   ├── RUC/
│   │   └── def67890-1234-5678-9abc-def012345678.pdf
│   └── Balance_Anual/
│       └── 456789ab-cdef-0123-4567-89abcdef0123.pdf
└── Distribuidora_123_S.R.L./
    ├── RUC/
    │   └── 789cdef0-1234-5678-9abc-def012345678.pdf
    ├── Certificado_de_Antecedentes/
    │   └── 01234567-89ab-cdef-0123-456789abcdef.pdf
    └── Certificaciones_de_Calidad/
        └── fedcba98-7654-3210-fedc-ba9876543210.pdf
""")
    
    # Ejemplo 2: Sin razón social (fallback)
    print("\n🔄 Ejemplo 2: Sin Razón Social (Fallback)")
    print("⚠️  Se usa cuando no hay razón social configurada")
    print("📂 Estructura:")
    print("""
idrive2/
├── user_123/
│   ├── RUC/
│   │   └── 123e4567-e89b-12d3-a456-426614174000.pdf
│   └── Patente_Municipal/
│       └── 987fcdeb-51a2-43d1-b789-123456789abc.pdf
└── user_456/
    ├── RUC/
    │   └── def67890-1234-5678-9abc-def012345678.pdf
    └── Contrato_Social/
        └── abc12345-6789-def0-ghij-klmnopqrstuv.pdf
""")
    
    # Ventajas y desventajas
    print("\n📊 Análisis de Ventajas y Desventajas")
    print("=" * 50)
    
    print("\n✅ VENTAJAS de usar Razón Social:")
    print("   • Admin puede identificar empresas fácilmente")
    print("   • Organización clara por empresa")
    print("   • Fácil navegación en el panel de iDrive2")
    print("   • Mejor experiencia para revisión de documentos")
    
    print("\n⚠️  CONSIDERACIONES:")
    print("   • Nombres de empresa se limpian (espacios → guiones bajos)")
    print("   • Caracteres especiales se reemplazan")
    print("   • Fallback a user_id si no hay razón social")
    print("   • URLs más largas pero más descriptivas")
    
    print("\n🎯 RECOMENDACIÓN:")
    print("   ✅ Usar razón social como carpeta principal")
    print("   ✅ Mantener user_id como fallback")
    print("   ✅ Estructura: {razon_social}/{tipo_documento}/{archivo}")

if __name__ == "__main__":
    show_folder_structure()
