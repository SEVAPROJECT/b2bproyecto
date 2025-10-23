-- Triggers para sincronización automática con Weaviate
-- Ejecutar estos scripts en la base de datos

-- 1. Función para notificar cambios en servicios
CREATE OR REPLACE FUNCTION notify_weaviate_sync()
RETURNS TRIGGER AS $$
BEGIN
    -- Enviar notificación a la aplicación para sincronizar con Weaviate
    PERFORM pg_notify('weaviate_sync', json_build_object(
        'action', TG_OP,
        'id_servicio', COALESCE(NEW.id_servicio, OLD.id_servicio),
        'timestamp', NOW()
    )::text);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger para INSERT de servicios
CREATE TRIGGER trigger_servicio_insert
    AFTER INSERT ON servicio
    FOR EACH ROW
    EXECUTE FUNCTION notify_weaviate_sync();

-- 3. Trigger para UPDATE de servicios
CREATE TRIGGER trigger_servicio_update
    AFTER UPDATE ON servicio
    FOR EACH ROW
    WHEN (OLD.estado IS DISTINCT FROM NEW.estado 
          OR OLD.nombre IS DISTINCT FROM NEW.nombre 
          OR OLD.descripcion IS DISTINCT FROM NEW.descripcion)
    EXECUTE FUNCTION notify_weaviate_sync();

-- 4. Trigger para DELETE de servicios
CREATE TRIGGER trigger_servicio_delete
    AFTER DELETE ON servicio
    FOR EACH ROW
    EXECUTE FUNCTION notify_weaviate_sync();
