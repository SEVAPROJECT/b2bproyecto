import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { UserCircleIcon, ExclamationCircleIcon } from '../icons';
import OptimizedLoading from '../ui/OptimizedLoading';
import { adminAPI } from '../../services/api';
import { API_CONFIG, buildApiUrl } from '../../config/api';

interface BackendUser {
    id: string;
    nombre_persona: string;
    email: string;
    rol_principal: string;
    estado: string;
    nombre_empresa?: string;
    foto_perfil?: string;
    fecha_creacion?: string;
    fecha_actualizacion?: string;
}

const AdminUsersPage: React.FC = () => {
    const [users, setUsers] = useState<BackendUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedUser, setSelectedUser] = useState<BackendUser | null>(null);
    const [showEditModal, setShowEditModal] = useState(false);
    const [availableRoles, setAvailableRoles] = useState<any[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchEmpresa, setSearchEmpresa] = useState('');
    const [searchEmpresaDebounced, setSearchEmpresaDebounced] = useState('');
    const [filterRole, setFilterRole] = useState('all');
    const [filterStatus, setFilterStatus] = useState('all');
    const [userPermissions, setUserPermissions] = useState<any>(null);
    const [isSearching, setIsSearching] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);
    const [notification, setNotification] = useState<{type: 'success' | 'error' | 'info', message: string} | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 12;
    const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
    const [resetPasswordData, setResetPasswordData] = useState<{user: BackendUser | null, newPassword: string | null}>({user: null, newPassword: null});
    const [isResettingPassword, setIsResettingPassword] = useState(false);

    // Función helper para mostrar notificaciones
    const showNotification = useCallback((type: 'success' | 'error' | 'info', message: string, duration: number = 3000) => {
        setNotification({ type, message });
        setTimeout(() => setNotification(null), duration);
    }, []);

    // Función para verificar si hay operaciones en curso
    const isOperationInProgress = useCallback(() => {
        return isUpdating || isSearching;
    }, [isUpdating, isSearching]);

    useEffect(() => {
        // Optimización: Cargar datos en paralelo para mejor rendimiento
        const loadAllData = async () => {
            try {
                // Cargar usuarios primero (más importante)
                await loadUsers();
                
                // Cargar roles y permisos en paralelo (menos críticos)
                await Promise.allSettled([
                    loadRoles(),
                    loadUserPermissions()
                ]);
            } catch (error) {
                console.error('Error cargando datos iniciales:', error);
            }
        };

        loadAllData();
    }, []);

    // Debouncing para búsqueda de empresa (500ms)
    useEffect(() => {
        const timer = setTimeout(() => {
            setSearchEmpresaDebounced(searchEmpresa);
        }, 500);

        return () => clearTimeout(timer);
    }, [searchEmpresa]);

    // Efecto para búsqueda de empresa con debouncing
    useEffect(() => {
        if (searchEmpresaDebounced !== undefined) {
            loadUsersWithSearch(searchEmpresaDebounced);
        }
    }, [searchEmpresaDebounced]);

    const loadUsers = async () => {
        try {
            setLoading(true);
            setError(null);
            setIsSearching(false);

            const url = buildApiUrl(API_CONFIG.ADMIN.USERS);

            // Optimización: Agregar timeout para evitar carga infinita
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de carga')), 6000)
            );

            const fetchPromise = fetch(url, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

            if (response.ok) {
                const data = await response.json();
                setUsers(data.usuarios || []);
            } else {
                // Manejo mejorado de errores
                if (response.status === 404) {
                    console.log('⚠️ Endpoint /admin/users no encontrado, usando datos vacíos');
                    setUsers([]);
                    return; // No mostrar error para 404, solo usar array vacío
                } else {
                    const errorText = await response.text();
                    throw new Error(`Error ${response.status}: ${errorText}`);
                }
            }
        } catch (err: any) {
            // Optimización: Mostrar error más específico
            if (err.message === 'Timeout de carga') {
                setError('La carga está tardando demasiado. Por favor, recarga la página.');
            } else if (err.message.includes('CORS') || err.message.includes('Failed to fetch')) {
                setError('Error de conexión con el servidor. Verifica tu conexión a internet.');
            } else {
                setError(err.message);
            }
        } finally {
            setLoading(false);
        }
    };

    const loadUsersWithSearch = async (empresaSearch: string) => {
        try {
            const trimmedSearch = empresaSearch?.trim() || '';

            // Solo mostrar indicador de búsqueda si hay texto real
            if (trimmedSearch) {
                setIsSearching(true);

                // Pequeño delay para mejor UX (al menos 200ms de indicador visual)
                await new Promise(resolve => setTimeout(resolve, 200));
            }

            // Construir URL con parámetros de búsqueda
            const urlParams = new URLSearchParams();
            if (trimmedSearch) {
                urlParams.append('search_empresa', trimmedSearch);
            }

            const url = buildApiUrl(`${API_CONFIG.ADMIN.USERS}${urlParams.toString() ? '?' + urlParams.toString() : ''}`);

            // Optimización: Agregar timeout para búsquedas
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de búsqueda')), 5000)
            );

            const fetchPromise = fetch(url, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

            if (response.ok) {
                const data = await response.json();
                setUsers(data.usuarios || []);
            } else {
                // Manejo mejorado de errores para búsqueda
                if (response.status === 404) {
                    console.log('⚠️ Endpoint /admin/users no encontrado en búsqueda, manteniendo lista actual');
                    // Mantener la lista actual en lugar de mostrar error
                } else {
                    const errorText = await response.text();
                    console.error(`Error en búsqueda: ${response.status}: ${errorText}`);
                }
            }
        } catch (err: any) {
            // Mantener la lista actual en caso de error de red
        } finally {
            setIsSearching(false);
        }
    };

    const loadRoles = async () => {
        try {
            // Optimización: Agregar timeout para roles
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de roles')), 6000)
            );

            const fetchPromise = fetch(buildApiUrl(API_CONFIG.ADMIN.ROLES), {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

            if (response.ok) {
                const data = await response.json();
                setAvailableRoles(data.roles || []);
            } else {
                const errorText = await response.text();
            }
        } catch (err: any) {
            // Optimización: No bloquear la UI si los roles fallan
            setAvailableRoles([]);
        }
    };

    const loadUserPermissions = async () => {
        try {
            // Optimización: Agregar timeout para permisos
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de permisos')), 6000)
            );

            const fetchPromise = fetch(buildApiUrl(`${API_CONFIG.ADMIN.USERS}/permissions`), {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

            if (response.ok) {
                const data = await response.json();
                setUserPermissions(data.permissions);
            } else {
                const errorText = await response.text();
            }
        } catch (err: any) {
            // Optimización: No bloquear la UI si los permisos fallan
            setUserPermissions(null);
        }
    };

    // Función para limpiar filtros
    const clearFilters = useCallback(() => {
        setSearchQuery('');
        setSearchEmpresa('');
        setSearchEmpresaDebounced('');
        setFilterRole('all');
        setFilterStatus('all');
        setCurrentPage(1);
        // No recargar usuarios, solo limpiar filtros
        showNotification('info', 'Filtros limpiados');
    }, [showNotification]);

    const handleEditUser = useCallback((user: BackendUser) => {
        if (isOperationInProgress()) {
            showNotification('info', 'Espera a que termine la operación actual', 3000);
            return;
        }
        setSelectedUser(user);
        setShowEditModal(true);
    }, [isOperationInProgress, showNotification]);

    const handleResetPassword = useCallback((user: BackendUser) => {
        if (isOperationInProgress()) {
            showNotification('info', 'Espera a que termine la operación actual', 3000);
            return;
        }
        
        // Verificar permisos de administrador
        if (!userPermissions?.is_admin) {
            showNotification('error', 'Solo los administradores pueden restablecer contraseñas', 4000);
            return;
        }
        
        setResetPasswordData({user, newPassword: null});
        setShowResetPasswordModal(true);
    }, [isOperationInProgress, showNotification, userPermissions]);

    const executePasswordReset = async () => {
        if (!resetPasswordData.user) return;
        
        try {
            setIsResettingPassword(true);
            const response = await fetch(buildApiUrl(`${API_CONFIG.ADMIN.USERS}/${resetPasswordData.user.id}/reset-password`), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (response.ok) {
                setResetPasswordData(prev => ({...prev, newPassword: result.new_password}));
                showNotification('success', `Contraseña restablecida exitosamente para ${resetPasswordData.user.nombre_persona}`, 5000);
            } else {
                throw new Error(result.detail || 'Error al restablecer la contraseña');
            }
        } catch (err: any) {
            showNotification('error', `Error: ${err.message}`, 5000);
        } finally {
            setIsResettingPassword(false);
        }
    };

    const closeResetPasswordModal = () => {
        setShowResetPasswordModal(false);
        setResetPasswordData({user: null, newPassword: null});
    };

    const handleDeactivateUser = async (userId: string): Promise<boolean> => {
        // Encontrar el usuario para saber su estado actual
        const user = users.find(u => u.id === userId);
        const isInactive = user?.estado === 'INACTIVO';

        const confirmMessage = isInactive
            ? '¿Estás seguro de que quieres reactivar este usuario?'
            : '¿Estás seguro de que quieres desactivar este usuario?';

        if (!confirm(confirmMessage)) {
            return false;
        }

        try {
            setIsUpdating(true);
            const response = await fetch(buildApiUrl(`${API_CONFIG.ADMIN.USERS}/${userId}/toggle-status`), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const result = await response.json();

                // Actualización optimista: cambiar estado del usuario localmente
                const newEstado = isInactive ? 'ACTIVO' : 'INACTIVO';
                const updatedUsers = users.map((user: BackendUser) =>
                    user.id === userId
                        ? { ...user, estado: newEstado }
                        : user
                );
                setUsers(updatedUsers);

                const actionMessage = isInactive ? 'reactivado' : 'desactivado';
                showNotification('success', result.message || `Usuario ${actionMessage} exitosamente`);

                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Error desactivando usuario');
            }
        } catch (err: any) {
            showNotification('error', `Error: ${err.message}`, 5000);
            return false;
        } finally {
            setIsUpdating(false);
        }
    };

    const handleUpdateProfile = async (profileData: any) => {
        try {
            setIsUpdating(true);

            // Validar permisos de email SOLO si se está intentando cambiar el email
            const emailChanged = profileData.email !== selectedUser?.email;
            if (emailChanged && !userPermissions?.can_edit_emails) {
                showNotification('error', 'No tienes permisos para editar emails. Este campo es de solo lectura para administradores.', 5000);
                return;
            }

            // Verificar que hay cambios reales antes de enviar
            const hasNameChange = profileData.nombre_persona !== selectedUser?.nombre_persona;
            const hasCompanyChange = profileData.nombre_empresa !== selectedUser?.nombre_empresa;
            const hasEmailChange = emailChanged;

            if (!hasNameChange && !hasCompanyChange && !hasEmailChange) {
                showNotification('info', 'No se detectaron cambios en el perfil.');
                return;
            }

            const response = await fetch(buildApiUrl(`${API_CONFIG.ADMIN.USERS}/${selectedUser?.id}/profile`), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(profileData)
            });

            const responseData = await response.json();

            if (response.ok) {
                // Actualización optimista: actualizar el usuario localmente sin recargar
                const updatedUsers = users.map((user: BackendUser) =>
                    user.id === selectedUser?.id
                        ? {
                            ...user,
                            nombre_persona: profileData.nombre_persona,
                            nombre_empresa: profileData.nombre_empresa,
                            email: profileData.email
                        }
                        : user
                );
                setUsers(updatedUsers);

                showNotification('success', 'Perfil actualizado exitosamente');
                setShowEditModal(false);
            } else {
                // Manejar errores específicos
                if (response.status === 401) {
                    showNotification('error', 'Sesión expirada. Por favor, refresca la página e inicia sesión nuevamente.', 5000);
                } else if (responseData.detail) {
                    showNotification('error', `Error: ${responseData.detail}`, 5000);
                } else {
                    showNotification('error', 'Error actualizando perfil', 4000);
                }
            }
        } catch (err: any) {
            showNotification('error', `Error: ${err.message}`, 5000);
        } finally {
            setIsUpdating(false);
        }
    };

    const getRoleBadgeColor = (role: string) => {
        switch (role) {
            case 'admin':
                return 'bg-red-100 text-red-800';
            case 'provider':
                return 'bg-blue-100 text-blue-800';
            case 'client':
                return 'bg-green-100 text-green-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getRoleDisplayName = (role: string) => {
        switch (role) {
            case 'admin':
                return 'Administrador';
            case 'provider':
                return 'Proveedor';
            case 'client':
                return 'Cliente';
            default:
                return role;
        }
    };

    const filteredUsers = useMemo(() => {
        let filtered = [...users];

        // Filtro por búsqueda
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(user =>
                user.nombre_persona.toLowerCase().includes(query) ||
                user.email.toLowerCase().includes(query)
            );
        }

        // Filtro por rol
        if (filterRole !== 'all') {
            filtered = filtered.filter(user =>
                user.rol_principal === filterRole
            );
        }

        // Filtro por estado
        if (filterStatus !== 'all') {
            filtered = filtered.filter(user => {
                return user.estado === filterStatus;
            });
        }

        return filtered;
    }, [users, searchQuery, filterRole, filterStatus]);

    // Paginación
    const paginatedUsers = useMemo(() => {
        const startIndex = (currentPage - 1) * itemsPerPage;
        return filteredUsers.slice(startIndex, startIndex + itemsPerPage);
    }, [filteredUsers, currentPage, itemsPerPage]);

    const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);

    if (loading) {
        return (
            <OptimizedLoading 
                message="Cargando usuarios..."
                showProgress={false}
            />
        );
    }

    if (error) {
        return (
            <div className="bg-slate-50 min-h-screen">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="bg-white p-8 rounded-xl shadow-md border border-slate-200/80">
                        <div className="text-center py-12">
                            <ExclamationCircleIcon className="mx-auto h-12 w-12 text-yellow-400" />
                            <h3 className="mt-2 text-lg font-semibold text-slate-800">Información no disponible</h3>
                            <p className="mt-1 text-sm text-slate-500">
                                {error.includes('Timeout') 
                                    ? 'La carga está tardando más de lo esperado. Algunos datos pueden no estar disponibles.'
                                    : 'No se pudieron cargar los usuarios en este momento. Verifica tu conexión.'
                                }
                            </p>
                            <button
                                onClick={loadUsers}
                                className="mt-4 btn-blue touch-manipulation"
                            >
                                <span>Reintentar</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
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

                    {/* Sistema de Notificaciones */}
                    {notification && (
                        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 ${
                            notification.type === 'success'
                                ? 'bg-green-100 border border-green-400 text-green-800'
                                : notification.type === 'error'
                                ? 'bg-red-100 border border-red-400 text-red-800'
                                : 'bg-blue-100 border border-blue-400 text-blue-800'
                        }`}>
                            <div className="flex items-center">
                                <div className="flex-1">
                                    <p className="text-sm font-medium">{notification.message}</p>
                                </div>
                                <button
                                    onClick={() => setNotification(null)}
                                    className="ml-4 text-gray-400 hover:text-gray-600"
                                >
                                    ✕
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Filtros y Búsqueda */}
                    <div className="bg-white p-4 sm:p-6 rounded-xl shadow-md border border-slate-200/80 mb-6">
                        {/* Indicadores de filtros activos */}
                        {(searchEmpresa || searchQuery || filterRole !== 'all' || filterStatus !== 'all') && (
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
                                            Rol: {filterRole === 'admin' ? 'Administrador' : filterRole === 'provider' ? 'Proveedor' : 'Cliente'}
                                        </span>
                                    )}
                                    {filterStatus !== 'all' && (
                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                            Estado: {filterStatus}
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 sm:gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Buscar Usuario
                                </label>
                                <input
                                    type="text"
                                    placeholder="Nombre o email..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Buscar Empresa
                                    {isSearching && searchEmpresa.trim() && (
                                        <span className="ml-2 text-xs text-blue-600 animate-pulse">
                                            🔍 Buscando...
                                        </span>
                                    )}
                                </label>
                                <input
                                    type="text"
                                    placeholder="Nombre de empresa..."
                                    value={searchEmpresa}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        setSearchEmpresa(value);
                                        // Nota: La búsqueda se realiza automáticamente con debouncing
                                    }}
                                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                />
                                {searchEmpresa.trim() && !isSearching && (
                                    <p className="text-xs text-slate-500 mt-1">
                                        Búsqueda automática activada
                                    </p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Rol
                                </label>
                                <select
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
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Estado
                                </label>
                                <select
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
                                {(searchEmpresa || searchQuery || filterRole !== 'all' || filterStatus !== 'all') && (
                                    <button
                                        onClick={clearFilters}
                                        className="w-full sm:w-auto bg-gray-500 text-white px-3 sm:px-4 py-2 text-sm rounded-lg hover:bg-gray-600 transition-colors"
                                    >
                                        Limpiar Filtros
                                    </button>
                                )}
                                <button
                                    onClick={loadUsers}
                                    className="w-full sm:w-auto bg-primary-600 text-white px-3 sm:px-4 py-2 text-sm rounded-lg hover:bg-primary-700 transition-colors"
                                >
                                    Actualizar
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Estadísticas */}
                    <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm border border-slate-200/80 mb-6">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                            <div>
                                <h3 className="text-base sm:text-lg font-medium text-slate-900">
                                    Total: {filteredUsers.length} usuarios
                                </h3>
                                {isSearching && (
                                    <span className="ml-2 text-blue-600 animate-pulse">
                                        🔄 Buscando...
                                    </span>
                                )}
                                {isUpdating && !isSearching && (
                                    <span className="ml-2 text-orange-600 animate-pulse">
                                        ⚡ Procesando...
                                    </span>
                                )}
                            </div>
                            <div className="text-right">
                                <div className="text-sm text-slate-500">
                                    {isSearching && (
                                        <span className="text-blue-600 animate-pulse">
                                            🔄 Buscando...
                                        </span>
                                    )}
                                    {isUpdating && !isSearching && (
                                        <span className="text-orange-600 animate-pulse">
                                            ⚡ Procesando...
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Lista de usuarios - Responsive */}
                    <div className="bg-white rounded-xl shadow-md border border-slate-200/80 overflow-hidden">
                        {/* Vista de tabla para desktop */}
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
                                    {paginatedUsers.map((user) => (
                                        <tr key={user.id} className="hover:bg-slate-50">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center">
                                                    <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center overflow-hidden flex-shrink-0">
                                                        {user.foto_perfil ? (
                                                            <img
                                                        src={user.foto_perfil.startsWith('/') 
                                                            ? `${API_CONFIG.BASE_URL.replace('/api/v1', '')}${user.foto_perfil}` 
                                                            : user.foto_perfil}
                                                                alt={`Foto de perfil de ${user.nombre_persona}`}
                                                                className="w-full h-full object-cover rounded-full"
                                                                onError={(e) => {
                                                                    const target = e.target as HTMLImageElement;
                                                                    target.style.display = 'none';
                                                                    const parent = target.parentElement;
                                                                    if (parent) {
                                                                        parent.innerHTML = '<svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>';
                                                                    }
                                                                }}
                                                            />
                                                        ) : (
                                                            <UserCircleIcon className="w-6 h-6 text-primary-600" />
                                                        )}
                                                    </div>
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
                                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                    user.estado === 'ACTIVO'
                                                        ? 'bg-green-100 text-green-800'
                                                        : 'bg-red-100 text-red-800'
                                                }`}>
                                                    {user.estado || 'ACTIVO'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                <div className="flex items-center space-x-2">
                                                    <button
                                                        onClick={() => handleEditUser(user)}
                                                        className="flex items-center space-x-1 px-3 py-1.5 text-sm font-medium text-primary-600 hover:text-primary-900 bg-primary-50 hover:bg-primary-100 rounded-md transition-colors border border-primary-200 hover:border-primary-300"
                                                        title="Editar información del usuario"
                                                    >
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                        </svg>
                                                        <span>Editar</span>
                                                    </button>
                                                    
                                                    <button
                                                        onClick={() => handleResetPassword(user)}
                                                        disabled={!userPermissions?.is_admin}
                                                        className={`flex items-center space-x-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors border ${
                                                            userPermissions?.is_admin
                                                                ? 'text-orange-600 hover:text-orange-900 bg-orange-50 hover:bg-orange-100 border-orange-200 hover:border-orange-300'
                                                                : 'text-gray-400 bg-gray-50 cursor-not-allowed border-gray-200'
                                                        }`}
                                                        title={
                                                            userPermissions?.is_admin 
                                                                ? "Restablecer contraseña del usuario" 
                                                                : "Solo administradores pueden restablecer contraseñas"
                                                        }
                                                    >
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1 7 2 1 9 z" />
                                                        </svg>
                                                        <span>Restablecer</span>
                                                        {!userPermissions?.is_admin && (
                                                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                                <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
                                                            </svg>
                                                        )}
                                                    </button>
                                                    
                                                    <button
                                                        onClick={async () => {
                                                            await handleDeactivateUser(user.id);
                                                        }}
                                                        disabled={isUpdating}
                                                        className={`flex items-center space-x-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors border disabled:opacity-50 disabled:cursor-not-allowed ${
                                                            user.estado === 'INACTIVO'
                                                                ? 'text-green-600 hover:text-green-900 bg-green-50 hover:bg-green-100 border-green-200 hover:border-green-300'
                                                                : 'text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 border-red-200 hover:border-red-300'
                                                        }`}
                                                        title={
                                                            user.estado === 'INACTIVO' 
                                                                ? "Reactivar usuario" 
                                                                : "Desactivar usuario"
                                                        }
                                                    >
                                                        {isUpdating ? (
                                                            <div className={`animate-spin rounded-full h-4 w-4 border-b-2 ${
                                                                user.estado === 'INACTIVO' ? 'border-green-600' : 'border-red-600'
                                                            }`}></div>
                                                        ) : (
                                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                {user.estado === 'INACTIVO' ? (
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                ) : (
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                )}
                                                            </svg>
                                                        )}
                                                        <span>
                                                            {isUpdating
                                                                ? 'Procesando...'
                                                                : user.estado === 'INACTIVO'
                                                                    ? 'Reactivar'
                                                                    : 'Desactivar'
                                                            }
                                                        </span>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Vista de tarjetas para móvil y tablet */}
                        <div className="lg:hidden">
                            <div className="divide-y divide-slate-200">
                                {paginatedUsers.map((user) => (
                                    <div key={user.id} className="p-4 hover:bg-slate-50 transition-colors">
                                        <div className="flex flex-col space-y-4">
                                            {/* Información del usuario */}
                                            <div className="flex items-center space-x-3">
                                                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center overflow-hidden flex-shrink-0">
                                                    {user.foto_perfil ? (
                                                        <img
                                                            src={user.foto_perfil.startsWith('/') 
                                                                ? `${API_CONFIG.BASE_URL.replace('/api/v1', '')}${user.foto_perfil}` 
                                                                : user.foto_perfil}
                                                            alt={`Foto de perfil de ${user.nombre_persona}`}
                                                            className="w-full h-full object-cover rounded-full"
                                                            onError={(e) => {
                                                                const target = e.target as HTMLImageElement;
                                                                target.style.display = 'none';
                                                                const parent = target.parentElement;
                                                                if (parent) {
                                                                    parent.innerHTML = '<svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>';
                                                                }
                                                            }}
                                                        />
                                                    ) : (
                                                        <UserCircleIcon className="w-6 h-6 text-primary-600" />
                                                    )}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <h3 className="text-lg font-medium text-slate-900 break-words">
                                                        {user.nombre_persona}
                                                    </h3>
                                                    <p className="text-sm text-slate-500 break-words">
                                                        {user.nombre_empresa}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Información adicional */}
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
                                                        <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${
                                                            user.estado === 'ACTIVO'
                                                                ? 'bg-green-100 text-green-800'
                                                                : 'bg-red-100 text-red-800'
                                                        }`}>
                                                            {user.estado || 'ACTIVO'}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Botones de acción */}
                                            <div className="flex flex-col space-y-2">
                                                <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                                                    <button
                                                        onClick={() => handleEditUser(user)}
                                                        className="w-full sm:w-auto flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium text-primary-600 hover:text-primary-900 bg-primary-50 hover:bg-primary-100 rounded-md transition-colors border border-primary-200 hover:border-primary-300"
                                                        title="Editar información del usuario"
                                                    >
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                        </svg>
                                                        <span>Editar</span>
                                                    </button>
                                                    
                                                    <button
                                                        onClick={() => handleResetPassword(user)}
                                                        disabled={!userPermissions?.is_admin}
                                                        className={`w-full sm:w-auto flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors border ${
                                                            userPermissions?.is_admin
                                                                ? 'text-orange-600 hover:text-orange-900 bg-orange-50 hover:bg-orange-100 border-orange-200 hover:border-orange-300'
                                                                : 'text-gray-400 bg-gray-50 cursor-not-allowed border-gray-200'
                                                        }`}
                                                        title={
                                                            userPermissions?.is_admin 
                                                                ? "Restablecer contraseña del usuario" 
                                                                : "Solo administradores pueden restablecer contraseñas"
                                                        }
                                                    >
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1 7 2 1 9 z" />
                                                        </svg>
                                                        <span>Restablecer</span>
                                                        {!userPermissions?.is_admin && (
                                                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                                <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
                                                            </svg>
                                                        )}
                                                    </button>
                                                </div>
                                                
                                                <button
                                                    onClick={async () => {
                                                        await handleDeactivateUser(user.id);
                                                    }}
                                                    disabled={isUpdating}
                                                    className={`w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors border disabled:opacity-50 disabled:cursor-not-allowed ${
                                                        user.estado === 'INACTIVO'
                                                            ? 'text-green-600 hover:text-green-900 bg-green-50 hover:bg-green-100 border-green-200 hover:border-green-300'
                                                            : 'text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 border-red-200 hover:border-red-300'
                                                    }`}
                                                    title={
                                                        user.estado === 'INACTIVO' 
                                                            ? "Reactivar usuario" 
                                                            : "Desactivar usuario"
                                                    }
                                                >
                                                    {isUpdating ? (
                                                        <div className={`animate-spin rounded-full h-4 w-4 border-b-2 ${
                                                            user.estado === 'INACTIVO' ? 'border-green-600' : 'border-red-600'
                                                        }`}></div>
                                                    ) : (
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            {user.estado === 'INACTIVO' ? (
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                            ) : (
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                            )}
                                                        </svg>
                                                    )}
                                                    <span>
                                                        {isUpdating
                                                            ? 'Procesando...'
                                                            : user.estado === 'INACTIVO'
                                                                ? 'Reactivar'
                                                                : 'Desactivar'
                                                        }
                                                    </span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Mensaje cuando no hay usuarios */}
                        {paginatedUsers.length === 0 && (
                            <div className="p-8 text-center">
                                <UserCircleIcon className="mx-auto h-12 w-12 text-slate-400" />
                                <h3 className="mt-2 text-lg font-medium text-slate-900">
                                    {users.length === 0 
                                        ? 'No hay usuarios disponibles' 
                                        : 'No se encontraron usuarios'
                                    }
                                </h3>
                                <p className="mt-1 text-sm text-slate-500">
                                    {users.length === 0 
                                        ? 'Los datos de usuarios no están disponibles en este momento. Verifica tu conexión.'
                                        : searchQuery || searchEmpresa || filterRole !== 'all' || filterStatus !== 'all'
                                            ? 'Intenta ajustar los filtros de búsqueda.'
                                            : 'No hay usuarios registrados en la plataforma.'
                                    }
                                </p>
                                {users.length === 0 && (
                                    <button
                                        onClick={loadUsers}
                                        className="mt-4 btn-blue touch-manipulation"
                                    >
                                        <span>Reintentar</span>
                                    </button>
                                )}
                            </div>
                        )}

                        {/* Paginación */}
                        {totalPages > 1 && (
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
                                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                    const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                                                    if (pageNum > totalPages) return null;

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
                        )}
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
                                                        src={resetPasswordData.user.foto_perfil.startsWith('/') 
                                                            ? `${API_CONFIG.BASE_URL.replace('/api/v1', '')}${resetPasswordData.user.foto_perfil}` 
                                                            : resetPasswordData.user.foto_perfil}
                                                        alt={`Foto de perfil de ${resetPasswordData.user.nombre_persona}`}
                                                        className="w-full h-full object-cover rounded-full"
                                                        onError={(e) => {
                                                            // Si la imagen falla al cargar, mostrar el icono por defecto
                                                            const target = e.target as HTMLImageElement;
                                                            target.style.display = 'none';
                                                            const parent = target.parentElement;
                                                            if (parent) {
                                                                parent.innerHTML = '<svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>';
                                                            }
                                                        }}
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

                                    {!resetPasswordData.newPassword ? (
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
                                    ) : (
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
                                                <label className="block text-sm font-medium text-slate-700">
                                                    Nueva Contraseña Temporal:
                                                </label>
                                                <div className="relative">
                                                    <input
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
                                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                                Nombre y Apellido
                                            </label>
                                            <input
                                                type="text"
                                                name="nombre_persona"
                                                defaultValue={selectedUser.nombre_persona}
                                                required
                                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                                Razón social de la empresa
                                            </label>
                                            <input
                                                type="text"
                                                name="nombre_empresa"
                                                defaultValue={selectedUser.nombre_empresa || ''}
                                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                                Email
                                            </label>
                                            <input
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
