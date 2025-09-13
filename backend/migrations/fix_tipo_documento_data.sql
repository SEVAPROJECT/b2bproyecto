-- Script para verificar y corregir los datos de tipo_documento
-- Ejecutar directamente en Supabase SQL Editor

-- 1. Primero, ver qué datos existen actualmente
SELECT 'Datos actuales en tipo_documento:' as info;
SELECT id_tip_documento, tipo_documento, es_requerido, created_at 
FROM tipo_documento 
ORDER BY id_tip_documento;

-- 2. Si no hay datos, insertar los tipos básicos
INSERT INTO tipo_documento (tipo_documento, es_requerido) VALUES
('RUC', true),
('Patente Municipal', true),
('Contrato Social', true),
('Balance Anual', false),
('Certificado de Antecedentes', false),
('Certificaciones de Calidad', false),
('Certificados del Rubro', false)
ON CONFLICT (tipo_documento) DO NOTHING;

-- 3. Verificar los datos después de la inserción
SELECT 'Datos después de la corrección:' as info;
SELECT id_tip_documento, tipo_documento, es_requerido, created_at 
FROM tipo_documento 
ORDER BY id_tip_documento;
