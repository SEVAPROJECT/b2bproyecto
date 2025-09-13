-- ============================================================================
-- MIGRACIÓN MANUAL: Agregar columna id_categoria a solicitud_servicio
-- ============================================================================
-- Ejecuta este archivo SQL directamente en tu base de datos PostgreSQL
-- ============================================================================

-- 1. Agregar la columna id_categoria (si no existe)
ALTER TABLE solicitud_servicio ADD COLUMN IF NOT EXISTS id_categoria BIGINT;

-- 2. Agregar la restricción de clave foránea (solo si no existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'solicitud_servicio_id_categoria_fkey'
    ) THEN
        ALTER TABLE solicitud_servicio
        ADD CONSTRAINT solicitud_servicio_id_categoria_fkey
        FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)
        ON DELETE SET NULL;
        RAISE NOTICE 'Clave foránea agregada exitosamente';
    ELSE
        RAISE NOTICE 'La clave foránea ya existe';
    END IF;
END $$;

-- 3. Crear índice para mejorar rendimiento (si no existe)
CREATE INDEX IF NOT EXISTS idx_solicitud_servicio_id_categoria
ON solicitud_servicio(id_categoria);

-- 4. Agregar comentario a la columna
COMMENT ON COLUMN solicitud_servicio.id_categoria IS 'Referencia a la categoría del servicio solicitado';

-- ============================================================================
-- VERIFICACIÓN: Ejecuta estas consultas para verificar que todo esté correcto
-- ============================================================================

-- Verificar que la columna existe
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'solicitud_servicio' AND column_name = 'id_categoria';

-- Verificar la clave foránea
-- SELECT
--     tc.constraint_name,
--     tc.table_name,
--     kcu.column_name,
--     ccu.table_name AS referenced_table,
--     ccu.column_name AS referenced_column
-- FROM information_schema.table_constraints tc
-- JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
-- JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
-- WHERE tc.constraint_type = 'FOREIGN KEY'
--     AND tc.table_name = 'solicitud_servicio'
--     AND kcu.column_name = 'id_categoria';

-- Verificar el índice
-- SELECT indexname, tablename, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'solicitud_servicio' AND indexname = 'idx_solicitud_servicio_id_categoria';

-- ============================================================================
-- ¡MIGRACIÓN COMPLETADA!
-- ============================================================================
-- Después de ejecutar este archivo, podrás:
-- ✅ Enviar solicitudes de nuevos servicios
-- ✅ Gestionar categorías sin errores
-- ✅ Ver servicios por categoría

