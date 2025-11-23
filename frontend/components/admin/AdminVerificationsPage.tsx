import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { CheckCircleIcon, ExclamationCircleIcon, XMarkIcon, ClockIcon } from '../../components/icons';
import OptimizedLoading from '../ui/OptimizedLoading';
import { adminAPI } from '../../services/api';
import { AuthContext } from '../../contexts/AuthContext';
import { useDateUtils } from '../../hooks/useDateUtils';
import { API_CONFIG, buildApiUrl } from '../../config/api';

const AdminVerificationsPage: React.FC = () => {
    const { user } = React.useContext(AuthContext);
    const dateUtils = useDateUtils();
    const [solicitudes, setSolicitudes] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedSolicitud, setSelectedSolicitud] = useState<any>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [showDetailModal, setShowDetailModal] = useState(false);
    const [rejectComment, setRejectComment] = useState('');
    const [processingAction, setProcessingAction] = useState<number | null>(null);
    const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
    
    // Estados para filtros
    const [filters, setFilters] = useState({
        dateFilter: 'all',
        companyFilter: 'all',
        statusFilter: 'all',
        customDate: ''
    });

    // Función para mostrar notificaciones
    const showNotification = (type: 'success' | 'error', message: string) => {
        setNotification({ type, message });
        setTimeout(() => setNotification(null), 4000);
    };

    // Función helper para formatear fechas
    const formatDate = (date: string | Date | null | undefined, format: 'dateOnly' | 'fullDateTime' = 'dateOnly') => {
        if (!date || !dateUtils.isValidDate(date)) {
            return 'Fecha inválida';
        }
        
        let result;
        if (format === 'fullDateTime') {
            result = dateUtils.convertUTCToParaguay(date);
        } else {
            result = dateUtils.convertUTCToParaguayDate(date);
        }
        
        return result;
    };

    // Función para limpiar filtros
    const resetFilters = useCallback(() => {
        setFilters({
            dateFilter: 'all',
            companyFilter: 'all',
            statusFilter: 'all',
            customDate: ''
        });
    }, []);

    // Funciones auxiliares para filtrado por fecha
    const matchesDateFilter = useCallback((requestDate: Date, dateFilter: string, customDate?: string): boolean => {
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
            case 'month': {
                const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                return requestDate >= monthAgo;
            }
            case 'year': {
                const yearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
                return requestDate >= yearAgo;
            }
            case 'custom':
                if (customDate) {
                    const customDateObj = new Date(customDate);
                    return requestDate.toDateString() === customDateObj.toDateString();
                }
                return true;
            default:
                return true;
        }
    }, []);

    const matchesCompanyFilter = useCallback((nombreEmpresa: string, companyFilter: string): boolean => {
        if (companyFilter === 'all') {
            return true;
        }
        return nombreEmpresa === companyFilter;
    }, []);

    const matchesStatusFilter = useCallback((estadoAprobacion: string, statusFilter: string): boolean => {
        if (statusFilter === 'all') {
            return true;
        }
        return estadoAprobacion === statusFilter;
    }, []);

    // Funciones auxiliares para obtener clases CSS y texto del estado
    const getEstadoClasses = useCallback((estado: string): string => {
        if (estado === 'aprobada') {
            return 'bg-green-100 text-green-800';
        }
        if (estado === 'rechazada') {
            return 'bg-red-100 text-red-800';
        }
        return 'bg-yellow-100 text-yellow-800';
    }, []);

    const getEstadoText = useCallback((estado: string): string => {
        if (estado === 'aprobada') {
            return 'Aprobada';
        }
        if (estado === 'rechazada') {
            return 'Rechazada';
        }
        return 'Pendiente';
    }, []);

    // Funciones auxiliares para estado de empresa
    const getEstadoEmpresaClasses = useCallback((estadoEmpresa: string): string => {
        if (estadoEmpresa === 'verificado') {
            return 'bg-green-100 text-green-800';
        }
        if (estadoEmpresa === 'pendiente') {
            return 'bg-yellow-100 text-yellow-800';
        }
        return 'bg-red-100 text-red-800';
    }, []);

    // Funciones auxiliares para verificado (booleano)
    const getVerificadoClasses = useCallback((verificado: boolean): string => {
        return verificado ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
    }, []);

    const getVerificadoText = useCallback((verificado: boolean): string => {
        return verificado ? 'Sí' : 'No';
    }, []);

    // Función para filtrar solicitudes
    const filterRequests = useCallback((requests: any[]) => {
        return requests.filter(request => {
            const requestDate = new Date(request.created_at || request.fecha_solicitud);
            const matchesDate = matchesDateFilter(requestDate, filters.dateFilter, filters.customDate);
            const matchesCompany = matchesCompanyFilter(request.nombre_empresa || '', filters.companyFilter);
            // El backend devuelve 'estado', no 'estado_aprobacion'
            const estadoAprobacion = request.estado_aprobacion || request.estado || '';
            const matchesStatus = matchesStatusFilter(estadoAprobacion, filters.statusFilter);

            return matchesDate && matchesCompany && matchesStatus;
        });
    }, [filters, matchesDateFilter, matchesCompanyFilter, matchesStatusFilter]);

    // Solicitudes filtradas
    const filteredRequests = useMemo(() => {
        return filterRequests(solicitudes);
    }, [solicitudes, filterRequests]);

    // Estadísticas memoizadas
    const statistics = useMemo(() => {
        const total = solicitudes.length;
        const filtered = filteredRequests.length;
        // El backend devuelve 'estado', no 'estado_aprobacion'
        const pending = solicitudes.filter(r => (r.estado_aprobacion || r.estado) === 'pendiente').length;
        const approved = solicitudes.filter(r => (r.estado_aprobacion || r.estado) === 'aprobada').length;
        const rejected = solicitudes.filter(r => (r.estado_aprobacion || r.estado) === 'rechazada').length;

        return { total, filtered, pending, approved, rejected };
    }, [solicitudes, filteredRequests]);

    // Empresas únicas para el filtro
    const uniqueCompanies = useMemo(() => {
        const companies = [...new Set(solicitudes.map(s => s.nombre_empresa).filter(Boolean))];
        return companies.sort();
    }, [solicitudes]);


    // Cargar solicitudes pendientes con optimizaciones
    const loadSolicitudes = useCallback(async () => {
        if (!user?.accessToken) {
            console.log('❌ No hay token de acceso, cancelando carga');
            setIsLoading(false);
            return;
        }

        if (user?.role !== 'admin') {
            console.log('🚫 Usuario no es administrador, cancelando carga');
            setError('Solo los administradores pueden ver las solicitudes pendientes');
            setIsLoading(false);
            return;
        }

        try {
            console.log('🚀 Iniciando carga de solicitudes pendientes...');
            setIsLoading(true);
            setError(null);
            
            // Optimización: Agregar timeout para evitar carga infinita
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de carga')), 10000)
            );
            
            const dataPromise = adminAPI.getSolicitudesPendientes(user.accessToken);
            
            const data = await Promise.race([dataPromise, timeoutPromise]) as any[];
            
            console.log('✅ Solicitudes cargadas:', data);
            console.log('📊 Número de solicitudes:', data?.length || 0);
            
            // Debug: Verificar estructura de la primera solicitud
            if (data && data.length > 0) {
                console.log('🔍 DEBUG - Primera solicitud:', data[0]);
                console.log('🔍 DEBUG - Campos de la primera solicitud:', Object.keys(data[0]));
                console.log('🔍 DEBUG - ID de verificación de la primera:', data[0].id_verificacion);
            }
            
            setSolicitudes(data || []);
        } catch (err: any) {
            console.error('❌ Error cargando solicitudes:', err);
            console.error('📋 Detalles del error:', err.detail || err.message);
            
            // Optimización: Mostrar error más específico
            if (err.message === 'Timeout de carga') {
                setError('La carga está tardando demasiado. Por favor, recarga la página.');
            } else {
                setError(err.detail || 'Error al cargar las solicitudes');
            }
        } finally {
            console.log('🏁 Finalizando carga de solicitudes');
            setIsLoading(false);
        }
    }, [user?.accessToken, user?.role]);

    useEffect(() => {
        loadSolicitudes();
    }, [user?.accessToken, user?.role]);

    // Aprobar solicitud con actualización optimista
    const handleAprobar = useCallback(async (solicitud: any) => {
        if (!user?.accessToken) return;

        if (!solicitud.id_verificacion) {
            showNotification('error', 'Error: No se pudo obtener el ID de la solicitud. Por favor, recarga la página e intenta nuevamente.');
            return;
        }

        try {
            setProcessingAction(solicitud.id_verificacion);
            
            // Actualización optimista: remover la solicitud de la lista inmediatamente
            setSolicitudes(prevSolicitudes => 
                prevSolicitudes.filter(s => s.id_verificacion !== solicitud.id_verificacion)
            );

            // Cerrar modal de detalles si está abierto
            setShowDetailModal(false);
            setSelectedSolicitud(null);

            // Mostrar mensaje de éxito inmediatamente
            showNotification('success', 'Solicitud aprobada exitosamente. El usuario ahora es proveedor.');

            // Llamar a la API en segundo plano
            await adminAPI.aprobarSolicitud(solicitud.id_verificacion, null, user.accessToken);

            // Nota: El usuario aprobado necesitará cerrar sesión y volver a iniciar
            // para que vea su nuevo rol de proveedor

        } catch (err: any) {
            console.error('Error aprobando solicitud:', err);
            
            // Revertir la actualización optimista en caso de error
            await loadSolicitudes();
            
            showNotification('error', err.detail || 'Error al aprobar la solicitud');
        } finally {
            setProcessingAction(null);
        }
    }, [user?.accessToken, loadSolicitudes, showNotification]);

    // Rechazar solicitud con actualización optimista
    const handleRechazar = useCallback(async (solicitud: any) => {
        if (!user?.accessToken) {
            showNotification('error', 'Error de autenticación. Por favor, inicia sesión nuevamente.');
            return;
        }

        if (!rejectComment.trim()) {
            showNotification('error', 'El comentario es obligatorio para rechazar una solicitud. Por favor, explica el motivo del rechazo.');
            return;
        }

        if (!solicitud.id_verificacion) {
            showNotification('error', 'Error: No se pudo obtener el ID de la solicitud. Por favor, recarga la página e intenta nuevamente.');
            return;
        }

        try {
            setProcessingAction(solicitud.id_verificacion);
            
            // Actualización optimista: remover la solicitud de la lista inmediatamente
            setSolicitudes(prevSolicitudes => 
                prevSolicitudes.filter(s => s.id_verificacion !== solicitud.id_verificacion)
            );

            // Cerrar modal y limpiar
            setShowRejectModal(false);
            setRejectComment('');
            setSelectedSolicitud(null);

            // Mostrar mensaje de éxito inmediatamente
            showNotification('success', 'Solicitud rechazada exitosamente');

            // Llamar a la API en segundo plano
            await adminAPI.rechazarSolicitud(solicitud.id_verificacion, rejectComment, user.accessToken);

        } catch (err: any) {
            console.error('Error rechazando solicitud:', err);
            
            // Revertir la actualización optimista en caso de error
            await loadSolicitudes();
            
            showNotification('error', err.detail || 'Error al rechazar la solicitud');
        } finally {
            setProcessingAction(null);
        }
    }, [user?.accessToken, rejectComment, loadSolicitudes]);

    // Abrir modal de rechazo
    const openRejectModal = useCallback((solicitud: any) => {
        setSelectedSolicitud(solicitud);
        setShowRejectModal(true);
    }, []);

    // Abrir modal de detalles
    const openDetailModal = useCallback((solicitud: any) => {
        console.log('🔍 Solicitud seleccionada:', solicitud);
        console.log('🔍 Campos disponibles:', Object.keys(solicitud));
        console.log('📧 Email encontrado:', solicitud.email_contacto);
        console.log('👤 Nombre encontrado:', solicitud.nombre_contacto);
        console.log('🏢 Empresa encontrada:', solicitud.nombre_empresa);
        console.log('⚠️ NOTA: Los objetos usuario y empresa son undefined - revisar estructura del backend');
        setSelectedSolicitud(solicitud);
        setShowDetailModal(true);
    }, []);

    // Componente de notificación
    const NotificationComponent = useMemo(() => {
        if (!notification) return null;
        
        return (
            <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md ${
                notification.type === 'success' 
                    ? 'bg-green-100 border border-green-400 text-green-700' 
                    : 'bg-red-100 border border-red-400 text-red-700'
            }`}>
                <div className="flex items-center">
                    <div className="flex-shrink-0">
                        {notification.type === 'success' ? (
                            <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                        ) : (
                            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                        )}
                    </div>
                    <div className="ml-3">
                        <p className="text-sm font-medium">{notification.message}</p>
                    </div>
                    <div className="ml-auto pl-3">
                        <button
                            onClick={() => setNotification(null)}
                            className="inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2"
                        >
                            <span className="sr-only">Cerrar</span>
                            <svg className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        );
    }, [notification]);

    if (isLoading) {
        return (
            <OptimizedLoading 
                message="Cargando solicitudes..."
                showProgress={false}
            />
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Notificaciones */}
            {NotificationComponent}

            {/* Header */}
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-6">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Solicitudes de Verificación</h1>
                            <p className="mt-1 text-sm text-gray-500">
                                Revisa y administra las solicitudes de verificación de proveedores
                            </p>
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


                {/* Filtros */}
                <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-medium text-gray-900">Filtros</h2>
                        <div className="flex space-x-2">
                            <button
                                onClick={resetFilters}
                                className="text-sm text-blue-600 hover:text-blue-800"
                            >
                                Limpiar Filtros
                            </button>
                        </div>
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

                        {/* Filtro por empresa */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Empresa</label>
                            <select
                                value={filters.companyFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, companyFilter: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todas las empresas</option>
                                {uniqueCompanies.map(company => (
                                    <option key={company} value={company}>
                                        {company}
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
                                        Mostrando {filteredRequests.length} de {solicitudes.length} resultados
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Requests Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredRequests.map((solicitud) => (
                        <div key={solicitud.id_verificacion} className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                            <div className="p-6">
                                <div className="flex items-center">
                                    <div className="flex-shrink-0">
                                        <CheckCircleIcon className="h-8 w-8 text-gray-400" />
                                    </div>
                                    <div className="ml-4 flex-1">
                                        <h3 className="text-lg font-medium text-gray-900">
                                            {solicitud.nombre_empresa || 'Empresa sin nombre'}
                                        </h3>
                                        <p className="text-sm text-gray-500">
                                            Contacto: {solicitud.nombre_contacto || 'Sin especificar'}
                                        </p>
                                        <p className="text-xs text-gray-400 mt-1">
                                            Solicitado: {formatDate(solicitud.created_at)}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-4 space-y-2">
                                    <div className="text-xs text-gray-500">
                                        <span className="font-medium">Email:</span> {solicitud.email_contacto || 'No disponible'}
                                    </div>
                                </div>
                                <div className="mt-4 flex items-center justify-between">
                                    {(() => {
                                        const estado = solicitud.estado_aprobacion || solicitud.estado || 'pendiente';
                                        return (
                                            <>
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEstadoClasses(estado)}`}>
                                                    {getEstadoText(estado)}
                                                </span>
                                                <div className="flex items-center space-x-3">
                                                    {estado === 'pendiente' && (
                                                        <>
                                                            <button
                                                                onClick={() => handleAprobar(solicitud)}
                                                                disabled={processingAction === solicitud.id_verificacion}
                                                                className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400"
                                                            >
                                                                <CheckCircleIcon className="h-4 w-4 mr-1" />
                                                                Aprobar
                                                            </button>
                                                            <button
                                                                onClick={() => openRejectModal(solicitud)}
                                                                disabled={processingAction === solicitud.id_verificacion}
                                                                className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400"
                                                            >
                                                                Rechazar
                                                            </button>
                                                        </>
                                                    )}
                                                    <button
                                                        onClick={() => openDetailModal(solicitud)}
                                                        className="text-blue-600 hover:text-blue-500 text-sm font-medium"
                                                    >
                                                        Ver detalles →
                                                    </button>
                                                </div>
                                            </>
                                        );
                                    })()}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {filteredRequests.length === 0 && solicitudes.length > 0 && (
                    <div className="text-center py-12">
                        <CheckCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay solicitudes que coincidan con los filtros</h3>
                        <p className="mt-1 text-sm text-gray-500">Intenta ajustar los filtros para ver más resultados.</p>
                    </div>
                )}

                {solicitudes.length === 0 && (
                    <div className="text-center py-12">
                        <CheckCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay solicitudes pendientes</h3>
                        <p className="mt-1 text-sm text-gray-500">Todas las solicitudes han sido procesadas.</p>
                    </div>
                )}
            </div>

            {/* Modal de detalles */}
            {showDetailModal && selectedSolicitud && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl p-4 sm:p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-semibold text-slate-800">
                                Detalles de Solicitud #{selectedSolicitud.id_verificacion}
                            </h3>
                            <button
                                onClick={() => {
                                    setShowDetailModal(false);
                                    setSelectedSolicitud(null);
                                }}
                                className="text-slate-400 hover:text-slate-600"
                            >
                                <XMarkIcon className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Información de la Empresa */}
                            <div className="bg-slate-50 rounded-lg p-4">
                                <h4 className="font-semibold text-slate-800 mb-3">📋 Información de la Empresa</h4>
                                <div className="space-y-2">
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Razón Social:</span>
                                        <p className="text-slate-800 font-medium">{selectedSolicitud.nombre_empresa || 'No disponible'}</p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Nombre de Fantasía:</span>
                                        <p className="text-slate-800">{selectedSolicitud.nombre_fantasia || 'No disponible'}</p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Estado de Empresa:</span>
                                        <span className={`px-2 py-1 font-semibold text-xs rounded-full ${
                                            getEstadoEmpresaClasses(selectedSolicitud.estado_empresa || '')
                                        }`}>
                                            {selectedSolicitud.estado_empresa || 'No disponible'}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Verificado:</span>
                                        <span className={`px-2 py-1 font-semibold text-xs rounded-full ${
                                            getVerificadoClasses(selectedSolicitud.verificado || false)
                                        }`}>
                                            {getVerificadoText(selectedSolicitud.verificado || false)}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Información de Contacto */}
                            <div className="bg-slate-50 rounded-lg p-4">
                                <h4 className="font-semibold text-slate-800 mb-3">👤 Información de Contacto</h4>
                                <div className="space-y-2">
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Persona de Contacto:</span>
                                        <p className="text-slate-800 font-medium">{selectedSolicitud.nombre_contacto || 'No disponible'}</p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Email de Contacto:</span>
                                        <p className="text-slate-800">{selectedSolicitud.email_contacto || 'No disponible'}</p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">ID de Perfil:</span>
                                        <p className="text-slate-800">#{selectedSolicitud.id_perfil || 'No disponible'}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Información de la Solicitud */}
                            <div className="bg-slate-50 rounded-lg p-4">
                                <h4 className="font-semibold text-slate-800 mb-3">📝 Información de la Solicitud</h4>
                                <div className="space-y-2">
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">ID de Solicitud:</span>
                                        <p className="text-slate-800 font-medium">#{selectedSolicitud.id_verificacion}</p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Fecha de Solicitud:</span>
                                        <p className="text-slate-800">
                                            {formatDate(selectedSolicitud.fecha_solicitud || selectedSolicitud.created_at, 'fullDateTime')}
                                        </p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Estado:</span>
                                        {(() => {
                                            const estado = selectedSolicitud.estado_aprobacion || selectedSolicitud.estado || 'pendiente';
                                            return (
                                                <span className={`px-2 py-1 font-semibold text-xs rounded-full ${getEstadoClasses(estado)}`}>
                                                    {getEstadoText(estado)}
                                                </span>
                                            );
                                        })()}
                                    </div>
                                    {selectedSolicitud.fecha_inicio && (
                                        <div>
                                            <span className="text-sm font-medium text-slate-600">Fecha de Inicio:</span>
                                            <p className="text-slate-800">
                                                {formatDate(selectedSolicitud.fecha_inicio)}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Documentos de la solicitud */}
                        {selectedSolicitud.documentos && selectedSolicitud.documentos.length > 0 && (
                            <div className="mt-6 bg-blue-50 rounded-lg p-4">
                                <h4 className="font-semibold text-blue-800 mb-4">📄 Documentos Presentados</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {selectedSolicitud.documentos.map((doc: any) => (
                                        <div key={doc.id_documento} className="bg-white rounded-lg p-3 border border-blue-200">
                                            <div className="flex items-center justify-between mb-2">
                                                <h5 className="font-medium text-blue-900">{doc.tipo_documento}</h5>
                                                <span className={`px-2 py-1 text-xs rounded-full ${
                                                    doc.es_requerido ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                                                }`}>
                                                    {doc.es_requerido ? 'Requerido' : 'Opcional'}
                                                </span>
                                            </div>
                                            <div className="space-y-1 text-sm">
                                                <div>
                                                    <span className="text-gray-600">Estado:</span>
                                                    <span className={`ml-1 px-2 py-1 text-xs rounded-full ${
                                                        doc.estado_revision === 'aprobado' ? 'bg-green-100 text-green-800' :
                                                        doc.estado_revision === 'rechazado' ? 'bg-red-100 text-red-800' :
                                                        'bg-yellow-100 text-yellow-800'
                                                    }`}>
                                                        {doc.estado_revision || 'Pendiente'}
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="text-gray-600">Fecha:</span>
                                                    <span className="ml-1">
                                                        {formatDate(doc.created_at)}
                                                    </span>
                                                </div>
                                                {doc.observacion && (
                                                    <div>
                                                        <span className="text-gray-600">Observación:</span>
                                                        <p className="text-gray-800 text-xs mt-1">{doc.observacion}</p>
                                                    </div>
                                                )}
                                                {doc.url_archivo && doc.url_archivo !== 'temp://pending' && !doc.url_archivo.startsWith('temp://') ? (
                                                    <div className="flex space-x-2">
                                                        <button
                                                            onClick={async (e) => {
                                                                e.preventDefault();
                                                                e.stopPropagation();
                                                                try {
                                                                    if (user?.accessToken) {
                                                                        // Crear URL con token de autorización
                                                                        const url = buildApiUrl(`/admin/verificaciones/${selectedSolicitud.id_verificacion}/documentos/${doc.id_documento}/servir`);
                                                                        
                                                                        // Crear una nueva ventana con el token en la URL
                                                                        const authUrl = `${url}?token=${encodeURIComponent(user.accessToken)}`;
                                                                        const newWindow = window.open(authUrl, '_blank');
                                                                        if (!newWindow) {
                                                                            alert('Por favor, permite popups para ver el documento');
                                                                        }
                                                                        
                                                                        console.log('✅ Documento abierto desde backend');
                                                                    }
                                                                } catch (error: any) {
                                                                    console.error('❌ Error abriendo documento:', error);
                                                                    const errorMessage = error?.message || '';
                                                                    if (errorMessage.includes('temporal')) {
                                                                        alert('Este documento es temporal y no está disponible para visualización.');
                                                                    } else if (errorMessage.includes('URL')) {
                                                                        alert('La URL del documento no es válida.');
                                                                    } else if (errorMessage.includes('403') || errorMessage.includes('Forbidden')) {
                                                                        alert('No se puede acceder al documento. Posiblemente requiere permisos especiales.');
                                                                    } else if (errorMessage.includes('autenticación')) {
                                                                        alert('Error de autenticación al acceder al documento.');
                                                                    } else {
                                                                        alert('Error al abrir el documento. Intenta descargarlo.');
                                                                    }
                                                                }
                                                            }}
                                                            className="text-blue-600 hover:text-blue-800 text-xs underline"
                                                        >
                                                            👁️ Ver documento
                                                        </button>
                                                        <button
                                                            onClick={async (e) => {
                                                                e.preventDefault();
                                                                e.stopPropagation();
                                                                try {
                                                                    if (user?.accessToken) {
                                                                        // Crear URL con token de autorización para descarga
                                                                        const url = buildApiUrl(`/admin/verificaciones/${selectedSolicitud.id_verificacion}/documentos/${doc.id_documento}/servir`);
                                                                        const authUrl = `${url}?token=${encodeURIComponent(user.accessToken)}`;
                                                                        
                                                                        // Crear enlace de descarga
                                                                        const link = document.createElement('a');
                                                                        link.href = authUrl;
                                                                        link.download = `${doc.tipo_documento}_${doc.id_documento}.pdf`;
                                                                        link.target = '_blank';
                                                                        link.rel = 'noopener noreferrer';
                                                                        
                                                                        // Agregar al DOM temporalmente
                                                                        document.body.appendChild(link);
                                                                        link.click();
                                                                        
                                                                        // Limpiar después de un delay
                                                                        setTimeout(() => {
                                                                            link.remove();
                                                                        }, 100);
                                                                        
                                                                        console.log('✅ Documento descargado desde backend');
                                                                    }
                                                                } catch (error: any) {
                                                                    console.error('❌ Error descargando documento:', error);
                                                                    const errorMessage = error?.message || '';
                                                                    if (errorMessage.includes('temporal')) {
                                                                        alert('Este documento es temporal y no está disponible para descarga.');
                                                                    } else if (errorMessage.includes('URL')) {
                                                                        alert('La URL del documento no es válida.');
                                                                    } else if (errorMessage.includes('403') || errorMessage.includes('Forbidden')) {
                                                                        alert('No se puede acceder al documento. Posiblemente requiere permisos especiales.');
                                                                    } else if (errorMessage.includes('autenticación')) {
                                                                        alert('Error de autenticación al acceder al documento.');
                                                                    } else {
                                                                        alert('Error al descargar el documento. Verifica que el archivo esté disponible.');
                                                                    }
                                                                }
                                                            }}
                                                            className="text-green-600 hover:text-green-800 text-xs underline"
                                                        >
                                                            📥 Descargar
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <div className="text-xs text-gray-500">
                                                        {doc.url_archivo === 'temp://pending' ? 
                                                            '⏳ Documento pendiente de carga' : 
                                                            '⚠️ Documento temporal no disponible'
                                                        }
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Comentarios existentes */}
                        {selectedSolicitud.comentario && (
                            <div className="mt-6 bg-amber-50 rounded-lg p-4">
                                <h4 className="font-semibold text-amber-800 mb-2">💬 Comentarios Existentes</h4>
                                <p className="text-amber-700">{selectedSolicitud.comentario}</p>
                            </div>
                        )}

                        {/* Acciones */}
                        <div className="mt-6 flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={() => {
                                    setShowDetailModal(false);
                                    handleAprobar(selectedSolicitud);
                                }}
                                disabled={processingAction === selectedSolicitud.id_verificacion}
                                className="flex items-center justify-center px-3 py-2 sm:px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                            >
                                {processingAction === selectedSolicitud.id_verificacion ? (
                                    <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2"></div>
                                ) : (
                                    <CheckCircleIcon className="w-4 h-4 mr-2" />
                                )}
                                <span className="hidden sm:inline">Aprobar Solicitud</span>
                                <span className="sm:hidden">Aprobar</span>
                            </button>
                            <button
                                onClick={() => {
                                    setShowDetailModal(false);
                                    openRejectModal(selectedSolicitud);
                                }}
                                disabled={processingAction === selectedSolicitud.id_verificacion}
                                className="flex items-center justify-center px-3 py-2 sm:px-4 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                            >
                                {processingAction === selectedSolicitud.id_verificacion ? (
                                    <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2"></div>
                                ) : (
                                    <ExclamationCircleIcon className="w-4 h-4 mr-2" />
                                )}
                                <span className="hidden sm:inline">Rechazar Solicitud</span>
                                <span className="sm:hidden">Rechazar</span>
                            </button>
                            <button
                                onClick={() => {
                                    setShowDetailModal(false);
                                    setSelectedSolicitud(null);
                                }}
                                className="flex items-center justify-center px-3 py-2 sm:px-4 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 text-sm sm:text-base"
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de rechazo */}
            {showRejectModal && selectedSolicitud && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl p-4 sm:p-6 w-full max-w-md">
                        <div className="mb-4">
                            <h3 className="text-lg font-medium text-gray-900">Rechazar Solicitud</h3>
                            <p className="text-sm text-gray-600 mt-2">
                                ¿Estás seguro de que quieres rechazar la solicitud de "{selectedSolicitud.nombre_servicio || selectedSolicitud.nombre_empresa}"?
                            </p>
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Comentario <span className="text-red-500">*</span>
                            </label>
                            <textarea
                                value={rejectComment}
                                onChange={(e) => setRejectComment(e.target.value)}
                                rows={3}
                                required
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                                placeholder="Explica el motivo del rechazo (obligatorio)..."
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                El comentario es obligatorio para rechazar una solicitud. Ayuda al proveedor a entender qué debe corregir.
                            </p>
                        </div>

                        <div className="flex flex-col sm:flex-row justify-end gap-3">
                            <button
                                onClick={() => {
                                    setShowRejectModal(false);
                                    setRejectComment('');
                                    setSelectedSolicitud(null);
                                }}
                                className="px-3 py-2 sm:px-4 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={() => handleRechazar(selectedSolicitud)}
                                disabled={processingAction === selectedSolicitud.id_verificacion || !rejectComment.trim()}
                                className="px-3 py-2 sm:px-4 text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 rounded-md"
                            >
                                {processingAction === selectedSolicitud.id_verificacion ? 'Procesando...' : 'Rechazar Solicitud'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminVerificationsPage;
