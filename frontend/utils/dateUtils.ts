/**
 * Utilidades para manejo de fechas con zona horaria GMT-3 (Paraguay)
 */

/**
 * Convierte una fecha UTC a zona horaria GMT-3 (Paraguay)
 * @param utcDate - Fecha en UTC (string o Date)
 * @returns Fecha en GMT-3 como string formateado
 */
export const convertUTCToParaguay = (utcDate: string | Date): string => {
  try {
    const date = typeof utcDate === 'string' ? new Date(utcDate) : utcDate;
    
    // Verificar si la fecha ya está en UTC-3 comparando con la hora local
    const now = new Date();
    const dateOffset = date.getTimezoneOffset();
    const nowOffset = now.getTimezoneOffset();
    
    // Si la fecha viene del backend y ya está en UTC-3, no restar horas
    // Solo formatear la fecha tal como viene
    let displayDate = date;
    
    // Solo convertir si la fecha viene en UTC puro (sin offset)
    if (dateOffset === 0 && nowOffset !== 0) {
      // La fecha viene en UTC, convertir a UTC-3
      displayDate = new Date(date.getTime() - (3 * 60 * 60 * 1000));
    }
    
    // Formatear manualmente para evitar problemas de timezone
    const day = displayDate.getDate().toString().padStart(2, '0');
    const month = (displayDate.getMonth() + 1).toString().padStart(2, '0');
    const year = displayDate.getFullYear();
    const hours = displayDate.getHours().toString().padStart(2, '0');
    const minutes = displayDate.getMinutes().toString().padStart(2, '0');
    const seconds = displayDate.getSeconds().toString().padStart(2, '0');
    
    return `${day}/${month}/${year}, ${hours}:${minutes}:${seconds}`;
  } catch (error) {
    console.error('Error convirtiendo fecha UTC a Paraguay:', error);
    return 'Fecha inválida';
  }
};

/**
 * Convierte una fecha UTC a formato de fecha solamente (DD/MM/YYYY)
 * @param utcDate - Fecha en UTC (string o Date)
 * @returns Fecha en formato DD/MM/YYYY
 */
export const convertUTCToParaguayDate = (utcDate: string | Date): string => {
  try {
    const date = typeof utcDate === 'string' ? new Date(utcDate) : utcDate;
    
    const paraguayTime = new Date(date.getTime() - (3 * 60 * 60 * 1000));
    
    // Formatear manualmente para evitar problemas de timezone
    const day = paraguayTime.getDate().toString().padStart(2, '0');
    const month = (paraguayTime.getMonth() + 1).toString().padStart(2, '0');
    const year = paraguayTime.getFullYear();
    
    return `${day}/${month}/${year}`;
  } catch (error) {
    console.error('Error convirtiendo fecha UTC a Paraguay:', error);
    return 'Fecha inválida';
  }
};

/**
 * Convierte una fecha UTC a formato de hora solamente (HH:MM:SS)
 * @param utcDate - Fecha en UTC (string o Date)
 * @returns Hora en formato HH:MM:SS
 */
export const convertUTCToParaguayTime = (utcDate: string | Date): string => {
  try {
    const date = typeof utcDate === 'string' ? new Date(utcDate) : utcDate;
    
    const paraguayTime = new Date(date.getTime() - (3 * 60 * 60 * 1000));
    
    // Formatear manualmente para evitar problemas de timezone
    const hours = paraguayTime.getHours().toString().padStart(2, '0');
    const minutes = paraguayTime.getMinutes().toString().padStart(2, '0');
    const seconds = paraguayTime.getSeconds().toString().padStart(2, '0');
    
    return `${hours}:${minutes}:${seconds}`;
  } catch (error) {
    console.error('Error convirtiendo hora UTC a Paraguay:', error);
    return 'Hora inválida';
  }
};

/**
 * Obtiene la fecha y hora actual en GMT-3 (Paraguay)
 * @returns Fecha actual en GMT-3
 */
export const getCurrentParaguayTime = (): Date => {
  const now = new Date();
  return new Date(now.getTime() - (3 * 60 * 60 * 1000));
};

/**
 * Formatea una fecha en formato legible para Paraguay
 * @param utcDate - Fecha en UTC (string o Date)
 * @returns Fecha formateada como "DD/MM/YYYY HH:MM:SS"
 */
export const formatParaguayDateTime = (utcDate: string | Date): string => {
  return convertUTCToParaguay(utcDate);
};

/**
 * Formatea una fecha en formato de fecha para Paraguay
 * @param utcDate - Fecha en UTC (string o Date)
 * @returns Fecha formateada como "DD/MM/YYYY"
 */
export const formatParaguayDate = (utcDate: string | Date): string => {
  return convertUTCToParaguayDate(utcDate);
};

/**
 * Verifica si una fecha es válida
 * @param date - Fecha a verificar
 * @returns true si la fecha es válida
 */
export const isValidDate = (date: string | Date): boolean => {
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    return !isNaN(d.getTime());
  } catch {
    return false;
  }
};

/**
 * Obtiene información sobre la zona horaria configurada
 * @returns Información de la zona horaria
 */
export const getTimezoneInfo = () => {
  const now = getCurrentParaguayTime();
  return {
    timezone: 'GMT-3',
    country: 'Paraguay',
    offset_hours: -3,
    current_time: formatParaguayDateTime(now),
    current_date: formatParaguayDate(now),
    iso_format: now.toISOString()
  };
};
