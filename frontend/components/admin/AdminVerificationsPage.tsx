import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { CheckCircleIcon, ExclamationCircleIcon, XMarkIcon } from '../../components/icons';
import OptimizedLoading from '../ui/OptimizedLoading';
import { adminAPI } from '../../services/api';
import { AuthContext } from '../../contexts/AuthContext';
import { useDateUtils } from '../../hooks/useDateUtils';
import { buildApiUrl } from '../../config/api';

const AdminVerificationsPage: React.FC = () => {
    const { user } = React.useContext(AuthContext);
    const dateUtils = useDateUtils();
    
    // Estado para la pestaña activa
    const [activeTab, setActiveTab] = useState<'ruc' | 'proveedores'>('ruc');
    
    // Estados para solicitudes de proveedores (existente)
    const [solicitudes, setSolicitudes] = useState<any[]>([]);
    
    // Estados para verificaciones de RUC (nuevo)
    const [verificacionesRUC, setVerificacionesRUC] = useState<any[]>([]);
    
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

    // Funciones helper para eliminar código duplicado
    const removeSolicitudFromState = (idVerificacion: number) => {
        setSolicitudes(prevSolicitudes => 
            prevSolicitudes.filter(s => s.id_verificacion !== idVerificacion)
        );
    };

    const closeDetailModal = () => {
        setShowDetailModal(false);
        setSelectedSolicitud(null);
    };

    const closeRejectModal = () => {
        setShowRejectModal(false);
        setRejectComment('');
        setSelectedSolicitud(null);
    };

    const buildDocumentUrl = (idVerificacion: number, idDocumento: number): string => {
        const url = buildApiUrl(`/admin/verificaciones/${idVerificacion}/documentos/${idDocumento}/servir`);
        return `${url}?token=${encodeURIComponent(user?.accessToken || '')}`;
    };

    const handleDocumentError = (error: any, action: 'visualización' | 'descarga'): void => {
        const errorMessage = error?.message || '';
        if (errorMessage.includes('temporal')) {
            alert(`Este documento es temporal y no está disponible para ${action}.`);
        } else if (errorMessage.includes('URL')) {
            alert('La URL del documento no es válida.');
        } else if (errorMessage.includes('403') || errorMessage.includes('Forbidden')) {
            alert('No se puede acceder al documento. Posiblemente requiere permisos especiales.');
        } else if (errorMessage.includes('autenticación')) {
            alert('Error de autenticación al acceder al documento.');
        } else {
            alert(`Error al ${action === 'visualización' ? 'abrir' : 'descargar'} el documento. ${action === 'descarga' ? 'Verifica que el archivo esté disponible.' : 'Intenta descargarlo.'}`);
        }
    };

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

    // Función helper para obtener las clases CSS según el estado de revisión del documento
    const getDocumentStatusClasses = (estadoRevision: string | undefined | null): string => {
        if (estadoRevision === 'aprobado') {
            return 'bg-green-100 text-green-800';
        }
        if (estadoRevision === 'rechazado') {
            return 'bg-red-100 text-red-800';
        }
        return 'bg-yellow-100 text-yellow-800';
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
            // Manejar diferentes formatos de fecha según el tipo de solicitud
            const requestDate = new Date(
                request.created_at || 
                request.fecha_solicitud || 
                request.fecha_creacion || 
                new Date()
            );
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

    // Verificaciones de RUC filtradas
    const filteredVerificacionesRUC = useMemo(() => {
        return filterRequests(verificacionesRUC);
    }, [verificacionesRUC, filterRequests]);

    // Empresas únicas para el filtro (proveedores)
    const uniqueCompanies = useMemo(() => {
        const companies = [...new Set(solicitudes.map(s => s.nombre_empresa).filter(Boolean))];
        return companies.sort((a, b) => {
            if (!a || !b) return 0;
            return a.localeCompare(b, 'es', { sensitivity: 'base' });
        });
    }, [solicitudes]);

    // Empresas únicas para el filtro (RUC)
    const uniqueCompaniesRUC = useMemo(() => {
        const companies = [...new Set(verificacionesRUC.map(v => v.nombre_empresa).filter(Boolean))];
        return companies.sort((a, b) => {
            if (!a || !b) return 0;
            return a.localeCompare(b, 'es', { sensitivity: 'base' });
        });
    }, [verificacionesRUC]);


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

    // Cargar verificaciones de RUC pendientes
    const loadVerificacionesRUC = useCallback(async () => {
        if (!user?.accessToken) {
            console.log('❌ No hay token de acceso, cancelando carga de RUC');
            setIsLoading(false);
            return;
        }

        if (user?.role !== 'admin') {
            console.log('🚫 Usuario no es administrador, cancelando carga de RUC');
            setError('Solo los administradores pueden ver las verificaciones de RUC');
            setIsLoading(false);
            return;
        }

        try {
            console.log('🚀 Iniciando carga de verificaciones de RUC pendientes...');
            setIsLoading(true);
            setError(null);
            
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de carga')), 10000)
            );
            
            const dataPromise = adminAPI.getVerificacionesRUCPendientes(user.accessToken);
            
            const data = await Promise.race([dataPromise, timeoutPromise]) as any[];
            
            console.log('✅ Verificaciones de RUC cargadas:', data);
            console.log('📊 Número de verificaciones de RUC:', data?.length || 0);
            
            setVerificacionesRUC(data || []);
        } catch (err: any) {
            console.error('❌ Error cargando verificaciones de RUC:', err);
            if (err.message === 'Timeout de carga') {
                setError('La carga está tardando demasiado. Por favor, recarga la página.');
            } else {
                setError(err.detail || 'Error al cargar las verificaciones de RUC');
            }
        } finally {
            console.log('🏁 Finalizando carga de verificaciones de RUC');
            setIsLoading(false);
        }
    }, [user?.accessToken, user?.role]);

    useEffect(() => {
        if (activeTab === 'proveedores') {
            loadSolicitudes();
        } else if (activeTab === 'ruc') {
            loadVerificacionesRUC();
        }
    }, [user?.accessToken, user?.role, activeTab, loadSolicitudes, loadVerificacionesRUC]);

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
            removeSolicitudFromState(solicitud.id_verificacion);

            // Cerrar modal de detalles si está abierto
            closeDetailModal();

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

    // Aprobar verificación de RUC
    const handleAprobarRUC = useCallback(async (verificacion: any) => {
        if (!user?.accessToken) return;

        if (!verificacion.id_verificacion_ruc) {
            showNotification('error', 'Error: No se pudo obtener el ID de la verificación. Por favor, recarga la página e intenta nuevamente.');
            return;
        }

        try {
            setProcessingAction(verificacion.id_verificacion_ruc);
            
            // Actualización optimista: actualizar el estado a "aprobada" inmediatamente
            setVerificacionesRUC(prev => 
                prev.map(v => 
                    v.id_verificacion_ruc === verificacion.id_verificacion_ruc
                        ? { ...v, estado: 'aprobada' }
                        : v
                )
            );

            // Cerrar modal de detalles si está abierto
            closeDetailModal();

            // Mostrar mensaje de éxito inmediatamente
            showNotification('success', 'Verificación de RUC aprobada exitosamente. El usuario ahora puede iniciar sesión.');

            // Llamar a la API en segundo plano
            await adminAPI.aprobarVerificacionRUC(verificacion.id_verificacion_ruc, null, user.accessToken);

        } catch (err: any) {
            console.error('Error aprobando verificación de RUC:', err);
            
            // Revertir la actualización optimista en caso de error
            await loadVerificacionesRUC();
            
            showNotification('error', err.detail || 'Error al aprobar la verificación de RUC');
        } finally {
            setProcessingAction(null);
        }
    }, [user?.accessToken, loadVerificacionesRUC, showNotification]);

    // Rechazar verificación de RUC
    const handleRechazarRUC = useCallback(async (verificacion: any) => {
        if (!user?.accessToken) return;

        if (!verificacion.id_verificacion_ruc) {
            showNotification('error', 'Error: No se pudo obtener el ID de la verificación. Por favor, recarga la página e intenta nuevamente.');
            return;
        }

        if (!rejectComment.trim()) {
            showNotification('error', 'Por favor, proporciona un comentario explicando el motivo del rechazo.');
            return;
        }

        try {
            setProcessingAction(verificacion.id_verificacion_ruc);
            
            // Actualización optimista: actualizar el estado a "rechazada" inmediatamente
            setVerificacionesRUC(prev => 
                prev.map(v => 
                    v.id_verificacion_ruc === verificacion.id_verificacion_ruc
                        ? { ...v, estado: 'rechazada' }
                        : v
                )
            );

            // Cerrar modales
            closeRejectModal();
            closeDetailModal();

            // Mostrar mensaje de éxito inmediatamente
            showNotification('success', 'Verificación de RUC rechazada. El usuario puede corregir y reenviar su documento.');

            // Llamar a la API en segundo plano
            await adminAPI.rechazarVerificacionRUC(verificacion.id_verificacion_ruc, rejectComment, user.accessToken);

        } catch (err: any) {
            console.error('Error rechazando verificación de RUC:', err);
            
            // Revertir la actualización optimista en caso de error
            await loadVerificacionesRUC();
            
            showNotification('error', err.detail || 'Error al rechazar la verificación de RUC');
        } finally {
            setProcessingAction(null);
            setRejectComment('');
        }
    }, [user?.accessToken, rejectComment, loadVerificacionesRUC, showNotification]);

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
            removeSolicitudFromState(solicitud.id_verificacion);

            // Cerrar modal y limpiar
            closeRejectModal();

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

            {/* Header con pestañas */}
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-6">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Solicitudes de Verificación</h1>
                            <p className="mt-1 text-sm text-gray-500">
                                Revisa y administra las solicitudes de verificación
                            </p>
                        </div>
                        
                        {/* Pestañas */}
                        <div className="mt-6 border-b border-gray-200">
                            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                                <button
                                    onClick={() => setActiveTab('ruc')}
                                    className={`
                                        ${activeTab === 'ruc'
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                        }
                                        whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                                    `}
                                >
                                    Verificación de RUC
                                    {verificacionesRUC.length > 0 && (
                                        <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                                            activeTab === 'ruc' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                                        }`}>
                                            {verificacionesRUC.length}
                                        </span>
                                    )}
                                </button>
                                <button
                                    onClick={() => setActiveTab('proveedores')}
                                    className={`
                                        ${activeTab === 'proveedores'
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                        }
                                        whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                                    `}
                                >
                                    Verificación de Proveedores
                                    {solicitudes.length > 0 && (
                                        <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                                            activeTab === 'proveedores' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                                        }`}>
                                            {solicitudes.length}
                                        </span>
                                    )}
                                </button>
                            </nav>
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
                            <label htmlFor="filter-date-verifications" className="block text-sm font-medium text-gray-700 mb-2">Fecha</label>
                            <select
                                id="filter-date-verifications"
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
                            <label htmlFor="filter-company-verifications" className="block text-sm font-medium text-gray-700 mb-2">Empresa</label>
                            <select
                                id="filter-company-verifications"
                                value={filters.companyFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, companyFilter: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todas las empresas</option>
                                {(activeTab === 'ruc' ? uniqueCompaniesRUC : uniqueCompanies).map(company => (
                                    <option key={company} value={company}>
                                        {company}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Filtro por estado */}
                        <div>
                            <label htmlFor="filter-status-verifications" className="block text-sm font-medium text-gray-700 mb-2">Estado</label>
                            <select
                                id="filter-status-verifications"
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
                                <label htmlFor="filter-custom-date-verifications" className="block text-sm font-medium text-gray-700 mb-2">Fecha específica</label>
                                <input
                                    id="filter-custom-date-verifications"
                                    type="date"
                                    value={filters.customDate}
                                    onChange={(e) => setFilters(prev => ({ ...prev, customDate: e.target.value }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* Contenido según pestaña activa */}
                {activeTab === 'ruc' ? (
                    <>
                        {/* Contador de verificaciones de RUC */}
                        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-medium text-gray-900">
                                        Total: {filteredVerificacionesRUC.length} verificaciones de RUC
                                    </h3>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm text-gray-500">
                                        {filteredVerificacionesRUC.length > 0 && (
                                            <span className="text-gray-600">
                                                Mostrando {filteredVerificacionesRUC.length} de {verificacionesRUC.length} resultados
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Grid de verificaciones de RUC */}
                        {filteredVerificacionesRUC.length === 0 ? (
                            <div className="bg-white p-8 rounded-lg shadow border border-gray-200 text-center">
                                <p className="text-gray-500">No hay verificaciones de RUC que coincidan con los filtros</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {filteredVerificacionesRUC.map((verificacion) => (
                                    <div key={verificacion.id_verificacion_ruc} className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                                        <div className="p-6">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0">
                                                    <CheckCircleIcon className="h-8 w-8 text-gray-400" />
                                                </div>
                                                <div className="ml-4 flex-1">
                                                    <h3 className="text-lg font-medium text-gray-900">
                                                        {verificacion.nombre_empresa || verificacion.nombre_persona || 'Usuario sin nombre'}
                                                    </h3>
                                                    <p className="text-sm text-gray-500">
                                                        Contacto: {verificacion.nombre_persona || 'Sin especificar'}
                                                    </p>
                                                    <p className="text-xs text-gray-400 mt-1">
                                                        Solicitado: {formatDate(verificacion.fecha_creacion)}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="mt-4 space-y-2">
                                                <div className="text-xs text-gray-500">
                                                    <span className="font-medium">Email:</span> {verificacion.email || 'No disponible'}
                                                </div>
                                                {verificacion.ruc && (
                                                    <div className="text-xs text-gray-500">
                                                        <span className="font-medium">RUC:</span> {verificacion.ruc}
                                                    </div>
                                                )}
                                                {verificacion.fecha_limite_verificacion && (
                                                    <div className="text-xs text-gray-500">
                                                        <span className="font-medium">Fecha límite:</span> {formatDate(verificacion.fecha_limite_verificacion)}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="mt-4 flex items-center justify-between">
                                                {(() => {
                                                    const estado = verificacion.estado || 'pendiente';
                                                    return (
                                                        <>
                                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEstadoClasses(estado)}`}>
                                                                {getEstadoText(estado)}
                                                            </span>
                                                            <div className="flex items-center space-x-3">
                                                                {estado === 'pendiente' && (
                                                                    <>
                                                                        <button
                                                                            onClick={() => handleAprobarRUC(verificacion)}
                                                                            disabled={processingAction === verificacion.id_verificacion_ruc}
                                                                            className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400"
                                                                        >
                                                                            <CheckCircleIcon className="h-4 w-4 mr-1" />
                                                                            Aprobar
                                                                        </button>
                                                                        <button
                                                                            onClick={() => {
                                                                                setSelectedSolicitud(verificacion);
                                                                                setShowRejectModal(true);
                                                                            }}
                                                                            disabled={processingAction === verificacion.id_verificacion_ruc}
                                                                            className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400"
                                                                        >
                                                                            <ExclamationCircleIcon className="h-4 w-4 mr-1" />
                                                                            Rechazar
                                                                        </button>
                                                                    </>
                                                                )}
                                                                <button
                                                                    onClick={() => {
                                                                        setSelectedSolicitud(verificacion);
                                                                        setShowDetailModal(true);
                                                                    }}
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
                        )}
                    </>
                ) : (
                    <>
                        {/* Contador de resultados para proveedores */}
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

                        {/* Requests Grid para proveedores */}
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
                    </>
                )}
            </div>

            {/* Modal de detalles */}
            {showDetailModal && selectedSolicitud && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl p-4 sm:p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-semibold text-slate-800">
                                {activeTab === 'ruc' 
                                    ? `Detalles de Verificación de RUC #${selectedSolicitud.id_verificacion_ruc || 'N/A'}`
                                    : `Detalles de Solicitud #${selectedSolicitud.id_verificacion || 'N/A'}`
                                }
                            </h3>
                            <button
                                onClick={closeDetailModal}
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
                                            activeTab === 'ruc' 
                                                ? getVerificadoClasses(selectedSolicitud.estado === 'aprobada' || selectedSolicitud.estado === 'rechazada')
                                                : getVerificadoClasses(selectedSolicitud.verificado || false)
                                        }`}>
                                            {activeTab === 'ruc'
                                                ? getVerificadoText(selectedSolicitud.estado === 'aprobada' || selectedSolicitud.estado === 'rechazada')
                                                : getVerificadoText(selectedSolicitud.verificado || false)
                                            }
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
                                        <p className="text-slate-800 font-medium">
                                            {activeTab === 'ruc' 
                                                ? (selectedSolicitud.nombre_persona || 'No disponible')
                                                : (selectedSolicitud.nombre_contacto || 'No disponible')
                                            }
                                        </p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Email de Contacto:</span>
                                        <p className="text-slate-800">
                                            {activeTab === 'ruc' 
                                                ? (selectedSolicitud.email || 'No disponible')
                                                : (selectedSolicitud.email_contacto || 'No disponible')
                                            }
                                        </p>
                                    </div>
                                    {activeTab === 'proveedores' && (
                                        <div>
                                            <span className="text-sm font-medium text-slate-600">ID de Perfil:</span>
                                            <p className="text-slate-800">#{selectedSolicitud.id_perfil || 'No disponible'}</p>
                                        </div>
                                    )}
                                    {activeTab === 'ruc' && selectedSolicitud.ruc && (
                                        <div>
                                            <span className="text-sm font-medium text-slate-600">RUC:</span>
                                            <p className="text-slate-800">{selectedSolicitud.ruc}</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Información de la Solicitud */}
                            <div className="bg-slate-50 rounded-lg p-4">
                                <h4 className="font-semibold text-slate-800 mb-3">📝 Información de la Solicitud</h4>
                                <div className="space-y-2">
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">
                                            {activeTab === 'ruc' ? 'ID de Verificación de RUC:' : 'ID de Solicitud:'}
                                        </span>
                                        <p className="text-slate-800 font-medium">
                                            #{activeTab === 'ruc' ? selectedSolicitud.id_verificacion_ruc : selectedSolicitud.id_verificacion}
                                        </p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-slate-600">Fecha de Solicitud:</span>
                                        <p className="text-slate-800">
                                            {activeTab === 'ruc' 
                                                ? formatDate(selectedSolicitud.fecha_creacion, 'fullDateTime')
                                                : formatDate(selectedSolicitud.fecha_solicitud || selectedSolicitud.created_at, 'fullDateTime')
                                            }
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
                                    {activeTab === 'ruc' && selectedSolicitud.fecha_limite_verificacion && (
                                        <div>
                                            <span className="text-sm font-medium text-slate-600">Fecha Límite de Verificación:</span>
                                            <p className="text-slate-800">
                                                {formatDate(selectedSolicitud.fecha_limite_verificacion, 'fullDateTime')}
                                            </p>
                                        </div>
                                    )}
                                    {activeTab === 'proveedores' && selectedSolicitud.fecha_inicio && (
                                        <div>
                                            <span className="text-sm font-medium text-slate-600">Fecha de Inicio:</span>
                                            <p className="text-slate-800">
                                                {formatDate(selectedSolicitud.fecha_inicio)}
                                            </p>
                                        </div>
                                    )}
                                    {activeTab === 'ruc' && selectedSolicitud.url_documento && (
                                        <div className="mt-4">
                                            <span className="text-sm font-medium text-slate-600">Documento RUC:</span>
                                            <div className="mt-2 flex items-center space-x-3">
                                                <button
                                                    onClick={async (e) => {
                                                        e.preventDefault();
                                                        e.stopPropagation();
                                                        try {
                                                            if (user?.accessToken) {
                                                                const authUrl = buildApiUrl(`/admin/verificaciones-ruc/${selectedSolicitud.id_verificacion_ruc}/documento/servir?token=${encodeURIComponent(user.accessToken)}`);
                                                                
                                                                // Mostrar indicador de carga
                                                                const button = e.currentTarget;
                                                                const originalText = button.textContent;
                                                                button.textContent = '⏳ Cargando...';
                                                                button.disabled = true;
                                                                
                                                                // Hacer fetch del archivo con autenticación
                                                                const response = await fetch(authUrl, {
                                                                    method: 'GET',
                                                                    headers: {
                                                                        'Authorization': `Bearer ${user.accessToken}`
                                                                    }
                                                                });
                                                                
                                                                if (!response.ok) {
                                                                    throw new Error(`Error al abrir: ${response.status} ${response.statusText}`);
                                                                }
                                                                
                                                                // Convertir respuesta a blob
                                                                const blob = await response.blob();
                                                                
                                                                // Crear URL del blob
                                                                const blobUrl = window.URL.createObjectURL(blob);
                                                                
                                                                // Abrir en nueva ventana
                                                                const newWindow = window.open(blobUrl, '_blank');
                                                                if (!newWindow) {
                                                                    showNotification('error', 'Por favor, permite popups para ver el documento');
                                                                }
                                                                
                                                                // Limpiar después de un delay
                                                                setTimeout(() => {
                                                                    window.URL.revokeObjectURL(blobUrl);
                                                                    button.textContent = originalText;
                                                                    button.disabled = false;
                                                                }, 1000);
                                                                
                                                                console.log('✅ Documento RUC abierto desde backend');
                                                            }
                                                        } catch (error: any) {
                                                            console.error('❌ Error abriendo documento RUC:', error);
                                                            showNotification('error', 'Error al abrir el documento RUC');
                                                            
                                                            // Restaurar botón en caso de error
                                                            const button = e.currentTarget;
                                                            button.textContent = '👁️ Ver documento RUC';
                                                            button.disabled = false;
                                                        }
                                                    }}
                                                    className="text-blue-600 hover:text-blue-800 text-xs underline disabled:opacity-50 disabled:cursor-not-allowed"
                                                >
                                                    👁️ Ver documento RUC
                                                </button>
                                                <button
                                                    onClick={async (e) => {
                                                        e.preventDefault();
                                                        e.stopPropagation();
                                                        try {
                                                            if (user?.accessToken) {
                                                                const authUrl = buildApiUrl(`/admin/verificaciones-ruc/${selectedSolicitud.id_verificacion_ruc}/documento/servir?token=${encodeURIComponent(user.accessToken)}`);
                                                                
                                                                // Mostrar indicador de carga
                                                                const button = e.currentTarget;
                                                                const originalText = button.textContent;
                                                                button.textContent = '⏳ Descargando...';
                                                                button.disabled = true;
                                                                
                                                                // Hacer fetch del archivo con autenticación
                                                                const response = await fetch(authUrl, {
                                                                    method: 'GET',
                                                                    headers: {
                                                                        'Authorization': `Bearer ${user.accessToken}`
                                                                    }
                                                                });
                                                                
                                                                if (!response.ok) {
                                                                    throw new Error(`Error al descargar: ${response.status} ${response.statusText}`);
                                                                }
                                                                
                                                                // Obtener el nombre del archivo del header Content-Disposition o usar uno por defecto
                                                                const contentDisposition = response.headers.get('Content-Disposition');
                                                                let filename = `RUC_${selectedSolicitud.id_verificacion_ruc}.pdf`;
                                                                if (contentDisposition) {
                                                                    const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                                                                    if (filenameMatch && filenameMatch[1]) {
                                                                        filename = filenameMatch[1].replace(/['"]/g, '');
                                                                    }
                                                                }
                                                                
                                                                // Convertir respuesta a blob
                                                                const blob = await response.blob();
                                                                
                                                                // Crear URL del blob
                                                                const blobUrl = window.URL.createObjectURL(blob);
                                                                
                                                                // Crear enlace de descarga
                                                                const link = document.createElement('a');
                                                                link.href = blobUrl;
                                                                link.download = filename;
                                                                link.style.display = 'none';
                                                                
                                                                // Agregar al DOM temporalmente
                                                                document.body.appendChild(link);
                                                                link.click();
                                                                
                                                                // Limpiar después de un delay
                                                                setTimeout(() => {
                                                                    link.remove();
                                                                    window.URL.revokeObjectURL(blobUrl);
                                                                    button.textContent = originalText;
                                                                    button.disabled = false;
                                                                }, 100);
                                                                
                                                                console.log('✅ Documento RUC descargado exitosamente');
                                                            }
                                                        } catch (error: any) {
                                                            console.error('❌ Error descargando documento RUC:', error);
                                                            showNotification('error', 'Error al descargar el documento RUC');
                                                            
                                                            // Restaurar botón en caso de error
                                                            const button = e.currentTarget;
                                                            button.textContent = '📥 Descargar';
                                                            button.disabled = false;
                                                        }
                                                    }}
                                                    className="text-green-600 hover:text-green-800 text-xs underline disabled:opacity-50 disabled:cursor-not-allowed"
                                                >
                                                    📥 Descargar
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Documentos de la solicitud (solo para proveedores) */}
                        {activeTab === 'proveedores' && selectedSolicitud.documentos && selectedSolicitud.documentos.length > 0 && (
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
                                                    <span className={`ml-1 px-2 py-1 text-xs rounded-full ${getDocumentStatusClasses(doc.estado_revision)}`}>
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
                                                                        const authUrl = buildDocumentUrl(selectedSolicitud.id_verificacion, doc.id_documento);
                                                                        const newWindow = window.open(authUrl, '_blank');
                                                                        if (!newWindow) {
                                                                            alert('Por favor, permite popups para ver el documento');
                                                                        }
                                                                        console.log('✅ Documento abierto desde backend');
                                                                    }
                                                                } catch (error: any) {
                                                                    console.error('❌ Error abriendo documento:', error);
                                                                    handleDocumentError(error, 'visualización');
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
                                                                        const authUrl = buildDocumentUrl(selectedSolicitud.id_verificacion, doc.id_documento);
                                                                        
                                                                        // Mostrar indicador de carga
                                                                        const button = e.currentTarget;
                                                                        const originalText = button.textContent;
                                                                        button.textContent = '⏳ Descargando...';
                                                                        button.disabled = true;
                                                                        
                                                                        // Hacer fetch del archivo con autenticación
                                                                        const response = await fetch(authUrl, {
                                                                            method: 'GET',
                                                                            headers: {
                                                                                'Authorization': `Bearer ${user.accessToken}`
                                                                            }
                                                                        });
                                                                        
                                                                        if (!response.ok) {
                                                                            throw new Error(`Error al descargar: ${response.status} ${response.statusText}`);
                                                                        }
                                                                        
                                                                        // Convertir respuesta a blob
                                                                        const blob = await response.blob();
                                                                        
                                                                        // Crear URL del blob
                                                                        const blobUrl = window.URL.createObjectURL(blob);
                                                                        
                                                                        // Crear enlace de descarga
                                                                        const link = document.createElement('a');
                                                                        link.href = blobUrl;
                                                                        link.download = `${doc.tipo_documento}_${doc.id_documento}.pdf`;
                                                                        link.style.display = 'none';
                                                                        
                                                                        // Agregar al DOM temporalmente
                                                                        document.body.appendChild(link);
                                                                        link.click();
                                                                        
                                                                        // Limpiar después de un delay
                                                                        setTimeout(() => {
                                                                            link.remove();
                                                                            window.URL.revokeObjectURL(blobUrl);
                                                                            button.textContent = originalText;
                                                                            button.disabled = false;
                                                                        }, 100);
                                                                        
                                                                        console.log('✅ Documento descargado exitosamente');
                                                                    }
                                                                } catch (error: any) {
                                                                    console.error('❌ Error descargando documento:', error);
                                                                    handleDocumentError(error, 'descarga');
                                                                    
                                                                    // Restaurar botón en caso de error
                                                                    const button = e.currentTarget;
                                                                    button.textContent = '📥 Descargar';
                                                                    button.disabled = false;
                                                                }
                                                            }}
                                                            className="text-green-600 hover:text-green-800 text-xs underline disabled:opacity-50 disabled:cursor-not-allowed"
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
                                    closeDetailModal();
                                    if (activeTab === 'ruc') {
                                        handleAprobarRUC(selectedSolicitud);
                                    } else {
                                        handleAprobar(selectedSolicitud);
                                    }
                                }}
                                disabled={processingAction === (activeTab === 'ruc' ? selectedSolicitud.id_verificacion_ruc : selectedSolicitud.id_verificacion)}
                                className="flex items-center justify-center px-3 py-2 sm:px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                            >
                                {processingAction === (activeTab === 'ruc' ? selectedSolicitud.id_verificacion_ruc : selectedSolicitud.id_verificacion) ? (
                                    <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2"></div>
                                ) : (
                                    <CheckCircleIcon className="w-4 h-4 mr-2" />
                                )}
                                <span className="hidden sm:inline">
                                    {activeTab === 'ruc' ? 'Aprobar Verificación de RUC' : 'Aprobar Solicitud'}
                                </span>
                                <span className="sm:hidden">Aprobar</span>
                            </button>
                            <button
                                onClick={() => {
                                    closeDetailModal();
                                    openRejectModal(selectedSolicitud);
                                }}
                                disabled={processingAction === (activeTab === 'ruc' ? selectedSolicitud.id_verificacion_ruc : selectedSolicitud.id_verificacion)}
                                className="flex items-center justify-center px-3 py-2 sm:px-4 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                            >
                                {processingAction === (activeTab === 'ruc' ? selectedSolicitud.id_verificacion_ruc : selectedSolicitud.id_verificacion) ? (
                                    <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2"></div>
                                ) : (
                                    <ExclamationCircleIcon className="w-4 h-4 mr-2" />
                                )}
                                <span className="hidden sm:inline">
                                    {activeTab === 'ruc' ? 'Rechazar Verificación de RUC' : 'Rechazar Solicitud'}
                                </span>
                                <span className="sm:hidden">Rechazar</span>
                            </button>
                            <button
                                onClick={closeDetailModal}
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
                            <label htmlFor="reject-comment-verifications" className="block text-sm font-medium text-gray-700 mb-2">
                                Comentario <span className="text-red-500">*</span>
                            </label>
                            <textarea
                                id="reject-comment-verifications"
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
                                onClick={closeRejectModal}
                                className="px-3 py-2 sm:px-4 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={() => {
                                    if (activeTab === 'ruc') {
                                        handleRechazarRUC(selectedSolicitud);
                                    } else {
                                        handleRechazar(selectedSolicitud);
                                    }
                                }}
                                disabled={processingAction === (activeTab === 'ruc' ? selectedSolicitud.id_verificacion_ruc : selectedSolicitud.id_verificacion) || !rejectComment.trim()}
                                className="px-3 py-2 sm:px-4 text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 rounded-md"
                            >
                                {processingAction === (activeTab === 'ruc' ? selectedSolicitud.id_verificacion_ruc : selectedSolicitud.id_verificacion) 
                                    ? 'Procesando...' 
                                    : (activeTab === 'ruc' ? 'Rechazar Verificación de RUC' : 'Rechazar Solicitud')
                                }
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminVerificationsPage;
