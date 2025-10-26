/**
 * Utilidades para manejo de fechas sin problemas de zona horaria
 * 
 * PROBLEMA: Al usar new Date(dateString) con formato YYYY-MM-DD,
 * JavaScript lo interpreta como UTC medianoche, causando que en
 * zonas horarias negativas (ej: Paraguay UTC-3) retroceda 1 día.
 * 
 * SOLUCIÓN: Estas funciones manipulan el string directamente
 * sin crear objetos Date, evitando conversiones de zona horaria.
 */

/**
 * Convierte fecha YYYY-MM-DD a DD/MM/YYYY
 * @param dateStr - Fecha en formato "YYYY-MM-DD"
 * @returns Fecha en formato "DD/MM/YYYY"
 * @example formatDateToDDMMYYYY("2025-11-13") // "13/11/2025"
 */
export const formatDateToDDMMYYYY = (dateStr: string): string => {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-');
    return `${day}/${month}/${year}`;
};

/**
 * Convierte Date object a string YYYY-MM-DD sin conversión UTC
 * @param date - Objeto Date
 * @returns Fecha en formato "YYYY-MM-DD"
 * @example formatDateToYYYYMMDD(new Date()) // "2025-11-13"
 */
export const formatDateToYYYYMMDD = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

/**
 * Formatea fecha YYYY-MM-DD a formato largo en español
 * @param dateStr - Fecha en formato "YYYY-MM-DD"
 * @returns Fecha en formato largo español, ej: "jueves, 13 de noviembre de 2025"
 * @example formatDateSpanishLong("2025-11-13") // "jueves, 13 de noviembre de 2025"
 */
export const formatDateSpanishLong = (dateStr: string): string => {
    if (!dateStr) return '';
    
    const [yearStr, monthStr, dayStr] = dateStr.split('-');
    const year = parseInt(yearStr, 10);
    const month = parseInt(monthStr, 10);
    const day = parseInt(dayStr, 10);
    
    // Crear fecha en hora local (no UTC) agregando 'T00:00:00' para forzar interpretación local
    const date = new Date(year, month - 1, day);
    
    return date.toLocaleDateString('es-ES', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
};

/**
 * Parsea fecha string a Date sin problemas de zona horaria
 * Agrega 'T00:00:00' para forzar interpretación en hora local
 * @param dateStr - Fecha en formato "YYYY-MM-DD"
 * @returns Objeto Date en hora local
 */
export const parseLocalDate = (dateStr: string): Date => {
    if (!dateStr) return new Date();
    
    const [yearStr, monthStr, dayStr] = dateStr.split('-');
    const year = parseInt(yearStr, 10);
    const month = parseInt(monthStr, 10) - 1; // Mes es 0-indexed en Date
    const day = parseInt(dayStr, 10);
    
    return new Date(year, month, day);
};

/**
 * Formatea fecha ISO a DD/MM/YYYY manejando correctamente la zona horaria
 * @param isoString - Fecha en formato ISO (puede incluir hora)
 * @returns Fecha en formato "DD/MM/YYYY"
 * @example formatISODateToDDMMYYYY("2025-11-13T10:00:00Z") // "13/11/2025"
 */
export const formatISODateToDDMMYYYY = (isoString: string): string => {
    if (!isoString) return '';
    
    // Extraer solo la parte de fecha (YYYY-MM-DD)
    const dateOnly = isoString.split('T')[0];
    return formatDateToDDMMYYYY(dateOnly);
};
