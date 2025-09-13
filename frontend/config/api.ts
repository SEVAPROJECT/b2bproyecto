// Configuración centralizada de la API
export const API_CONFIG = {
    // URL base de la API - puede ser configurada por variables de entorno
    BASE_URL: (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000',
    
    // Endpoints de autenticación
    AUTH: {
        LOGIN: '/api/v1/auth/login',
        REGISTER: '/api/v1/auth/register',
        ME: '/api/v1/auth/me',
        REFRESH: '/api/v1/auth/refresh',
        LOGOUT: '/api/v1/auth/logout',
    },
    
    // Endpoints de administración
    ADMIN: {
        USERS: '/api/v1/admin/users',
        ROLES: '/api/v1/admin/roles',
        VERIFICATIONS: '/api/v1/admin/verificaciones/pendientes',
        CATEGORIES: '/api/v1/admin/categories',
        SERVICE_REQUESTS: '/api/v1/admin/service-requests',
    },
    
    // Endpoints de proveedores
    PROVIDERS: {
        SERVICES: '/api/v1/provider/services',
        UPLOAD_IMAGE: '/api/v1/provider/services/upload-image',
        VERIFICATION: '/api/v1/providers/solicitar-verificacion',
        DIAGNOSTIC: '/api/v1/providers/diagnostic/storage',
    },
    
    // Endpoints de servicios
    SERVICES: {
        LIST: '/api/v1/services/list',
        WITH_PROVIDERS: '/api/v1/services/with-providers',
        BY_CATEGORY: '/api/v1/services/by-category',
    },
    
    // Endpoints de categorías
    CATEGORIES: {
        LIST: '/api/v1/categories/',
        CREATE: '/api/v1/categories/',
        UPDATE: '/api/v1/categories/',
    },
    
    // Endpoints de ubicaciones
    LOCATIONS: {
        DEPARTMENTS: '/api/v1/locations/departamentos',
        CITIES: '/api/v1/locations/ciudades',
        NEIGHBORHOODS: '/api/v1/locations/barrios',
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
