import { useMemo } from 'react';
import {
  formatDateToDDMMYYYY,
  formatDateToYYYYMMDD,
  formatISODateToDDMMYYYY,
  parseLocalDate
} from '../utils/dateUtils';

/**
 * Hook personalizado para manejo de fechas con zona horaria GMT-3 (Paraguay)
 * Actualizado para usar las nuevas funciones que evitan problemas de conversión UTC
 */
export const useDateUtils = () => {
  const dateUtils = useMemo(() => ({
    /**
     * Convierte una fecha YYYY-MM-DD a DD/MM/YYYY sin conversión UTC
     */
    convertUTCToParaguay: (date: string | Date) => {
      if (typeof date === 'string') {
        return formatISODateToDDMMYYYY(date);
      }
      return formatDateToDDMMYYYY(formatDateToYYYYMMDD(date));
    },
    
    /**
     * Convierte una fecha a formato DD/MM/YYYY
     */
    convertUTCToParaguayDate: (date: string | Date) => {
      if (typeof date === 'string') {
        // Si es formato ISO (YYYY-MM-DD o con hora)
        if (date.includes('-')) {
          return formatISODateToDDMMYYYY(date);
        }
        return date;
      }
      return formatDateToDDMMYYYY(formatDateToYYYYMMDD(date));
    },
    
    /**
     * Extrae la hora de un string de fecha
     */
    convertUTCToParaguayTime: (date: string | Date) => {
      if (typeof date === 'string') {
        // Si tiene formato ISO con hora (YYYY-MM-DDTHH:MM:SS)
        if (date.includes('T')) {
          const timePart = date.split('T')[1];
          return timePart ? timePart.substring(0, 8) : '00:00:00';
        }
        return '00:00:00';
      }
      const d = date instanceof Date ? date : new Date(date);
      return d.toTimeString().substring(0, 8);
    },
    
    /**
     * Formatea una fecha en formato completo de fecha y hora
     */
    formatParaguayDateTime: (date: string | Date) => {
      if (typeof date === 'string') {
        const dateOnly = date.split('T')[0];
        const timeOnly = date.includes('T') ? date.split('T')[1].substring(0, 5) : '00:00';
        return `${formatDateToDDMMYYYY(dateOnly)} ${timeOnly}`;
      }
      const dateStr = formatDateToYYYYMMDD(date);
      const timeStr = date.toTimeString().substring(0, 5);
      return `${formatDateToDDMMYYYY(dateStr)} ${timeStr}`;
    },
    
    /**
     * Formatea una fecha en formato de fecha para Paraguay
     */
    formatParaguayDate: (date: string | Date) => {
      if (typeof date === 'string') {
        return formatISODateToDDMMYYYY(date);
      }
      return formatDateToDDMMYYYY(formatDateToYYYYMMDD(date));
    },
    
    /**
     * Obtiene la fecha y hora actual en GMT-3 (Paraguay)
     */
    getCurrentParaguayTime: () => {
      const now = new Date();
      return formatDateToDDMMYYYY(formatDateToYYYYMMDD(now)) + ' ' + now.toTimeString().substring(0, 8);
    },
    
    /**
     * Obtiene información sobre la zona horaria configurada
     */
    getTimezoneInfo: () => ({
      timezone: 'America/Asuncion',
      offset: 'GMT-3',
      name: 'Paraguay Standard Time'
    }),
    
    /**
     * Verifica si una fecha es válida
     */
    isValidDate: (date: string | Date | null | undefined): boolean => {
      if (!date) return false;
      if (typeof date === 'string') {
        // Validar formato YYYY-MM-DD o ISO
        if (/^\d{4}-\d{2}-\d{2}/.test(date)) {
          const d = parseLocalDate(date.split('T')[0]);
          return !Number.isNaN(d.getTime());
        }
        return false;
      }
      return date instanceof Date && !Number.isNaN(date.getTime());
    }
  }), []);

  return dateUtils;
};

/**
 * Hook para formatear fechas específicas
 * @param utcDate - Fecha en UTC o formato YYYY-MM-DD
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
