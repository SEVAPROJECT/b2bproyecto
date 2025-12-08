-- Migración: Agregar token_correccion y token_expiracion a verificacion_ruc
-- Estas columnas permiten que usuarios con RUC rechazado puedan corregir sin volver a cargar todos sus datos

ALTER TABLE verificacion_ruc 
ADD COLUMN IF NOT EXISTS token_correccion VARCHAR(100) UNIQUE,
ADD COLUMN IF NOT EXISTS token_expiracion TIMESTAMP WITH TIME ZONE;

-- Crear índice para búsquedas rápidas por token
CREATE INDEX IF NOT EXISTS idx_verificacion_ruc_token_correccion ON verificacion_ruc(token_correccion);

-- Comentarios
COMMENT ON COLUMN verificacion_ruc.token_correccion IS 'Token único para permitir corrección de RUC rechazado sin reingresar todos los datos';
COMMENT ON COLUMN verificacion_ruc.token_expiracion IS 'Fecha de expiración del token de corrección (30 días desde el rechazo)';

