// Configuración centralizada de la API
const getApiBaseUrl = (): string => {
    // Si estamos en Railway (producción), usar la URL del backend de Railway
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        // En Railway, cada servicio tiene su propia URL
        // Usar variable de entorno o URL hardcodeada temporalmente
        const backendUrl = (import.meta as any).env?.VITE_BACKEND_HOST || 'https://backend-production-249d.up.railway.app';
        return `${backendUrl}/api/v1`;
    }
    
    // En desarrollo local
    return 'http://localhost:8000/api/v1';
};

export const API_CONFIG = {
    // URL base de la API - detecta automáticamente el entorno
    BASE_URL: getApiBaseUrl(),
    
    // Endpoints de autenticación
    AUTH: {
        LOGIN: '/auth/signin',
        REGISTER: '/auth/signup',
        ME: '/auth/me',
        REFRESH: '/auth/refresh',
        LOGOUT: '/auth/logout',
        RESET_PASSWORD: '/auth/reset-password',
        VERIFICATION_STATUS: '/auth/verificacion-estado',
    },
    
    // Endpoints de administración
    ADMIN: {
        USERS: '/admin/users',
        ROLES: '/admin/roles',
        VERIFICATIONS: '/admin/verificaciones/pendientes',
        CATEGORIES: '/admin/categories',
        SERVICE_REQUESTS: '/admin/service-requests',
        DASHBOARD_STATS: '/admin/stats/dashboard/stats',
        REPORTS: {
            PROVIDERS_VERIFIED: '/admin/reports/proveedores-verificados',
        },
    },
    
    // Endpoints de proveedores
    PROVIDERS: {
        SERVICES: '/provider/services',
        UPLOAD_IMAGE: '/provider/services/upload-image',
        VERIFICATION: '/providers/solicitar-verificacion',
        DIAGNOSTIC: '/providers/diagnostic/storage',
    },
    
    // Endpoints de servicios
    SERVICES: {
        LIST: '/services/list',
        UNIFIED: '/services/services', // Endpoint unificado que reemplaza with-providers y filtered
        BY_CATEGORY: '/services/by-category',
    },
    
    // Endpoints de categorías
    CATEGORIES: {
        LIST: '/categories/',
        CREATE: '/categories/',
        UPDATE: '/categories/',
    },
    
    // Endpoints de ubicaciones
    LOCATIONS: {
        DEPARTMENTS: '/locations/departamentos',
        CITIES: '/locations/ciudades',
        NEIGHBORHOODS: '/locations/barrios',
    },
};

// Función helper para construir URLs completas
export const buildApiUrl = (endpoint: string): string => {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Función helper para obtener headers de autenticación
export const getAuthHeaders = (): Record<string, string> => {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

// Función helper para obtener headers con JSON
export const getJsonHeaders = (): Record<string, string> => {
    return {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
    };
};
