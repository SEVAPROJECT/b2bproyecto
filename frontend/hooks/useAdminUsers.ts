import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { API_CONFIG, buildApiUrl } from '../config/api';

export interface BackendUser {
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

interface UserPermissions {
    is_admin: boolean;
    can_edit_users: boolean;
    can_edit_emails: boolean;
    can_reset_passwords: boolean;
    can_deactivate_users: boolean;
}

interface Notification {
    type: 'success' | 'error' | 'info';
    message: string;
}

const DEFAULT_PERMISSIONS: UserPermissions = {
    is_admin: true,
    can_edit_users: true,
    can_edit_emails: true,
    can_reset_passwords: true,
    can_deactivate_users: true
};

export const useAdminUsers = () => {
    // Estados principales
    const [allUsers, setAllUsers] = useState<BackendUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [availableRoles, setAvailableRoles] = useState<any[]>([]);
    const [userPermissions, setUserPermissions] = useState<UserPermissions>(DEFAULT_PERMISSIONS);
    
    // Estados de búsqueda y filtros
    const [searchQuery, setSearchQuery] = useState('');
    const [searchEmpresa, setSearchEmpresa] = useState('');
    const [filterRole, setFilterRole] = useState('all');
    const [filterStatus, setFilterStatus] = useState('all');
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalUsers, setTotalUsers] = useState(0);
    
    // Estados de operaciones
    const [isSearching, setIsSearching] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);
    const [notification, setNotification] = useState<Notification | null>(null);
    
    // Estados de modales
    const [selectedUser, setSelectedUser] = useState<BackendUser | null>(null);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
    const [resetPasswordData, setResetPasswordData] = useState<{user: BackendUser | null, newPassword: string | null}>({user: null, newPassword: null});
    const [isResettingPassword, setIsResettingPassword] = useState(false);

    const itemsPerPage = 12;

    // Función helper para mostrar notificaciones
    const showNotification = useCallback((type: 'success' | 'error' | 'info', message: string, duration: number = 3000) => {
        setNotification({ type, message });
        setTimeout(() => setNotification(null), duration);
    }, []);

    // Función para verificar si hay operaciones en curso
    const isOperationInProgress = useCallback(() => {
        return isUpdating || isSearching;
    }, [isUpdating, isSearching]);

    // Ref para prevenir llamadas múltiples
    const isLoadingRef = useRef(false);
    // Ref para mantener referencia estable a loadUsers
    const loadUsersRef = useRef<typeof loadUsers>();
    // Ref para saber si es la carga inicial
    const isInitialLoadRef = useRef(true);

    // Función helper para verificar si se debe saltar la carga
    const shouldSkipLoad = useCallback((retryCount: number): boolean => {
        if (isLoadingRef.current && retryCount === 0) {
            console.log('⚠️ Carga ya en progreso, saltando llamada duplicada');
            return true;
        }
        return false;
    }, []);

    // Función helper para configurar estados de loading
    const setLoadingStates = useCallback(() => {
        if (isInitialLoadRef.current) {
            setLoading(true);
        } else {
            setIsSearching(true);
        }
    }, []);

    // Función helper para construir URL con parámetros
    const buildUsersUrl = useCallback((page: number, searchEmpresaParam?: string, searchNombreParam?: string): string => {
        const urlParams = new URLSearchParams();
        urlParams.append('page', page.toString());
        urlParams.append('limit', '100');
        
        if (searchEmpresaParam?.trim()) {
            urlParams.append('search_empresa', searchEmpresaParam.trim());
        }
        
        if (searchNombreParam?.trim()) {
            urlParams.append('search_nombre', searchNombreParam.trim());
        }

        return buildApiUrl(`${API_CONFIG.ADMIN.USERS}?${urlParams.toString()}`);
    }, []);

    // Función helper para realizar el fetch con timeout
    const fetchUsersWithTimeout = useCallback(async (url: string): Promise<Response> => {
        const timeoutPromise = new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Timeout de usuarios')), 10000)
        );

        const fetchPromise = fetch(url, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });

        return await Promise.race([fetchPromise, timeoutPromise]);
    }, []);

    // Función helper para procesar respuesta exitosa
    const processSuccessfulResponse = useCallback((data: any) => {
        console.log('✅ Usuarios cargados:', data.usuarios?.length || 0);
        
        setAllUsers(data.usuarios || []);
        setTotalUsers(data.total || 0);
        setTotalPages(data.total_pages || 1);
        setCurrentPage(data.page || 1);
        
        isInitialLoadRef.current = false;
    }, []);

    // Función helper para manejar errores de respuesta
    const handleResponseError = useCallback(async (
        response: Response,
        page: number,
        searchEmpresaParam: string | undefined,
        searchNombreParam: string | undefined,
        retryCount: number
    ): Promise<boolean> => {
        console.log('❌ Error en respuesta del servidor:', response.status);
        
        if (response.status === 500 && retryCount < 2) {
            console.log(`🔄 Reintentando carga de usuarios... (${retryCount + 1}/2)`);
            await new Promise(resolve => setTimeout(resolve, 1000));
            return true; // Indica que se debe reintentar
        }
        
        setError('Error al cargar usuarios. Verifica tu conexión.');
        setAllUsers(prev => prev.length === 0 ? [] : prev);
        return false;
    }, []);

    // Función helper para manejar errores de excepción
    const handleFetchError = useCallback(async (
        error: unknown,
        page: number,
        searchEmpresaParam: string | undefined,
        searchNombreParam: string | undefined,
        retryCount: number
    ): Promise<boolean> => {
        console.error('❌ Error cargando usuarios:', error);
        
        if (error instanceof Error && 
            (error.message.includes('Timeout') || error.message.includes('Failed to fetch')) && 
            retryCount < 2) {
            console.log(`🔄 Reintentando por ${error.message.includes('Timeout') ? 'timeout' : 'conexión'}... (${retryCount + 1}/2)`);
            await new Promise(resolve => setTimeout(resolve, 1000));
            return true; // Indica que se debe reintentar
        }
        
        setError('Error al cargar usuarios. Verifica tu conexión.');
        setAllUsers(prev => prev.length === 0 ? [] : prev);
        return false;
    }, []);

    // Función helper para limpiar estados de loading
    const clearLoadingStates = useCallback(() => {
        isLoadingRef.current = false;
        setLoading(false);
        setIsSearching(false);
    }, []);

    // Función para cargar usuarios
    const loadUsers = useCallback(async (page: number = 1, searchEmpresaParam?: string, searchNombreParam?: string, retryCount: number = 0) => {
        try {
            if (shouldSkipLoad(retryCount)) {
                return;
            }
            
            isLoadingRef.current = true;
            setLoadingStates();
            setError(null);

            console.log(`📊 Cargando usuarios optimizado... (intento ${retryCount + 1})`);

            const url = buildUsersUrl(page, searchEmpresaParam, searchNombreParam);
            console.log(`🔗 URL de carga: ${url}`);
            const token = localStorage.getItem('access_token');
            console.log(`🔑 Token presente: ${token ? 'Sí' : 'No'}`);
            
            const response = await fetchUsersWithTimeout(url);
            console.log(`📡 Respuesta recibida: ${response.status} ${response.statusText}`);

            if (response.ok) {
                const data = await response.json();
                console.log(`✅ Datos recibidos: ${data.usuarios?.length || 0} usuarios`);
                processSuccessfulResponse(data);
            } else {
                const shouldRetry = await handleResponseError(response, page, searchEmpresaParam, searchNombreParam, retryCount);
                if (shouldRetry) {
                    return loadUsers(page, searchEmpresaParam, searchNombreParam, retryCount + 1);
                }
            }

        } catch (error) {
            const shouldRetry = await handleFetchError(error, page, searchEmpresaParam, searchNombreParam, retryCount);
            if (shouldRetry) {
                return loadUsers(page, searchEmpresaParam, searchNombreParam, retryCount + 1);
            }
        } finally {
            clearLoadingStates();
        }
    }, [shouldSkipLoad, setLoadingStates, buildUsersUrl, fetchUsersWithTimeout, processSuccessfulResponse, handleResponseError, handleFetchError, clearLoadingStates]);
    
    // Actualizar ref cuando loadUsers cambie
    useEffect(() => {
        loadUsersRef.current = loadUsers;
    }, [loadUsers]);

    // Función para cargar roles
    const loadRoles = useCallback(async () => {
        try {
            console.log('📋 Cargando roles...');
            
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de roles')), 3000)
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
                console.log('✅ Roles cargados:', data.roles?.length || 0);
            } else {
                console.warn('⚠️ Error en respuesta de roles:', response.status);
                setAvailableRoles([]);
            }
        } catch (err: any) {
            console.warn('⚠️ Error cargando roles (no crítico):', err.message);
            setAvailableRoles([]);
        }
    }, []);

    // Función para cargar permisos
    const loadUserPermissions = useCallback(async () => {
        try {
            console.log('🔐 Cargando permisos de administrador...');

            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de permisos')), 5000)
            );

            const fetchPromise = fetch(buildApiUrl(`${API_CONFIG.ADMIN.USERS}/permissions`), {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Permisos obtenidos:', data.permissions);
                setUserPermissions(data.permissions);
            } else {
                console.log('⚠️ API de permisos devolvió', response.status, '- usando permisos por defecto');
                throw new Error(`API devolvió ${response.status}`);
            }
        } catch (err: any) {
            console.warn('⚠️ Error cargando permisos (usando por defecto):', err.message);
            console.log('✅ Asumiendo permisos de administrador por defecto');
            setUserPermissions(DEFAULT_PERMISSIONS);
        }
    }, []);

    // Cargar datos iniciales (solo una vez al montar)
    useEffect(() => {
        const loadAllData = async () => {
            try {
                console.log('🚀 Iniciando carga de datos iniciales...');
                await loadUserPermissions();
                await loadUsers(1);
                loadRoles().catch(error => {
                    console.warn('⚠️ Error cargando roles (no crítico):', error);
                });
            } catch (error) {
                console.error('❌ Error cargando datos iniciales:', error);
                // No establecer error aquí, dejar que loadUsers lo maneje
            }
        };

        loadAllData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Solo ejecutar una vez al montar

    // Funciones auxiliares para filtrado
    const matchesSearchQuery = useCallback((user: BackendUser, query: string): boolean => {
        if (!query.trim() || query.length >= 3) {
            return true; // Búsquedas largas se manejan en backend
        }
        const lowerQuery = query.toLowerCase();
        return user.nombre_persona.toLowerCase().includes(lowerQuery) ||
               user.email.toLowerCase().includes(lowerQuery);
    }, []);

    const matchesSearchEmpresa = useCallback((user: BackendUser, query: string): boolean => {
        if (!query.trim() || query.length >= 3) {
            return true; // Búsquedas largas se manejan en backend
        }
        const lowerQuery = query.toLowerCase();
        return user.nombre_empresa?.toLowerCase().includes(lowerQuery) ?? false;
    }, []);

    const matchesRoleFilter = useCallback((user: BackendUser, roleFilter: string): boolean => {
        if (roleFilter === 'all') {
            return true;
        }
        return user.rol_principal === roleFilter;
    }, []);

    const matchesStatusFilter = useCallback((user: BackendUser, statusFilter: string): boolean => {
        if (statusFilter === 'all') {
            return true;
        }
        return user.estado === statusFilter;
    }, []);

    // Usuarios filtrados
    const filteredUsers = useMemo(() => {
        console.log('🔍 DEBUG: filteredUsers - allUsers.length:', allUsers.length);
        
        return allUsers.filter(user => {
            const matchesSearch = matchesSearchQuery(user, searchQuery);
            const matchesEmpresa = matchesSearchEmpresa(user, searchEmpresa);
            const matchesRole = matchesRoleFilter(user, filterRole);
            const matchesStatus = matchesStatusFilter(user, filterStatus);
            
            return matchesSearch && matchesEmpresa && matchesRole && matchesStatus;
        });
    }, [allUsers, searchQuery, searchEmpresa, filterRole, filterStatus, matchesSearchQuery, matchesSearchEmpresa, matchesRoleFilter, matchesStatusFilter]);

    // Debouncing para búsqueda de nombre/email
    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchQuery.length >= 3) {
                const loadUsersFn = loadUsersRef.current;
                if (loadUsersFn) {
                    setIsSearching(true);
                    loadUsersFn(1, undefined, searchQuery);
                }
            } else if (searchQuery.length === 0 && searchEmpresa.length === 0) {
                // Si se borra la búsqueda, recargar sin filtros
                const loadUsersFn = loadUsersRef.current;
                if (loadUsersFn) {
                    loadUsersFn(1, '', '');
                }
            } else {
                // Si la búsqueda es muy corta, solo limpiar el indicador
                setIsSearching(false);
            }
        }, 500);

        return () => clearTimeout(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchQuery]);

    // Debouncing para búsqueda de empresa
    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchEmpresa.length >= 3) {
                const loadUsersFn = loadUsersRef.current;
                if (loadUsersFn) {
                    setIsSearching(true);
                    loadUsersFn(1, searchEmpresa, undefined);
                }
            } else if (searchEmpresa.length === 0 && searchQuery.length === 0) {
                // Si se borra la búsqueda, recargar sin filtros
                const loadUsersFn = loadUsersRef.current;
                if (loadUsersFn) {
                    loadUsersFn(1, '', '');
                }
            } else {
                // Si la búsqueda es muy corta, solo limpiar el indicador
                setIsSearching(false);
            }
        }, 500);

        return () => clearTimeout(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchEmpresa]);

    // Función para limpiar filtros
    const clearFilters = useCallback(() => {
        setSearchQuery('');
        setSearchEmpresa('');
        setFilterRole('all');
        setFilterStatus('all');
        setCurrentPage(1);
        loadUsers(1, '', '');
        showNotification('info', 'Filtros limpiados');
    }, [loadUsers, showNotification]);

    // Funciones de manejo de usuarios
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

        if (!userPermissions?.is_admin && !userPermissions?.can_reset_passwords) {
            showNotification('error', 'No tienes permisos para restablecer contraseñas', 4000);
            return;
        }
        
        setResetPasswordData({user, newPassword: null});
        setShowResetPasswordModal(true);
    }, [isOperationInProgress, showNotification, userPermissions]);

    const executePasswordReset = useCallback(async () => {
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
    }, [resetPasswordData, showNotification]);

    const closeResetPasswordModal = useCallback(() => {
        setShowResetPasswordModal(false);
        setResetPasswordData({user: null, newPassword: null});
    }, []);

    const handleDeactivateUser = useCallback(async (userId: string): Promise<boolean> => {
        const user = allUsers.find(u => u.id === userId);
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

                const newEstado = isInactive ? 'ACTIVO' : 'INACTIVO';
                const updatedUsers = allUsers.map((user: BackendUser) =>
                    user.id === userId
                        ? { ...user, estado: newEstado }
                        : user
                );
                setAllUsers(updatedUsers);

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
    }, [allUsers, showNotification]);

    const handleUpdateProfile = useCallback(async (profileData: any) => {
        try {
            setIsUpdating(true);

            const emailChanged = profileData.email !== selectedUser?.email;
            if (emailChanged && !userPermissions?.can_edit_emails) {
                showNotification('error', 'No tienes permisos para editar emails. Este campo es de solo lectura para administradores.', 5000);
                return;
            }

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
                const updatedUsers = allUsers.map((user: BackendUser) =>
                    user.id === selectedUser?.id
                        ? {
                            ...user,
                            nombre_persona: profileData.nombre_persona,
                            nombre_empresa: profileData.nombre_empresa,
                            email: profileData.email
                        }
                        : user
                );
                setAllUsers(updatedUsers);

                showNotification('success', 'Perfil actualizado exitosamente');
                setShowEditModal(false);
            } else if (response.status === 401) {
                showNotification('error', 'Sesión expirada. Por favor, refresca la página e inicia sesión nuevamente.', 5000);
            } else if (responseData.detail) {
                showNotification('error', `Error: ${responseData.detail}`, 5000);
            } else {
                showNotification('error', 'Error actualizando perfil', 4000);
            }
        } catch (err: any) {
            showNotification('error', `Error: ${err.message}`, 5000);
        } finally {
            setIsUpdating(false);
        }
    }, [selectedUser, allUsers, userPermissions, showNotification]);

    // Funciones auxiliares para UI
    const getRoleBadgeColor = useCallback((role: string) => {
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
    }, []);

    const getRoleDisplayName = useCallback((role: string) => {
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
    }, []);

    // Paginación
    const paginatedUsers = useMemo(() => {
        return filteredUsers;
    }, [filteredUsers]);

    return {
        // Estados
        allUsers,
        loading,
        error,
        availableRoles,
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
        setSelectedUser,
        
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
    };
};

