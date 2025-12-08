-- Migración: Actualizar estados de verificacion_ruc de masculino a femenino
-- Cambia "aprobado" -> "aprobada" y "rechazado" -> "rechazada" para coincidir con el frontend

UPDATE verificacion_ruc
SET estado = 'aprobada'
WHERE estado = 'aprobado';

UPDATE verificacion_ruc
SET estado = 'rechazada'
WHERE estado = 'rechazado';

-- Verificar que no queden estados antiguos
SELECT estado, COUNT(*) as cantidad
FROM verificacion_ruc
GROUP BY estado;

