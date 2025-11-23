import { Service, Category, Faq, ChartDataPoint, SignUpData, SignUpResponse, TokenResponse, LoginData, AuthError, BackendCategory, BackendCategoryIn, BackendService, BackendServiceIn, ServiceRequest, ServiceRequestIn, CategoryRequest, CategoryRequestIn, Currency, RateType } from '../types';
import {
    PaintBrushIcon,
    CodeBracketIcon,
    PresentationChartLineIcon,
    BriefcaseIcon,
} from '../components/icons';
import { API_CONFIG, buildApiUrl } from '../config/api';

// Definir API_BASE_URL para compatibilidad con código existente
const API_BASE_URL = API_CONFIG.BASE_URL;

// Log para debugging
console.log('🔗 API Base URL:', API_CONFIG.BASE_URL);
console.log('🌍 Environment:', (globalThis as Window).location?.hostname || 'unknown');

// Función helper para crear errores con formato esperado
const createApiError = (message: string): Error & { detail: string } => {
    const error = new Error(message) as Error & { detail: string };
    error.detail = message;
    return error;
};

// Función helper para manejar errores de la API
const handleApiError = async (response: Response): Promise<AuthError> => {
    try {
        const errorData = await response.json();
        return {
            detail: errorData.detail || 'Error desconocido',
            status_code: response.status
        };
    } catch {
        return {
            detail: `Error ${response.status}: ${response.statusText}`,
            status_code: response.status
        };
    }
};

// Funciones de autenticación
export const authAPI = {
    // Registro de usuario
    async signUp(data: SignUpData): Promise<SignUpResponse | TokenResponse> {
        try {
            console.log('🚀 Intentando registro en:', buildApiUrl(API_CONFIG.AUTH.REGISTER));
            const response = await fetch(buildApiUrl(API_CONFIG.AUTH.REGISTER), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en signUp:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Inicio de sesión
    async signIn(data: LoginData): Promise<TokenResponse> {
        try {
            console.log('🔐 Intentando login en:', buildApiUrl(API_CONFIG.AUTH.LOGIN));
            const response = await fetch(buildApiUrl(API_CONFIG.AUTH.LOGIN), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en signIn:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Refrescar token
    async refreshToken(refreshToken: string): Promise<TokenResponse> {
        try {
            const response = await fetch(buildApiUrl(API_CONFIG.AUTH.REFRESH), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Cerrar sesión
    async logout(accessToken: string): Promise<void> {
        try {
            const response = await fetch(buildApiUrl(API_CONFIG.AUTH.LOGOUT), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }
        } catch (error) {
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener perfil del usuario
    async getProfile(accessToken?: string) {
        try {
            const headers: Record<string, string> = {};
            
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }
            
            const response = await fetch(buildApiUrl(API_CONFIG.AUTH.ME), {
                method: 'GET',
                headers,
                credentials: 'include', // Importante: incluir cookies HttpOnly
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Restablecer contraseña
    async resetPassword(email: string): Promise<{ message: string }> {
        try {
            console.log('🔑 Intentando restablecer contraseña para:', email);
            const response = await fetch(buildApiUrl(API_CONFIG.AUTH.RESET_PASSWORD), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en resetPassword:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener estado de verificación del usuario actual
    async getVerificacionEstado(accessToken: string): Promise<any> {
        try {
            console.log(`🔍 Obteniendo estado de verificación...`);
            const response = await fetch(buildApiUrl(API_CONFIG.AUTH.VERIFICATION_STATUS), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Estado de verificación obtenido:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en getVerificacionEstado:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

export const MOCK_SERVICES: Service[] = [
    {
        id: '1',
        title: 'Auditoría de experiencia de usuario',
        description: 'Análisis y optimización de flujos para mejorar la conversión y retención.',
        longDescription: 'Ofrecemos un análisis exhaustivo de la experiencia de usuario de su producto digital. Identificamos puntos de fricción, evaluamos la usabilidad y proponemos mejoras concretas para aumentar la satisfacción del cliente, la conversión y la retención a largo plazo.',
        category: 'Diseño',
        price: 5000000,
        priceType: 'por proyecto',
        providerId: 'p1',
        providerName: 'Creative Solutions',
        providerLogoUrl: 'https://picsum.photos/seed/p1/40/40',
        rating: 4.9,
        reviewCount: 34,
        imageUrl: 'https://picsum.photos/seed/s1/400/250',
        createdAt: '2023-05-10',
        status: 'active',
    },
    {
        id: '2',
        title: 'Gestión de envíos nacionales',
        description: 'Soluciones logísticas para encomiendas y pymes en Paraguay.',
        longDescription: 'Nos encargamos de toda la logística de sus envíos a nivel nacional. Ofrecemos recolección, empaque, seguimiento en tiempo real y entrega puerta a puerta. Ideal para e-commerce y empresas que necesitan una solución logística confiable.',
        category: 'Logística',
        price: 800000,
        priceType: 'por proyecto',
        providerId: 'p2',
        providerName: 'LogiPY',
        providerLogoUrl: 'https://picsum.photos/seed/p2/40/40',
        rating: 4.7,
        reviewCount: 58,
        imageUrl: 'https://picsum.photos/seed/s2/400/250',
        createdAt: '2023-05-15',
        status: 'active',
    },
    {
        id: '3',
        title: 'Landing page optimizada',
        description: 'Creación de landing pages para validación de ideas o lanzamientos.',
        longDescription: 'Diseñamos y desarrollamos landing pages de alto impacto visual y optimizadas para la conversión. Perfectas para lanzar un nuevo producto, validar una idea de negocio o captar leads para una campaña específica. Incluye integración con herramientas de analítica.',
        category: 'Desarrollo Web',
        price: 2500000,
        priceType: 'por proyecto',
        providerId: 'p3',
        providerName: 'WebDev Masters',
        providerLogoUrl: 'https://picsum.photos/seed/p3/40/40',
        rating: 5,
        reviewCount: 22,
        imageUrl: 'https://picsum.photos/seed/s3/400/250',
        createdAt: '2023-05-20',
        status: 'active',
    },
    {
        id: '4',
        title: 'Asesoramiento Contable para Pymes',
        description: 'Servicios contables mensuales para mantener tus finanzas en orden.',
        longDescription: 'Brindamos un servicio integral de contabilidad mensual que incluye liquidación de impuestos, presentación de informes, y asesoramiento financiero para optimizar la carga tributaria y asegurar el cumplimiento de todas las normativas vigentes.',
        category: 'Consultoría',
        price: 1200000,
        priceType: 'por hora',
        providerId: 'p4',
        providerName: 'Contadores Asociados',
        providerLogoUrl: 'https://picsum.photos/seed/p4/40/40',
        rating: 4.8,
        reviewCount: 41,
        imageUrl: 'https://picsum.photos/seed/s4/400/250',
        createdAt: '2023-04-18',
        status: 'active',
    },
    {
        id: '5',
        title: 'Desarrollo de App Móvil MVP',
        description: 'Construimos el Producto Mínimo Viable de tu aplicación móvil.',
        longDescription: 'Transformamos tu idea en una aplicación móvil funcional. Nos enfocamos en desarrollar un MVP (Producto Mínimo Viable) para que puedas lanzar al mercado rápidamente, obtener feedback de usuarios reales y validar tu modelo de negocio antes de una gran inversión.',
        category: 'Desarrollo Web',
        price: 25000000,
        priceType: 'por proyecto',
        providerId: 'p3',
        providerName: 'WebDev Masters',
        providerLogoUrl: 'https://picsum.photos/seed/p3/40/40',
        rating: 4.9,
        reviewCount: 15,
        imageUrl: 'https://picsum.photos/seed/s5/400/250',
        createdAt: '2023-03-25',
        status: 'active',
    },
    {
        id: '6',
        title: 'Campaña de Marketing Digital',
        description: 'Gestión de redes sociales y pauta publicitaria en Google y Meta.',
        longDescription: 'Planificamos y ejecutamos campañas de marketing digital 360°. Gestionamos tus perfiles en redes sociales, creamos contenido atractivo y administramos tu presupuesto publicitario en plataformas como Google Ads y Meta Ads para maximizar tu alcance y conversiones.',
        category: 'Marketing y Publicidad',
        price: 3000000,
        priceType: 'por proyecto',
        providerId: 'p1',
        providerName: 'Creative Solutions',
        providerLogoUrl: 'https://picsum.photos/seed/p1/40/40',
        rating: 4.6,
        reviewCount: 67,
        imageUrl: 'https://picsum.photos/seed/s6/400/250',
        createdAt: '2023-05-01',
        status: 'active',
    },
];

export const MOCK_CATEGORIES: Category[] = [
    {
        id: 'cat1',
        name: 'Diseño',
        description: 'Mejora la experiencia visual y funcional de tus productos digitales.',
        icon: PaintBrushIcon,
    },
    {
        id: 'cat2',
        name: 'Desarrollo Web',
        description: 'Sitios, apps y soluciones a medida para tu negocio online.',
        icon: CodeBracketIcon,
    },
    {
        id: 'cat3',
        name: 'Marketing y Publicidad',
        description: 'Aumenta tu visibilidad y conectá con más clientes.',
        icon: PresentationChartLineIcon,
    },
    {
        id: 'cat4',
        name: 'Logística',
        description: 'Servicios de envío, almacenamiento y distribución.',
        icon: BriefcaseIcon,
    },
];

export const MOCK_FAQS: Faq[] = [
    {
        question: '¿Cómo funciona la verificación de empresas proveedoras?',
        answer: 'Para garantizar la confianza en nuestra plataforma, ofrecemos un proceso de verificación que valida la documentación legal de cada empresa. Solo los proveedores que cumplen con los requisitos establecidos pueden ofrecer sus servicios, asegurando así calidad, transparencia y mayor credibilidad dentro del sistema.',
    },
    {
        question: '¿Es gratis publicar un servicio?',
        answer: 'Sí, podés empezar con nuestro plan gratuito. Luego, podés optar por un plan de pago si querés destacar tu perfil o usar herramientas premium.',
    },
    {
        question: '¿Puedo editar mis servicios después de publicarlos?',
        answer: 'Totalmente. Podés modificar la información, precio e imágenes desde tu panel en cualquier momento.',
    },
    {
        question: '¿Cómo reciben los clientes mis servicios?',
        answer: 'Los clientes pueden encontrarte por categoría, palabras clave o ubicación. Tu perfil y tus calificaciones son clave para atraer nuevos proyectos.',
    },
];

// Mock data for dashboard charts
export const getReservationsChartData = (): ChartDataPoint[] => [
    { name: 'Jan', value: 20 },
    { name: 'Feb', value: 30 },
    { name: 'Mar', value: 25 },
    { name: 'Apr', value: 45 },
    { name: 'May', value: 50 },
    { name: 'Jun', value: 48 },
];

export const getRatingsChartData = (): ChartDataPoint[] => [
    { name: 'Jan', value: 4.5 },
    { name: 'Feb', value: 4.6 },
    { name: 'Mar', value: 4.5 },
    { name: 'Apr', value: 4.7 },
    { name: 'May', value: 4.8 },
    { name: 'Jun', value: 4.9 },
];

export const getAdminUsersChartData = (): ChartDataPoint[] => [
    { name: 'Jan', value: 120 },
    { name: 'Feb', value: 150 },
    { name: 'Mar', value: 180 },
    { name: 'Apr', value: 220 },
    { name: 'May', value: 250 },
    { name: 'Jun', value: 300 },
];
export const getAdminPublicationsChartData = (): ChartDataPoint[] => [
    { name: 'Jan', value: 200 },
    { name: 'Feb', value: 210 },
    { name: 'Mar', value: 250 },
    { name: 'Apr', value: 280 },
    { name: 'May', value: 320 },
    { name: 'Jun', value: 350 },
];

// API para proveedores
export const providersAPI = {
    // Enviar solicitud de verificación de proveedor
               async submitProviderApplication(
               data: {
                   perfil_in: string; // JSON string como espera el backend
                   documentos: File[];
                   nombres_tip_documento: string[];
                   comentario_solicitud?: string;
               },
               accessToken: string
           ): Promise<{ message: string }> {
                try {
            console.log('📤 Enviando solicitud de proveedor a:', `${API_BASE_URL}/providers/solicitar-verificacion`);
            console.log('🔍 Datos a enviar:', data);
            console.log('🔍 Token de acceso:', accessToken ? 'Presente' : 'Ausente');
            
            // Crear FormData para enviar archivos
            const formData = new FormData();
            
            // Agregar datos del perfil como JSON string
            formData.append('perfil_in', data.perfil_in);
            console.log('📄 Perfil agregado al FormData');
            
            // Agregar documentos y sus nombres de tipo
            data.documentos.forEach((documento, index) => {
                formData.append('documentos', documento);
                formData.append('nombres_tip_documento', data.nombres_tip_documento[index]);
                console.log(`📎 Documento ${index + 1}:`, documento.name, 'Tipo:', data.nombres_tip_documento[index]);
            });
            
            // Agregar comentario si existe
            if (data.comentario_solicitud) {
                formData.append('comentario_solicitud', data.comentario_solicitud);
                console.log('💬 Comentario agregado:', data.comentario_solicitud);
            }
            
            console.log('🚀 Iniciando fetch request...');
            const response = await fetch(`${API_BASE_URL}/providers/solicitar-verificacion`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    // No incluir Content-Type para FormData, el navegador lo establece automáticamente
                },
                body: formData,
            });

            console.log('📡 Respuesta recibida:', response.status, response.statusText);

            if (!response.ok) {
                console.log('❌ Error en la respuesta:', response.status, response.statusText);
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Respuesta exitosa:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en submitProviderApplication:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

// API para administradores
export const adminAPI = {
    // Obtener todos los usuarios
    async getAllUsers(accessToken: string): Promise<any[]> {
        try {
            const endpoint = `${API_BASE_URL}/admin/users`;
            console.log('👥 Obteniendo todos los usuarios desde:', endpoint);

            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log('📡 Estado de respuesta usuarios:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.log('❌ Respuesta de error del backend:', errorText);
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Usuarios obtenidos:', result);
            console.log('📊 Total de usuarios:', result?.length || 0);

            return Array.isArray(result) ? result : [];
        } catch (error) {
            console.error('❌ Error en getAllUsers:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener todas las solicitudes de verificación (para estadísticas)
    async getAllSolicitudesVerificacion(accessToken: string): Promise<any[]> {
        try {
            const endpoint = `${API_BASE_URL}/admin/verificaciones/todas`;
            console.log('📋 Obteniendo todas las solicitudes de verificación desde:', endpoint);

            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log('📡 Estado de respuesta todas las solicitudes:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.log('❌ Respuesta de error del backend:', errorText);
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Todas las solicitudes obtenidas:', result);
            console.log('📊 Total de solicitudes:', result?.length || 0);

            return Array.isArray(result) ? result : [];
        } catch (error) {
            console.error('❌ Error en getAllSolicitudesVerificacion:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener todas las solicitudes de servicios (para administradores)
    async getAllSolicitudesServicios(accessToken: string): Promise<any[]> {
        try {
            const endpoint = `${API_BASE_URL}/admin/service-requests/todas`;
            console.log('📋 Obteniendo todas las solicitudes de servicios desde:', endpoint);

            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log('📡 Estado de respuesta todas las solicitudes de servicios:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.log('❌ Respuesta de error del backend:', errorText);
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Todas las solicitudes de servicios obtenidas:', result);
            console.log('📊 Total de solicitudes de servicios:', result?.length || 0);

            return Array.isArray(result) ? result : [];
        } catch (error) {
            console.error('❌ Error en getAllSolicitudesServicios:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // NUEVO: Obtener todas las solicitudes de servicios usando endpoint modificado
    async getAllSolicitudesServiciosModificado(accessToken: string): Promise<any[]> {
        try {
            const endpoint = `${API_BASE_URL}/service-requests/?all=true&admin=true&limit=100`;
            console.log('📋 Obteniendo todas las solicitudes de servicios (endpoint modificado) desde:', endpoint);

            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log('📡 Estado de respuesta (endpoint modificado):', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.log('❌ Respuesta de error del backend (endpoint modificado):', errorText);
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Solicitudes obtenidas (endpoint modificado):', result);
            console.log('📊 Total de solicitudes (endpoint modificado):', result?.length || 0);

            return Array.isArray(result) ? result : [];
        } catch (error) {
            console.error('❌ Error en getAllSolicitudesServiciosModificado:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener solicitudes pendientes
    async getSolicitudesPendientes(accessToken: string): Promise<any[]> {
        try {
            const endpoint = `${API_BASE_URL}/admin/verificaciones/pendientes`;
            console.log('📋 Obteniendo solicitudes pendientes desde:', endpoint);

            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log('📡 Estado de respuesta:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.log('❌ Respuesta de error del backend:', errorText);
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Solicitudes pendientes obtenidas:', result);
            console.log('📊 Tipo de resultado:', typeof result);
            console.log('📊 Es array:', Array.isArray(result));
            console.log('📊 Longitud del resultado:', result?.length || 'N/A');

            return Array.isArray(result) ? result : [];
        } catch (error) {
            console.error('❌ Error en getSolicitudesPendientes:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener detalles de una solicitud específica
    async getDetalleSolicitud(solicitudId: number, accessToken: string): Promise<any> {
        try {
            console.log(`📋 Obteniendo detalles de solicitud ${solicitudId}...`);
            const response = await fetch(`${API_BASE_URL}/admin/verificaciones/${solicitudId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Detalles de solicitud obtenidos:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en getDetalleSolicitud:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Aprobar una solicitud
    async aprobarSolicitud(solicitudId: number, comentario: string | null, accessToken: string): Promise<any> {
        try {
            console.log(`✅ Aprobando solicitud ${solicitudId}...`);
            const response = await fetch(`${API_BASE_URL}/admin/verificaciones/${solicitudId}/aprobar`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ comentario }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Solicitud aprobada:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en aprobarSolicitud:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Rechazar una solicitud
    async rechazarSolicitud(solicitudId: number, comentario: string, accessToken: string): Promise<any> {
        try {
            console.log(`❌ Rechazando solicitud ${solicitudId}...`);
            console.log(`📝 Comentario: ${comentario}`);
            
            const response = await fetch(`${API_BASE_URL}/admin/verificaciones/${solicitudId}/rechazar`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ comentario }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Solicitud rechazada:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en rechazarSolicitud:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener documentos de una solicitud
    async getDocumentosSolicitud(solicitudId: number, accessToken: string): Promise<any> {
        try {
            console.log(`📄 Obteniendo documentos de solicitud ${solicitudId}...`);
            const response = await fetch(`${API_BASE_URL}/admin/verificaciones/${solicitudId}/documentos`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Documentos obtenidos:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en getDocumentosSolicitud:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener datos completos de la solicitud de verificación
    async getVerificacionDatos(accessToken: string): Promise<any> {
        try {
            console.log(`📋 Obteniendo datos de verificación...`);
            const response = await fetch(`${API_BASE_URL}/auth/verificacion-datos`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Datos de verificación obtenidos:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en getVerificacionDatos:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Descargar un documento específico
    async descargarDocumento(solicitudId: number, documentoId: number, accessToken: string): Promise<any> {
        try {
            console.log(`📥 Descargando documento ${documentoId} de solicitud ${solicitudId}...`);
            const response = await fetch(`${API_BASE_URL}/admin/verificaciones/${solicitudId}/documentos/${documentoId}/descargar`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Información de descarga obtenida:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en descargarDocumento:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Ver un documento específico
    async verDocumento(solicitudId: number, documentoId: number, accessToken: string): Promise<any> {
        try {
            console.log(`👁️ Obteniendo información para ver documento ${documentoId} de solicitud ${solicitudId}...`);
            const response = await fetch(`${API_BASE_URL}/admin/verificaciones/${solicitudId}/documentos/${documentoId}/ver`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Información de visualización obtenida:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en verDocumento:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Reportes
    async getReporteUsuariosActivos(accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/reports/usuarios-activos`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getReporteUsuariosActivos:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    async getReporteProveedoresVerificados(accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/reports/proveedores-verificados`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getReporteProveedoresVerificados:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    async getReporteSolicitudesProveedores(accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/reports/solicitudes-proveedores`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getReporteSolicitudesProveedores:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    async getReporteCategorias(accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/reports/categorias`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getReporteCategorias:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    async getReporteServicios(accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/reports/servicios`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getReporteServicios:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener documentos del proveedor autenticado
    async getMisDocumentos(accessToken: string): Promise<any> {
        try {
            console.log(`📋 Obteniendo documentos del proveedor...`);
            const response = await fetch(`${API_BASE_URL}/providers/mis-documentos`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Documentos del proveedor obtenidos:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en getMisDocumentos:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener datos de la solicitud del proveedor autenticado
    async getMisDatosSolicitud(accessToken: string): Promise<any> {
        try {
            console.log(`📋 Obteniendo datos de solicitud del proveedor...`);
            const response = await fetch(`${API_BASE_URL}/providers/mis-datos-solicitud`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Datos de solicitud del proveedor obtenidos:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en getMisDatosSolicitud:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Endpoint de prueba para verificar datos
    async testDatos(accessToken: string): Promise<any> {
        try {
            console.log(`🧪 Probando endpoint de datos...`);
            const response = await fetch(`${API_BASE_URL}/providers/test-datos`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Datos de prueba obtenidos:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en testDatos:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Auto-desactivar usuario (darse de baja del sistema)
    async selfDeactivateUser(accessToken: string): Promise<any> {
        try {
            console.log('🔍 Usuario solicitando auto-desactivación...');
            const response = await fetch(`${API_BASE_URL}/admin/users/self-deactivate`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Usuario auto-desactivado exitosamente:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en selfDeactivateUser:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener estadísticas del dashboard
    async getDashboardStats(accessToken: string): Promise<any> {
        try {
            console.log('📊 Obteniendo estadísticas del dashboard...');
            const response = await fetch(buildApiUrl(API_CONFIG.ADMIN.DASHBOARD_STATS), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const result = await response.json();
            console.log('✅ Estadísticas del dashboard obtenidas:', result);
            return result;
        } catch (error) {
            console.error('❌ Error en getDashboardStats:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

// APIs para gestión de categorías
export const categoriesAPI = {
    // Obtener todas las categorías
    async getCategories(accessToken?: string, activeOnly: boolean = true): Promise<BackendCategory[]> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
            };
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const params = new URLSearchParams();
            params.append('active_only', activeOnly.toString());

            const response = await fetch(buildApiUrl(`${API_CONFIG.CATEGORIES.LIST}?${params.toString()}`), {
                method: 'GET',
                headers,
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getCategories:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Crear nueva categoría
    async createCategory(categoryData: BackendCategoryIn, accessToken: string): Promise<BackendCategory> {
        try {
            const response = await fetch(buildApiUrl(API_CONFIG.CATEGORIES.CREATE), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(categoryData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en createCategory:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Actualizar categoría
    async updateCategory(categoryId: number, categoryData: Partial<BackendCategoryIn>, accessToken: string): Promise<BackendCategory> {
        try {
            const response = await fetch(buildApiUrl(`${API_CONFIG.CATEGORIES.UPDATE}/${categoryId}`), {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(categoryData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en updateCategory:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

// Funciones helper para getFilteredServices
// Construir headers con autenticación
const buildAuthHeaders = (accessToken?: string): Record<string, string> => {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
    }
    return headers;
};

// Construir parámetros de filtros
const buildFilterParams = (
    limit: number,
    offset: number,
    filters?: {
        currency?: string;
        min_price?: number;
        max_price?: number;
        category_id?: number;
        department?: string;
        city?: string;
        search?: string;
        min_rating?: number;
        date_from?: string;
        date_to?: string;
    }
): URLSearchParams => {
    const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
    });

    if (!filters) {
        return params;
    }

    if (filters.currency) params.append('currency', filters.currency);
    if (filters.min_price !== undefined) params.append('min_price', filters.min_price.toString());
    if (filters.max_price !== undefined) params.append('max_price', filters.max_price.toString());
    if (filters.category_id) params.append('category_id', filters.category_id.toString());
    if (filters.department) params.append('department', filters.department);
    if (filters.city) params.append('city', filters.city);
    if (filters.search) params.append('search', filters.search);
    if (filters.min_rating !== undefined && filters.min_rating > 0) params.append('min_rating', filters.min_rating.toString());
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);

    return params;
};

// Realizar petición de servicios filtrados
const performFilteredServicesRequest = async (headers: Record<string, string>, params: URLSearchParams): Promise<Response> => {
    return fetch(`${buildApiUrl(API_CONFIG.SERVICES.UNIFIED)}?${params}`, {
        method: 'GET',
        headers,
    });
};

// APIs para gestión de servicios
export const servicesAPI = {
    // Obtener todos los servicios
    async getServices(accessToken?: string): Promise<BackendService[]> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
            };
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const response = await fetch(`${API_BASE_URL}/services/list`, {
                method: 'GET',
                headers,
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getServices:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener servicios con información del proveedor (usando endpoint unificado)
    async getServicesWithProviders(
        limit: number = 5, 
        offset: number = 0, 
        accessToken?: string,
        filters?: {
            currency?: string;
            min_price?: number;
            max_price?: number;
        }
    ): Promise<{
        services: BackendService[];
        pagination: {
            total: number;
            page: number;
            total_pages: number;
            limit: number;
            offset: number;
        };
        filters_applied: any;
    }> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
            };
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const params = new URLSearchParams({
                limit: limit.toString(),
                offset: offset.toString()
            });

            // Agregar filtros si están presentes
            if (filters) {
                if (filters.currency) params.append('currency', filters.currency);
                if (filters.min_price !== undefined) params.append('min_price', filters.min_price.toString());
                if (filters.max_price !== undefined) params.append('max_price', filters.max_price.toString());
            }

            const response = await fetch(`${buildApiUrl(API_CONFIG.SERVICES.UNIFIED)}?${params}`, {
                method: 'GET',
                headers,
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getServicesWithProviders:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener servicios filtrados (usando endpoint unificado)
    async getFilteredServices(
        limit: number = 10,
        offset: number = 0,
        accessToken?: string,
        filters?: {
            currency?: string;
            min_price?: number;
            max_price?: number;
            category_id?: number;
            department?: string;
            city?: string;
            search?: string;
            min_rating?: number;
            date_from?: string;
            date_to?: string;
        }
    ): Promise<{
        services: BackendService[];
        pagination: {
            total: number;
            page: number;
            total_pages: number;
            limit: number;
            offset: number;
        };
        filters_applied: any;
    }> {
        try {
            const headers = buildAuthHeaders(accessToken);
            const params = buildFilterParams(limit, offset, filters);
            const response = await performFilteredServicesRequest(headers, params);

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getFilteredServices:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },


    // Obtener servicios por categoría
    async getServicesByCategory(categoryId: number, accessToken?: string): Promise<BackendService[]> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
            };
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const response = await fetch(`${API_BASE_URL}/services/category/${categoryId}`, {
                method: 'GET',
                headers,
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getServicesByCategory:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Crear nuevo servicio
    async createService(serviceData: BackendServiceIn, accessToken: string): Promise<BackendService> {
        try {
            const response = await fetch(`${API_BASE_URL}/services/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(serviceData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en createService:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Actualizar servicio existente
    async updateService(serviceId: number, serviceData: Partial<BackendServiceIn>, accessToken: string): Promise<BackendService> {
        try {
            const response = await fetch(`${API_BASE_URL}/services/${serviceId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(serviceData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en updateService:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Actualizar estado del servicio (activar/desactivar) - Para administradores
    async updateServiceStatus(serviceId: number, estado: boolean, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/services/${serviceId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ estado }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en updateServiceStatus:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener plantillas de servicios
    async getServiceTemplates(): Promise<any[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/services/templates`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getServiceTemplates:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener plantillas de servicios por categoría
    async getServiceTemplatesByCategory(categoryId: number): Promise<any[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/services/templates/category/${categoryId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getServiceTemplatesByCategory:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener TODOS los servicios (activos e inactivos) por categoría
    async getAllServicesByCategory(categoryId: number): Promise<any[]> {
        try {
            console.log('🔗 Llamando a getAllServicesByCategory para categoría:', categoryId);
            const url = `${API_BASE_URL}/services/all/category/${categoryId}`;
            console.log('🌐 URL:', url);
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            console.log('📡 Respuesta del servidor:', response.status, response.statusText);

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const data = await response.json();
            console.log('📊 Datos recibidos:', data);
            return data;
        } catch (error) {
            console.error('❌ Error en getAllServicesByCategory:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

// Funciones helper para getAllServiceRequests
// Intentar obtener solicitudes desde endpoint modificado
const tryModifiedEndpoint = async (accessToken: string): Promise<ServiceRequest[] | null> => {
    try {
        console.log('🔗 Usando adminAPI.getAllSolicitudesServiciosModificado...');
        const result = await adminAPI.getAllSolicitudesServiciosModificado(accessToken);
        
        if (Array.isArray(result) && result.length > 0) {
            logServiceRequestsFound(result, 'endpoint modificado');
            return result;
        }
        
        console.log('⚠️ Endpoint modificado devolvió array vacío, probando adminAPI original...');
        return null;
    } catch (modifiedError) {
        console.log('⚠️ Endpoint modificado falló, probando adminAPI original:', modifiedError);
        return null;
    }
};

// Intentar obtener solicitudes desde adminAPI original
const tryOriginalAdminAPI = async (accessToken: string): Promise<ServiceRequest[] | null> => {
    try {
        console.log('🔗 Usando adminAPI.getAllSolicitudesServicios...');
        const result = await adminAPI.getAllSolicitudesServicios(accessToken);
        
        if (Array.isArray(result) && result.length > 0) {
            logServiceRequestsFound(result, 'adminAPI');
            return result;
        }
        
        console.log('⚠️ adminAPI devolvió array vacío, probando fallbacks...');
        return null;
    } catch (adminError) {
        console.log('⚠️ adminAPI falló, probando fallbacks:', adminError);
        return null;
    }
};

// Loggear información de solicitudes encontradas
const logServiceRequestsFound = (result: ServiceRequest[], source: string): void => {
    console.log('🔍 Primera solicitud encontrada:', result[0]);
    console.log('🔍 Estados encontrados:', [...new Set(result.map(r => r.estado_aprobacion))]);
    console.log(`📊 Total de solicitudes desde ${source}:`, result.length);
};

// Procesar respuesta de un endpoint
const processEndpointResponse = async (endpoint: string, response: Response): Promise<ServiceRequest[] | null> => {
    const result = await response.json();
    console.log(`✅ Solicitudes obtenidas desde ${endpoint}:`, result);
    console.log('📊 Total de solicitudes:', result?.length || 0);
    
    if (Array.isArray(result)) {
        if (result.length > 0) {
            logServiceRequestsFound(result, endpoint);
            if (result.length > 1) {
                console.log('🎯 ¡Encontrado endpoint con múltiples solicitudes! Usando este endpoint.');
                return result;
            }
        } else {
            console.log('⚠️ Endpoint devolvió array vacío');
        }
        return result;
    }
    
    return null;
};

// Intentar obtener solicitudes desde endpoints de fallback
const tryFallbackEndpoints = async (accessToken: string): Promise<ServiceRequest[] | null> => {
    const endpoints = [
        '/admin/service-requests/todas',
        '/admin/service-requests',
        '/service-requests/?all=true&admin=true&limit=100',
        '/service-requests/?all=true',
        '/service-requests/?status=all',
        '/service-requests/?include_all=true',
        '/service-requests/all',
        '/service-requests/?limit=100',
        '/service-requests/?offset=0&limit=100',
        '/service-requests/?admin=true',
        '/service-requests/?user_role=admin',
        '/service-requests/'
    ];
    
    for (const endpoint of endpoints) {
        try {
            console.log(`🔗 Probando endpoint: ${endpoint}`);
            
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log(`📡 Estado de respuesta ${endpoint}:`, response.status, response.statusText);

            if (response.ok) {
                const result = await processEndpointResponse(endpoint, response);
                if (result) {
                    return result;
                }
            } else {
                console.log(`❌ Endpoint ${endpoint} falló con status:`, response.status);
            }
        } catch (endpointError) {
            console.log(`⚠️ Error en endpoint ${endpoint}:`, endpointError);
            continue;
        }
    }
    
    return null;
};

// APIs para gestión de solicitudes de servicios
export const serviceRequestsAPI = {
    // Obtener todas las solicitudes pendientes
    async getPendingRequests(accessToken: string): Promise<ServiceRequest[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/service-requests/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getPendingRequests:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener todas las solicitudes de servicios (para administradores)
    async getAllServiceRequests(accessToken: string): Promise<ServiceRequest[]> {
        try {
            console.log('🔍 Intentando obtener todas las solicitudes de servicios para administrador...');
            
            // Intentar endpoint modificado
            const modifiedResult = await tryModifiedEndpoint(accessToken);
            if (modifiedResult) {
                return modifiedResult;
            }

            // Intentar adminAPI original
            const adminResult = await tryOriginalAdminAPI(accessToken);
            if (adminResult) {
                return adminResult;
            }
            
            // Intentar endpoints de fallback
            const fallbackResult = await tryFallbackEndpoints(accessToken);
            if (fallbackResult) {
                return fallbackResult;
            }
            
            // Si ningún endpoint devuelve datos, retornar array vacío
            console.log('ℹ️ Ningún endpoint devolvió solicitudes. Retornando array vacío.');
            console.log('🔍 Verifica que el backend tenga el endpoint correcto para traer todas las solicitudes de servicios.');
            console.log('💡 Sugerencia: Crear endpoint /admin/service-requests/todas similar a /admin/verificaciones/todas');
            return [];
            
        } catch (error) {
            console.error('❌ Error en getAllServiceRequests:', error);
            return [];
        }
    },

    // Aprobar solicitud
    async approveRequest(requestId: number, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/service-requests/${requestId}/approve`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en approveRequest:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Rechazar solicitud
    async rejectRequest(requestId: number, comentario_admin?: string, accessToken?: string): Promise<any> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
            };
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const response = await fetch(`${API_BASE_URL}/service-requests/${requestId}/reject`, {
                method: 'PUT',
                headers,
                body: JSON.stringify({ comentario_admin: comentario_admin || null }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en rejectRequest:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Proponer nuevo servicio (para proveedores)
    async proposeService(requestData: ServiceRequestIn, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/providers/services/proponer`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en proposeService:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener mis solicitudes de servicios (para proveedores)
    async getMyServiceRequests(accessToken: string): Promise<ServiceRequest[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/service-requests/my-requests`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getMyServiceRequests:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

// APIs para gestión de servicios del proveedor
export const providerServicesAPI = {
    // Obtener servicios del proveedor
    async getProviderServices(accessToken: string): Promise<any[]> {
        try {
            console.log('🔍 getProviderServices - Iniciando petición');
            console.log('🔍 getProviderServices - URL:', `${API_BASE_URL}/provider/services/`);
            console.log('🔍 getProviderServices - Token disponible:', accessToken ? 'SÍ' : 'NO');
            
            const response = await fetch(`${API_BASE_URL}/provider/services/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log('🔍 getProviderServices - Respuesta recibida:', response.status, response.statusText);

            if (!response.ok) {
                console.log('🔍 getProviderServices - Error en respuesta:', response.status);
                
                // Si es error 401 o 500, no hacer logout, solo lanzar error controlado
                if (response.status === 401 || response.status === 500) {
                    console.log('⚠️ Error 401/500 en getProviderServices, no haciendo logout');
                    console.log('🔍 getProviderServices - Devolviendo array vacío en lugar de error');
                    // En lugar de lanzar error, devolver array vacío para que la página funcione
                    return [];
                }
                
                const error = await handleApiError(response);
                throw error;
            }

            const data = await response.json();
            console.log('🔍 getProviderServices - Datos recibidos:', data.length, 'servicios');
            return data;
        } catch (error) {
            console.error('❌ Error en getProviderServices:', error);
            console.log('🔍 getProviderServices - Devolviendo array vacío por error');
            // En lugar de lanzar error, devolver array vacío para que la página funcione
            return [];
        }
    },

    // Obtener un servicio específico del proveedor
    async getProviderService(serviceId: number, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/provider/services/${serviceId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getProviderService:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Actualizar servicio del proveedor
    async updateProviderService(serviceId: number, serviceData: any, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/provider/services/${serviceId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(serviceData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en updateProviderService:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener opciones de monedas
    async getCurrencies(accessToken: string): Promise<any[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/provider/services/options/monedas`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getCurrencies:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener opciones de tipos de tarifa
    async getRateTypes(accessToken: string): Promise<any[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/provider/services/options/tipos-tarifa`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getRateTypes:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Agregar tarifa a servicio
    async addTarifaToService(serviceId: number, tarifaData: any, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/provider/services/${serviceId}/tarifas`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(tarifaData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en addTarifaToService:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Eliminar tarifa de servicio
    async removeTarifaFromService(serviceId: number, tarifaId: number, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/provider/services/${serviceId}/tarifas/${tarifaId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en removeTarifaFromService:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Actualizar estado del servicio (activar/desactivar)
    async updateServiceStatus(serviceId: number, estado: boolean, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/provider/services/${serviceId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ estado }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en updateServiceStatus:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Crear servicio desde plantilla
    async createServiceFromTemplate(templateData: any, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/provider/services/from-template`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(templateData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en createServiceFromTemplate:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

// APIs adicionales
export const additionalAPI = {
    // Obtener monedas activas
    async getCurrencies(accessToken?: string): Promise<Currency[]> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
            };
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const response = await fetch(`${API_BASE_URL}/additional/currencies`, {
                method: 'GET',
                headers,
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getCurrencies:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener tipos de tarifa
    async getRateTypes(accessToken?: string): Promise<RateType[]> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
            };
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const response = await fetch(`${API_BASE_URL}/additional/rate-types`, {
                method: 'GET',
                headers,
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getRateTypes:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

// APIs para gestión de solicitudes de categorías
export const categoryRequestsAPI = {
    // Crear una nueva solicitud de categoría
    async createCategoryRequest(request: CategoryRequestIn, accessToken: string): Promise<CategoryRequest> {
        try {
            const response = await fetch(`${API_BASE_URL}/category-requests/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en createCategoryRequest:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener solicitudes de categorías del proveedor actual
    async getMyCategoryRequests(accessToken: string): Promise<CategoryRequest[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/category-requests/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en getMyCategoryRequests:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener todas las solicitudes de categorías (para administradores)
    async getAllCategoryRequests(accessToken: string): Promise<CategoryRequest[]> {
        try {
            const response = await fetch(buildApiUrl('/category-requests/admin/todas'), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const data = await response.json();
            console.log('📊 Datos recibidos:', data);
            return data;
        } catch (error) {
            console.error('❌ Error en getAllCategoryRequests:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Obtener user_id usando id_perfil
    async getUserIdByProfile(idPerfil: number, accessToken: string): Promise<{success: boolean, user_id?: string, message?: string}> {
        try {
            console.log('🔗 Obteniendo user_id para id_perfil:', idPerfil);
            const response = await fetch(buildApiUrl(`/admin/users/user-id-by-profile/${idPerfil}`), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            const data = await response.json();
            console.log('📊 User ID obtenido:', data);
            return data;
        } catch (error) {
            console.error('❌ Error obteniendo user_id por id_perfil:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Aprobar una solicitud de categoría
    async approveCategoryRequest(requestId: number, comentario: string | null, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/category-requests/${requestId}/approve`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ comentario }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en approveCategoryRequest:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Rechazar una solicitud de categoría
    async rejectCategoryRequest(requestId: number, comentario: string, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/category-requests/${requestId}/reject`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ comentario }),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en rejectCategoryRequest:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};

// Funciones de perfil de usuario
export const profileAPI = {
    // Actualizar perfil del usuario
    async updateProfile(profileData: { nombre_persona?: string; foto_perfil?: string }, accessToken: string): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/profile`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(profileData),
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en updateProfile:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    },

    // Subir foto de perfil
    async uploadProfilePhoto(file: File, accessToken: string): Promise<any> {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE_URL}/auth/upload-profile-photo`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const error = await handleApiError(response);
                throw error;
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Error en uploadProfilePhoto:', error);
            if (error instanceof Error) {
                throw createApiError(error.message);
            }
            throw error;
        }
    }
};
