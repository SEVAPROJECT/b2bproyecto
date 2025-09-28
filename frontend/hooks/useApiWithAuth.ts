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
                
                // Manejar errores 500 del servidor sin hacer logout
                if (refreshError instanceof Error) {
                    if (refreshError.message.includes('500') || 
                        refreshError.message.includes('Error temporal del servidor') ||
                        refreshError.message.includes('Error interno del servidor')) {
                        console.log('⚠️ Error 500 en refresh, manteniendo sesión y reintentando con token actual');
                        
                        // Reintentar la petición original con el token actual (sin renovar)
                        try {
                            response = await fetch(url, {
                                ...fetchOptions,
                                headers: {
                                    'Authorization': `Bearer ${user?.accessToken}`,
                                    'Content-Type': 'application/json',
                                    ...fetchOptions.headers,
                                },
                            });
                            console.log('✅ Petición reintentada con token actual');
                        } catch (retryError) {
                            console.error('❌ Error en reintento:', retryError);
                            throw new Error('Error temporal del servidor. Por favor, intenta nuevamente.');
                        }
                    } else {
                        // Solo hacer logout en errores de autenticación reales (no 500)
                        throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
                    }
                } else {
                    throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
                }
            }
        }

        return response;
    };

    return { apiRequest };
};
