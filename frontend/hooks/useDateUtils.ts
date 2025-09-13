import { useMemo } from 'react';
import {
  convertUTCToParaguay,
  convertUTCToParaguayDate,
  convertUTCToParaguayTime,
  formatParaguayDateTime,
  formatParaguayDate,
  getCurrentParaguayTime,
  getTimezoneInfo,
  isValidDate
} from '../utils/dateUtils';

/**
 * Hook personalizado para manejo de fechas con zona horaria GMT-3 (Paraguay)
 */
export const useDateUtils = () => {
  const dateUtils = useMemo(() => ({
    /**
     * Convierte una fecha UTC a zona horaria GMT-3 (Paraguay)
     */
    convertUTCToParaguay,
    
    /**
     * Convierte una fecha UTC a formato de fecha solamente (DD/MM/YYYY)
     */
    convertUTCToParaguayDate,
    
    /**
     * Convierte una fecha UTC a formato de hora solamente (HH:MM:SS)
     */
    convertUTCToParaguayTime,
    
    /**
     * Formatea una fecha en formato legible para Paraguay
     */
    formatParaguayDateTime,
    
    /**
     * Formatea una fecha en formato de fecha para Paraguay
     */
    formatParaguayDate,
    
    /**
     * Obtiene la fecha y hora actual en GMT-3 (Paraguay)
     */
    getCurrentParaguayTime,
    
    /**
     * Obtiene información sobre la zona horaria configurada
     */
    getTimezoneInfo,
    
    /**
     * Verifica si una fecha es válida
     */
    isValidDate
  }), []);

  return dateUtils;
};

/**
 * Hook para formatear fechas específicas
 * @param utcDate - Fecha en UTC
 * @returns Objeto con fechas formateadas
 */
export const useFormattedDate = (utcDate: string | Date | null | undefined) => {
  const { convertUTCToParaguay, convertUTCToParaguayDate, convertUTCToParaguayTime, isValidDate } = useDateUtils();

  return useMemo(() => {
    if (!utcDate || !isValidDate(utcDate)) {
      return {
        fullDateTime: 'Fecha inválida',
        dateOnly: 'Fecha inválida',
        timeOnly: 'Hora inválida',
        isValid: false
      };
    }

    return {
      fullDateTime: convertUTCToParaguay(utcDate),
      dateOnly: convertUTCToParaguayDate(utcDate),
      timeOnly: convertUTCToParaguayTime(utcDate),
      isValid: true
    };
  }, [utcDate, convertUTCToParaguay, convertUTCToParaguayDate, convertUTCToParaguayTime, isValidDate]);
};
