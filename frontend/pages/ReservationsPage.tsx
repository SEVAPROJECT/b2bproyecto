import React from 'react';
import { 
    ClipboardDocumentListIcon, 
    FunnelIcon,
    CheckCircleIcon,
    ClockIcon,
    XCircleIcon
} from '../components/icons';
import { useAuth } from '../contexts/AuthContext';
import CalificacionModal from '../components/CalificacionModal';
import { formatDateSpanishLong } from '../utils/dateUtils';
import { useReservations, Reserva } from '../hooks/useReservations';

// Funciones auxiliares para formateo de tiempo
const formatTime = (timeString: string | null): string => {
    if (!timeString) return 'No especificada';
    return timeString.substring(0, 5); // HH:MM
};

// Funciones helper para el modal
const getModalTitle = (accion: string): string => {
    if (accion === 'confirmada') return 'Confirmar Reserva';
    if (accion === 'cancelada') return 'Cancelar Reserva';
    if (accion === 'completada') return 'Marcar como Completada';
    return 'Confirmar Acción';
};

const getModalLabelText = (accion: string): string => {
    if (accion === 'cancelada') return 'Motivo de cancelación (obligatorio)';
    if (accion === 'completada') return 'Observación (recomendado)';
    return 'Observación (opcional)';
};

const getTextareaClasses = (accion: string, observacion: string): string => {
    if (accion === 'cancelada' && !observacion.trim()) {
        return 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 border-red-300 focus:ring-red-500';
    }
    if (accion === 'completada' && !observacion.trim()) {
        return 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 border-yellow-300 focus:ring-yellow-500';
    }
    return 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 border-gray-300 focus:ring-blue-500';
};

const getTextareaPlaceholder = (accion: string): string => {
    if (accion === 'cancelada') return 'Debés ingresar un motivo para cancelar la reserva...';
    if (accion === 'completada') return 'Describe cómo se completó el servicio...';
    return 'Agrega una observación sobre esta acción...';
};

const getButtonText = (accion: string): string => {
    if (accion === 'confirmada') return 'Confirmar';
    if (accion === 'cancelada') return 'Cancelar Reserva';
    if (accion === 'completada') return 'Marcar como Completada';
    return 'Confirmar';
};

const getButtonClasses = (accion: string): string => {
    if (accion === 'cancelada') return 'px-4 py-2 text-white rounded-md bg-red-600 hover:bg-red-700';
    if (accion === 'confirmada') return 'px-4 py-2 text-white rounded-md bg-green-600 hover:bg-green-700';
    return 'px-4 py-2 text-white rounded-md bg-blue-600 hover:bg-blue-700';
};

// Componente para el estado de carga
const LoadingState: React.FC = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
        <div className="flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
            <p className="text-gray-600">Cargando reservas...</p>
        </div>
    </div>
);

// Componente para el estado de error
interface ErrorStateProps {
    error: string;
}

const ErrorState: React.FC<ErrorStateProps> = ({ error }) => (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
    </div>
);

// Componente para el estado vacío
interface EmptyStateProps {
    activeFiltersCount: number;
}

const EmptyState: React.FC<EmptyStateProps> = ({ activeFiltersCount }) => (
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
);

// Componente para el header
interface HeaderProps {
    showFilters: boolean;
    activeFiltersCount: number;
    onToggleFilters: () => void;
}

const Header: React.FC<HeaderProps> = ({ showFilters, activeFiltersCount, onToggleFilters }) => (
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
            <button
                onClick={onToggleFilters}
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
);

// Componente para las tabs
interface TabsProps {
    userRole?: string;
    activeTab: string;
    onTabChange: (tab: string) => void;
}

const Tabs: React.FC<TabsProps> = ({ userRole, activeTab, onTabChange }) => (
    <div className="mb-6">
        <nav className="flex space-x-8">
            {userRole !== 'provider' && (
                <button
                    onClick={() => onTabChange('mis-reservas')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'mis-reservas'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                >
                    Mis Reservas
                </button>
            )}
            {userRole === 'provider' && (
                <>
                    <button
                        onClick={() => onTabChange('mis-reservas-cliente')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'mis-reservas-cliente'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Mis Reservas como Cliente
                    </button>
                    <button
                        onClick={() => onTabChange('reservas-proveedor')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'reservas-proveedor'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Reservas de Mis Servicios
                    </button>
                </>
            )}
        </nav>
    </div>
);

// Componente para las estadísticas
interface StatisticsProps {
    total: number;
    activeFiltersCount: number;
    currentPage: number;
    totalPages: number;
}

const Statistics: React.FC<StatisticsProps> = ({ total, activeFiltersCount, currentPage, totalPages }) => (
    <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
                <span className="font-semibold text-gray-900">{total}</span> reserva(s) encontrada(s)
                {activeFiltersCount > 0 && (
                    <span className="ml-2">con <span className="font-semibold">{activeFiltersCount}</span> filtro(s) activo(s)</span>
                )}
            </div>
            <div className="text-sm text-gray-600">
                Página <span className="font-semibold text-gray-900">{currentPage}</span> de <span className="font-semibold text-gray-900">{totalPages}</span>
            </div>
        </div>
    </div>
);

// Componente para la paginación
interface PaginationProps {
    currentPage: number;
    totalPages: number;
    hasPrev: boolean;
    hasNext: boolean;
    onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({ currentPage, totalPages, hasPrev, hasNext, onPageChange }) => {
    if (totalPages <= 1) return null;

    return (
        <div className="mt-6 flex items-center justify-between bg-white rounded-lg shadow-sm border border-gray-200 px-4 py-3">
            <button
                onClick={() => onPageChange(currentPage - 1)}
                disabled={!hasPrev}
                className={`px-4 py-2 text-sm font-medium rounded-lg ${
                    hasPrev
                        ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
            >
                ← Anterior
            </button>
            <span className="text-sm text-gray-700">
                Página {currentPage} de {totalPages}
            </span>
            <button
                onClick={() => onPageChange(currentPage + 1)}
                disabled={!hasNext}
                className={`px-4 py-2 text-sm font-medium rounded-lg ${
                    hasNext
                        ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
            >
                Siguiente →
            </button>
        </div>
    );
};

// Componente para el panel de filtros
interface FiltersPanelProps {
    searchFilter: string;
    nombreServicio: string;
    nombreEmpresa: string;
    fechaDesde: string;
    fechaHasta: string;
    estadoFilter: string;
    nombreContacto: string;
    onSearchFilterChange: (value: string) => void;
    onNombreServicioChange: (value: string) => void;
    onNombreEmpresaChange: (value: string) => void;
    onFechaDesdeChange: (value: string) => void;
    onFechaHastaChange: (value: string) => void;
    onEstadoFilterChange: (value: string) => void;
    onNombreContactoChange: (value: string) => void;
    onClearFilters: () => void;
}

const FiltersPanel: React.FC<FiltersPanelProps> = ({
    searchFilter,
    nombreServicio,
    nombreEmpresa,
    fechaDesde,
    fechaHasta,
    estadoFilter,
    nombreContacto,
    onSearchFilterChange,
    onNombreServicioChange,
    onNombreEmpresaChange,
    onFechaDesdeChange,
    onFechaHastaChange,
    onEstadoFilterChange,
    onNombreContactoChange,
    onClearFilters
}) => (
    <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Filtros de búsqueda</h3>
            <button
                onClick={onClearFilters}
                className="text-sm text-gray-600 hover:text-gray-900 font-medium"
            >
                Limpiar filtros
            </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
                <label htmlFor="search-filter" className="block text-sm font-medium text-gray-700 mb-1">
                    Búsqueda general
                </label>
                <input
                    id="search-filter"
                    type="text"
                    value={searchFilter}
                    onChange={(e) => onSearchFilterChange(e.target.value)}
                    placeholder="Buscar en servicio o empresa..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
            </div>
            <div>
                <label htmlFor="nombre-servicio-filter" className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre del servicio
                </label>
                <input
                    id="nombre-servicio-filter"
                    type="text"
                    value={nombreServicio}
                    onChange={(e) => onNombreServicioChange(e.target.value)}
                    placeholder="Filtrar por servicio..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
            </div>
            <div>
                <label htmlFor="nombre-empresa-filter" className="block text-sm font-medium text-gray-700 mb-1">
                    Empresa
                </label>
                <input
                    id="nombre-empresa-filter"
                    type="text"
                    value={nombreEmpresa}
                    onChange={(e) => onNombreEmpresaChange(e.target.value)}
                    placeholder="Filtrar por empresa..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
            </div>
            <div>
                <label htmlFor="fecha-desde-filter" className="block text-sm font-medium text-gray-700 mb-1">
                    Desde fecha
                </label>
                <input
                    id="fecha-desde-filter"
                    type="date"
                    value={fechaDesde}
                    max={fechaHasta || undefined}
                    onChange={(e) => {
                        const nuevaFechaDesde = e.target.value;
                        onFechaDesdeChange(nuevaFechaDesde);
                        // Si la fecha hasta es menor que la nueva fecha desde, limpiar fecha hasta
                        if (fechaHasta && nuevaFechaDesde && fechaHasta < nuevaFechaDesde) {
                            onFechaHastaChange('');
                        }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                {fechaDesde && fechaHasta && fechaDesde > fechaHasta && (
                    <p className="mt-1 text-sm text-red-600">
                        ⚠️ La fecha "desde" no puede ser mayor que la fecha "hasta"
                    </p>
                )}
            </div>
            <div>
                <label htmlFor="fecha-hasta-filter" className="block text-sm font-medium text-gray-700 mb-1">
                    Hasta fecha
                </label>
                <input
                    id="fecha-hasta-filter"
                    type="date"
                    value={fechaHasta}
                    min={fechaDesde || undefined}
                    onChange={(e) => {
                        const nuevaFechaHasta = e.target.value;
                        if (fechaDesde && nuevaFechaHasta && nuevaFechaHasta < fechaDesde) {
                            alert('⚠️ La fecha "hasta" debe ser mayor o igual a la fecha "desde"');
                            return;
                        }
                        onFechaHastaChange(nuevaFechaHasta);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                {fechaDesde && fechaHasta && fechaHasta < fechaDesde && (
                    <p className="mt-1 text-sm text-red-600">
                        ⚠️ La fecha "hasta" debe ser mayor o igual a la fecha "desde"
                    </p>
                )}
            </div>
            <div>
                <label htmlFor="estado-filter" className="block text-sm font-medium text-gray-700 mb-1">
                    Estado
                </label>
                <select
                    id="estado-filter"
                    value={estadoFilter}
                    onChange={(e) => onEstadoFilterChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                    <option value="all">Todos los estados</option>
                    <option value="pendiente">Pendiente</option>
                    <option value="confirmada">Confirmada</option>
                    <option value="cancelada">Cancelada</option>
                    <option value="completada">Completada</option>
                </select>
            </div>
            <div>
                <label htmlFor="nombre-contacto-filter" className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre de contacto
                </label>
                <input
                    id="nombre-contacto-filter"
                    type="text"
                    value={nombreContacto}
                    onChange={(e) => onNombreContactoChange(e.target.value)}
                    placeholder="Filtrar por contacto..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
            </div>
        </div>
    </div>
);

// Componente para el modal de confirmación
interface ConfirmationModalProps {
    show: boolean;
    modalData: { accion: string; observacion: string } | null;
    onClose: () => void;
    onConfirm: () => void;
    onObservacionChange: (value: string) => void;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
    show,
    modalData,
    onClose,
    onConfirm,
    onObservacionChange
}) => {
    if (!show || !modalData) return null;

    return (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div className="mt-3">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                        {getModalTitle(modalData.accion)}
                    </h3>
                    <div className="mb-4">
                        <label htmlFor="modal-observacion" className="block text-sm font-medium text-gray-700 mb-2">
                            {getModalLabelText(modalData.accion)}:
                        </label>
                        <textarea
                            id="modal-observacion"
                            value={modalData.observacion}
                            onChange={(e) => onObservacionChange(e.target.value)}
                            className={getTextareaClasses(modalData.accion, modalData.observacion)}
                            rows={3}
                            placeholder={getTextareaPlaceholder(modalData.accion)}
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
                            onClick={onClose}
                            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                        >
                            Salir
                        </button>
                        <button
                            onClick={onConfirm}
                            className={getButtonClasses(modalData.accion)}
                        >
                            {getButtonText(modalData.accion)}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Componente helper para botón de calificación
interface RatingButtonProps {
    onClick: () => void;
    label: string;
}

const RatingButton: React.FC<RatingButtonProps> = ({ onClick, label }) => (
    <div className="mt-4">
        <button
            onClick={onClick}
            className="bg-yellow-600 text-white px-4 py-2 rounded text-sm hover:bg-yellow-700 transition-all duration-200 hover:scale-105"
        >
            ⭐ {label}
        </button>
    </div>
);

// Componente helper para mostrar una calificación individual
interface RatingCardProps {
    title: string;
    puntaje: number;
    comentario: string;
    nps?: number;
    bgColor: 'blue' | 'green';
}

const RatingCard: React.FC<RatingCardProps> = ({ title, puntaje, comentario, nps, bgColor }) => {
    const bgClass = bgColor === 'blue' ? 'bg-blue-50 border-blue-200' : 'bg-green-50 border-green-200';
    const textClass = bgColor === 'blue' ? 'text-blue-900' : 'text-green-900';
    const textSecondaryClass = bgColor === 'blue' ? 'text-blue-800' : 'text-green-800';
    const textTertiaryClass = bgColor === 'blue' ? 'text-blue-600' : 'text-green-600';

    return (
        <div className={`${bgClass} border rounded-lg p-3`}>
            <div className="flex items-center justify-between mb-2">
                <h4 className={`text-sm font-semibold ${textClass}`}>{title}</h4>
                <div className="flex items-center">
                    <span className="text-yellow-500 mr-1">⭐</span>
                    <span className={`text-sm font-bold ${textClass}`}>{puntaje}/5</span>
                </div>
            </div>
            <p className={`text-sm ${textSecondaryClass} italic`}>"{comentario}"</p>
            {nps && (
                <p className={`text-xs ${textTertiaryClass} mt-1`}>NPS: {nps}/10</p>
            )}
        </div>
    );
};

// Helper para obtener el badge de estado
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

// Componente para la tarjeta de reserva
interface ReservationCardProps {
    reserva: Reserva;
    activeTab: string;
    accionLoading: number | null;
    onAccionReserva: (id: number, accion: string) => void;
    onConfirmarReserva: (id: number) => void;
    onCalificar: (id: number) => void;
}

const ReservationCard: React.FC<ReservationCardProps> = ({
    reserva,
    activeTab,
    accionLoading,
    onAccionReserva,
    onConfirmarReserva,
    onCalificar
}) => {
    const isLoading = accionLoading === reserva.id_reserva;
    const isProviderTab = activeTab === 'reservas-proveedor';
    const isClientTab = activeTab === 'mis-reservas' || activeTab === 'mis-reservas-cliente';

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex flex-col lg:flex-row gap-6">
                {reserva.imagen_servicio && (
                    <div className="flex-shrink-0">
                        <img
                            src={reserva.imagen_servicio}
                            alt={reserva.nombre_servicio}
                            className="w-full lg:w-48 h-48 object-cover rounded-lg"
                        />
                    </div>
                )}
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
                            <p className="text-sm font-medium text-gray-700 mb-1">📅 Fecha de servicio</p>
                            <p className="text-sm text-gray-900">{formatDateSpanishLong(reserva.fecha)}</p>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-700 mb-1">⏰ Horario</p>
                            <p className="text-sm text-gray-900">
                                {reserva.hora_inicio ? formatTime(reserva.hora_inicio) : '--'} - {reserva.hora_fin ? formatTime(reserva.hora_fin) : '--'}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-700 mb-1">👤 Contacto</p>
                            <p className="text-sm text-gray-900">{reserva.nombre_contacto || 'No especificado'}</p>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-700 mb-1">💰 Precio</p>
                            <p className="text-sm font-bold text-gray-900">
                                {reserva.simbolo_moneda || '₲'} {(reserva.precio_servicio || 0).toLocaleString('es-PY')}
                            </p>
                        </div>
                    </div>
                    {reserva.descripcion && (
                        <div className="mb-4">
                            <p className="text-sm font-medium text-gray-700 mb-1">📝 Descripción</p>
                            <p className="text-sm text-gray-600">{reserva.descripcion}</p>
                        </div>
                    )}
                    {reserva.observacion && (
                        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                            <p className="text-sm font-medium text-yellow-800 mb-1">💡 Observaciones</p>
                            <p className="text-sm text-yellow-700">{reserva.observacion}</p>
                        </div>
                    )}
                    {(reserva.email_contacto || reserva.telefono_contacto) && (
                        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                            {reserva.email_contacto && <span>📧 {reserva.email_contacto}</span>}
                            {reserva.telefono_contacto && <span>📞 {reserva.telefono_contacto}</span>}
                        </div>
                    )}
                    {isProviderTab && (
                        <ProviderReservationActions
                            reserva={reserva}
                            isLoading={isLoading}
                            onAccionReserva={onAccionReserva}
                            onCalificar={onCalificar}
                        />
                    )}
                    {isClientTab && reserva.estado === 'pendiente' && (
                        <ClientReservationActions
                            reserva={reserva}
                            isLoading={isLoading}
                            onConfirmarReserva={onConfirmarReserva}
                            onAccionReserva={onAccionReserva}
                        />
                    )}
                    {isClientTab && reserva.estado === 'completada' && (
                        <ClientCompletedActions
                            reserva={reserva}
                            onCalificar={onCalificar}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

// Componente para acciones de proveedor
interface ProviderReservationActionsProps {
    reserva: Reserva;
    isLoading: boolean;
    onAccionReserva: (id: number, accion: string) => void;
    onCalificar: (id: number) => void;
}

const ProviderReservationActions: React.FC<ProviderReservationActionsProps> = ({
    reserva,
    isLoading,
    onAccionReserva,
    onCalificar
}) => {
    const showRatingButton = reserva.estado === 'completada' && !reserva.ya_calificado_por_proveedor;

    return (
        <div className="mt-4 pt-4 border-t border-gray-200">
            {reserva.estado === 'pendiente' && (
                <div className="flex space-x-2">
                    <ActionButton
                        onClick={() => onAccionReserva(reserva.id_reserva, 'confirmada')}
                        disabled={isLoading}
                        className="bg-green-600 hover:bg-green-700"
                        loading={isLoading}
                    >
                        Aceptar
                    </ActionButton>
                    <ActionButton
                        onClick={() => onAccionReserva(reserva.id_reserva, 'cancelada')}
                        disabled={isLoading}
                        className="bg-red-600 hover:bg-red-700"
                        loading={isLoading}
                    >
                        Cancelar
                    </ActionButton>
                </div>
            )}
            {reserva.estado === 'confirmada' && (
                <ActionButton
                    onClick={() => onAccionReserva(reserva.id_reserva, 'completada')}
                    disabled={isLoading}
                    className="bg-blue-600 hover:bg-blue-700"
                    loading={isLoading}
                >
                    Marcar como Completada
                </ActionButton>
            )}
            {showRatingButton && (
                <RatingButton
                    onClick={() => onCalificar(reserva.id_reserva)}
                    label="Calificar Cliente"
                />
            )}
            {reserva.estado === 'completada' && (
                <CompletedRatingsDisplay
                    calificacionCliente={reserva.calificacion_cliente}
                    calificacionProveedor={reserva.calificacion_proveedor}
                    isProvider={true}
                />
            )}
        </div>
    );
};

// Componente para acciones de cliente
interface ClientReservationActionsProps {
    reserva: Reserva;
    isLoading: boolean;
    onConfirmarReserva: (id: number) => void;
    onAccionReserva: (id: number, accion: string) => void;
}

const ClientReservationActions: React.FC<ClientReservationActionsProps> = ({
    reserva,
    isLoading,
    onConfirmarReserva,
    onAccionReserva
}) => (
    <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex space-x-3">
            {/* Botón Confirmar oculto para clientes cuando estado = pendiente */}
            <ActionButton
                onClick={() => onAccionReserva(reserva.id_reserva, 'cancelada')}
                disabled={isLoading}
                className="bg-red-600 hover:bg-red-700"
                loading={isLoading}
            >
                Cancelar
            </ActionButton>
        </div>
    </div>
);

// Componente para acciones de cliente cuando está completada
interface ClientCompletedActionsProps {
    reserva: Reserva;
    onCalificar: (id: number) => void;
}

const ClientCompletedActions: React.FC<ClientCompletedActionsProps> = ({
    reserva,
    onCalificar
}) => {
    const showRatingButton = !reserva.ya_calificado_por_cliente;

    return (
        <>
            {showRatingButton && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                    <RatingButton
                        onClick={() => onCalificar(reserva.id_reserva)}
                        label="Calificar Servicio"
                    />
                </div>
            )}
            <CompletedRatingsDisplay
                calificacionCliente={reserva.calificacion_cliente}
                calificacionProveedor={reserva.calificacion_proveedor}
                isProvider={false}
            />
        </>
    );
};

// Componente para mostrar calificaciones
interface CompletedRatingsDisplayProps {
    calificacionCliente?: { puntaje: number; comentario: string; nps?: number } | null;
    calificacionProveedor?: { puntaje: number; comentario: string } | null;
    isProvider: boolean;
}

const CompletedRatingsDisplay: React.FC<CompletedRatingsDisplayProps> = ({
    calificacionCliente,
    calificacionProveedor,
    isProvider
}) => {
    const getClienteTitle = () => isProvider ? 'Calificación del cliente:' : 'Tu calificación del servicio:';
    const getProveedorTitle = () => isProvider ? 'Tu calificación del cliente:' : 'Calificación del proveedor:';

    return (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
            {calificacionCliente && (
                <RatingCard
                    title={getClienteTitle()}
                    puntaje={calificacionCliente.puntaje}
                    comentario={calificacionCliente.comentario}
                    nps={calificacionCliente.nps}
                    bgColor="blue"
                />
            )}
            {calificacionProveedor && (
                <RatingCard
                    title={getProveedorTitle()}
                    puntaje={calificacionProveedor.puntaje}
                    comentario={calificacionProveedor.comentario}
                    bgColor="green"
                />
            )}
        </div>
    );
};

// Componente helper para botones de acción
interface ActionButtonProps {
    onClick: () => void;
    disabled: boolean;
    className: string;
    loading: boolean;
    children: React.ReactNode;
}

const ActionButton: React.FC<ActionButtonProps> = ({
    onClick,
    disabled,
    className,
    loading,
    children
}) => (
    <button
        onClick={onClick}
        disabled={disabled}
        className={`text-white px-3 py-1 rounded text-sm transition-all duration-200 ${
            disabled ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
        } ${className}`}
    >
        {loading ? (
            <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Procesando...
            </span>
        ) : (
            children
        )}
    </button>
);

// Componente principal
const ReservationsPage: React.FC = () => {
    const { user } = useAuth();
    const {
        reservas,
        loading,
        error,
        pagination,
        searchFilter,
        setSearchFilter,
        nombreServicio,
        setNombreServicio,
        nombreEmpresa,
        setNombreEmpresa,
        fechaDesde,
        setFechaDesde,
        fechaHasta,
        setFechaHasta,
        estadoFilter,
        setEstadoFilter,
        nombreContacto,
        setNombreContacto,
        showFilters,
        setShowFilters,
        activeTab,
        setActiveTab,
        showModal,
        setShowModal,
        modalData,
        setModalData,
        accionLoading,
        mensajeExito,
        sincronizando,
        showCalificacionModal,
        setShowCalificacionModal,
        calificacionReservaId,
        setCalificacionReservaId,
        calificacionLoading,
        activeFiltersCount,
        loadReservas,
        handleClearFilters,
        handleAccionReserva,
        handleConfirmarReserva,
        handleCalificar,
        handleEnviarCalificacion,
        confirmarAccion,
    } = useReservations();


    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <Header
                    showFilters={showFilters}
                    activeFiltersCount={activeFiltersCount}
                    onToggleFilters={() => setShowFilters(!showFilters)}
                />

                <Tabs
                    userRole={user?.role}
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                />


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

                {showFilters && (
                    <FiltersPanel
                        searchFilter={searchFilter}
                        nombreServicio={nombreServicio}
                        nombreEmpresa={nombreEmpresa}
                        fechaDesde={fechaDesde}
                        fechaHasta={fechaHasta}
                        estadoFilter={estadoFilter}
                        nombreContacto={nombreContacto}
                        onSearchFilterChange={setSearchFilter}
                        onNombreServicioChange={setNombreServicio}
                        onNombreEmpresaChange={setNombreEmpresa}
                        onFechaDesdeChange={setFechaDesde}
                        onFechaHastaChange={setFechaHasta}
                        onEstadoFilterChange={setEstadoFilter}
                        onNombreContactoChange={setNombreContacto}
                        onClearFilters={handleClearFilters}
                    />
                )}

                <Statistics
                    total={pagination.total}
                    activeFiltersCount={activeFiltersCount}
                    currentPage={pagination.page}
                    totalPages={pagination.total_pages}
                />

                {loading ? (
                    <LoadingState />
                ) : error ? (
                    <ErrorState error={error} />
                ) : reservas.length === 0 ? (
                    <EmptyState activeFiltersCount={activeFiltersCount} />
                ) : (
                    <div className="space-y-4">
                        {reservas.map((reserva) => (
                            <ReservationCard
                                key={reserva.id_reserva}
                                reserva={reserva}
                                activeTab={activeTab}
                                accionLoading={accionLoading}
                                onAccionReserva={handleAccionReserva}
                                onConfirmarReserva={handleConfirmarReserva}
                                onCalificar={handleCalificar}
                            />
                        ))}
                    </div>
                )}

                {!loading && reservas.length > 0 && (
                    <Pagination
                        currentPage={pagination.page}
                        totalPages={pagination.total_pages}
                        hasPrev={pagination.has_prev}
                        hasNext={pagination.has_next}
                        onPageChange={loadReservas}
                    />
                )}

                <ConfirmationModal
                    show={showModal}
                    modalData={modalData}
                    onClose={() => {
                        setShowModal(false);
                        setModalData(null);
                    }}
                    onConfirm={confirmarAccion}
                    onObservacionChange={(value) => setModalData(modalData ? {...modalData, observacion: value} : null)}
                />

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
