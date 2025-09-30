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

// Tipos
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

// Funciones auxiliares para formateo de fechas
const formatDateSpanish = (dateString: string): string => {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (error) {
        console.error('Error formateando fecha:', error);
        return dateString;
    }
};

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

    const API_URL = import.meta.env.VITE_API_URL || 'https://backend-production-249d.up.railway.app';

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
            if (estadoFilter !== 'all') params.append('estado', estadoFilter);
            if (nombreContacto.trim()) params.append('nombre_contacto', nombreContacto.trim());

            console.log('🔍 Cargando reservas con params:', params.toString());

            const response = await fetch(`${API_URL}/api/v1/reservas/mis-reservas-test?${params}`, {
                headers: {
                    'Authorization': `Bearer ${user.accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Error al cargar reservas');
            }

            const data = await response.json();
            console.log('📊 Reservas cargadas:', data);

            // Adaptar respuesta del endpoint de prueba
            if (data.reservas) {
                setReservas(data.reservas);
                setPagination({
                    total: data.total || data.reservas.length,
                    page: 1,
                    limit: 20,
                    offset: 0,
                    total_pages: 1,
                    has_next: false,
                    has_prev: false
                });
            } else {
                setReservas([]);
                setPagination({
                    total: 0,
                    page: 1,
                    limit: 20,
                    offset: 0,
                    total_pages: 0,
                    has_next: false,
                    has_prev: false
                });
            }
        } catch (error) {
            console.error('Error al cargar reservas:', error);
            setError('Error al cargar las reservas. Por favor, inténtalo de nuevo.');
        } finally {
            setLoading(false);
        }
    }, [user, searchFilter, nombreServicio, nombreEmpresa, fechaDesde, fechaHasta, estadoFilter, nombreContacto, pagination.limit, API_URL]);

    // Cargar al montar y cuando cambien filtros
    useEffect(() => {
        loadReservas(1);
    }, [searchFilter, nombreServicio, nombreEmpresa, fechaDesde, fechaHasta, estadoFilter, nombreContacto]);

    // Limpiar filtros
    const handleClearFilters = () => {
        setSearchFilter('');
        setNombreServicio('');
        setNombreEmpresa('');
        setFechaDesde('');
        setFechaHasta('');
        setEstadoFilter('all');
        setNombreContacto('');
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
                                Mis Reservas
                            </h1>
                            <p className="mt-2 text-gray-600">
                                Gestiona y consulta todas tus reservas de servicios
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
                                    onChange={(e) => setEstadoFilter(e.target.value)}
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
                                                    {formatDateSpanish(reserva.fecha)}
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm font-medium text-gray-700 mb-1">
                                                    ⏰ Horario
                                                </p>
                                                <p className="text-sm text-gray-900">
                                                    {formatTime(reserva.hora_inicio)} - {formatTime(reserva.hora_fin)}
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm font-medium text-gray-700 mb-1">
                                                    👤 Contacto
                                                </p>
                                                <p className="text-sm text-gray-900">
                                                    {reserva.nombre_contacto}
                                                </p>
                                            </div>

                                            <div>
                                                <p className="text-sm font-medium text-gray-700 mb-1">
                                                    💰 Precio
                                                </p>
                                                <p className="text-sm font-bold text-gray-900">
                                                    ${reserva.precio_servicio.toLocaleString('es-ES')}
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
            </div>
        </div>
    );
};

export default ReservationsPage;
