import { useAuth } from '../contexts/AuthContext';

interface ApiRequestOptions extends RequestInit {
    url: string;
}

export const useApiWithAuth = () => {
    const { user, refreshToken } = useAuth();

    const apiRequest = async (options: ApiRequestOptions) => {
        const { url, ...fetchOptions } = options;
        
        // Primera petición
        let response = await fetch(url, {
            ...fetchOptions,
            headers: {
                'Authorization': `Bearer ${user?.accessToken}`,
                'Content-Type': 'application/json',
                ...fetchOptions.headers,
            },
        });

        // Si es error 401, intentar renovar token y reintentar
        if (response.status === 401) {
            console.log('🔄 Token expirado, intentando renovar...');
            console.log('🔍 Refresh token disponible:', localStorage.getItem('refresh_token') ? 'SÍ' : 'NO');
            
            try {
                const newToken = await refreshToken();
                console.log('✅ Token renovado, reintentando petición...');
                
                // Reintentar con el nuevo token
                response = await fetch(url, {
                    ...fetchOptions,
                    headers: {
                        'Authorization': `Bearer ${newToken}`,
                        'Content-Type': 'application/json',
                        ...fetchOptions.headers,
                    },
                });
            } catch (refreshError) {
                console.error('❌ Error al renovar token:', refreshError);
                console.log('🔍 Refresh token en localStorage:', localStorage.getItem('refresh_token'));
                
                // No hacer logout automático en errores 500 del refresh
                if (refreshError instanceof Error && refreshError.message.includes('500')) {
                    console.log('⚠️ Error 500 en refresh, manteniendo sesión');
                    throw new Error('Error temporal del servidor. Por favor, intenta nuevamente.');
                }
                
                throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
            }
        }

        return response;
    };

    return { apiRequest };
};
