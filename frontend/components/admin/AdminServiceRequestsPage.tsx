import React, { useState, useEffect, useContext, useCallback, useMemo } from 'react';
import { CheckCircleIcon, ClockIcon, PencilIcon, XMarkIcon } from '../icons';
import OptimizedLoading from '../ui/OptimizedLoading';
import StandardFilters from '../ui/StandardFilters';
import StandardStatistics from '../ui/StandardStatistics';
import { useStandardFilters } from '../../hooks/useStandardFilters';
import { serviceRequestsAPI, categoriesAPI } from '../../services/api';
import { AuthContext } from '../../contexts/AuthContext';

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

// Función de filtrado de solicitudes optimizada con memoización
const filterRequests = (requests: ServiceRequest[], filters: any) => {
    // Si no hay filtros activos, retornar todas las solicitudes
    if (filters.dateFilter === 'all' && filters.categoryFilter === 'all' && filters.statusFilter === 'all') {
        return requests;
    }

    return requests.filter(request => {
        // Filtro por fecha
        if (filters.dateFilter !== 'all') {
            const now = new Date();
            const requestDate = new Date(request.created_at);

            switch (filters.dateFilter) {
                case 'today':
                    if (requestDate.toDateString() !== now.toDateString()) return false;
                    break;
                case 'week':
                    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    if (requestDate < weekAgo) return false;
                    break;
                case 'month':
                    if (requestDate.getMonth() !== now.getMonth() || requestDate.getFullYear() !== now.getFullYear()) return false;
                    break;
                case 'year':
                    if (requestDate.getFullYear() !== now.getFullYear()) return false;
                    break;
                case 'custom':
                    if (filters.customDate) {
                        const selectedDate = parseDateString(filters.customDate);
                        if (!datesEqual(requestDate, selectedDate)) {
                            return false;
                        }
                    }
                    break;
            }
        }

        // Filtro por categoría
        if (filters.categoryFilter !== 'all' && request.id_categoria?.toString() !== filters.categoryFilter) {
            return false;
        }

        // Filtro por estado
        if (filters.statusFilter !== 'all' && request.estado_aprobacion !== filters.statusFilter) {
            return false;
        }

        return true;
    });
};

interface ServiceRequest {
    id_solicitud: number;
    nombre_servicio: string;
    descripcion: string;
    nombre_empresa?: string;
    nombre_contacto?: string;
    email_contacto?: string;
    nombre_categoria?: string;
    id_categoria?: number;
    estado_aprobacion?: string;
    created_at: string;
    id_perfil?: number;
}

const AdminServiceRequestsPage: React.FC = () => {
    const { user } = useContext(AuthContext);
    const [requests, setRequests] = useState<ServiceRequest[]>([]);
    const [filteredRequests, setFilteredRequests] = useState<ServiceRequest[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingEmails, setLoadingEmails] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Estados de filtros
    const [filters, setFilters] = useState({
        dateFilter: 'all',
        customDate: '',
        categoryFilter: 'all',
        statusFilter: 'all'
    });
    const [rejectComment, setRejectComment] = useState<string>('');
    const [selectedRequest, setSelectedRequest] = useState<ServiceRequest | null>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editForm, setEditForm] = useState({
        nombre_servicio: '',
        descripcion: '',
        nombre_empresa: '',
        nombre_contacto: '',
        email_contacto: '',
        id_categoria: ''
    });

    useEffect(() => {
        loadRequests();
    }, []);

    // Aplicar filtros cuando cambien (memoizado)
    const filteredRequestsMemo = useMemo(() => {
        return filterRequests(requests, filters);
    }, [requests, filters]);

    useEffect(() => {
        setFilteredRequests(filteredRequestsMemo);
    }, [filteredRequestsMemo]);

    const resetFilters = useCallback(() => {
        setFilters({
            dateFilter: 'all',
            customDate: '',
            categoryFilter: 'all',
            statusFilter: 'all'
        });
    }, []);

    // Función optimizada para cargar solicitudes
    const loadRequests = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            console.log('🚀 Cargando solicitudes de servicios (versión optimizada)...');

            // Cargar solicitudes y categorías en paralelo
            const [requestsData, categoriesData] = await Promise.all([
                serviceRequestsAPI.getAllServiceRequests(accessToken),
                categoriesAPI.getCategories(accessToken)
            ]);
            
            console.log('📊 Solicitudes obtenidas:', requestsData.length);
            console.log('📂 Categorías obtenidas:', categoriesData.length);
            
            // Procesar solicitudes básicas primero (sin emails)
            const requestsBasic = requestsData.map(request => ({
                ...request,
                email_contacto: request.email_contacto || 'Cargando...',
                nombre_empresa: request.nombre_empresa || '',
                nombre_contacto: request.nombre_contacto || '',
                nombre_categoria: request.nombre_categoria || ''
            }));
            
            // Establecer datos básicos inmediatamente
            setRequests(requestsBasic);
            setCategories(categoriesData.filter(cat => cat.estado));
            setLoading(false);
            
            // Cargar emails en segundo plano (lazy loading)
            loadEmailsInBackground(requestsData, accessToken);
            
        } catch (err: any) {
            console.error('❌ Error cargando solicitudes:', err);
            setError(err.detail || 'Error al cargar las solicitudes');
            setLoading(false);
        }
    }, []);

    // Función para cargar emails reales usando la misma lógica que los reportes de proveedores
    const loadEmailsInBackground = useCallback(async (requestsData: ServiceRequest[], accessToken: string) => {
        try {
            setLoadingEmails(true);
            console.log('📧 Obteniendo emails reales usando lógica de reportes de proveedores...');
            
            // Usar el endpoint de proveedores verificados que sí funciona correctamente
            const apiBaseUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
            const proveedoresResponse = await fetch(`${apiBaseUrl}/api/v1/admin/reports/proveedores-verificados`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!proveedoresResponse.ok) {
                console.log('❌ No se pudo obtener reporte de proveedores');
                return;
            }
            
            const proveedoresData = await proveedoresResponse.json();
            const proveedores = proveedoresData.proveedores || [];
            console.log('🏢 Proveedores obtenidos del reporte:', proveedores.length);
            
            // Crear diccionario de emails por nombre de contacto (mismo método que usan los reportes)
            const emailsDict: {[key: string]: string} = {};
            proveedores.forEach((proveedor: any) => {
                if (proveedor.nombre_contacto && proveedor.email_contacto && proveedor.email_contacto !== 'No disponible') {
                    emailsDict[proveedor.nombre_contacto] = proveedor.email_contacto;
                }
            });
            
            console.log('📧 Emails extraídos del reporte de proveedores:', Object.keys(emailsDict).length);
            
            // Procesar solicitudes con emails reales
            const requestsWithEmails = requestsData.map(request => {
                let emailContacto = 'No especificado';
                
                // Buscar email real por nombre de contacto (mismo método que los reportes)
                if (request.nombre_contacto && request.nombre_contacto !== 'No especificado') {
                    const userEmail = emailsDict[request.nombre_contacto];
                    if (userEmail) {
                        emailContacto = userEmail;
                        console.log(`✅ Email real encontrado para contacto ${request.nombre_contacto}: ${emailContacto}`);
                    } else {
                        console.log(`❌ No se encontró email para contacto ${request.nombre_contacto}`);
                    }
                }
                
                return {
                    ...request,
                    email_contacto: emailContacto,
                    nombre_empresa: request.nombre_empresa || '',
                    nombre_contacto: request.nombre_contacto || '',
                    nombre_categoria: request.nombre_categoria || ''
                };
            });
            
            // Actualizar con emails reales
            setRequests(requestsWithEmails);
            console.log('✅ Emails reales aplicados exitosamente');
            
        } catch (error) {
            console.error('❌ Error obteniendo emails reales:', error);
        } finally {
            setLoadingEmails(false);
        }
    }, []);

    // Calcular estadísticas memoizadas
    const statistics = useMemo(() => {
        const total = filteredRequests.length;
        const pending = filteredRequests.filter(r => r.estado_aprobacion === 'pendiente').length;
        const approved = filteredRequests.filter(r => r.estado_aprobacion === 'aprobada').length;
        const rejected = filteredRequests.filter(r => r.estado_aprobacion === 'rechazada').length;
        
        return { total, pending, approved, rejected };
    }, [filteredRequests]);

    // Funciones de acción optimizadas
    const handleApprove = useCallback(async (requestId: number) => {
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            await serviceRequestsAPI.approveRequest(requestId, accessToken);
            
            // Actualizar estado local sin recargar
            setRequests(prev => prev.map(req => 
                req.id_solicitud === requestId 
                    ? { ...req, estado_aprobacion: 'aprobada' }
                    : req
            ));
            
            setSuccess('Solicitud aprobada exitosamente');
            setTimeout(() => setSuccess(null), 3000);
        } catch (error) {
            setError('Error al aprobar la solicitud');
        }
    }, []);

    const handleReject = useCallback(async (requestId: number, comment: string) => {
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            await serviceRequestsAPI.rejectRequest(requestId, comment, accessToken);
            
            // Actualizar estado local sin recargar
            setRequests(prev => prev.map(req => 
                req.id_solicitud === requestId 
                    ? { ...req, estado_aprobacion: 'rechazada', comentario_admin: comment }
                    : req
            ));
            
            setShowRejectModal(false);
            setRejectComment('');
            setSuccess('Solicitud rechazada exitosamente');
            setTimeout(() => setSuccess(null), 3000);
        } catch (error) {
            setError('Error al rechazar la solicitud');
        }
    }, []);

    const handleEdit = useCallback(async (requestId: number, formData: any) => {
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            // TODO: Implementar updateRequest en la API
            console.log('Actualizando solicitud:', requestId, formData);
            
            // Actualizar estado local sin recargar
            setRequests(prev => prev.map(req => 
                req.id_solicitud === requestId 
                    ? { ...req, ...formData }
                    : req
            ));
            
            setShowEditModal(false);
            setSuccess('Solicitud actualizada exitosamente');
            setTimeout(() => setSuccess(null), 3000);
        } catch (error) {
            setError('Error al actualizar la solicitud');
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
                    <h1 className="text-3xl font-bold text-gray-900">Solicitudes de Servicios</h1>
                    <p className="mt-2 text-gray-600">Gestiona las solicitudes de nuevos servicios</p>
            </div>

                {/* Mensajes de estado */}
                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
                        <p className="text-red-800">{error}</p>
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

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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

                        {/* Fecha personalizada */}
                        {filters.dateFilter === 'custom' && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Fecha específica</label>
                                <input
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
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-lg font-medium text-gray-900">
                                Total: {filteredRequests.length} solicitudes
                            </h3>
                        </div>
                        <div className="text-right">
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
                                        <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                                <div className="flex items-center space-x-3 mb-2">
                                            <h3 className="text-lg font-medium text-gray-900">{request.nombre_servicio}</h3>
                                                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                        request.estado_aprobacion === 'pendiente' ? 'bg-yellow-100 text-yellow-800' :
                                                        request.estado_aprobacion === 'aprobada' ? 'bg-green-100 text-green-800' :
                                                        'bg-red-100 text-red-800'
                                                    }`}>
                                                        {request.estado_aprobacion}
                                                    </span>
                                                </div>
                                                
                                                <p className="text-gray-600 mb-2">{request.descripcion}</p>
                                                
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-500">
                                                    <div>
                                                        <span className="font-medium">Empresa:</span> {request.nombre_empresa || 'No especificada'}
                                                    </div>
                                                    <div>
                                                    <span className="font-medium">Contacto:</span> {request.nombre_contacto || 'No especificado'}
                                                    </div>
                                                    <div>
                                                        <span className="font-medium">Email:</span> 
                                                        {loadingEmails && request.email_contacto === 'Cargando...' ? (
                                                            <span className="text-blue-600"> Cargando...</span>
                                                        ) : (
                                                            <span> {request.email_contacto || 'No especificado'}</span>
                                                        )}
                                                    </div>
                                                </div>
                                                
                                                <div className="mt-2 text-sm text-gray-500">
                                                    <span className="font-medium">Categoría:</span> {request.nombre_categoria || 'No especificada'} | 
                                                    <span className="font-medium ml-2">Fecha:</span> {new Date(request.created_at).toLocaleDateString('es-ES')}
                                                </div>
                                            </div>
                                            
                                            <div className="flex space-x-2 ml-4">
                                                {request.estado_aprobacion === 'pendiente' && (
                                                    <>
                                            <button
                                                onClick={() => handleApprove(request.id_solicitud)}
                                                            className="flex items-center px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                                            >
                                                            <CheckCircleIcon className="w-4 h-4 mr-1" />
                                                Aprobar
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setSelectedRequest(request);
                                                    setShowRejectModal(true);
                                                }}
                                                            className="flex items-center px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
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
                                                            nombre_servicio: request.nombre_servicio,
                                                            descripcion: request.descripcion,
                                                            nombre_empresa: request.nombre_empresa || '',
                                                            nombre_contacto: request.nombre_contacto || '',
                                                            email_contacto: request.email_contacto || '',
                                                            id_categoria: request.id_categoria?.toString() || ''
                                                        });
                                                        setShowEditModal(true);
                                                    }}
                                                    className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
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
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Rechazar Solicitud</h3>
                        <p className="text-gray-600 mb-4">
                            ¿Estás seguro de que deseas rechazar la solicitud "{selectedRequest.nombre_servicio}"?
                        </p>
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Comentario (opcional)
                            </label>
                            <textarea
                                value={rejectComment}
                                onChange={(e) => setRejectComment(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                rows={3}
                                placeholder="Motivo del rechazo..."
                            />
                        </div>
                        <div className="flex space-x-3">
                            <button
                                onClick={() => {
                                    setShowRejectModal(false);
                                    setRejectComment('');
                                }}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={() => handleReject(selectedRequest.id_solicitud, rejectComment)}
                                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
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
                        <h3 className="text-lg font-medium text-gray-900 mb-4">Editar Solicitud</h3>
                        <form onSubmit={(e) => {
                            e.preventDefault();
                            handleEdit(selectedRequest.id_solicitud, editForm);
                        }}>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre del Servicio *
                                    </label>
                                    <input
                                        type="text"
                                        value={editForm.nombre_servicio}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, nombre_servicio: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Categoría
                                    </label>
                                    <select
                                        value={editForm.id_categoria}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, id_categoria: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="">Seleccionar categoría</option>
                                        {categories.map(category => (
                                            <option key={category.id_categoria} value={category.id_categoria}>
                                                {category.nombre}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Descripción *
                                </label>
                                <textarea
                                    value={editForm.descripcion}
                                    onChange={(e) => setEditForm(prev => ({ ...prev, descripcion: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    rows={3}
                                    required
                                />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre de la Empresa
                                    </label>
                                    <input
                                        type="text"
                                        value={editForm.nombre_empresa}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, nombre_empresa: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre de Contacto
                                    </label>
                                    <input
                                        type="text"
                                        value={editForm.nombre_contacto}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, nombre_contacto: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>

                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Email de Contacto
                                </label>
                                <input
                                    type="email"
                                    value={editForm.email_contacto}
                                    onChange={(e) => setEditForm(prev => ({ ...prev, email_contacto: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div className="flex space-x-3">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowEditModal(false);
                                        setEditForm({
                                            nombre_servicio: '',
                                            descripcion: '',
                                            nombre_empresa: '',
                                            nombre_contacto: '',
                                            email_contacto: '',
                                            id_categoria: ''
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

export default AdminServiceRequestsPage;