-- Script para crear tipos de documentos básicos
-- Ejecutar directamente en Supabase SQL Editor

-- Insertar tipos de documentos básicos si no existen
INSERT INTO tipo_documento (id_tip_documento, tipo_documento, es_requerido) VALUES
(1, 'RUC', true),
(2, 'Patente Municipal', true),
(3, 'Contrato Social', true),
(4, 'Balance Financiero', false),
(5, 'Certificado de Calidad', false),
(6, 'Certificaciones del Rubro', false),
(7, 'Otros Documentos', false)
ON CONFLICT (id_tip_documento) DO NOTHING;
