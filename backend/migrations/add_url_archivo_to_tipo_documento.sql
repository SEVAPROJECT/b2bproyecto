-- Script para agregar la columna url_archivo a la tabla tipo_documento
-- Ejecutar directamente en Supabase SQL Editor

ALTER TABLE tipo_documento 
ADD COLUMN url_archivo VARCHAR(500) NOT NULL DEFAULT 'temp://pending';

-- Comentario para la columna
COMMENT ON COLUMN tipo_documento.url_archivo IS 'URL del archivo subido (iDrive, local, etc.)';
