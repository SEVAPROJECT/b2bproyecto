import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
    ClipboardDocumentListIcon, 
    MagnifyingGlassIcon,
    CalendarDaysIcon,
    FunnelIcon,
    XMarkIcon,
    CheckCircleIcon,
    ClockIcon,
    XCircleIcon
} from '../components/icons';
import { useAuth } from '../contexts/AuthContext';
import { buildApiUrl, getJsonHeaders } from '../config/api';
import CalificacionModal from '../components/CalificacionModal';
import { formatDateSpanishLong, formatDateToDDMMYYYY } from '../utils/dateUtils';

// Tipos
interface Calificacion {
    puntaje: number;
    comentario: string;
    nps?: number;
}

interface Reserva {
    id_reserva: number;
    id_servicio: number;
    id_usuario: string;
    descripcion: string;
    observacion: string | null;
    fecha: string;
    hora_inicio: string | null;
    hora_fin: string | null;
    estado: string;
    created_at: string;
    updated_at: string;
    nombre_servicio: string;
    descripcion_servicio: string;
    precio_servicio: number;
    imagen_servicio: string | null;
    nombre_empresa: string;
    razon_social: string;
    id_perfil: number;
    nombre_contacto: string;
    email_contacto: string | null;
    telefono_contacto: string | null;
    nombre_categoria: string | null;
    ya_calificado_por_cliente?: boolean;
    ya_calificado_por_proveedor?: boolean;
    calificacion_cliente?: Calificacion | null;
    calificacion_proveedor?: Calificacion | null;
}

interface PaginationInfo {
    total: number;
    page: number;
    limit: number;
    offset: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
}

interface ReservasResponse {
    reservas: Reserva[];
    pagination: PaginationInfo;
}

// Funciones auxiliares para formateo de tiempo
const formatTime = (timeString: string | null): string => {
    if (!timeString) return 'No especificada';
    return timeString.substring(0, 5); // HH:MM
};

// Componente principal
const ReservationsPage: React.FC = () => {
    const { user } = useAuth();
    const [reservas, setReservas] = useState<Reserva[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [pagination, setPagination] = useState<PaginationInfo>({
        total: 0,
        page: 1,
        limit: 20,
        offset: 0,
        total_pages: 0,
        has_next: false,
        has_prev: false
    });

    // Estados de filtros
    const [searchFilter, setSearchFilter] = useState('');
    const [nombreServicio, setNombreServicio] = useState('');
    const [nombreEmpresa, setNombreEmpresa] = useState('');
    const [fechaDesde, setFechaDesde] = useState('');
    const [fechaHasta, setFechaHasta] = useState('');
    const [estadoFilter, setEstadoFilter] = useState('all');
    
    const [nombreContacto, setNombreContacto] = useState('');
    const [showFilters, setShowFilters] = useState(false);

    // Estados para las pestañas y funcionalidad de proveedor
    const [activeTab, setActiveTab] = useState<'mis-reservas' | 'reservas-proveedor' | 'agenda'>('mis-reservas');
    
    // Debug: Log cuando cambia el estado del filtro
    useEffect(() => {
        console.log('🔍 Estado del filtro cambió a:', estadoFilter);
        console.log('🔍 ActiveTab actual:', activeTab);
    }, [estadoFilter, activeTab]);
    
    // Configurar pestaña inicial según el rol del usuario
    useEffect(() => {
        console.log('🔄 Configurando pestaña - user?.role:', user?.role, 'activeTab:', activeTab);
        if (user?.role === 'provider' && activeTab === 'mis-reservas') {
            console.log('🔄 Cambiando a pestaña proveedor');
            setActiveTab('reservas-proveedor');
        } else if (user?.role !== 'provider' && activeTab !== 'mis-reservas') {
            console.log('🔄 Cambiando a pestaña mis-reservas');
            setActiveTab('mis-reservas');
        }
    }, [user?.role, activeTab]);
    const [showModal, setShowModal] = useState(false);
    const [modalData, setModalData] = useState<{reservaId: number, accion: string, observacion: string} | null>(null);
    const [accionLoading, setAccionLoading] = useState<number | null>(null);
    const [mensajeExito, setMensajeExito] = useState<string | null>(null);
    const [sincronizando, setSincronizando] = useState(false);
    const [showCalificacionModal, setShowCalificacionModal] = useState(false);
    const [calificacionReservaId, setCalificacionReservaId] = useState<number | null>(null);
    const [calificacionLoading, setCalificacionLoading] = useState(false);

    // Debug: Verificar que el componente se está cargando
    console.log('🔍 ReservationsPage cargado - activeTab:', activeTab);

    // Usar la configuración centralizada de API

    // Cargar reservas
    const loadReservas = useCallback(async (page: number = 1) => {
        if (!user?.accessToken) return;

        try {
        setLoading(true);
            setError(null);

            // Construir query params
            const params = new URLSearchParams();
            params.append('limit', pagination.limit.toString());
            params.append('offset', ((page - 1) * pagination.limit).toString());

            if (searchFilter.trim()) params.append('search', searchFilter.trim());
            if (nombreServicio.trim()) params.append('nombre_servicio', nombreServicio.trim());
            if (nombreEmpresa.trim()) params.append('nombre_empresa', nombreEmpresa.trim());
            if (fechaDesde) params.append('fecha_desde', fechaDesde);
            if (fechaHasta) params.append('fecha_hasta', fechaHasta);
            if (estadoFilter !== 'all') {
                console.log('🔍 Agregando filtro de estado:', estadoFilter);
                params.append('estado', estadoFilter);
            } else {
                console.log('🔍 No se agrega filtro de estado (es "all")');
            }
            if (nombreContacto.trim()) params.append('nombre_contacto', nombreContacto.trim());

            // Determinar qué endpoint usar según la pestaña activa
            let endpoint = '';
            if (activeTab === 'mis-reservas') {
                endpoint = '/reservas/mis-reservas';
            } else if (activeTab === 'reservas-proveedor') {
                endpoint = '/reservas/reservas-proveedor';
            } else {
                // Para agenda, no cargar reservas
                setReservas([]);
                setLoading(false);
                return;
            }

            console.log('🔍 Cargando reservas con params:', params.toString());
            console.log('🔍 Estado filter actual:', estadoFilter);
            
            const urlConParams = `${buildApiUrl(endpoint)}?${params.toString()}`;
            console.log('🔍 URL completa:', urlConParams);

            const response = await fetch(urlConParams, {
                headers: getJsonHeaders(),
            });

            if (!response.ok) {
                throw new Error('Error al cargar reservas');
            }

            const data = await response.json();
            console.log('📊 Reservas cargadas:', data);

            // Mapeo simplificado para el endpoint de prueba
            const reservasData = data.reservas || data || [];
            console.log('📊 Estados de reservas encontradas:', reservasData.map((r: any) => r.estado));
            console.log('📊 Verificando campo ya_calificado_por_cliente:', reservasData.map((r: any) => ({
                id: r.id_reserva,
                ya_calificado_cliente: r.ya_calificado_por_cliente,
                ya_calificado_proveedor: r.ya_calificado_por_proveedor
            })));
            
            const reservasMapeadas = reservasData.map((reserva: any) => ({
                id_reserva: reserva.id_reserva,
                nombre_servicio: reserva.nombre_servicio || reserva.servicio?.nombre || 'Servicio sin nombre',
                nombre_empresa: reserva.nombre_empresa || reserva.servicio?.empresa || 'Empresa sin nombre',
                fecha: reserva.fecha,
                estado: reserva.estado,
                descripcion: reserva.descripcion,
                observacion: reserva.observacion || '',
                hora_inicio: reserva.hora_inicio,
                hora_fin: reserva.hora_fin,
                nombre_contacto: reserva.nombre_contacto || 'No especificado',
                email_contacto: reserva.email_contacto || null,
                precio_servicio: reserva.precio_servicio || reserva.servicio?.precio || 0,
                imagen_servicio: reserva.imagen_servicio || reserva.servicio?.imagen,
                nombre_categoria: reserva.nombre_categoria || reserva.servicio?.categoria || 'Sin categoría',
                ya_calificado_por_cliente: reserva.ya_calificado_por_cliente || false,
                ya_calificado_por_proveedor: reserva.ya_calificado_por_proveedor || false,
                calificacion_cliente: reserva.calificacion_cliente,
                calificacion_proveedor: reserva.calificacion_proveedor
            }));

            setReservas(reservasMapeadas);
            setPagination({
                total: data.total || reservasData.length,
                page: 1,
                limit: 20,
                offset: 0,
                total_pages: 1,
                has_next: false,
                has_prev: false
            });
            
            console.log('📊 Reservas mapeadas después del filtro:', reservasMapeadas.length);
            console.log('📊 Filtro aplicado:', estadoFilter);
        } catch (error) {
            console.error('Error al cargar reservas:', error);
            setError('Error al cargar las reservas. Por favor, inténtalo de nuevo.');
        } finally {
            setLoading(false);
        }
    }, [user, searchFilter, nombreServicio, nombreEmpresa, fechaDesde, fechaHasta, estadoFilter, nombreContacto, pagination.limit, activeTab]);

    // Cargar al montar y cuando cambien filtros o pestaña
    useEffect(() => {
        console.log('🔄 useEffect ejecutado - estadoFilter:', estadoFilter);
        console.log('🔄 useEffect ejecutado - activeTab:', activeTab);
        console.log('🔄 useEffect ejecutado - searchFilter:', searchFilter);
        loadReservas(1);
    }, [searchFilter, nombreServicio, nombreEmpresa, fechaDesde, fechaHasta, estadoFilter, nombreContacto, activeTab]);

    // Limpiar filtros
    const handleClearFilters = () => {
        console.log('🧹 Limpiando filtros - estadoFilter será resetado a "all"');
        setSearchFilter('');
        setNombreServicio('');
        setNombreEmpresa('');
        setFechaDesde('');
        setFechaHasta('');
        setEstadoFilter('all');
        setNombreContacto('');
    };

    // Funciones para cambio de estado de reservas
    const actualizarEstadoReserva = async (reservaId: number, nuevoEstado: string, observacion?: string) => {
        try {
            if (!user) return;

            setAccionLoading(reservaId);
            setError(null);

            // Usar endpoint específico para cancelación
            const endpoint = nuevoEstado === 'cancelada' ? `/reservas/${reservaId}/cancelar` : `/reservas/${reservaId}/estado`;
            const body = nuevoEstado === 'cancelada' 
                ? { motivo: observacion || '' }
                : { nuevo_estado: nuevoEstado, observacion: observacion || '' };

            const response = await fetch(buildApiUrl(endpoint), {
                method: 'PUT',
                headers: getJsonHeaders(),
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al actualizar estado');
            }

            const result = await response.json();
            console.log('Estado actualizado:', result);

            // Mensaje específico para cancelación
            if (nuevoEstado === 'cancelada') {
                setMensajeExito('✅ Reserva cancelada - Los cambios se sincronizarán automáticamente');
            } else {
                setMensajeExito(`Reserva ${nuevoEstado} exitosamente`);
            }
            setTimeout(() => setMensajeExito(null), 5000);

            // Refetch inmediato para sincronización
            setSincronizando(true);
            await loadReservas(1);
            setSincronizando(false);
            setShowModal(false);
            setModalData(null);
        } catch (err) {
            setError('Error al actualizar el estado de la reserva');
            console.error('Error:', err);
        } finally {
            setAccionLoading(null);
        }
    };

    const handleAccionReserva = (reservaId: number, accion: string) => {
        if (accionLoading === reservaId) {
            return;
        }
        
        setModalData({
            reservaId,
            accion,
            observacion: ''
        });
        setShowModal(true);
    };

    const handleConfirmarReserva = async (reservaId: number) => {
        if (accionLoading === reservaId) {
            return;
        }
        
        try {
            setAccionLoading(reservaId);
            setError(null);

            const response = await fetch(buildApiUrl(`/reservas/${reservaId}/confirmar`), {
                method: 'PUT',
                headers: getJsonHeaders()
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al confirmar la reserva');
            }

            const result = await response.json();
            console.log('Reserva confirmada:', result);

            setMensajeExito('✅ Reserva confirmada');
            setTimeout(() => setMensajeExito(null), 3000);

            await loadReservas(1);
        } catch (err) {
            setError('Error al confirmar la reserva');
            console.error('Error:', err);
        } finally {
            setAccionLoading(null);
        }
    };

    // Funciones para calificación
    const handleCalificar = (reservaId: number) => {
        setCalificacionReservaId(reservaId);
        setShowCalificacionModal(true);
    };

    const handleEnviarCalificacion = async (data: {puntaje: number, comentario: string, satisfaccion_nps?: number}) => {
        if (!calificacionReservaId) return;

        try {
            setCalificacionLoading(true);
            setError(null);

            // Determinar el endpoint según la pestaña activa
            const endpoint = activeTab === 'reservas-proveedor' 
                ? `/calificacion/proveedor/${calificacionReservaId}`
                : `/calificacion/cliente/${calificacionReservaId}`;

            const response = await fetch(buildApiUrl(endpoint), {
                method: 'POST',
                headers: getJsonHeaders(),
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al enviar calificación');
            }

            setMensajeExito('✅ Calificación registrada con éxito');
            setTimeout(() => setMensajeExito(null), 3000);

            // Recargar datos para actualizar UI
            await loadReservas(1);
            setShowCalificacionModal(false);
            setCalificacionReservaId(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Error al enviar calificación');
            console.error('Error:', err);
        } finally {
            setCalificacionLoading(false);
        }
    };

    const confirmarAccion = () => {
        if (!modalData) return;
        
        if (modalData.accion === 'cancelada' && !modalData.observacion.trim()) {
            setError('Debés ingresar un motivo para cancelar la reserva');
            return;
        }
        
        if (modalData.accion === 'completada' && !modalData.observacion.trim()) {
            setError('Es recomendable agregar una observación al marcar como completada');
            return;
        }
        
        actualizarEstadoReserva(modalData.reservaId, modalData.accion, modalData.observacion);
    };

    // Badges de estado
    const getEstadoBadge = (estado: string) => {
        const badges: { [key: string]: { label: string; className: string; icon: React.ReactNode } } = {
            'pendiente': {
                label: 'Pendiente',
                className: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
                icon: <ClockIcon className="w-4 h-4" />
            },
            'confirmada': {
                label: 'Confirmada',
                className: 'bg-green-100 text-green-800 border border-green-200',
                icon: <CheckCircleIcon className="w-4 h-4" />
            },
            'cancelada': {
                label: 'Cancelada',
                className: 'bg-red-100 text-red-800 border border-red-200',
                icon: <XCircleIcon className="w-4 h-4" />
            },
            'completada': {
                label: 'Completada',
                className: 'bg-blue-100 text-blue-800 border border-blue-200',
                icon: <CheckCircleIcon className="w-4 h-4" />
            }
        };

        const badge = badges[estado.toLowerCase()] || {
            label: estado,
            className: 'bg-gray-100 text-gray-800 border border-gray-200',
            icon: null
        };

        return (
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${badge.className}`}>
                {badge.icon}
                {badge.label}
            </span>
        );
    };

    // Contar filtros activos
    const activeFiltersCount = useMemo(() => {
        let count = 0;
        if (searchFilter.trim()) count++;
        if (nombreServicio.trim()) count++;
        if (nombreEmpresa.trim()) count++;
        if (fechaDesde) count++;
        if (fechaHasta) count++;
        if (estadoFilter !== 'all') count++;
        if (nombreContacto.trim()) count++;
        return count;
    }, [searchFilter, nombreServicio, nombreEmpresa, fechaDesde, fechaHasta, estadoFilter, nombreContacto]);

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center justify-between flex-wrap gap-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                                <ClipboardDocumentListIcon className="h-8 w-8 text-primary-600" />
                                Gestión de Reservas
                            </h1>
                            <p className="mt-2 text-gray-600">
                                Administra tus reservas y disponibilidades
                            </p>
                        </div>

                        {/* Botón de filtros */}
                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50 transition-colors"
                        >
                            <FunnelIcon className="h-5 w-5 text-gray-600" />
                            <span className="text-sm font-medium text-gray-700">
                                Filtros
                                {activeFiltersCount > 0 && (
                                    <span className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-primary-600 rounded-full">
                                        {activeFiltersCount}
                                    </span>
                                )}
                            </span>
                        </button>
                    </div>
                </div>

                {/* Tabs - Mostrar pestañas según el rol del usuario */}
                <div className="mb-6">
                    <nav className="flex space-x-8">
                        {/* Solo clientes ven "Mis Reservas" */}
                        {user?.role !== 'provider' && (
                            <button
                                onClick={() => setActiveTab('mis-reservas')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                    activeTab === 'mis-reservas'
                                        ? 'border-blue-500 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                            >
                                Mis Reservas
                            </button>
                        )}
                        
                        {/* Solo proveedores ven estas pestañas */}
                        {user?.role === 'provider' && (
                            <>
                                <button
                                    onClick={() => setActiveTab('reservas-proveedor')}
                                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                        activeTab === 'reservas-proveedor'
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                                >
                                    Reservas de Mis Servicios
                                </button>
                                <button
                                    onClick={() => setActiveTab('agenda')}
                                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                        activeTab === 'agenda'
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                                >
                                    Mi Agenda
                                </button>
                            </>
                        )}
                    </nav>
                </div>


                {/* Mensaje de éxito */}
                {mensajeExito && (
                    <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4 animate-fade-in">
                        <div className="flex">
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-green-800">Éxito</h3>
                                <div className="mt-2 text-sm text-green-700">{mensajeExito}</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Indicador de sincronización */}
                {sincronizando && (
                    <div className="mb-4 bg-blue-50 border border-blue-200 rounded-md p-4 animate-fade-in">
                        <div className="flex items-center">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-3"></div>
                            <div className="text-sm text-blue-700">
                                Sincronizando cambios con el servidor...
                            </div>
                        </div>
                    </div>
                )}

                {/* Panel de filtros */}
                {showFilters && (
                    <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-900">Filtros de búsqueda</h3>
                            <button
                                onClick={handleClearFilters}
                                className="text-sm text-gray-600 hover:text-gray-900 font-medium"
                            >
                                Limpiar filtros
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {/* Búsqueda general */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Búsqueda general
                                </label>
                                <input
                                    type="text"
                                    value={searchFilter}
                                    onChange={(e) => setSearchFilter(e.target.value)}
                                    placeholder="Buscar en servicio o empresa..."
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>

                            {/* Nombre del servicio */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Nombre del servicio
                                </label>
                                <input
                                    type="text"
                                    value={nombreServicio}
                                    onChange={(e) => setNombreServicio(e.target.value)}
                                    placeholder="Filtrar por servicio..."
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>

                            {/* Nombre de empresa */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Empresa
                                </label>
                                <input
                                    type="text"
                                    value={nombreEmpresa}
                                    onChange={(e) => setNombreEmpresa(e.target.value)}
                                    placeholder="Filtrar por empresa..."
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>

                            {/* Fecha desde */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Desde fecha
                                </label>
                                <input
                                    type="date"
                                    value={fechaDesde}
                                    onChange={(e) => setFechaDesde(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>

                            {/* Fecha hasta */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Hasta fecha
                                </label>
                                <input
                                    type="date"
                                    value={fechaHasta}
                                    onChange={(e) => setFechaHasta(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>

                            {/* Estado */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Estado
                                </label>
                                <select
                                    value={estadoFilter}
                                    onChange={(e) => {
                                        console.log('🔍 Cambiando filtro de estado a:', e.target.value);
                                        setEstadoFilter(e.target.value);
                                    }}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                >
                                    <option value="all">Todos los estados</option>
                                    <option value="pendiente">Pendiente</option>
                                    <option value="confirmada">Confirmada</option>
                                    <option value="cancelada">Cancelada</option>
                                    <option value="completada">Completada</option>
                                </select>
                            </div>

                            {/* Nombre de contacto */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Nombre de contacto
                                </label>
                                <input
                                    type="text"
                                    value={nombreContacto}
                                    onChange={(e) => setNombreContacto(e.target.value)}
                                    placeholder="Filtrar por contacto..."
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Estadísticas */}
                <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                                        <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-600">
                            <span className="font-semibold text-gray-900">{pagination.total}</span> reserva(s) encontrada(s)
                            {activeFiltersCount > 0 && (
                                <span className="ml-2">con <span className="font-semibold">{activeFiltersCount}</span> filtro(s) activo(s)</span>
                            )}
                        </div>
                        <div className="text-sm text-gray-600">
                            Página <span className="font-semibold text-gray-900">{pagination.page}</span> de <span className="font-semibold text-gray-900">{pagination.total_pages}</span>
                        </div>
                    </div>
                </div>

                {/* Contenido */}
                {loading ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
                        <div className="flex flex-col items-center justify-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
                            <p className="text-gray-600">Cargando reservas...</p>
                                                </div>
                                                    </div>
                ) : error ? (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <p className="text-red-800">{error}</p>
                                                    </div>
                ) : reservas.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
                        <div className="text-center">
                            <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No hay reservas</h3>
                            <p className="text-gray-600">
                                {activeFiltersCount > 0
                                    ? 'No se encontraron reservas con los filtros aplicados.'
                                    : 'Aún no has realizado ninguna reserva.'}
                            </p>
                                                    </div>
                                                </div>
                ) : (
                    <div className="space-y-4">
                        {reservas.map((reserva) => (
                            <div
                                key={reserva.id_reserva}
                                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                            >
                                <div className="flex flex-col lg:flex-row gap-6">
                                    {/* Imagen del servicio */}
                                    {reserva.imagen_servicio && (
                                        <div className="flex-shrink-0">
                                            <img
                                                src={reserva.imagen_servicio}
                                                alt={reserva.nombre_servicio}
                                                className="w-full lg:w-48 h-48 object-cover rounded-lg"
                                            />
                                        </div>
                                    )}

                                    {/* Contenido principal */}
                                    <div className="flex-1">
                                        <div className="flex items-start justify-between mb-4">
                                            <div>
                                                <h3 className="text-xl font-bold text-gray-900 mb-1">
                                                    {reserva.nombre_servicio}
                                                </h3>
                                                <p className="text-sm text-gray-600">
                                                    {reserva.nombre_empresa}
                                                </p>
                                                {reserva.nombre_categoria && (
                                                    <span className="inline-block mt-2 px-2 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded">
                                                        {reserva.nombre_categoria}
                                                    </span>
                                                )}
                                            </div>
                                            {getEstadoBadge(reserva.estado)}
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                            <div>
                                                <p className="text-sm font-medium text-gray-700 mb-1">
                                                    📅 Fecha de servicio
                                                </p>
                                                <p className="text-sm text-gray-900">
                                                    {formatDateSpanishLong(reserva.fecha)}
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm font-medium text-gray-700 mb-1">
                                                    ⏰ Horario
                                                </p>
                                                <p className="text-sm text-gray-900">
                                                    {reserva.hora_inicio ? formatTime(reserva.hora_inicio) : '--'} - {reserva.hora_fin ? formatTime(reserva.hora_fin) : '--'}
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm font-medium text-gray-700 mb-1">
                                                    👤 Contacto
                                                </p>
                                                <p className="text-sm text-gray-900">
                                                    {reserva.nombre_contacto || 'No especificado'}
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm font-medium text-gray-700 mb-1">
                                                    💰 Precio
                                                </p>
                                                <p className="text-sm font-bold text-gray-900">
                                                    ${(reserva.precio_servicio || 0).toLocaleString('es-ES')}
                                                </p>
                                            </div>
                                        </div>

                                        {reserva.descripcion && (
                                            <div className="mb-4">
                                                <p className="text-sm font-medium text-gray-700 mb-1">
                                                    📝 Descripción
                                                </p>
                                                <p className="text-sm text-gray-600">
                                                    {reserva.descripcion}
                                                </p>
                                            </div>
                                        )}

                                        {reserva.observacion && (
                                            <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                                                <p className="text-sm font-medium text-yellow-800 mb-1">
                                                    💡 Observaciones
                                                </p>
                                                <p className="text-sm text-yellow-700">
                                                    {reserva.observacion}
                                                </p>
                                            </div>
                                        )}

                                        {/* Información de contacto */}
                                        {(reserva.email_contacto || reserva.telefono_contacto) && (
                                            <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                                {reserva.email_contacto && (
                                                    <span>📧 {reserva.email_contacto}</span>
                                                )}
                                                {reserva.telefono_contacto && (
                                                    <span>📞 {reserva.telefono_contacto}</span>
                                                )}
                                            </div>
                                        )}

                                        {/* Botones de acción para proveedores */}
                                        {activeTab === 'reservas-proveedor' && (
                                            <div className="mt-4 pt-4 border-t border-gray-200">
                                                {reserva.estado === 'pendiente' && (
                                                    <div className="flex space-x-2">
                                                        <button
                                                            onClick={() => handleAccionReserva(reserva.id_reserva, 'confirmada')}
                                                            disabled={accionLoading === reserva.id_reserva}
                                                            className={`bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition-all duration-200 ${
                                                                accionLoading === reserva.id_reserva 
                                                                    ? 'opacity-50 cursor-not-allowed' 
                                                                    : 'hover:scale-105'
                                                            }`}
                                                        >
                                                            {accionLoading === reserva.id_reserva ? (
                                                                <span className="flex items-center">
                                                                    <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                                    </svg>
                                                                    Procesando...
                                                                </span>
                                                            ) : (
                                                                'Aceptar'
                                                            )}
                                                        </button>
                                                        <button
                                                            onClick={() => handleAccionReserva(reserva.id_reserva, 'cancelada')}
                                                            disabled={accionLoading === reserva.id_reserva}
                                                            className={`bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition-all duration-200 ${
                                                                accionLoading === reserva.id_reserva 
                                                                    ? 'opacity-50 cursor-not-allowed' 
                                                                    : 'hover:scale-105'
                                                            }`}
                                                        >
                                                            {accionLoading === reserva.id_reserva ? (
                                                                <span className="flex items-center">
                                                                    <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                                    </svg>
                                                                    Procesando...
                                                                </span>
                                                            ) : (
                                                                'Cancelar'
                                                            )}
                                                        </button>
                                                    </div>
                                                )}
                                                {reserva.estado === 'confirmada' && (
                                                    <div className="flex space-x-2">
                                                        <button
                                                            onClick={() => handleAccionReserva(reserva.id_reserva, 'completada')}
                                                            disabled={accionLoading === reserva.id_reserva}
                                                            className={`bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-all duration-200 ${
                                                                accionLoading === reserva.id_reserva 
                                                                    ? 'opacity-50 cursor-not-allowed' 
                                                                    : 'hover:scale-105'
                                                            }`}
                                                        >
                                                            {accionLoading === reserva.id_reserva ? (
                                                                <span className="flex items-center">
                                                                    <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                                    </svg>
                                                                    Procesando...
                                                                </span>
                                                            ) : (
                                                                'Marcar como Completada'
                                                            )}
                                                        </button>
                                                    </div>
                                                )}
                                                
                                                {/* Botón de calificar para proveedores */}
                                                {(() => {
                                                    const shouldShowButton = reserva.estado === 'completada' && 
                                                                            !reserva.ya_calificado_por_proveedor;
                                                    
                                                    console.log(`🔍 Botón Calificar Cliente - Reserva ${reserva.id_reserva}:`, {
                                                        estado: reserva.estado,
                                                        ya_calificado: reserva.ya_calificado_por_proveedor,
                                                        shouldShow: shouldShowButton
                                                    });
                                                    
                                                    return shouldShowButton ? (
                                                        <div className="mt-4">
                                                            <button
                                                                onClick={() => handleCalificar(reserva.id_reserva)}
                                                                className="bg-yellow-600 text-white px-4 py-2 rounded text-sm hover:bg-yellow-700 transition-all duration-200 hover:scale-105"
                                                            >
                                                                ⭐ Calificar Cliente
                                                            </button>
                                                        </div>
                                                    ) : null;
                                                })()}
                                                
                                                {/* Mostrar calificaciones (Proveedor) */}
                                                {reserva.estado === 'completada' && (
                                                    <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                                                        {/* Calificación del cliente hacia el servicio */}
                                                        {reserva.calificacion_cliente && (
                                                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                                                <div className="flex items-center justify-between mb-2">
                                                                    <h4 className="text-sm font-semibold text-blue-900">Calificación del cliente:</h4>
                                                                    <div className="flex items-center">
                                                                        <span className="text-yellow-500 mr-1">⭐</span>
                                                                        <span className="text-sm font-bold text-blue-900">{reserva.calificacion_cliente.puntaje}/5</span>
                                                                    </div>
                                                                </div>
                                                                <p className="text-sm text-blue-800 italic">"{reserva.calificacion_cliente.comentario}"</p>
                                                                {reserva.calificacion_cliente.nps && (
                                                                    <p className="text-xs text-blue-600 mt-1">NPS: {reserva.calificacion_cliente.nps}/10</p>
                                                                )}
                                                            </div>
                                                        )}
                                                        
                                                        {/* Mi calificación (como proveedor) */}
                                                        {reserva.calificacion_proveedor && (
                                                            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                                                <div className="flex items-center justify-between mb-2">
                                                                    <h4 className="text-sm font-semibold text-green-900">Tu calificación del cliente:</h4>
                                                                    <div className="flex items-center">
                                                                        <span className="text-yellow-500 mr-1">⭐</span>
                                                                        <span className="text-sm font-bold text-green-900">{reserva.calificacion_proveedor.puntaje}/5</span>
                                                                    </div>
                                                                </div>
                                                                <p className="text-sm text-green-800 italic">"{reserva.calificacion_proveedor.comentario}"</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* Botones de acción para clientes */}
                                        {activeTab === 'mis-reservas' && reserva.estado === 'pendiente' && (
                                            <div className="mt-4 pt-4 border-t border-gray-200">
                                                <div className="flex space-x-3">
                                                    <button
                                                        onClick={() => handleConfirmarReserva(reserva.id_reserva)}
                                                        disabled={accionLoading === reserva.id_reserva}
                                                        className={`bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 transition-all duration-200 ${
                                                            accionLoading === reserva.id_reserva 
                                                                ? 'opacity-50 cursor-not-allowed' 
                                                                : 'hover:scale-105'
                                                        }`}
                                                    >
                                                        {accionLoading === reserva.id_reserva ? (
                                                            <span className="flex items-center">
                                                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                                </svg>
                                                                Procesando...
                                                            </span>
                                                        ) : (
                                                            'Confirmar'
                                                        )}
                                                    </button>
                                                    <button
                                                        onClick={() => handleAccionReserva(reserva.id_reserva, 'cancelada')}
                                                        disabled={accionLoading === reserva.id_reserva}
                                                        className={`bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700 transition-all duration-200 ${
                                                            accionLoading === reserva.id_reserva 
                                                                ? 'opacity-50 cursor-not-allowed' 
                                                                : 'hover:scale-105'
                                                        }`}
                                                    >
                                                        {accionLoading === reserva.id_reserva ? (
                                                            <span className="flex items-center">
                                                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                                </svg>
                                                                Procesando...
                                                            </span>
                                                        ) : (
                                                            'Cancelar'
                                                        )}
                                                    </button>
                                                </div>
                                            </div>
                                        )}

                                        {/* Botón de calificar para clientes */}
                                        {(() => {
                                            const shouldShowButton = activeTab === 'mis-reservas' && 
                                                                    reserva.estado === 'completada' && 
                                                                    !reserva.ya_calificado_por_cliente;
                                            
                                            console.log(`🔍 Botón Calificar - Reserva ${reserva.id_reserva}:`, {
                                                activeTab,
                                                estado: reserva.estado,
                                                ya_calificado: reserva.ya_calificado_por_cliente,
                                                shouldShow: shouldShowButton
                                            });
                                            
                                            return shouldShowButton ? (
                                                <div className="mt-4 pt-4 border-t border-gray-200">
                                                    <button
                                                        onClick={() => handleCalificar(reserva.id_reserva)}
                                                        className="bg-yellow-600 text-white px-4 py-2 rounded text-sm hover:bg-yellow-700 transition-all duration-200 hover:scale-105"
                                                    >
                                                        ⭐ Calificar Servicio
                                                    </button>
                                                </div>
                                            ) : null;
                                        })()}

                                        {/* Mostrar calificaciones (Cliente) */}
                                        {activeTab === 'mis-reservas' && reserva.estado === 'completada' && (
                                            <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                                                {/* Mi calificación (como cliente) */}
                                                {reserva.calificacion_cliente && (
                                                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <h4 className="text-sm font-semibold text-blue-900">Tu calificación del servicio:</h4>
                                                            <div className="flex items-center">
                                                                <span className="text-yellow-500 mr-1">⭐</span>
                                                                <span className="text-sm font-bold text-blue-900">{reserva.calificacion_cliente.puntaje}/5</span>
                                                            </div>
                                                        </div>
                                                        <p className="text-sm text-blue-800 italic">"{reserva.calificacion_cliente.comentario}"</p>
                                                        {reserva.calificacion_cliente.nps && (
                                                            <p className="text-xs text-blue-600 mt-1">NPS: {reserva.calificacion_cliente.nps}/10</p>
                                                        )}
                                                    </div>
                                                )}
                                                
                                                {/* Calificación del proveedor hacia mí */}
                                                {reserva.calificacion_proveedor && (
                                                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <h4 className="text-sm font-semibold text-green-900">Calificación del proveedor:</h4>
                                                            <div className="flex items-center">
                                                                <span className="text-yellow-500 mr-1">⭐</span>
                                                                <span className="text-sm font-bold text-green-900">{reserva.calificacion_proveedor.puntaje}/5</span>
                                                            </div>
                                                        </div>
                                                        <p className="text-sm text-green-800 italic">"{reserva.calificacion_proveedor.comentario}"</p>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Paginación */}
                {!loading && reservas.length > 0 && pagination.total_pages > 1 && (
                    <div className="mt-6 flex items-center justify-between bg-white rounded-lg shadow-sm border border-gray-200 px-4 py-3">
                        <button
                            onClick={() => loadReservas(pagination.page - 1)}
                            disabled={!pagination.has_prev}
                            className={`px-4 py-2 text-sm font-medium rounded-lg ${
                                pagination.has_prev
                                    ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            }`}
                        >
                            ← Anterior
                        </button>

                        <span className="text-sm text-gray-700">
                            Página {pagination.page} de {pagination.total_pages}
                        </span>

                        <button
                            onClick={() => loadReservas(pagination.page + 1)}
                            disabled={!pagination.has_next}
                            className={`px-4 py-2 text-sm font-medium rounded-lg ${
                                pagination.has_next
                                    ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            }`}
                        >
                            Siguiente →
                        </button>
                </div>
                )}

                {/* Modal de confirmación */}
                {showModal && modalData && (
                    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                        <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                            <div className="mt-3">
                                <h3 className="text-lg font-medium text-gray-900 mb-4">
                                    {modalData.accion === 'confirmada' ? 'Confirmar Reserva' : 
                                     modalData.accion === 'cancelada' ? 'Cancelar Reserva' : 
                                     modalData.accion === 'completada' ? 'Marcar como Completada' : 'Confirmar Acción'}
                                </h3>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        {modalData.accion === 'cancelada' ? 'Motivo de cancelación (obligatorio)' : 
                                         modalData.accion === 'completada' ? 'Observación (recomendado)' : 
                                         'Observación (opcional)'}:
                                    </label>
                                    <textarea
                                        value={modalData.observacion}
                                        onChange={(e) => setModalData({...modalData, observacion: e.target.value})}
                                        className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                                            modalData.accion === 'cancelada' && !modalData.observacion.trim()
                                                ? 'border-red-300 focus:ring-red-500'
                                                : (modalData.accion === 'completada' && !modalData.observacion.trim())
                                                ? 'border-yellow-300 focus:ring-yellow-500'
                                                : 'border-gray-300 focus:ring-blue-500'
                                        }`}
                                        rows={3}
                                        placeholder={
                                            modalData.accion === 'cancelada'
                                                ? 'Debés ingresar un motivo para cancelar la reserva...'
                                                : modalData.accion === 'completada'
                                                ? 'Describe cómo se completó el servicio...'
                                                : 'Agrega una observación sobre esta acción...'
                                        }
                                    />
                                    {modalData.accion === 'cancelada' && !modalData.observacion.trim() && (
                                        <p className="mt-1 text-sm text-red-600">
                                            ❌ Debés ingresar un motivo para cancelar la reserva
                                        </p>
                                    )}
                                    {modalData.accion === 'completada' && !modalData.observacion.trim() && (
                                        <p className="mt-1 text-sm text-yellow-600">
                                            ⚠️ Es recomendable agregar una observación para esta acción
                                        </p>
                                    )}
                                </div>
                                <div className="flex justify-end space-x-3">
                                    <button
                                        onClick={() => {
                                            setShowModal(false);
                                            setModalData(null);
                                        }}
                                        className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                                    >
                                        Salir
                                    </button>
                                    <button
                                        onClick={confirmarAccion}
                                        className={`px-4 py-2 text-white rounded-md ${
                                            modalData.accion === 'cancelada' ? 'bg-red-600 hover:bg-red-700' :
                                            modalData.accion === 'confirmada' ? 'bg-green-600 hover:bg-green-700' :
                                            'bg-blue-600 hover:bg-blue-700'
                                        }`}
                                    >
                                        {modalData.accion === 'confirmada' ? 'Confirmar' : 
                                         modalData.accion === 'cancelada' ? 'Cancelar Reserva' : 
                                         modalData.accion === 'completada' ? 'Marcar como Completada' : 'Confirmar'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Modal de calificación */}
                <CalificacionModal
                    isOpen={showCalificacionModal}
                    onClose={() => {
                        setShowCalificacionModal(false);
                        setCalificacionReservaId(null);
                    }}
                    onSubmit={handleEnviarCalificacion}
                    tipo={activeTab === 'reservas-proveedor' ? 'proveedor' : 'cliente'}
                    reservaId={calificacionReservaId || 0}
                    loading={calificacionLoading}
                />
            </div>
        </div>
    );
};

export default ReservationsPage;
