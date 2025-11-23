import React, { useCallback } from 'react';
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
import { useReservations } from '../hooks/useReservations';

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

    // Badges de estado
    const getEstadoBadge = useCallback((estado: string) => {
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
    }, []);

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
                                    {getModalTitle(modalData.accion)}
                                </h3>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        {getModalLabelText(modalData.accion)}:
                                    </label>
                                    <textarea
                                        value={modalData.observacion}
                                        onChange={(e) => setModalData({...modalData, observacion: e.target.value})}
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
                                        className={getButtonClasses(modalData.accion)}
                                    >
                                        {getButtonText(modalData.accion)}
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
