-- Script para crear tipos de documentos con IDs específicos
-- Ejecutar directamente en Supabase SQL Editor

-- Primero, verificar si la secuencia necesita ser ajustada
SELECT setval('tipo_documento_id_tip_documento_seq', (SELECT COALESCE(MAX(id_tip_documento), 0) FROM tipo_documento));

-- Insertar tipos de documentos con IDs específicos
INSERT INTO tipo_documento (id_tip_documento, tipo_documento, es_requerido) VALUES
(1, 'RUC', true),
(2, 'Patente Municipal', true),
(3, 'Contrato Social', true)
ON CONFLICT (id_tip_documento) DO UPDATE SET
    tipo_documento = EXCLUDED.tipo_documento,
    es_requerido = EXCLUDED.es_requerido;
