import { BackendService } from '../types';

/**
 * Obtiene el símbolo de moneda basado en el código de moneda
 */
const getCurrencySymbolFromCode = (currencyCode: string): string => {
    if (currencyCode === 'USD') return '$';
    if (currencyCode === 'BRL') return 'R$';
    if (currencyCode === 'ARS') return '$';
    return '₲';
};

/**
 * Formatea el precio de un servicio según su moneda
 */
export const formatPriceProfessional = (price: number, service: BackendService): string => {
    const currencySymbol = getCurrencySymbolFromCode(service.moneda);
    
    if (service.moneda === 'USD') {
        return `${currencySymbol} ${price.toLocaleString('en-US')}`;
    } else if (service.moneda === 'BRL') {
        return `${currencySymbol} ${price.toLocaleString('pt-BR')}`;
    } else if (service.moneda === 'ARS') {
        return `${currencySymbol} ${price.toLocaleString('es-AR')}`;
    } else {
        return `${currencySymbol} ${price.toLocaleString('es-PY')}`;
    }
};

/**
 * Obtiene el símbolo de moneda basado en el ID o código ISO
 */
export const getCurrencySymbol = (service: BackendService): string => {
    return getCurrencySymbolFromCode(service.moneda);
};

/**
 * Formatea una fecha a formato corto local
 */
export const formatDateShortLocal = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-PY', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
};

/**
 * Obtiene la fecha de hoy en formato ISO string
 */
export const getTodayDateString = (): string => {
    return new Date().toISOString().split('T')[0];
};

/**
 * Calcula el tiempo transcurrido desde una fecha
 */
export const getTimeAgo = (dateString: string): string => {
    const now = new Date();
    const publishDate = new Date(dateString);
    const diffInMs = now.getTime() - publishDate.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'hoy';
    if (diffInDays === 1) return 'hace 1 día';
    if (diffInDays < 7) return `hace ${diffInDays} días`;
    if (diffInDays < 30) {
        const weeks = Math.floor(diffInDays / 7);
        return weeks === 1 ? 'hace 1 semana' : `hace ${weeks} semanas`;
    }
    if (diffInDays < 365) {
        const months = Math.floor(diffInDays / 30);
        return months === 1 ? 'hace 1 mes' : `hace ${months} meses`;
    }
    const years = Math.floor(diffInDays / 365);
    return years === 1 ? 'hace 1 año' : `hace ${years} años`;
};
