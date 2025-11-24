import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { CheckCircleIcon, ClockIcon, PencilIcon, XMarkIcon } from '../icons';
import OptimizedLoading from '../ui/OptimizedLoading';
import { categoryRequestsAPI } from '../../services/api';
import { API_CONFIG, buildApiUrl } from '../../config/api';

// Función helper para ajustar fecha a zona horaria de Argentina (UTC-3)
const adjustToArgentinaTime = (date: Date): Date => {
    return new Date(date.getTime() - 3 * 60 * 60 * 1000);
};

// Función helper para formatear fecha con zona horaria de Argentina
const formatArgentinaDate = (dateString: string): string => {
    try {
        const date = new Date(dateString);
        const adjustedDate = adjustToArgentinaTime(date);
        return adjustedDate.toLocaleDateString('es-AR', { hour12: false });
    } catch (error) {
        console.error('Error formateando fecha Argentina:', error);
        return dateString;
    }
};

// Tipo temporal para CategoryRequest
interface CategoryRequest {
    id_solicitud: number;
    id_perfil: number;
    nombre_categoria: string;
    descripcion: string;
    nombre_empresa?: string;
    nombre_contacto?: string;
    email_contacto?: string;
    estado_aprobacion: string;
    comentario_admin?: string;
    created_at: string;
    user_id?: string; // ID del usuario que hizo la solicitud
}

// Funciones auxiliares para manejo de fechas
const parseDateString = (dateString: string): Date => {
    const [year, month, day] = dateString.split('-').map(Number);
    return new Date(year, month - 1, day);
};

const normalizeDate = (date: Date): Date => {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
};

const datesEqual = (date1: Date, date2: Date): boolean => {
    const d1 = normalizeDate(date1);
    const d2 = normalizeDate(date2);
    return d1.getTime() === d2.getTime();
};

// Función auxiliar para verificar si una fecha cumple con el filtro
const matchesDateFilter = (requestDate: Date, dateFilter: string, customDate?: string): boolean => {
    if (dateFilter === 'all') {
        return true;
    }

    const now = new Date();

    switch (dateFilter) {
        case 'today':
            return requestDate.toDateString() === now.toDateString();
        case 'week': {
            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            return requestDate >= weekAgo;
        }
        case 'month':
            return requestDate.getMonth() === now.getMonth() && requestDate.getFullYear() === now.getFullYear();
        case 'year':
            return requestDate.getFullYear() === now.getFullYear();
        case 'custom': {
            if (customDate) {
                const selectedDate = parseDateString(customDate);
                return datesEqual(requestDate, selectedDate);
            }
            return true;
        }
        default:
            return true;
    }
};

// Función auxiliar para verificar si el estado cumple con el filtro
const matchesStatusFilter = (estadoAprobacion: string, statusFilter: string): boolean => {
    if (statusFilter === 'all') {
        return true;
    }
    return estadoAprobacion === statusFilter;
};

// Función de filtrado de solicitudes optimizada con memoización
const filterRequests = (requests: CategoryRequest[], filters: any) => {
    // Si no hay filtros activos, retornar todas las solicitudes
    if (filters.dateFilter === 'all' && filters.statusFilter === 'all') {
        return requests;
    }

    return requests.filter(request => {
        const requestDate = new Date(request.created_at);
        const matchesDate = matchesDateFilter(requestDate, filters.dateFilter, filters.customDate);
        const matchesStatus = matchesStatusFilter(request.estado_aprobacion, filters.statusFilter);
        
        return matchesDate && matchesStatus;
    });
};

// Función auxiliar para obtener las clases CSS según el estado de aprobación
const getEstadoAprobacionClasses = (estadoAprobacion: string): string => {
    if (estadoAprobacion === 'pendiente') {
        return 'bg-yellow-100 text-yellow-800';
    }
    if (estadoAprobacion === 'aprobada') {
        return 'bg-green-100 text-green-800';
    }
    return 'bg-red-100 text-red-800';
};

const AdminCategoryRequestsPage: React.FC = () => {
    const [requests, setRequests] = useState<CategoryRequest[]>([]);
    const [filteredRequests, setFilteredRequests] = useState<CategoryRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingEmails, setLoadingEmails] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Estados de filtros
    const [filters, setFilters] = useState({
        dateFilter: 'all',
        customDate: '',
        statusFilter: 'all'
    });
    const [rejectComment, setRejectComment] = useState<string>('');
    const [selectedRequest, setSelectedRequest] = useState<CategoryRequest | null>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editForm, setEditForm] = useState({
        nombre_categoria: '',
        descripcion: '',
        nombre_empresa: '',
        nombre_contacto: '',
        email_contacto: ''
    });

    useEffect(() => {
        loadRequests();
    }, []);

    // Aplicar filtros cuando cambien (memoizado)
    const filteredRequestsMemo = useMemo(() => {
        return filterRequests(requests, filters);
    }, [requests, filters]);

    useEffect(() => {
        // Usar una copia del array para evitar problemas de referencia
        setFilteredRequests([...filteredRequestsMemo]);
    }, [filteredRequestsMemo]);

    const resetFilters = useCallback(() => {
        setFilters({
            dateFilter: 'all',
            customDate: '',
            statusFilter: 'all'
        });
    }, []);

    // Función optimizada para cargar solicitudes
    const loadRequests = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                setError('No se encontró token de acceso. Por favor, inicia sesión nuevamente.');
                setLoading(false);
                return;
            }

            console.log('🚀 Cargando solicitudes de categorías...');
            const requestsData = await categoryRequestsAPI.getAllCategoryRequests(accessToken);
            console.log('📊 Solicitudes obtenidas:', requestsData?.length || 0);
            
            // Verificar que requestsData sea un array
            if (!Array.isArray(requestsData)) {
                console.error('❌ La respuesta no es un array:', requestsData);
                setError('Error: La respuesta del servidor no es válida');
                setLoading(false);
                return;
            }
            
            // Procesar solicitudes básicas primero (sin emails)
            // Asegurar que cada request tenga un id_solicitud único y válido
            const requestsBasic = requestsData
                .filter(request => request?.id_solicitud) // Filtrar requests inválidos
                .map(request => ({
                    ...request,
                    email_contacto: request.email_contacto || 'Cargando...',
                    nombre_empresa: request.nombre_empresa || '',
                    nombre_contacto: request.nombre_contacto || ''
                }));
            
            // Establecer datos básicos inmediatamente
            setRequests(requestsBasic);
            setLoading(false);
            
            // Cargar emails en segundo plano (lazy loading) solo si hay requests válidos
            if (requestsBasic.length > 0) {
                loadEmailsInBackground(requestsData, accessToken);
            }
            
        } catch (err: any) {
            console.error('❌ Error cargando solicitudes:', err);
            console.error('❌ Error completo:', err);
            const errorMessage = err?.detail || err?.message || 'Error al cargar las solicitudes. Por favor, intenta nuevamente.';
            setError(errorMessage);
            setLoading(false);
        }
    }, []);

    // Funciones auxiliares para búsqueda de emails
    // Función helper para extraer email de userData (elimina código duplicado)
    const extractEmailFromUserData = (userData: any): string | null => {
        if (!userData) return null;
        return typeof userData === 'string' ? userData : userData.email || null;
    };

    const getEmailByUserId = (user_id: string | undefined, emailsDict: {[key: string]: any}): string | null => {
        if (!user_id || !emailsDict[user_id]) {
            return null;
        }
        return extractEmailFromUserData(emailsDict[user_id]);
    };

    const findEmailByNombreMatch = (nombreContacto: string, emailsDict: {[key: string]: any}): string | null => {
        const emailMatch = Object.entries(emailsDict).find(([key, value]) => {
            const email = extractEmailFromUserData(value);
            if (!email) return false;
            
            const emailLower = email.toLowerCase();
            const nombreLower = nombreContacto.toLowerCase();
            
            const nombres = nombreLower.split(' ').filter(n => n.length > 2);
            if (nombres.length >= 2) {
                const emailLocal = emailLower.split('@')[0];
                const coincidencias = nombres.filter(nombre => 
                    emailLocal.includes(nombre) || nombre.includes(emailLocal)
                );
                return coincidencias.length >= 2;
            }
            
            return false;
        });
        
        if (emailMatch) {
            return extractEmailFromUserData(emailMatch[1]);
        }
        return null;
    };

    const getEmailByNombreContacto = (nombreContacto: string, emailsDict: {[key: string]: any}): string | null => {
        return extractEmailFromUserData(emailsDict[nombreContacto]);
    };

    const findEmailForRequest = (request: CategoryRequest, emailsDict: {[key: string]: any}): string => {
        const defaultEmail = 'No especificado';
        
        if (!request.nombre_contacto || request.nombre_contacto === 'No especificado') {
            return defaultEmail;
        }

        // Método 1: Buscar por ID de usuario (más confiable)
        const emailByUserId = getEmailByUserId(request.user_id, emailsDict);
        if (emailByUserId) {
            return emailByUserId;
        }

        // Método 2: Búsqueda más precisa por nombre en emails
        if (request.id_perfil) {
            const emailByMatch = findEmailByNombreMatch(request.nombre_contacto, emailsDict);
            if (emailByMatch) {
                return emailByMatch;
            }
        }

        // Método 3: Búsqueda por nombre de contacto (fallback)
        const emailByNombre = getEmailByNombreContacto(request.nombre_contacto, emailsDict);
        if (emailByNombre) {
            return emailByNombre;
        }

        return defaultEmail;
    };

    // Estrategia 1: Intentar endpoint específico de emails-only
    const tryLoadEmailsFromEmailsOnlyEndpoint = async (
        requestsData: CategoryRequest[], 
        accessToken: string
    ): Promise<{[key: string]: any}> => {
        try {
            const hasUserId = requestsData.some(request => request.user_id);
            let endpointUrl = buildApiUrl(API_CONFIG.ADMIN.USERS + '/emails-only');
            
            if (hasUserId) {
                const firstUserId = requestsData.find(request => request.user_id)?.user_id;
                if (firstUserId) {
                    endpointUrl += `?user_id=${firstUserId}`;
                }
            }
            
            const emailsResponse = await fetch(endpointUrl, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (emailsResponse.ok) {
                const emailsData = await emailsResponse.json();
                return emailsData.emails || {};
            }
        } catch (error) {
            if (process.env.NODE_ENV === 'development') {
                console.debug('Estrategia 1 (emails-only) falló, intentando estrategia 2:', error);
            }
        }
        return {};
    };

    // Estrategia 2: Usar endpoint de usuarios con emails
    const tryLoadEmailsFromUsersEndpoint = async (accessToken: string): Promise<{[key: string]: any}> => {
        try {
            const usersResponse = await fetch(buildApiUrl(API_CONFIG.ADMIN.USERS + '?page=1&limit=100'), {
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (usersResponse.ok) {
                const usersData = await usersResponse.json();
                const users = usersData.usuarios || [];
                
                const emailsDict: {[key: string]: any} = {};
                for (const user of users) {
                    if (user.nombre_contacto && user.email) {
                        emailsDict[user.nombre_contacto] = user.email;
                    }
                }
                return emailsDict;
            }
        } catch (error) {
            if (process.env.NODE_ENV === 'development') {
                console.debug('Estrategia 2 (usuarios con emails) falló, usando datos existentes:', error);
            }
        }
        return {};
    };

    // Procesar solicitudes con emails reales
    const processRequestsWithEmails = (
        requestsData: CategoryRequest[], 
        emailsDict: {[key: string]: any}
    ): CategoryRequest[] => {
        return requestsData.map(request => {
            const emailContacto = findEmailForRequest(request, emailsDict);
            
            return {
                ...request,
                email_contacto: emailContacto,
                nombre_empresa: request.nombre_empresa || '',
                nombre_contacto: request.nombre_contacto || ''
            };
        });
    };

    // Función optimizada para cargar emails reales con múltiples estrategias
    const loadEmailsInBackground = useCallback(async (requestsData: CategoryRequest[], accessToken: string) => {
        try {
            setLoadingEmails(true);
            
            // ESTRATEGIA 1: Intentar endpoint específico de emails-only
            let emailsDict = await tryLoadEmailsFromEmailsOnlyEndpoint(requestsData, accessToken);
            
            // ESTRATEGIA 2: Si la primera falla, usar endpoint de usuarios con emails
            if (Object.keys(emailsDict).length === 0) {
                emailsDict = await tryLoadEmailsFromUsersEndpoint(accessToken);
            }
            
            // ESTRATEGIA 3: Si ambas fallan, usar datos existentes y mostrar mensaje
            if (Object.keys(emailsDict).length === 0) {
                setLoadingEmails(false);
                return;
            }
            
            // Procesar solicitudes con emails reales
            const requestsWithEmails = processRequestsWithEmails(requestsData, emailsDict);
            
            // Actualizar con emails reales usando función de actualización que preserva la estructura
            setRequests(prevRequests => {
                // Si no hay requests previos, usar los nuevos directamente
                if (prevRequests.length === 0) {
                    return requestsWithEmails;
                }
                
                // Crear un mapa de requests existentes por id_solicitud para preservar referencias
                const prevMap = new Map(prevRequests.map(req => [req.id_solicitud, req]));
                
                // Actualizar solo los emails, manteniendo el mismo orden y estructura
                const updated = requestsWithEmails.map(newRequest => {
                    const prevRequest = prevMap.get(newRequest.id_solicitud);
                    if (prevRequest) {
                        // Solo actualizar el email si es diferente para evitar re-renders innecesarios
                        if (prevRequest.email_contacto === newRequest.email_contacto) {
                            return prevRequest; // Mantener la misma referencia
                        }
                        return {
                            ...prevRequest,
                            email_contacto: newRequest.email_contacto
                        };
                    }
                    return newRequest;
                });
                
                return updated;
            });
            
        } catch (error) {
            console.error('Error obteniendo emails reales:', error);
        } finally {
            setLoadingEmails(false);
        }
    }, []);

    // Funciones helper para eliminar código duplicado
    const getAccessToken = (): string | null => {
        return localStorage.getItem('access_token');
    };

    const updateRequestInState = (requestId: number, updates: Partial<CategoryRequest>) => {
        setRequests(prev => prev.map(req => 
            req.id_solicitud === requestId 
                ? { ...req, ...updates }
                : req
        ));
    };

    const showSuccessMessage = (message: string) => {
        setSuccess(message);
        setTimeout(() => setSuccess(null), 3000);
    };

    const showErrorMessage = (message: string) => {
        setError(message);
        setTimeout(() => setError(null), 3000);
    };

    const handleEdit = useCallback(async (requestId: number, formData: any) => {
        try {
            const accessToken = getAccessToken();
            if (!accessToken) return;

            //Implementar updateCategoryRequest en la API
            console.log('Actualizando solicitud de categoría:', requestId, formData);
            
            // Actualizar estado local sin recargar
            updateRequestInState(requestId, formData);
            
            setShowEditModal(false);
            showSuccessMessage('Solicitud actualizada exitosamente');
        } catch (error) {
            console.error('Error al actualizar la solicitud:', error);
            showErrorMessage('Error al actualizar la solicitud');
        }
    }, []);

    // Funciones de acción optimizadas
    const handleApprove = useCallback(async (requestId: number) => {
        try {
            const accessToken = getAccessToken();
            if (!accessToken) return;

            await categoryRequestsAPI.approveCategoryRequest(requestId, null, accessToken);
            
            // Actualizar estado local sin recargar
            updateRequestInState(requestId, { estado_aprobacion: 'aprobada' });
            
            showSuccessMessage('Solicitud aprobada exitosamente');
        } catch (error) {
            console.error('Error al aprobar la solicitud:', error);
            showErrorMessage('Error al aprobar la solicitud');
        }
    }, []);

    const handleReject = useCallback(async (requestId: number, comment: string) => {
        try {
            const accessToken = getAccessToken();
            if (!accessToken) return;

            await categoryRequestsAPI.rejectCategoryRequest(requestId, comment, accessToken);
            
            // Actualizar estado local sin recargar
            updateRequestInState(requestId, { estado_aprobacion: 'rechazada', comentario_admin: comment });
            
            setShowRejectModal(false);
            setRejectComment('');
            showSuccessMessage('Solicitud rechazada exitosamente');
        } catch (error) {
            console.error('Error al rechazar la solicitud:', error);
            showErrorMessage('Error al rechazar la solicitud');
        }
    }, []);

    // Renderizado optimizado
    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <OptimizedLoading />
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">Solicitudes de Categorías</h1>
                    <p className="mt-2 text-gray-600">Gestiona las solicitudes de nuevas categorías</p>
                </div>

                {/* Mensajes de estado */}
                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
                        <div className="flex items-center justify-between">
                            <p className="text-red-800">{error}</p>
                            <button
                                onClick={() => {
                                    setError(null);
                                    loadRequests();
                                }}
                                className="ml-4 text-sm text-red-600 hover:text-red-800 underline"
                            >
                                Reintentar
                            </button>
                        </div>
                    </div>
                )}

                {success && (
                    <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
                        <p className="text-green-800">{success}</p>
                    </div>
                )}

                {/* Filtros */}
                <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-medium text-gray-900">Filtros</h2>
                        <button
                            onClick={resetFilters}
                            className="text-sm text-blue-600 hover:text-blue-800"
                        >
                            Limpiar Filtros
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Filtro por fecha */}
                        <div>
                            <label htmlFor="filter-date" className="block text-sm font-medium text-gray-700 mb-2">Fecha</label>
                            <select
                                id="filter-date"
                                value={filters.dateFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, dateFilter: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todas las fechas</option>
                                <option value="today">Hoy</option>
                                <option value="week">Esta semana</option>
                                <option value="month">Este mes</option>
                                <option value="year">Este año</option>
                                <option value="custom">Fecha específica</option>
                            </select>
                        </div>

                        {/* Filtro por estado */}
                        <div>
                            <label htmlFor="filter-status" className="block text-sm font-medium text-gray-700 mb-2">Estado</label>
                            <select
                                id="filter-status"
                                value={filters.statusFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, statusFilter: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todos los estados</option>
                                <option value="pendiente">Pendiente</option>
                                <option value="aprobada">Aprobada</option>
                                <option value="rechazada">Rechazada</option>
                            </select>
                        </div>

                        {/* Fecha personalizada */}
                        {filters.dateFilter === 'custom' && (
                            <div>
                                <label htmlFor="filter-custom-date" className="block text-sm font-medium text-gray-700 mb-2">Fecha específica</label>
                                <input
                                    id="filter-custom-date"
                                    type="date"
                                    value={filters.customDate}
                                    onChange={(e) => setFilters(prev => ({ ...prev, customDate: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* Contador de resultados */}
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <div className="text-center sm:text-left">
                            <h3 className="text-lg font-medium text-gray-900">
                                Total: {filteredRequests.length} solicitudes
                            </h3>
                        </div>
                        <div className="text-center sm:text-right">
                            <div className="text-sm text-gray-500">
                                {filteredRequests.length > 0 && (
                                    <span className="text-gray-600">
                                        Mostrando {filteredRequests.length} de {requests.length} resultados
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Lista de solicitudes */}
                <div className="bg-white rounded-lg shadow border border-gray-200">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-lg font-medium text-gray-900">
                            Solicitudes
                        </h2>
                    </div>

                    <div className="p-6">
                        {filteredRequests.length === 0 ? (
                            <div className="text-center py-12">
                                <ClockIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-gray-900 mb-2">No hay solicitudes</h3>
                                <p className="text-gray-500">No se encontraron solicitudes que coincidan con los filtros aplicados.</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {filteredRequests.map((request) => (
                                    <div key={request.id_solicitud} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between space-y-4 sm:space-y-0">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3 mb-2">
                                                    <h3 className="text-lg font-medium text-gray-900 break-words">{request.nombre_categoria}</h3>
                                                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getEstadoAprobacionClasses(request.estado_aprobacion)}`}>
                                                        {request.estado_aprobacion}
                                                    </span>
                                                </div>
                                                
                                                <p className="text-gray-600 mb-2 break-words">{request.descripcion}</p>
                                                
                                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 text-sm text-gray-500">
                                                    <div className="break-words">
                                                        <span className="font-medium">Empresa:</span> {request.nombre_empresa || 'No especificada'}
                                                    </div>
                                                    <div className="break-words">
                                                        <span className="font-medium">Contacto:</span> {request.nombre_contacto || 'No especificado'}
                                                    </div>
                                                    <div className="break-words sm:col-span-2 lg:col-span-1">
                                                        <span className="font-medium">Email:</span> 
                                                        {loadingEmails && request.email_contacto === 'Cargando...' ? (
                                                            <span className="text-blue-600"> Cargando...</span>
                                                        ) : (
                                                            <span> {request.email_contacto || 'No especificado'}</span>
                                                        )}
                                                    </div>
                                                </div>
                                                
                                                <div className="mt-2 text-sm text-gray-500 break-words">
                                                    <span className="font-medium">Fecha:</span> {formatArgentinaDate(request.created_at)}
                                                </div>
                                            </div>
                                            
                                            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2 sm:ml-4">
                                                {request.estado_aprobacion === 'pendiente' && (
                                                    <>
                                                        <button
                                                            onClick={() => handleApprove(request.id_solicitud)}
                                                            className="w-full sm:w-auto flex items-center justify-center px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                                                        >
                                                            <CheckCircleIcon className="w-4 h-4 mr-1" />
                                                            Aprobar
                                                        </button>
                                                        <button
                                                            onClick={() => {
                                                                setSelectedRequest(request);
                                                                setShowRejectModal(true);
                                                            }}
                                                            className="w-full sm:w-auto flex items-center justify-center px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                                                        >
                                                            <XMarkIcon className="w-4 h-4 mr-1" />
                                                            Rechazar
                                                        </button>
                                                    </>
                                                )}
                                                
                                                <button
                                                    onClick={() => {
                                                        setSelectedRequest(request);
                                                        setEditForm({
                                                            nombre_categoria: request.nombre_categoria,
                                                            descripcion: request.descripcion,
                                                            nombre_empresa: request.nombre_empresa || '',
                                                            nombre_contacto: request.nombre_contacto || '',
                                                            email_contacto: request.email_contacto || ''
                                                        });
                                                        setShowEditModal(true);
                                                    }}
                                                    className="w-full sm:w-auto flex items-center justify-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                                                >
                                                    <PencilIcon className="w-4 h-4 mr-1" />
                                                    Editar
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Modal de Rechazo */}
            {showRejectModal && selectedRequest && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg p-4 sm:p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">Rechazar Solicitud</h3>
                        <p className="text-gray-600 mb-4 text-sm sm:text-base">
                            ¿Estás seguro de que deseas rechazar la solicitud "{selectedRequest.nombre_categoria}"?
                        </p>
                        <div className="mb-4">
                            <label htmlFor="reject-comment" className="block text-sm font-medium text-gray-700 mb-2">
                                Comentario *
                            </label>
                            <textarea
                                id="reject-comment"
                                value={rejectComment}
                                onChange={(e) => setRejectComment(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
                                rows={3}
                                placeholder="Motivo del rechazo..."
                                required
                            />
                        </div>
                        <div className="flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={() => {
                                    setShowRejectModal(false);
                                    setRejectComment('');
                                }}
                                className="flex-1 px-3 py-2 sm:px-4 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 text-sm sm:text-base"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={() => {
                                    if (rejectComment.trim()) {
                                        handleReject(selectedRequest.id_solicitud, rejectComment);
                                    }
                                }}
                                disabled={!rejectComment.trim()}
                                className="flex-1 px-3 py-2 sm:px-4 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                            >
                                Rechazar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Edición */}
            {showEditModal && selectedRequest && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">Editar Solicitud de Categoría</h3>
                        <form onSubmit={(e) => {
                            e.preventDefault();
                            handleEdit(selectedRequest.id_solicitud, editForm);
                        }}>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label htmlFor="edit-nombre-categoria" className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre de la Categoría *
                                    </label>
                                    <input
                                        id="edit-nombre-categoria"
                                        type="text"
                                        value={editForm.nombre_categoria}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, nombre_categoria: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        required
                                    />
                                </div>
                                <div>
                                    <label htmlFor="edit-nombre-empresa" className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre de la Empresa
                                    </label>
                                    <input
                                        id="edit-nombre-empresa"
                                        type="text"
                                        value={editForm.nombre_empresa}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, nombre_empresa: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>

                            <div className="mb-4">
                                <label htmlFor="edit-descripcion" className="block text-sm font-medium text-gray-700 mb-2">
                                    Descripción *
                                </label>
                                <textarea
                                    id="edit-descripcion"
                                    value={editForm.descripcion}
                                    onChange={(e) => setEditForm(prev => ({ ...prev, descripcion: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    rows={3}
                                    required
                                />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label htmlFor="edit-nombre-contacto" className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre de Contacto
                                    </label>
                                    <input
                                        id="edit-nombre-contacto"
                                        type="text"
                                        value={editForm.nombre_contacto}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, nombre_contacto: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="edit-email-contacto" className="block text-sm font-medium text-gray-700 mb-2">
                                        Email de Contacto
                                    </label>
                                    <input
                                        id="edit-email-contacto"
                                        type="email"
                                        value={editForm.email_contacto}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, email_contacto: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>

                            <div className="flex space-x-3">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowEditModal(false);
                                        setEditForm({
                                            nombre_categoria: '',
                                            descripcion: '',
                                            nombre_empresa: '',
                                            nombre_contacto: '',
                                            email_contacto: ''
                                        });
                                    }}
                                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                >
                                    Guardar Cambios
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminCategoryRequestsPage;
