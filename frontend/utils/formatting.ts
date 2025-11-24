import { BackendService } from '../types';
import { API_CONFIG } from '../config/api';

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
 * Obtiene la moneda del servicio basándose en id_moneda o codigo_iso_moneda
 */
export const getServiceCurrency = (service: BackendService): string => {
    // Primero intentar mapear por ID de moneda (más confiable)
    if (service.id_moneda) {
        switch (service.id_moneda) {
            case 1:
                return 'GS';
            case 2:
                return 'USD';
            case 3:
                return 'BRL';
            case 4:
            case 8:
                return 'ARS';
            default:
                return 'GS';
        }
    }

    // Si no hay ID de moneda, intentar usar código ISO si está disponible
    const serviceWithIso = service as BackendService & { codigo_iso_moneda?: string };
    if (serviceWithIso.codigo_iso_moneda) {
        return serviceWithIso.codigo_iso_moneda.trim();
    }

    // Si hay moneda en el servicio (legacy), usarla
    if (service.moneda) {
        return service.moneda;
    }

    // Si aún no hay moneda, asumir Guaraní
    return 'GS';
};

/**
 * Obtiene el símbolo de moneda basado en el código de moneda
 */
export const getCurrencySymbol = (currency: string): string => {
    return getCurrencySymbolFromCode(currency);
};

/**
 * Formatea el precio según la moneda
 */
export const formatPriceByCurrency = (price: number, currency: string): string => {
    const symbol = getCurrencySymbol(currency);
    if (currency === 'USD') {
        return `${symbol} ${price.toLocaleString('en-US')}`;
    }
    if (currency === 'BRL') {
        return `${symbol} ${price.toLocaleString('pt-BR')}`;
    }
    if (currency === 'ARS') {
        return `${symbol} ${price.toLocaleString('es-AR')}`;
    }
    return `${symbol} ${price.toLocaleString('es-PY')}`;
};

/**
 * Formatea el precio de un servicio según su moneda (función unificada)
 */
export const formatPriceProfessional = (price: number, service: BackendService): string => {
    const serviceCurrency = getServiceCurrency(service);
    return formatPriceByCurrency(price, serviceCurrency);
};

/**
 * Obtiene el símbolo de moneda basado en el servicio (alias para compatibilidad)
 */
export const getCurrencySymbolFromService = (service: BackendService): string => {
    const currency = getServiceCurrency(service);
    return getCurrencySymbol(currency);
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

/**
 * Obtiene la URL completa de una imagen del servicio
 */
export const getServiceImageUrl = (imagePath: string | null): string | null => {
    if (!imagePath) return null;
    
    // Si es una URL completa (Supabase Storage o iDrive), usarla directamente
    if (imagePath.startsWith('http')) {
        return imagePath;
    }
    
    // Si es una ruta local, construir URL completa
    const baseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
    return `${baseUrl}${imagePath}`;
};
