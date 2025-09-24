/**
 * Obtiene la URL base de la API desde las variables de entorno
 */
export const getApiBaseUrl = (): string => {
    return (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
};

/**
 * Construye la URL completa para una imagen
 */
export const getImageUrl = (imagePath: string | null): string | null => {
    if (!imagePath) return null;
    
    // Si ya es una URL completa (iDrive), usarla directamente
    if (imagePath.startsWith('http')) {
        return imagePath;
    }
    
    // Si es una ruta local, construir URL completa
    const baseUrl = getApiBaseUrl();
    return `${baseUrl}${imagePath}`;
};

/**
 * Maneja errores de API de forma consistente
 */
export const handleApiError = (error: any, defaultMessage: string = 'Error en la operación'): string => {
    console.error('API Error:', error);
    
    if (error?.response?.data?.message) {
        return error.response.data.message;
    }
    
    if (error?.message) {
        return error.message;
    }
    
    return defaultMessage;
};

/**
 * Valida si una respuesta de API es exitosa
 */
export const isApiResponseSuccess = (response: any): boolean => {
    return response && (response.status === 200 || response.status === 201);
};
