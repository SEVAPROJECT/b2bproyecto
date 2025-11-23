import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { 
    
    PlusCircleIcon, 
    BuildingStorefrontIcon, 
    ClockIcon
} from '../../components/icons';
import { AuthContext } from '../../contexts/AuthContext';
import { categoriesAPI, serviceRequestsAPI, categoryRequestsAPI } from '../../services/api';
import { ServiceRequest, CategoryRequest } from '../../types';

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


// Tipo unificado para manejar ambos tipos de solicitudes
type UnifiedRequest = (ServiceRequest & { tipo: 'servicio' }) | (CategoryRequest & { tipo: 'categoria' });

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

const formatDateSpanish = (date: Date): string => {
    return date.toLocaleDateString('es-ES', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
};

const formatDateStringSpanish = (dateString: string): string => {
    const date = parseDateString(dateString);
    return formatDateSpanish(date);
};

// Funciones auxiliares fuera del componente para evitar errores de referencia
const getRequestName = (request: UnifiedRequest): string => {
    if (request.tipo === 'servicio') {
        return request.nombre_servicio || '';
    } else {
        return request.nombre_categoria || '';
    }
};

const getRequestTypeLabel = (request: UnifiedRequest): string => {
    return request.tipo === 'servicio' ? 'Servicio' : 'Categoría';
};

const getRequestTypeIcon = (request: UnifiedRequest): string => {
    return request.tipo === 'servicio' ? '🛠️' : '📂';
};

// Funciones helper para reducir complejidad cognitiva
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

const matchesCategoryFilter = (requestCategory: number | undefined, categoryFilter: string): boolean => {
    if (categoryFilter === 'all') {
        return true;
    }
    return requestCategory?.toString() === categoryFilter;
};

const matchesStatusFilter = (estadoAprobacion: string, statusFilter: string): boolean => {
    if (statusFilter === 'all') {
        return true;
    }
    return estadoAprobacion === statusFilter;
};

const matchesTypeFilter = (tipo: string, typeFilter: string): boolean => {
    if (typeFilter === 'all') {
        return true;
    }
    return tipo === typeFilter;
};

const matchesSearchFilter = (request: UnifiedRequest, searchFilter: string): boolean => {
    if (!searchFilter || searchFilter.trim() === '') {
        return true;
    }
    
    const searchTerm = searchFilter.toLowerCase().trim();
    const requestName = getRequestName(request)?.toLowerCase() || '';
    const requestDescription = request.descripcion?.toLowerCase() || '';
    
    return requestName.includes(searchTerm) || requestDescription.includes(searchTerm);
};

// Función de filtrado de solicitudes (refactorizada para reducir complejidad cognitiva)
const filterRequests = (requests: UnifiedRequest[], filters: any) => {
    return requests.filter(request => {
        const requestDate = new Date(request.created_at);
        
        const matchesDate = matchesDateFilter(requestDate, filters.dateFilter, filters.customDate);
        const matchesCategory = matchesCategoryFilter(request.id_categoria, filters.categoryFilter);
        const matchesStatus = matchesStatusFilter(request.estado_aprobacion, filters.statusFilter);
        const matchesType = matchesTypeFilter(request.tipo, filters.typeFilter);
        const matchesSearch = matchesSearchFilter(request, filters.searchFilter);
        
        if (!matchesCategory) {
            console.log('🚫 Filtro categoría rechaza:', {
                requestId: request.id_solicitud,
                requestCategory: request.id_categoria,
                filterCategory: filters.categoryFilter,
                requestName: getRequestName(request)
            });
        }
        
        return matchesDate && matchesCategory && matchesStatus && matchesType && matchesSearch;
    });
};

const ProviderMyRequestsPage: React.FC = () => {
    
    const [requests, setRequests] = useState<UnifiedRequest[]>([]);
    const [filteredRequests, setFilteredRequests] = useState<UnifiedRequest[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    
    // Estados para el formulario de nueva solicitud
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [requestType, setRequestType] = useState<'servicio' | 'categoria'>('servicio');
    const [submittingRequest, setSubmittingRequest] = useState(false);
    const [newServiceName, setNewServiceName] = useState('');
    const [newServiceDescription, setNewServiceDescription] = useState('');
    const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);

    // Estados de filtros
    const [filters, setFilters] = useState({
        dateFilter: 'all',
        customDate: '',
        categoryFilter: 'all',
        statusFilter: 'all',
        typeFilter: 'all',
        searchFilter: ''
    });

    useEffect(() => {
        loadData();
    }, []);

    // Aplicar filtros cuando cambien (con logging para debug)
    useEffect(() => {
        console.log('🔍 Aplicando filtros:', {
            totalRequests: requests.length,
            filters: filters,
            requests: requests.slice(0, 2) // Solo los primeros 2 para debug
        });
        const filtered = filterRequests(requests, filters);
        console.log('✅ Filtros aplicados:', {
            filteredCount: filtered.length,
            filtered: filtered.slice(0, 2) // Solo los primeros 2 para debug
        });
        
        // Forzar actualización del estado
        setFilteredRequests([]);
        setTimeout(() => setFilteredRequests(filtered), 0);
    }, [requests, filters]);

    const loadData = async () => {
        try {
            setLoading(true);
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            // Cargar solicitudes de servicios, categorías y categorías disponibles en paralelo
            const [serviceRequestsData, categoryRequestsData, categoriesData] = await Promise.all([
                serviceRequestsAPI.getMyServiceRequests(accessToken),
                categoryRequestsAPI.getMyCategoryRequests(accessToken),
                categoriesAPI.getCategories(accessToken)
            ]);

            // Combinar y marcar el tipo de solicitud, enriqueciendo con nombres de categorías
            const unifiedRequests: UnifiedRequest[] = [
                ...serviceRequestsData.map(req => {
                    const categoria = categoriesData.find(cat => cat.id_categoria === req.id_categoria);
                    return { 
                        ...req, 
                        tipo: 'servicio' as const,
                        nombre_categoria: categoria?.nombre || 'No especificado'
                    };
                }),
                ...categoryRequestsData.map(req => ({ ...req, tipo: 'categoria' as const }))
            ];

            // Ordenar por fecha de creación (más recientes primero)
            unifiedRequests.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

            setRequests(unifiedRequests);
            setCategories(categoriesData.filter(cat => cat.estado)); // Solo categorías activas
        } catch (err: any) {
            setError(err.detail || 'Error al cargar los datos');
        } finally {
            setLoading(false);
        }
    };

    // Función para recargar datos sin mostrar el estado de carga
    const loadDataSilently = async () => {
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            // Cargar solicitudes de servicios, categorías y categorías disponibles en paralelo
            const [serviceRequestsData, categoryRequestsData, categoriesData] = await Promise.all([
                serviceRequestsAPI.getMyServiceRequests(accessToken),
                categoryRequestsAPI.getMyCategoryRequests(accessToken),
                categoriesAPI.getCategories(accessToken)
            ]);

            // Combinar y marcar el tipo de solicitud, enriqueciendo con nombres de categorías
            const unifiedRequests: UnifiedRequest[] = [
                ...serviceRequestsData.map(req => {
                    const categoria = categoriesData.find(cat => cat.id_categoria === req.id_categoria);
                    return { 
                        ...req, 
                        tipo: 'servicio' as const,
                        nombre_categoria: categoria?.nombre || 'No especificado'
                    };
                }),
                ...categoryRequestsData.map(req => ({ ...req, tipo: 'categoria' as const }))
            ];

            // Ordenar por fecha de creación (más recientes primero)
            unifiedRequests.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

            setRequests(unifiedRequests);
            setCategories(categoriesData.filter(cat => cat.estado)); // Solo categorías activas
        } catch (err: any) {
            console.error('Error al recargar datos silenciosamente:', err);
        }
    };

    const resetFilters = () => {
        setFilters({
            dateFilter: 'all',
            customDate: '',
            categoryFilter: 'all',
            statusFilter: 'all',
            typeFilter: 'all',
            searchFilter: ''
        });
    };

    const getStatusColor = (estado: string) => {
        switch (estado) {
            case 'aprobada':
                return 'bg-green-100 text-green-800';
            case 'rechazada':
                return 'bg-red-100 text-red-800';
            case 'pendiente':
                return 'bg-yellow-100 text-yellow-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusText = (estado: string) => {
        switch (estado) {
            case 'aprobada':
                return 'Aprobada';
            case 'rechazada':
                return 'Rechazada';
            case 'pendiente':
                return 'Pendiente';
            default:
                return estado;
        }
    };

    const renderRequestsContent = () => {
        if (filteredRequests.length > 0) {
            return (
                <div className="divide-y divide-gray-200">
                    {filteredRequests.map((request) => {
                        // Detectar si es una solicitud temporal (optimista)
                        const isOptimistic = request.id > 1000000000000; // IDs temporales son timestamps
                        
                        return (
                        <div key={request.id_solicitud} className={`p-4 hover:bg-gray-50 transition-colors duration-200 ${isOptimistic ? 'bg-blue-50 border-l-4 border-blue-400' : ''}`}>
                            <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
                                {/* Icono del tipo de solicitud */}
                                <div className="flex-shrink-0 mx-auto sm:mx-0">
                                    <div className={`h-16 w-16 rounded-lg border flex items-center justify-center ${isOptimistic ? 'bg-blue-100 border-blue-200' : 'bg-gray-100 border-gray-200'}`}>
                                        {isOptimistic ? (
                                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                        ) : (
                                            <span className="text-2xl">{getRequestTypeIcon(request)}</span>
                                        )}
                                    </div>
                                </div>

                                {/* Información principal */}
                                <div className="flex-1 min-w-0 text-center sm:text-left">
                                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
                                                <h3 className="text-lg font-semibold text-gray-900 break-words">{getRequestName(request)}</h3>
                                                <div className="flex flex-wrap justify-center sm:justify-start gap-2">
                                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                        {getRequestTypeLabel(request)}
                                                    </span>
                                                    {isOptimistic && (
                                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                                            Enviando...
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <p className="text-sm text-gray-600 mt-1 break-words">{request.descripcion}</p>
                                        </div>
                                        <div className="flex justify-center sm:justify-end">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.estado_aprobacion)}`}>
                                                {getStatusText(request.estado_aprobacion)}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Información compacta - responsive */}
                                <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-6 text-sm">
                                    {/* Categoría - Solo para servicios */}
                                    {request.tipo === 'servicio' && (
                                        <div className="text-center">
                                            <p className="text-xs font-medium text-gray-500 mb-1">📂 Categoría</p>
                                            <p className="font-semibold text-blue-600 break-words">
                                                {request.nombre_categoria || 'No especificado'}
                                            </p>
                                        </div>
                                    )}

                                    {/* Empresa */}
                                    <div className="text-center">
                                        <p className="text-xs font-medium text-gray-500 mb-1">🏢 Empresa</p>
                                        <p className="font-semibold text-gray-600 break-words">
                                            {request.nombre_empresa || 'No especificado'}
                                        </p>
                                    </div>

                                    {/* Fecha */}
                                    <div className="text-center">
                                        <p className="text-xs font-medium text-gray-500 mb-1">📅 Fecha</p>
                                        <p className="font-semibold text-gray-600">
                                            {formatArgentinaDate(request.created_at)}
                                        </p>
                                    </div>

                                    {/* Estado */}
                                    <div className="text-center">
                                        <p className="text-xs font-medium text-gray-500 mb-1">📊 Estado</p>
                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.estado_aprobacion)}`}>
                                            {getStatusText(request.estado_aprobacion)}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Mostrar comentario del admin si fue rechazada */}
                            {request.estado_aprobacion === 'rechazada' && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                    <div className="bg-red-50 border-l-4 border-red-400 rounded-r-md p-3">
                                        <div className="flex items-start">
                                            <div className="flex-shrink-0">
                                                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                                </svg>
                                            </div>
                                            <div className="ml-3">
                                                <h4 className="text-sm font-medium text-red-800 mb-1">Motivo del rechazo</h4>
                                                <p className="text-sm text-red-700">
                                                    {request.comentario_admin?.trim() || "Sin motivo especificado"}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                        );
                    })}
                </div>
            );
        }
        
        if (requests.length === 0) {
            return (
                <div className="text-center py-12">
                    <PlusCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No has enviado solicitudes</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        Explora las categorías disponibles para solicitar nuevos servicios.
                    </p>
                    <Link
                        to="/dashboard/explore-categories"
                        className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                    >
                        <BuildingStorefrontIcon className="h-5 w-5 mr-2" />
                        Explorar Categorías
                    </Link>
                </div>
            );
        }
        
        return (
            <div className="text-center py-12">
                <ClockIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No hay solicitudes</h3>
                <p className="text-gray-500">No se encontraron solicitudes que coincidan con los filtros aplicados.</p>
                <button
                    onClick={resetFilters}
                    className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                >
                    🔄 Limpiar Filtros
                </button>
            </div>
        );
    };

    const handleCreateRequest = async () => {
        if (!newServiceName.trim() || !newServiceDescription.trim()) {
            setError('Por favor completa todos los campos requeridos');
            setTimeout(() => setError(null), 3000);
            return;
        }

        // Para servicios, también necesitamos la categoría
        if (requestType === 'servicio' && !selectedCategoryId) {
            setError('Por favor selecciona una categoría para el servicio');
            setTimeout(() => setError(null), 3000);
            return;
        }

        // Crear objeto de solicitud optimista
        const tempId = Date.now(); // ID temporal para la actualización optimista
        
        try {
            setSubmittingRequest(true);
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;
            const optimisticRequest: UnifiedRequest = {
                id: tempId,
                nombre_servicio: requestType === 'servicio' ? newServiceName.trim() : '',
                nombre_categoria: requestType === 'categoria' ? newServiceName.trim() : '',
                descripcion: newServiceDescription.trim(),
                estado: 'pendiente',
                fecha_solicitud: new Date().toISOString().split('T')[0],
                id_categoria: selectedCategoryId || 0,
                comentario_admin: null,
                tipo: requestType
            } as UnifiedRequest;

            // Actualización optimista: agregar la solicitud inmediatamente
            setRequests(prevRequests => [optimisticRequest, ...prevRequests]);

            // Limpiar formulario inmediatamente
            setNewServiceName('');
            setNewServiceDescription('');
            setSelectedCategoryId(null);
            setShowCreateForm(false);

            // Mostrar mensaje de éxito inmediatamente
            if (requestType === 'servicio') {
                setSuccess('Solicitud de servicio enviada exitosamente');
            } else {
                setSuccess('Solicitud de categoría enviada exitosamente');
            }

            // Llamar a la API en segundo plano
            let createdRequest;
            if (requestType === 'servicio') {
                createdRequest = await serviceRequestsAPI.proposeService({
                    nombre_servicio: newServiceName.trim(),
                    descripcion: newServiceDescription.trim(),
                    id_categoria: selectedCategoryId!,
                    comentario_admin: null
                }, accessToken);
            } else {
                createdRequest = await categoryRequestsAPI.createCategoryRequest({
                    nombre_categoria: newServiceName.trim(),
                    descripcion: newServiceDescription.trim()
                }, accessToken);
            }

            // Actualizar la solicitud optimista con los datos reales
            if (createdRequest) {
                setRequests(prevRequests => 
                    prevRequests.map(req => 
                        req.id === tempId 
                            ? { ...createdRequest, tipo: requestType } as UnifiedRequest
                            : req
                    )
                );
            } else {
                // Si no se devuelve la solicitud creada, recargar solo los datos
                // pero sin mostrar el estado de carga
                await loadDataSilently();
            }
            
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            // Revertir la actualización optimista en caso de error
            setRequests(prevRequests => 
                prevRequests.filter(req => req.id !== tempId)
            );
            
            setError(err.detail || 'Error al enviar solicitud');
            setTimeout(() => setError(null), 3000);
        } finally {
            setSubmittingRequest(false);
        }
    };

    const handleCancelCreate = () => {
        setShowCreateForm(false);
        setRequestType('servicio');
        setNewServiceName('');
        setNewServiceDescription('');
        setSelectedCategoryId(null);
        setError(null);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Cargando tus solicitudes...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900">Mis Solicitudes</h1>
                                <p className="mt-1 text-sm text-gray-500">
                                    Revisa el estado de todas las solicitudes de servicios y categorías que has enviado
                                </p>
                            </div>
                            <button
                                onClick={() => setShowCreateForm(true)}
                                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                <PlusCircleIcon className="h-5 w-5 mr-2" />
                                Nueva Solicitud
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Messages */}
                {error && (
                    <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
                        <div className="text-sm text-red-700">{error}</div>
                    </div>
                )}
                {success && (
                    <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4">
                        <div className="text-sm text-green-700">{success}</div>
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

                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                        {/* Filtro por fecha */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Fecha</label>
                            <select
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

                        {/* Filtro por categoría */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Categoría</label>
                            <select
                                value={filters.categoryFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, categoryFilter: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todas las categorías</option>
                                {categories.map(category => (
                                    <option key={category.id_categoria} value={category.id_categoria}>
                                        {category.nombre}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Filtro por estado */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Estado</label>
                            <select
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

                        {/* Filtro por tipo de solicitud */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo</label>
                            <select
                                value={filters.typeFilter || 'all'}
                                onChange={(e) => setFilters(prev => ({ ...prev, typeFilter: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todos los tipos</option>
                                <option value="servicio">Servicios</option>
                                <option value="categoria">Categorías</option>
                            </select>
                        </div>

                        {/* Fecha personalizada */}
                        {filters.dateFilter === 'custom' ? (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Fecha específica</label>
                                <input
                                    type="date"
                                    value={filters.customDate}
                                    onChange={(e) => setFilters(prev => ({ ...prev, customDate: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        ) : (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
                                <input
                                    type="text"
                                    value={filters.searchFilter || ''}
                                    onChange={(e) => setFilters(prev => ({ ...prev, searchFilter: e.target.value }))}
                                    placeholder="Buscar por nombre..."
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

                {/* Error Message */}
                {error && (
                    <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
                        <div className="text-sm text-red-700">{error}</div>
                    </div>
                )}

                {/* Requests List */}
                <div key={`requests-${filteredRequests.length}-${filters.categoryFilter}`} className="bg-white shadow overflow-hidden sm:rounded-md">
                    {(() => {
                        console.log('🎨 RENDERIZANDO:', {
                            filteredRequestsLength: filteredRequests.length,
                            filteredRequestsIds: filteredRequests.map(r => r.id_solicitud),
                            showingList: filteredRequests.length > 0
                        });
                        return null;
                    })()}
                    {renderRequestsContent()}
                </div>
            </div>

            {/* Modal para crear nueva solicitud */}
            {showCreateForm && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
                    <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-auto">
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    Nueva Solicitud
                                </h3>
                                <button
                                    onClick={handleCancelCreate}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>

                            <form onSubmit={(e) => { e.preventDefault(); handleCreateRequest(); }}>
                                <div className="space-y-4">
                                    {/* Tipo de solicitud */}
                                    <div>
                                        <label htmlFor="requestType" className="block text-sm font-medium text-gray-700 mb-2">
                                            Tipo de Solicitud *
                                        </label>
                                        <select
                                            id="requestType"
                                            value={requestType}
                                            onChange={(e) => setRequestType(e.target.value as 'servicio' | 'categoria')}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            required
                                        >
                                            <option value="servicio">🛠️ Servicio</option>
                                            <option value="categoria">📂 Categoría</option>
                                        </select>
                                    </div>

                                    {/* Nombre del servicio/categoría */}
                                    <div>
                                        <label htmlFor="serviceName" className="block text-sm font-medium text-gray-700 mb-2">
                                            {requestType === 'servicio' ? 'Nombre del Servicio' : 'Nombre de la Categoría'} *
                                        </label>
                                        <input
                                            type="text"
                                            id="serviceName"
                                            value={newServiceName}
                                            onChange={(e) => setNewServiceName(e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder={requestType === 'servicio' ? "Ej: Servicio de Catering Premium" : "Ej: Servicios de Limpieza"}
                                            required
                                        />
                                    </div>

                                    {/* Categoría - Solo para servicios */}
                                    {requestType === 'servicio' && (
                                        <div>
                                            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                                                Categoría *
                                            </label>
                                            <select
                                                id="category"
                                                value={selectedCategoryId || ''}
                                                onChange={(e) => setSelectedCategoryId(Number(e.target.value))}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                required
                                            >
                                                <option value="">Selecciona una categoría</option>
                                                {categories.map(category => (
                                                    <option key={category.id_categoria} value={category.id_categoria}>
                                                        {category.nombre}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    )}

                                    {/* Descripción */}
                                    <div>
                                        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                                            {requestType === 'servicio' ? 'Descripción del Servicio' : 'Descripción de la Categoría'} *
                                        </label>
                                        <textarea
                                            id="description"
                                            value={newServiceDescription}
                                            onChange={(e) => setNewServiceDescription(e.target.value)}
                                            rows={4}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder={requestType === 'servicio' ? "Describe detalladamente el servicio que deseas ofrecer..." : "Describe detalladamente la categoría que deseas proponer..."}
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="flex justify-end space-x-3 mt-6">
                                    <button
                                        type="button"
                                        onClick={handleCancelCreate}
                                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                                    >
                                        Cancelar
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={submittingRequest}
                                        className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed rounded-md transition-colors duration-200"
                                    >
                                        {submittingRequest ? (
                                            <>
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                Enviando...
                                            </>
                                        ) : (
                                            'Enviar Solicitud'
                                        )}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProviderMyRequestsPage;
