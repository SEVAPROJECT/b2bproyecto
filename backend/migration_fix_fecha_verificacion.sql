-- Migración para permitir NULL en fecha_verificacion
-- Ejecutar este script en la base de datos para corregir la estructura

-- Cambiar la columna fecha_verificacion para permitir NULL
ALTER TABLE perfil_empresa ALTER COLUMN fecha_verificacion DROP NOT NULL;

-- Comentario explicativo
COMMENT ON COLUMN perfil_empresa.fecha_verificacion IS 'Fecha cuando el administrador aprobó la verificación. NULL si aún no ha sido verificada.';
