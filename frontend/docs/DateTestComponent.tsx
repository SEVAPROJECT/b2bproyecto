import React, { useState, useEffect } from 'react';
import { useDateUtils, useFormattedDate } from '../hooks/useDateUtils';

/**
 * Componente de prueba para verificar el funcionamiento de las utilidades de fecha
 */
const DateTestComponent: React.FC = () => {
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const dateUtils = useDateUtils();
  
  // Fecha de ejemplo desde el backend (UTC)
  const exampleUTCDate = "2025-09-10T23:41:11.726157+00:00";
  const formattedExample = useFormattedDate(exampleUTCDate);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const timezoneInfo = dateUtils.getTimezoneInfo();

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">
        🕐 Prueba de Utilidades de Fecha - GMT-3 (Paraguay)
      </h2>

      {/* Información de zona horaria */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-blue-800">
          📍 Información de Zona Horaria
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p><strong>Zona horaria:</strong> {timezoneInfo.timezone}</p>
            <p><strong>País:</strong> {timezoneInfo.country}</p>
            <p><strong>Offset:</strong> {timezoneInfo.offset_hours} horas</p>
          </div>
          <div>
            <p><strong>Hora actual:</strong> {timezoneInfo.current_time}</p>
            <p><strong>Fecha actual:</strong> {timezoneInfo.current_date}</p>
          </div>
        </div>
      </div>

      {/* Reloj en tiempo real */}
      <div className="mb-6 p-4 bg-green-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-green-800">
          ⏰ Reloj en Tiempo Real (GMT-3)
        </h3>
        <div className="text-2xl font-mono text-green-700">
          {dateUtils.formatParaguayDateTime(currentTime)}
        </div>
      </div>

      {/* Prueba de conversión de fecha UTC */}
      <div className="mb-6 p-4 bg-yellow-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-yellow-800">
          🔄 Prueba de Conversión UTC → GMT-3
        </h3>
        <div className="space-y-2">
          <p><strong>Fecha UTC original:</strong> {exampleUTCDate}</p>
          <p><strong>Fecha y hora convertida:</strong> {formattedExample.fullDateTime}</p>
          <p><strong>Solo fecha:</strong> {formattedExample.dateOnly}</p>
          <p><strong>Solo hora:</strong> {formattedExample.timeOnly}</p>
          <p><strong>¿Es válida?</strong> {formattedExample.isValid ? '✅ Sí' : '❌ No'}</p>
        </div>
      </div>

      {/* Pruebas con diferentes formatos */}
      <div className="mb-6 p-4 bg-purple-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-purple-800">
          🧪 Pruebas con Diferentes Formatos
        </h3>
        <div className="space-y-2">
          <p><strong>Fecha actual (GMT-3):</strong> {dateUtils.formatParaguayDateTime(new Date())}</p>
          <p><strong>Solo fecha actual:</strong> {dateUtils.formatParaguayDate(new Date())}</p>
          <p><strong>Fecha inválida:</strong> {dateUtils.formatParaguayDateTime('fecha-invalida')}</p>
        </div>
      </div>

      {/* Instrucciones de uso */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-gray-800">
          📖 Instrucciones de Uso
        </h3>
        <div className="text-sm text-gray-600 space-y-1">
          <p>• Las fechas del backend vienen en UTC</p>
          <p>• Usar <code>useFormattedDate()</code> para convertir automáticamente</p>
          <p>• Usar <code>useDateUtils()</code> para funciones específicas</p>
          <p>• Todas las fechas se muestran en GMT-3 (Paraguay)</p>
        </div>
      </div>
    </div>
  );
};

export default DateTestComponent;
