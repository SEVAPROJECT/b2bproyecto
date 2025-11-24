import React from 'react';
import { UserCircleIcon, ExclamationCircleIcon } from '../icons';
import { API_CONFIG } from '../../config/api';
import { useAdminUsers, BackendUser } from '../../hooks/useAdminUsers';

// Función helper para obtener las clases CSS según el tipo de notificación
const getNotificationClasses = (type: string): string => {
    if (type === 'success') {
        return 'bg-green-100 border border-green-400 text-green-800';
    }
    if (type === 'error') {
        return 'bg-red-100 border border-red-400 text-red-800';
    }
    return 'bg-blue-100 border border-blue-400 text-blue-800';
};

// Función helper para obtener el nombre del rol en español
const getRoleDisplayNameFromFilter = (filterRole: string): string => {
    if (filterRole === 'admin') {
        return 'Administrador';
    }
    if (filterRole === 'provider') {
        return 'Proveedor';
    }
    return 'Cliente';
};

// Función helper para obtener el texto del botón de activar/desactivar
const getToggleUserStatusButtonText = (isUpdating: boolean, userEstado: string): string => {
    if (isUpdating) {
        return 'Procesando...';
    }
    if (userEstado === 'INACTIVO') {
        return 'Reactivar';
    }
    return 'Desactivar';
};

// Función helper para obtener la URL de la foto de perfil
const getUserPhotoUrl = (fotoPerfil: string | undefined): string => {
    if (!fotoPerfil) return '';
    return fotoPerfil.startsWith('/') 
        ? `${API_CONFIG.BASE_URL.replace('/api/v1', '')}${fotoPerfil}` 
        : fotoPerfil;
};

// Función helper para manejar el error de carga de imagen
const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const target = e.target as HTMLImageElement;
    target.style.display = 'none';
    const parent = target.parentElement;
    if (parent) {
        parent.innerHTML = '<svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>';
    }
};

// Función helper para obtener las clases CSS del estado del usuario (elimina código duplicado)
const getEstadoClasses = (estado: string | undefined): string => {
    return estado === 'ACTIVO'
        ? 'bg-green-100 text-green-800'
        : 'bg-red-100 text-red-800';
};

// Componente para renderizar la foto de perfil del usuario
interface UserPhotoProps {
    fotoPerfil?: string;
    nombrePersona: string;
    size?: 'sm' | 'md';
}

const UserPhoto: React.FC<UserPhotoProps> = ({ fotoPerfil, nombrePersona, size = 'sm' }) => {
    const sizeClasses = size === 'sm' ? 'w-10 h-10' : 'w-12 h-12';
    const iconSize = 'w-6 h-6'; // Tamaño constante para el icono
    
    return (
        <div className={`${sizeClasses} bg-primary-100 rounded-full flex items-center justify-center overflow-hidden flex-shrink-0`}>
            {fotoPerfil ? (
                <img
                    src={getUserPhotoUrl(fotoPerfil)}
                    alt={`Foto de perfil de ${nombrePersona}`}
                    className="w-full h-full object-cover rounded-full"
                    onError={handleImageError}
                />
            ) : (
                <UserCircleIcon className={`${iconSize} text-primary-600`} />
            )}
        </div>
    );
};

// Componente para los botones de acción del usuario (editar y restablecer)
interface UserActionButtonsProps {
    user: BackendUser;
    isUpdating: boolean;
    userPermissions?: { is_admin?: boolean; can_reset_passwords?: boolean };
    onEdit: (user: BackendUser) => void;
    onResetPassword: (user: BackendUser) => void;
    onDeactivate: (userId: string) => Promise<void>;
    variant?: 'desktop' | 'mobile';
}

const UserActionButtons: React.FC<UserActionButtonsProps> = ({
    user,
    isUpdating,
    userPermissions,
    onEdit,
    onResetPassword,
    onDeactivate,
    variant = 'desktop'
}) => {
    const canResetPassword = userPermissions?.is_admin || userPermissions?.can_reset_passwords;
    const isInactive = user.estado === 'INACTIVO';
    
    const buttonBaseClasses = variant === 'desktop' 
        ? 'flex items-center space-x-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors border'
        : 'w-full sm:w-auto flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors border';
    
    const editButtonClasses = variant === 'desktop'
        ? `${buttonBaseClasses} text-primary-600 hover:text-primary-900 bg-primary-50 hover:bg-primary-100 border-primary-200 hover:border-primary-300`
        : 'w-full sm:w-auto flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium text-primary-600 hover:text-primary-900 bg-primary-50 hover:bg-primary-100 rounded-md transition-colors border border-primary-200 hover:border-primary-300';
    
    const resetButtonClasses = `${buttonBaseClasses} ${
        canResetPassword
            ? 'text-orange-600 hover:text-orange-900 bg-orange-50 hover:bg-orange-100 border-orange-200 hover:border-orange-300'
            : 'text-gray-400 bg-gray-50 cursor-not-allowed border-gray-200'
    }`;
    
    // Extraer clases de estado para reducir complejidad cognitiva
    const getInactiveStateClasses = () => {
        return isInactive
            ? 'text-green-600 hover:text-green-900 bg-green-50 hover:bg-green-100 border-green-200 hover:border-green-300'
            : 'text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 border-red-200 hover:border-red-300';
    };

    const inactiveStateClasses = getInactiveStateClasses();
    
    const toggleButtonClasses = variant === 'desktop'
        ? `${buttonBaseClasses} disabled:opacity-50 disabled:cursor-not-allowed ${inactiveStateClasses}`
        : `w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors border disabled:opacity-50 disabled:cursor-not-allowed ${inactiveStateClasses}`;

    return (
        <>
            <button
                onClick={() => onEdit(user)}
                className={editButtonClasses}
                title="Editar información del usuario"
            >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <span>Editar</span>
            </button>
            
            <button
                onClick={() => onResetPassword(user)}
                disabled={!canResetPassword}
                className={resetButtonClasses}
                title={canResetPassword ? "Restablecer contraseña del usuario" : "No tienes permisos para restablecer contraseñas"}
            >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>Restablecer</span>
                {!userPermissions?.is_admin && (
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
                    </svg>
                )}
            </button>
            
            {variant === 'desktop' && (
                <button
                    onClick={async () => await onDeactivate(user.id)}
                    disabled={isUpdating}
                    className={toggleButtonClasses}
                    title={isInactive ? "Reactivar usuario" : "Desactivar usuario"}
                >
                    {isUpdating ? (
                        <div className={`animate-spin rounded-full h-4 w-4 border-b-2 ${
                            isInactive ? 'border-green-600' : 'border-red-600'
                        }`}></div>
                    ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            {isInactive ? (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            ) : (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            )}
                        </svg>
                    )}
                    <span>{getToggleUserStatusButtonText(isUpdating, user.estado)}</span>
                </button>
            )}
        </>
    );
};

// Componente para el botón de activar/desactivar (solo para móvil)
interface ToggleUserStatusButtonProps {
    user: BackendUser;
    isUpdating: boolean;
    onDeactivate: (userId: string) => Promise<void>;
}

const ToggleUserStatusButton: React.FC<ToggleUserStatusButtonProps> = ({
    user,
    isUpdating,
    onDeactivate
}) => {
    const isInactive = user.estado === 'INACTIVO';
    
    return (
        <button
            onClick={async () => await onDeactivate(user.id)}
            disabled={isUpdating}
            className={`w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors border disabled:opacity-50 disabled:cursor-not-allowed ${
                isInactive
                    ? 'text-green-600 hover:text-green-900 bg-green-50 hover:bg-green-100 border-green-200 hover:border-green-300'
                    : 'text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 border-red-200 hover:border-red-300'
            }`}
            title={isInactive ? "Reactivar usuario" : "Desactivar usuario"}
        >
            {isUpdating ? (
                <div className={`animate-spin rounded-full h-4 w-4 border-b-2 ${
                    isInactive ? 'border-green-600' : 'border-red-600'
                }`}></div>
            ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isInactive ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    )}
                </svg>
            )}
            <span>{getToggleUserStatusButtonText(isUpdating, user.estado)}</span>
        </button>
    );
};

// Componente para el estado de carga
const LoadingState: React.FC = () => (
    <div className="bg-slate-50 min-h-screen">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 mb-2">Gestión de Usuarios</h1>
                    <p className="text-slate-600">Administrá los usuarios registrados en la plataforma</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-slate-200/80 p-8">
                    <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mr-3"></div>
                        <span className="text-slate-600">Cargando usuarios...</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
);

// Componente para el estado de error
interface ErrorStateProps {
    error: string;
    onRetry: () => void;
}

const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry }) => {
    const getErrorMessage = () => {
        return error.includes('Timeout')
            ? 'La carga está tardando más de lo esperado. Algunos datos pueden no estar disponibles.'
            : 'No se pudieron cargar los usuarios en este momento. Verifica tu conexión.';
    };

    return (
        <div className="bg-slate-50 min-h-screen">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-white p-8 rounded-xl shadow-md border border-slate-200/80">
                    <div className="text-center py-12">
                        <ExclamationCircleIcon className="mx-auto h-12 w-12 text-yellow-400" />
                        <h3 className="mt-2 text-lg font-semibold text-slate-800">Información no disponible</h3>
                        <p className="mt-1 text-sm text-slate-500">{getErrorMessage()}</p>
                        <button onClick={onRetry} className="mt-4 btn-blue touch-manipulation">
                            <span>Reintentar</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Componente para el banner de notificaciones
interface NotificationBannerProps {
    notification: { type: string; message: string } | null;
    onClose: () => void;
}

const NotificationBanner: React.FC<NotificationBannerProps> = ({ notification, onClose }) => {
    if (!notification) return null;

    return (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 ${getNotificationClasses(notification.type)}`}>
            <div className="flex items-center">
                <div className="flex-1">
                    <p className="text-sm font-medium">{notification.message}</p>
                </div>
                <button onClick={onClose} className="ml-4 text-gray-400 hover:text-gray-600">
                    ✕
                </button>
            </div>
        </div>
    );
};

// Componente para los filtros activos
interface ActiveFiltersProps {
    searchQuery: string;
    searchEmpresa: string;
    filterRole: string;
    filterStatus: string;
    getRoleDisplayNameFromFilter: (role: string) => string;
}

const ActiveFilters: React.FC<ActiveFiltersProps> = ({
    searchQuery,
    searchEmpresa,
    filterRole,
    filterStatus,
    getRoleDisplayNameFromFilter
}) => {
    const hasActiveFilters = searchEmpresa || searchQuery || filterRole !== 'all' || filterStatus !== 'all';
    
    if (!hasActiveFilters) return null;

    return (
        <div className="mb-4">
            <div className="flex flex-wrap gap-2">
                {searchQuery && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Usuario: "{searchQuery}"
                    </span>
                )}
                {searchEmpresa && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Empresa: "{searchEmpresa}"
                    </span>
                )}
                {filterRole !== 'all' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        Rol: {getRoleDisplayNameFromFilter(filterRole)}
                    </span>
                )}
                {filterStatus !== 'all' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Estado: {filterStatus}
                    </span>
                )}
            </div>
        </div>
    );
};

// Componente para la sección de filtros
interface FiltersSectionProps {
    searchQuery: string;
    searchEmpresa: string;
    filterRole: string;
    filterStatus: string;
    isSearching: boolean;
    setSearchQuery: (value: string) => void;
    setSearchEmpresa: (value: string) => void;
    setFilterRole: (value: string) => void;
    setFilterStatus: (value: string) => void;
    clearFilters: () => void;
    loadUsers: (page: number) => void;
    currentPage: number;
    getRoleDisplayNameFromFilter: (role: string) => string;
}

const FiltersSection: React.FC<FiltersSectionProps> = ({
    searchQuery,
    searchEmpresa,
    filterRole,
    filterStatus,
    isSearching,
    setSearchQuery,
    setSearchEmpresa,
    setFilterRole,
    setFilterStatus,
    clearFilters,
    loadUsers,
    currentPage,
    getRoleDisplayNameFromFilter
}) => {
    const hasActiveFilters = searchEmpresa || searchQuery || filterRole !== 'all' || filterStatus !== 'all';

    return (
        <div className="bg-white p-4 sm:p-6 rounded-xl shadow-md border border-slate-200/80 mb-6">
            <ActiveFilters
                searchQuery={searchQuery}
                searchEmpresa={searchEmpresa}
                filterRole={filterRole}
                filterStatus={filterStatus}
                getRoleDisplayNameFromFilter={getRoleDisplayNameFromFilter}
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 sm:gap-4">
                <div>
                    <label htmlFor="search-user" className="block text-sm font-medium text-slate-700 mb-2">
                        Buscar Usuario
                        {isSearching && searchQuery.trim() && (
                            <span className="ml-2 text-xs text-blue-600 animate-pulse">🔍 Buscando...</span>
                        )}
                    </label>
                    <input
                        id="search-user"
                        type="text"
                        placeholder="Nombre o email..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    />
                </div>
                <div>
                    <label htmlFor="search-empresa" className="block text-sm font-medium text-slate-700 mb-2">
                        Buscar Empresa
                        {isSearching && searchEmpresa.trim() && (
                            <span className="ml-2 text-xs text-blue-600 animate-pulse">🔍 Buscando...</span>
                        )}
                    </label>
                    <input
                        id="search-empresa"
                        type="text"
                        placeholder="Nombre de empresa..."
                        value={searchEmpresa}
                        onChange={(e) => setSearchEmpresa(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    />
                    {searchEmpresa.trim() && !isSearching && (
                        <p className="text-xs text-slate-500 mt-1">Búsqueda automática activada</p>
                    )}
                </div>
                <div>
                    <label htmlFor="filter-role" className="block text-sm font-medium text-slate-700 mb-2">
                        Rol
                    </label>
                    <select
                        id="filter-role"
                        value={filterRole}
                        onChange={(e) => setFilterRole(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    >
                        <option value="all">Todos los roles</option>
                        <option value="admin">Administrador</option>
                        <option value="provider">Proveedor</option>
                        <option value="client">Cliente</option>
                    </select>
                </div>
                <div>
                    <label htmlFor="filter-status" className="block text-sm font-medium text-slate-700 mb-2">
                        Estado
                    </label>
                    <select
                        id="filter-status"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    >
                        <option value="all">Todos los estados</option>
                        <option value="ACTIVO">Activo</option>
                        <option value="INACTIVO">Inactivo</option>
                    </select>
                </div>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-2 sm:space-x-2">
                    {hasActiveFilters && (
                        <button
                            onClick={clearFilters}
                            className="w-full sm:w-auto bg-gray-500 text-white px-3 sm:px-4 py-2 text-sm rounded-lg hover:bg-gray-600 transition-colors"
                        >
                            Limpiar Filtros
                        </button>
                    )}
                    <button
                        onClick={() => loadUsers(currentPage)}
                        className="w-full sm:w-auto bg-primary-600 text-white px-3 sm:px-4 py-2 text-sm rounded-lg hover:bg-primary-700 transition-colors"
                    >
                        Actualizar
                    </button>
                </div>
            </div>
        </div>
    );
};

// Componente para las estadísticas
interface StatsSectionProps {
    totalUsers: number;
    isSearching: boolean;
    isUpdating: boolean;
}

const StatsSection: React.FC<StatsSectionProps> = ({ totalUsers, isSearching, isUpdating }) => {
    console.log('🔍 StatsSection - totalUsers recibido:', totalUsers, 'tipo:', typeof totalUsers);
    
    // Asegurar que totalUsers sea un número válido
    const displayTotal = typeof totalUsers === 'number' ? totalUsers : 0;
    
    return (
        <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm border border-slate-200/80 mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                    <h3 className="text-base sm:text-lg font-medium text-slate-900">Total: {displayTotal} usuarios</h3>
                    {isSearching && (
                        <span className="ml-2 text-blue-600 animate-pulse">🔄 Buscando...</span>
                    )}
                    {isUpdating && !isSearching && (
                        <span className="ml-2 text-orange-600 animate-pulse">⚡ Procesando...</span>
                    )}
                </div>
                <div className="text-right">
                    <div className="text-sm text-slate-500">
                        {isSearching && <span className="text-blue-600 animate-pulse">🔄 Buscando...</span>}
                        {isUpdating && !isSearching && <span className="text-orange-600 animate-pulse">⚡ Procesando...</span>}
                    </div>
                </div>
            </div>
        </div>
    );
};

// Componente para el mensaje cuando no hay usuarios
interface EmptyUsersMessageProps {
    allUsers: BackendUser[];
    searchQuery: string;
    searchEmpresa: string;
    filterRole: string;
    filterStatus: string;
    onRetry: () => void;
}

const EmptyUsersMessage: React.FC<EmptyUsersMessageProps> = ({
    allUsers,
    searchQuery,
    searchEmpresa,
    filterRole,
    filterStatus,
    onRetry
}) => {
    const hasFilters = searchQuery || searchEmpresa || filterRole !== 'all' || filterStatus !== 'all';
    const hasNoUsers = allUsers.length === 0;

    return (
        <div className="p-8 text-center">
            <UserCircleIcon className="mx-auto h-12 w-12 text-slate-400" />
            <h3 className="mt-2 text-lg font-medium text-slate-900">
                {hasNoUsers ? 'No hay usuarios disponibles' : 'No se encontraron usuarios'}
            </h3>
            <p className="mt-1 text-sm text-slate-500">
                {hasNoUsers
                    ? 'Los datos de usuarios no están disponibles en este momento. Verifica tu conexión.'
                    : hasFilters
                        ? 'Intenta ajustar los filtros de búsqueda.'
                        : 'No hay usuarios registrados en la plataforma.'}
            </p>
            {hasNoUsers && (
                <button onClick={onRetry} className="mt-4 btn-blue touch-manipulation">
                    <span>Reintentar</span>
                </button>
            )}
        </div>
    );
};

// Componente para la tabla de usuarios (desktop)
interface UsersTableProps {
    users: BackendUser[];
    isUpdating: boolean;
    userPermissions?: { is_admin?: boolean; can_reset_passwords?: boolean };
    onEdit: (user: BackendUser) => void;
    onResetPassword: (user: BackendUser) => void;
    onDeactivate: (userId: string) => Promise<void>;
    getRoleBadgeColor: (role: string) => string;
    getRoleDisplayName: (role: string) => string;
}

const UsersTable: React.FC<UsersTableProps> = ({
    users,
    isUpdating,
    userPermissions,
    onEdit,
    onResetPassword,
    onDeactivate,
    getRoleBadgeColor,
    getRoleDisplayName
}) => (
    <div className="hidden lg:block overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
                <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Usuario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Rol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Acciones
                    </th>
                </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
                {users.map((user) => (
                    <tr key={user.id} className="hover:bg-slate-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                                <UserPhoto fotoPerfil={user.foto_perfil} nombrePersona={user.nombre_persona} size="sm" />
                                <div className="ml-4 min-w-0">
                                    <div className="text-sm font-medium text-slate-900 truncate">
                                        {user.nombre_persona}
                                    </div>
                                    <div className="text-sm text-slate-500 truncate">
                                        {user.nombre_empresa}
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-slate-900">{user.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleBadgeColor(user.rol_principal)}`}>
                                {getRoleDisplayName(user.rol_principal)}
                            </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getEstadoClasses(user.estado)}`}>
                                {user.estado || 'ACTIVO'}
                            </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex items-center space-x-2">
                                <UserActionButtons
                                    user={user}
                                    isUpdating={isUpdating}
                                    userPermissions={userPermissions}
                                    onEdit={onEdit}
                                    onResetPassword={onResetPassword}
                                    onDeactivate={onDeactivate}
                                    variant="desktop"
                                />
                            </div>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);

// Componente para las tarjetas de usuarios (móvil)
interface UsersCardsProps {
    users: BackendUser[];
    isUpdating: boolean;
    userPermissions?: { is_admin?: boolean; can_reset_passwords?: boolean };
    onEdit: (user: BackendUser) => void;
    onResetPassword: (user: BackendUser) => void;
    onDeactivate: (userId: string) => Promise<void>;
    getRoleBadgeColor: (role: string) => string;
    getRoleDisplayName: (role: string) => string;
}

const UsersCards: React.FC<UsersCardsProps> = ({
    users,
    isUpdating,
    userPermissions,
    onEdit,
    onResetPassword,
    onDeactivate,
    getRoleBadgeColor,
    getRoleDisplayName
}) => (
    <div className="lg:hidden">
        <div className="divide-y divide-slate-200">
            {users.map((user) => (
                <div key={user.id} className="p-4 hover:bg-slate-50 transition-colors">
                    <div className="flex flex-col space-y-4">
                        <div className="flex items-center space-x-3">
                            <UserPhoto fotoPerfil={user.foto_perfil} nombrePersona={user.nombre_persona} size="md" />
                            <div className="flex-1 min-w-0">
                                <h3 className="text-lg font-medium text-slate-900 break-words">
                                    {user.nombre_persona}
                                </h3>
                                <p className="text-sm text-slate-500 break-words">
                                    {user.nombre_empresa}
                                </p>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                            <div>
                                <span className="font-medium text-slate-700">Email:</span>
                                <p className="text-slate-900 break-words">{user.email}</p>
                            </div>
                            <div>
                                <span className="font-medium text-slate-700">Rol:</span>
                                <div className="mt-1">
                                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getRoleBadgeColor(user.rol_principal)}`}>
                                        {getRoleDisplayName(user.rol_principal)}
                                    </span>
                                </div>
                            </div>
                            <div className="sm:col-span-2">
                                <span className="font-medium text-slate-700">Estado:</span>
                                <div className="mt-1">
                                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getEstadoClasses(user.estado)}`}>
                                        {user.estado || 'ACTIVO'}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="flex flex-col space-y-2">
                            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                                <UserActionButtons
                                    user={user}
                                    isUpdating={isUpdating}
                                    userPermissions={userPermissions}
                                    onEdit={onEdit}
                                    onResetPassword={onResetPassword}
                                    onDeactivate={onDeactivate}
                                    variant="mobile"
                                />
                            </div>
                            <ToggleUserStatusButton
                                user={user}
                                isUpdating={isUpdating}
                                onDeactivate={onDeactivate}
                            />
                        </div>
                    </div>
                </div>
            ))}
        </div>
    </div>
);

// Componente para la paginación
interface PaginationProps {
    currentPage: number;
    totalPages: number;
    itemsPerPage: number;
    filteredUsers: BackendUser[];
    setCurrentPage: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({
    currentPage,
    totalPages,
    itemsPerPage,
    filteredUsers,
    setCurrentPage
}) => {
    if (totalPages <= 1) return null;

    const getPageNumbers = () => {
        const pages: (number | null)[] = [];
        const maxVisible = 5;
        const startPage = Math.max(1, Math.min(totalPages - maxVisible + 1, currentPage - 2));
        
        for (let i = 0; i < maxVisible; i++) {
            const pageNum = startPage + i;
            if (pageNum <= totalPages) {
                pages.push(pageNum);
            }
        }
        return pages;
    };

    return (
        <div className="bg-white px-4 py-3 border-t border-slate-200 sm:px-6">
            <div className="flex items-center justify-between">
                <div className="flex-1 flex justify-between sm:hidden">
                    <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center px-4 py-2 border border-slate-300 text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Anterior
                    </button>
                    <button
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage === totalPages}
                        className="ml-3 relative inline-flex items-center px-4 py-2 border border-slate-300 text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Siguiente
                    </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                        <p className="text-sm text-slate-700">
                            Mostrando{' '}
                            <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span>
                            {' '}a{' '}
                            <span className="font-medium">
                                {Math.min(currentPage * itemsPerPage, filteredUsers.length)}
                            </span>
                            {' '}de{' '}
                            <span className="font-medium">{filteredUsers.length}</span>
                            {' '}resultados
                        </p>
                    </div>
                    <div>
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                            <button
                                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                disabled={currentPage === 1}
                                className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-slate-300 bg-white text-sm font-medium text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Anterior
                            </button>
                            {getPageNumbers().map((pageNum) => {
                                if (pageNum === null) return null;
                                return (
                                    <button
                                        key={pageNum}
                                        onClick={() => setCurrentPage(pageNum)}
                                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                            currentPage === pageNum
                                                ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                                                : 'bg-white border-slate-300 text-slate-500 hover:bg-slate-50'
                                        }`}
                                    >
                                        {pageNum}
                                    </button>
                                );
                            })}
                            <button
                                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                disabled={currentPage === totalPages}
                                className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-slate-300 bg-white text-sm font-medium text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Siguiente
                            </button>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
    );
};

const AdminUsersPage: React.FC = () => {
    const {
        // Estados
        allUsers,
        loading,
        error,
        userPermissions,
        searchQuery,
        searchEmpresa,
        filterRole,
        filterStatus,
        currentPage,
        setCurrentPage,
        totalPages,
        totalUsers,
        notification,
        setNotification,
        isSearching,
        isUpdating,
        selectedUser,
        showEditModal,
        setShowEditModal,
        showResetPasswordModal,
        resetPasswordData,
        isResettingPassword,
        itemsPerPage,
        
        // Setters
        setSearchQuery,
        setSearchEmpresa,
        setFilterRole,
        setFilterStatus,
        
        // Funciones
        loadUsers,
        clearFilters,
        handleEditUser,
        handleResetPassword,
        executePasswordReset,
        closeResetPasswordModal,
        handleDeactivateUser,
        handleUpdateProfile,
        getRoleBadgeColor,
        getRoleDisplayName,
        showNotification,
        filteredUsers,
        paginatedUsers
    } = useAdminUsers();

    // Log para depuración cuando cambia totalUsers
    React.useEffect(() => {
        console.log('🔍 AdminUsersPage - totalUsers actualizado:', totalUsers, 'tipo:', typeof totalUsers);
    }, [totalUsers]);

    if (loading) {
        return <LoadingState />;
    }

    if (error) {
        return <ErrorState error={error} onRetry={() => loadUsers(1, undefined, undefined, filterRole)} />;
    }

    return (
        <div className="bg-slate-50 min-h-screen">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="max-w-7xl mx-auto">
                    {/* Encabezado */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-slate-900 mb-2">Gestión de Usuarios</h1>
                        <p className="text-slate-600">Administrá los usuarios registrados en la plataforma</p>
                        
                        
                    </div>

                    <NotificationBanner notification={notification} onClose={() => setNotification(null)} />

                    <FiltersSection
                        searchQuery={searchQuery}
                        searchEmpresa={searchEmpresa}
                        filterRole={filterRole}
                        filterStatus={filterStatus}
                        isSearching={isSearching}
                        setSearchQuery={setSearchQuery}
                        setSearchEmpresa={setSearchEmpresa}
                        setFilterRole={setFilterRole}
                        setFilterStatus={setFilterStatus}
                        clearFilters={clearFilters}
                        loadUsers={loadUsers}
                        currentPage={currentPage}
                        getRoleDisplayNameFromFilter={getRoleDisplayNameFromFilter}
                    />

                    <StatsSection 
                        key={`stats-${totalUsers}-${isSearching}-${isUpdating}`}
                        totalUsers={totalUsers} 
                        isSearching={isSearching} 
                        isUpdating={isUpdating} 
                    />

                    {/* Lista de usuarios - Responsive */}
                    <div className="bg-white rounded-xl shadow-md border border-slate-200/80 overflow-hidden relative">
                        {isSearching && (
                            <div className="absolute inset-0 bg-white/70 backdrop-blur-sm z-10 flex items-center justify-center rounded-xl">
                                <div className="flex flex-col items-center gap-2">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                    <span className="text-sm font-medium text-slate-700">Buscando usuarios...</span>
                                </div>
                            </div>
                        )}
                        
                        <UsersTable
                            users={paginatedUsers}
                            isUpdating={isUpdating}
                            userPermissions={userPermissions}
                            onEdit={handleEditUser}
                            onResetPassword={handleResetPassword}
                            onDeactivate={handleDeactivateUser}
                            getRoleBadgeColor={getRoleBadgeColor}
                            getRoleDisplayName={getRoleDisplayName}
                        />

                        <UsersCards
                            users={paginatedUsers}
                            isUpdating={isUpdating}
                            userPermissions={userPermissions}
                            onEdit={handleEditUser}
                            onResetPassword={handleResetPassword}
                            onDeactivate={handleDeactivateUser}
                            getRoleBadgeColor={getRoleBadgeColor}
                            getRoleDisplayName={getRoleDisplayName}
                        />

                        {paginatedUsers.length === 0 && (
                            <EmptyUsersMessage
                                allUsers={allUsers}
                                searchQuery={searchQuery}
                                searchEmpresa={searchEmpresa}
                                filterRole={filterRole}
                                filterStatus={filterStatus}
                                onRetry={() => loadUsers(1)}
                            />
                        )}

                        <Pagination
                            currentPage={currentPage}
                            totalPages={totalPages}
                            itemsPerPage={itemsPerPage}
                            filteredUsers={filteredUsers}
                            setCurrentPage={setCurrentPage}
                        />
                    </div>

                    {/* Modal de Restablecimiento de Contraseña */}
                    {showResetPasswordModal && resetPasswordData.user && (
                        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-lg font-medium text-slate-900">
                                        🔑 Restablecer Contraseña
                                    </h3>
                                    <button
                                        onClick={closeResetPasswordModal}
                                        className="text-gray-400 hover:text-gray-600"
                                    >
                                        ✕
                                    </button>
                                </div>
                                
                                <div className="space-y-4">
                                    <div className="bg-slate-50 p-4 rounded-lg">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center overflow-hidden">
                                                {resetPasswordData.user.foto_perfil ? (
                                                    <img
                                                        src={getUserPhotoUrl(resetPasswordData.user.foto_perfil)}
                                                        alt={`Foto de perfil de ${resetPasswordData.user.nombre_persona}`}
                                                        className="w-full h-full object-cover rounded-full"
                                                        onError={handleImageError}
                                                    />
                                                ) : (
                                                    <UserCircleIcon className="w-6 h-6 text-primary-600" />
                                                )}
                                            </div>
                                            <div>
                                                <div className="text-sm font-medium text-slate-900">
                                                    {resetPasswordData.user.nombre_persona}
                                                </div>
                                                <div className="text-sm text-slate-500">
                                                    {resetPasswordData.user.email}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {resetPasswordData.newPassword ? (
                                        <div className="space-y-3">
                                            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                                <div className="flex items-start">
                                                    <div className="flex-shrink-0">
                                                        <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                                        </svg>
                                                    </div>
                                                    <div className="ml-3">
                                                        <h4 className="text-sm font-medium text-green-800">
                                                            Contraseña restablecida exitosamente
                                                        </h4>
                                                        <p className="mt-1 text-sm text-green-700">
                                                            La nueva contraseña temporal ha sido generada. Compártela de forma segura con el usuario.
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-2">
                                                <label htmlFor="new-password-temp" className="block text-sm font-medium text-slate-700">
                                                    Nueva Contraseña Temporal:
                                                </label>
                                                <div className="relative">
                                                    <input
                                                        id="new-password-temp"
                                                        type="text"
                                                        value={resetPasswordData.newPassword}
                                                        readOnly
                                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 font-mono text-sm"
                                                    />
                                                    <button
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(resetPasswordData.newPassword || '');
                                                            showNotification('success', 'Contraseña copiada al portapapeles', 2000);
                                                        }}
                                                        className="absolute right-2 top-1/2 transform -translate-y-1/2 text-slate-500 hover:text-slate-700"
                                                        title="Copiar al portapapeles"
                                                    >
                                                        📋
                                                    </button>
                                                </div>
                                                <p className="text-xs text-slate-500">
                                                    Haz clic en el ícono para copiar la contraseña
                                                </p>
                                            </div>


                                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                                <h5 className="text-sm font-medium text-blue-800 mb-2">📋 Instrucciones importantes:</h5>
                                                <ul className="text-xs text-blue-700 space-y-1">
                                                    <li>• Comparte esta contraseña de forma segura con el usuario</li>
                                                    <li>• Recomienda al usuario cambiar la contraseña en su próximo inicio de sesión</li>
                                                    <li>• Esta contraseña es temporal y debe ser cambiada</li>
                                                </ul>
                                            </div>

                                            <div className="flex justify-end">
                                                <button
                                                    onClick={closeResetPasswordModal}
                                                    className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors touch-manipulation"
                                                >
                                                    Cerrar
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                                                <div className="flex items-start">
                                                    <div className="flex-shrink-0">
                                                        <ExclamationCircleIcon className="h-5 w-5 text-yellow-400" />
                                                    </div>
                                                    <div className="ml-3">
                                                        <h4 className="text-sm font-medium text-yellow-800">
                                                            Confirmación requerida
                                                        </h4>
                                                        <p className="mt-1 text-sm text-yellow-700">
                                                            ¿Estás seguro de que quieres restablecer la contraseña de este usuario? 
                                                            Se generará una nueva contraseña temporal que deberás compartir de forma segura.
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>

                                            
                                            <div className="flex justify-end space-x-3">
                                                <button
                                                    onClick={closeResetPasswordModal}
                                                    disabled={isResettingPassword}
                                                    className="btn-uniform btn-secondary disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
                                                >
                                                    <span>Cancelar</span>
                                                </button>
                                                <button
                                                    onClick={executePasswordReset}
                                                    disabled={isResettingPassword}
                                                    className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation flex items-center space-x-2"
                                                >
                                                    {isResettingPassword && (
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                                    )}
                                                    <span>{isResettingPassword ? 'Restableciendo...' : 'Confirmar Restablecimiento'}</span>
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Modal de Edición de Perfil */}
                    {showEditModal && selectedUser && (
                        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                                <h3 className="text-lg font-medium text-slate-900 mb-4">
                                    Editar Perfil de Usuario
                                </h3>
                                <form onSubmit={(e) => {
                                    e.preventDefault();
                                    const formData = new FormData(e.target as HTMLFormElement);
                                    handleUpdateProfile({
                                        nombre_persona: formData.get('nombre_persona') as string,
                                        nombre_empresa: formData.get('nombre_empresa') as string,
                                        email: formData.get('email') as string
                                    });
                                }}>
                                    <div className="space-y-4">
                                        <div>
                                            <label htmlFor="edit-nombre-persona" className="block text-sm font-medium text-slate-700 mb-1">
                                                Nombre y Apellido
                                            </label>
                                            <input
                                                id="edit-nombre-persona"
                                                type="text"
                                                name="nombre_persona"
                                                defaultValue={selectedUser.nombre_persona}
                                                required
                                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="edit-nombre-empresa" className="block text-sm font-medium text-slate-700 mb-1">
                                                Razón social de la empresa
                                            </label>
                                            <input
                                                id="edit-nombre-empresa"
                                                type="text"
                                                name="nombre_empresa"
                                                defaultValue={selectedUser.nombre_empresa || ''}
                                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="edit-email" className="block text-sm font-medium text-slate-700 mb-1">
                                                Email
                                            </label>
                                            <input
                                                id="edit-email"
                                                type="email"
                                                name="email"
                                                defaultValue={selectedUser.email}
                                                required
                                                readOnly={!userPermissions?.can_edit_emails}
                                                className={`w-full px-3 py-2 border rounded-lg focus:ring-primary-500 focus:border-primary-500 ${
                                                    userPermissions?.can_edit_emails
                                                        ? 'border-slate-300'
                                                        : 'border-slate-200 bg-slate-50 text-slate-600 cursor-not-allowed'
                                                }`}
                                                placeholder={userPermissions?.can_edit_emails ? '' : 'Solo administradores pueden editar emails'}
                                            />
                                        </div>
                                    </div>
                                    <div className="flex justify-end space-x-3 mt-6">
                                        <button
                                            type="button"
                                            onClick={() => setShowEditModal(false)}
                                            disabled={isUpdating}
                                            className="btn-uniform btn-secondary disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
                                        >
                                            <span>Cancelar</span>
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={isUpdating}
                                            className="btn-blue disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
                                        >
                                            {isUpdating && (
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                            )}
                                            <span>{isUpdating ? 'Actualizando...' : 'Actualizar'}</span>
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminUsersPage;
