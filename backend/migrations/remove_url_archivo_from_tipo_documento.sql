-- Script para eliminar la columna url_archivo de la tabla tipo_documento
-- Ejecutar directamente en Supabase SQL Editor

ALTER TABLE tipo_documento 
DROP COLUMN url_archivo;
