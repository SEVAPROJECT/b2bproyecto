import { useAuth } from '../contexts/AuthContext';

interface ApiRequestOptions extends RequestInit {
    url: string;
}

export const useApiWithAuth = () => {
    const { user, refreshToken } = useAuth();

    // Función helper para construir los headers de la petición
    const buildHeaders = (token: string | undefined, customHeaders?: HeadersInit): HeadersInit => {
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...customHeaders,
        };
    };

    // Función helper para realizar la petición fetch
    const performFetch = async (url: string, fetchOptions: RequestInit, token: string | undefined): Promise<Response> => {
        return await fetch(url, {
            ...fetchOptions,
            headers: buildHeaders(token, fetchOptions.headers),
        });
    };

    // Función helper para verificar si es un error 500 del servidor
    const isServerError = (error: unknown): boolean => {
        if (!(error instanceof Error)) {
            return false;
        }
        return error.message.includes('500') || 
               error.message.includes('Error temporal del servidor') ||
               error.message.includes('Error interno del servidor');
    };

    // Función helper para reintentar con el token actual
    const retryWithCurrentToken = async (
        url: string,
        fetchOptions: RequestInit,
        currentToken: string | undefined
    ): Promise<Response> => {
        try {
            const response = await performFetch(url, fetchOptions, currentToken);
            console.log('✅ Petición reintentada con token actual');
            return response;
        } catch (retryError) {
            console.error('❌ Error en reintento:', retryError);
            throw new Error('Error temporal del servidor. Por favor, intenta nuevamente.');
        }
    };

    // Función helper para manejar el error 401 y renovar el token
    const handle401Error = async (
        url: string,
        fetchOptions: RequestInit
    ): Promise<Response> => {
        console.log('🔄 Token expirado, intentando renovar...');
        console.log('🔍 Refresh token disponible:', localStorage.getItem('refresh_token') ? 'SÍ' : 'NO');
        
        try {
            const newToken = await refreshToken();
            console.log('✅ Token renovado, reintentando petición...');
            return await performFetch(url, fetchOptions, newToken);
        } catch (refreshError) {
            console.error('❌ Error al renovar token:', refreshError);
            console.log('🔍 Refresh token en localStorage:', localStorage.getItem('refresh_token'));
            
            // Manejar errores 500 del servidor sin hacer logout
            if (isServerError(refreshError)) {
                console.log('⚠️ Error 500 en refresh, manteniendo sesión y reintentando con token actual');
                return await retryWithCurrentToken(url, fetchOptions, user?.accessToken);
            }
            
            // Solo hacer logout en errores de autenticación reales (no 500)
            throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
        }
    };

    const apiRequest = async (options: ApiRequestOptions) => {
        const { url, ...fetchOptions } = options;
        
        // Primera petición
        let response = await performFetch(url, fetchOptions, user?.accessToken);

        // Si es error 401, intentar renovar token y reintentar
        if (response.status === 401) {
            response = await handle401Error(url, fetchOptions);
        }

        return response;
    };

    return { apiRequest };
};
