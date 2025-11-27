// @refresh reset
import React, { createContext, useContext, useState, useEffect, useRef, useMemo, ReactNode } from 'react';
import { AuthContextType, User, ProviderApplicationStatus, UserRole, ProviderStatus } from '../types/auth';
import { ProviderOnboardingData } from '../types/provider';
import { authAPI, providersAPI } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
    children: ReactNode;
}

const AuthProvider = ({ children }: AuthProviderProps) => {
    const [user, setUser] = useState<User | null>(null);
    const [providerStatus, setProviderStatus] = useState<ProviderStatus>('none');
    const [providerApplication, setProviderApplication] = useState<ProviderApplicationStatus>({
        status: 'none',
        documents: {}
    });
    const [isLoading, setIsLoading] = useState(true); // Iniciar en true para verificar autenticación
    const [error, setError] = useState<string | null>(null);
    const loadingUserRef = useRef(false); // Para evitar cargas duplicadas

    // Función helper para validar condiciones previas antes de cargar usuario
    const shouldLoadUser = (): boolean => {
        if (user) {
            console.log('🔍 Usuario ya cargado, saliendo');
            return false;
        }
        if (loadingUserRef.current) {
            console.log('🔍 Ya se está cargando, saliendo');
            return false;
        }
        return true;
    };

    // Función helper para obtener y validar el token de acceso
    const getAccessToken = (): string | null => {
        const accessToken = localStorage.getItem('access_token');
        console.log('🔍 accessToken:', accessToken ? 'Presente' : 'No presente');
        if (!accessToken) {
            console.log('🔍 No hay token, reseteando loading=false y saliendo');
            setIsLoading(false);
            return null;
        }
        return accessToken;
    };

    // Función helper para determinar el rol del usuario desde el perfil
    const determineUserRole = (profile: any): UserRole => {
        let userRole: UserRole = 'client';
        
        if (profile.roles && Array.isArray(profile.roles)) {
            const rolesLower = new Set(profile.roles.map((role: string) => role.toLowerCase()));
            console.log('🎭 Roles en minúsculas:', Array.from(rolesLower));
            
            if (rolesLower.has('admin') || rolesLower.has('administrador')) {
                userRole = 'admin';
                console.log('Usuario es ADMIN (verificado en backend)');
            } else if (rolesLower.has('provider') || rolesLower.has('proveedor')) {
                userRole = 'provider';
                console.log('🏢 Usuario es PROVIDER (verificado en backend)');
            } else {
                console.log('👤 Usuario es CLIENT (verificado en backend)');
            }
        } else {
            console.log('⚠️ No se encontraron roles en el perfil:', profile);
        }
        
        return userRole;
    };

    // Función helper para obtener el estado de verificación del proveedor
    const getProviderVerificationStatus = async (accessToken: string): Promise<{
        status: ProviderStatus;
        application: ProviderApplicationStatus;
    }> => {
        let providerStatus: ProviderStatus = 'none';
        let providerApplication: ProviderApplicationStatus = { status: 'none', documents: {} };
        
        try {
            const verificationStatus = await authAPI.getVerificacionEstado(accessToken);
            console.log('📋 Estado de verificación al cargar:', verificationStatus);
            
            if (verificationStatus.estado) {
                const estado = verificationStatus.estado as ProviderStatus;
                providerStatus = estado;
                providerApplication = {
                    status: estado,
                    submittedAt: verificationStatus.fecha_solicitud,
                    reviewedAt: verificationStatus.fecha_revision,
                    rejectionReason: verificationStatus.comentario,
                    documents: {}
                };
            }
        } catch (verificationError) {
            console.log('⚠️ No se pudo obtener estado de verificación al cargar:', verificationError);
        }
        
        return { status: providerStatus, application: providerApplication };
    };

    // Función helper para construir el objeto User desde el perfil
    const buildUserFromProfile = (
        profile: any,
        accessToken: string,
        userRole: UserRole,
        providerStatus: ProviderStatus,
        providerApplication: ProviderApplicationStatus
    ): User => {
        return {
            id: profile.id || `user_${Date.now()}`,
            name: profile.nombre_persona || profile.nombre || profile.first_name || profile.name || profile.email?.split('@')[0] || 'Usuario',
            email: profile.email || profile.correo || 'usuario@email.com',
            role: userRole,
            companyName: profile.nombre_empresa || profile.razon_social || profile.company_name || 'Mi Empresa',
            ruc: profile.ruc || null,
            accessToken: accessToken,
            createdAt: profile.created_at || new Date().toISOString(),
            updatedAt: profile.updated_at || new Date().toISOString(),
            providerStatus: providerStatus,
            providerApplication: providerApplication,
            foto_perfil: profile.foto_perfil || null
        };
    };

    // Función helper para manejar errores al cargar usuario
    const handleLoadUserError = (err: any) => {
        console.error('❌ Error cargando usuario:', err);
        console.error('❌ Tipo de error:', typeof err);
        console.error('❌ Propiedades del error:', Object.keys(err));
        console.error('❌ Status del error:', err.status);
        console.error('❌ Message del error:', err.message);
        console.error('❌ Detail del error:', err.detail);
        
        if (err.status === 401 || err.status === 403 || 
            err.message?.includes('401') ||
            err.message?.includes('403')) {
            console.log('🔐 Error de autenticación, limpiando localStorage');
            localStorage.removeItem('access_token');
        } else if (err.message?.includes('Timeout')) {
            console.log('⏰ Timeout de conexión, manteniendo sesión para reintento');
        } else {
            console.log('⚠️ Error de conexión, manteniendo sesión para reintento');
        }
    };

    // Verificar si hay un usuario logueado al cargar la app
    useEffect(() => {
        const loadUser = async () => {
            console.log('🔍 loadUser ejecutándose...');
            console.log('🔍 user:', user);
            console.log('🔍 loadingUserRef.current:', loadingUserRef.current);
            
            if (!shouldLoadUser()) {
                return;
            }
            
            const accessToken = getAccessToken();
            if (!accessToken) {
                return;
            }
            
            console.log('🔍 Estableciendo loading=true y cargando usuario...');
            loadingUserRef.current = true;
            setIsLoading(true);
            
            try {
                console.log('🔑 Token encontrado, obteniendo perfil...');
                const profile = await authAPI.getProfile(accessToken);
                console.log('👤 Perfil obtenido:', profile);
                console.log('🔍 Campos disponibles en el perfil:', Object.keys(profile));
                console.log('📝 Valores de campos de nombre posibles:', {
                    nombre_persona: profile.nombre_persona,
                    nombre: profile.nombre,
                    first_name: profile.first_name,
                    name: profile.name,
                    email: profile.email,
                    correo: profile.correo
                });
                console.log('📸 Foto de perfil en perfil:', profile.foto_perfil);
                console.log('🏢 RUC en perfil del backend:', profile.ruc);

                const userRole = determineUserRole(profile);
                const { status: providerStatus, application: providerApplication } = 
                    await getProviderVerificationStatus(accessToken);

                const newUser = buildUserFromProfile(
                    profile,
                    accessToken,
                    userRole,
                    providerStatus,
                    providerApplication
                );
                
                console.log('🏢 RUC mapeado en newUser:', newUser.ruc);
                console.log('👤 Usuario completo creado:', newUser);
                
                setUser(newUser);
                setProviderStatus(newUser.providerStatus);
                setProviderApplication(newUser.providerApplication);
            } catch (err: any) {
                handleLoadUserError(err);
            } finally {
                console.log('🔍 Finally: reseteando loading=false');
                setIsLoading(false);
                loadingUserRef.current = false;
            }
        };

        loadUser();
    }, []); // Sin dependencias para ejecutar solo una vez

    // Debug: monitorear cambios en el estado del usuario
    useEffect(() => {
        console.log('🔍 Estado del usuario cambió:', {
            user: user ? 'Usuario presente' : 'Usuario null',
            isAuthenticated: !!user,
            isLoading: isLoading
        });
    }, [user, isLoading]);

    // Debug: monitorear cambios en isLoading específicamente
    useEffect(() => {
        console.log('🔍 isLoading cambió a:', isLoading);
    }, [isLoading]);

    const login = async (email: string, password: string) => {
        console.log('🔐 LOGIN INICIADO');
        try {
            console.log('🔐 Estableciendo isLoading=true');
            setIsLoading(true);
            setError(null);

            // Llamada real a la API (solo refresh_token se establece en cookie)
            console.log('🔐 Iniciando signIn...');
            const response = await authAPI.signIn({ email, password });
            console.log('✅ SignIn exitoso:', response);

            // Obtener datos reales del usuario desde el backend
            console.log('👤 Obteniendo perfil...');
            const profile = await authAPI.getProfile(response.access_token);
            console.log('✅ Perfil obtenido:', profile);

            // Usar funciones helper para determinar rol y construir usuario
            const userRole = determineUserRole(profile);
            const { status: providerStatus, application: providerApplication } = 
                await getProviderVerificationStatus(response.access_token);

            // Mapear el perfil a la estructura User usando función helper
            console.log('🏢 RUC en perfil del login:', profile.ruc);
            const userData = buildUserFromProfile(
                profile,
                response.access_token,
                userRole,
                providerStatus,
                providerApplication
            );
            console.log('🏢 RUC mapeado en userData del login:', userData.ruc);

            // Guardar ambos tokens en localStorage
            localStorage.setItem('access_token', response.access_token);
            if (response.refresh_token) {
                localStorage.setItem('refresh_token', response.refresh_token);
                console.log('✅ Refresh token guardado en localStorage');
            } else {
                // console.warn('⚠️ No se recibió refresh_token del servidor');
                // Nota: refresh_token se envía como HttpOnly cookie, no en la respuesta JSON
            }
            
            setUser(userData);
            setProviderStatus(userData.providerStatus);
            setProviderApplication(userData.providerApplication);

            // Login exitoso - React Router manejará la redirección automáticamente
            console.log('✅ Login exitoso, usuario autenticado correctamente');

        } catch (err: any) {
            console.error('❌ CATCH: Error en login:', err);
            // Manejar específicamente el error de cuenta inactiva
            const errorMessage = err.detail || err.message || 'Error al iniciar sesión';
            console.error('❌ Error message:', errorMessage);
            
            if (errorMessage.includes('inactiva') || errorMessage.includes('inactive') || 
                errorMessage.includes('desactivada') || errorMessage.includes('desactivado')) {
                setError('Tu cuenta está inactiva. Por favor, contacta al administrador en b2bseva.notificaciones@gmail.com para más detalles.');
            } else {
                setError(errorMessage);
            }
            throw err;
        } finally {
            console.log('🔐 FINALLY: Reseteando isLoading=false');
            setIsLoading(false);
        }
    };

    const register = async (data: { companyName: string; name: string; email: string; password: string; ruc?: string }) => {
        try {
            setIsLoading(true);
            setError(null);
            
            // Validar contraseña antes de enviar
            if (data.password.length < 8) {
                setError('La contraseña debe tener al menos 8 caracteres');
                return;
            }
            
            if (!/[A-Z]/.test(data.password)) {
                setError('La contraseña debe contener al menos una letra mayúscula');
                return;
            }
            
            if (!/[a-z]/.test(data.password)) {
                setError('La contraseña debe contener al menos una letra minúscula');
                return;
            }
            
            if (!/\d/.test(data.password)) {
                setError('La contraseña debe contener al menos un número');
                return;
            }
            
            if (!/[!@#$%^&*(),.?":{}|<>]/.test(data.password)) {
                setError('La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?":{}|<>)');
                return;
            }
            
            const response = await authAPI.signUp({
                email: data.email,
                password: data.password,
                nombre_persona: data.name,
                nombre_empresa: data.companyName,
                ruc: data.ruc,
            });
            
            // Si la respuesta incluye tokens, el usuario se autenticó automáticamente
            if ('access_token' in response) {
                localStorage.setItem('access_token', response.access_token);
                localStorage.setItem('refresh_token', response.refresh_token);
                
                const newUser: User = {
                    id: Date.now(),
                    role: 'client', // Por defecto, todos los usuarios son clientes
                    companyName: data.companyName,
                    name: data.name,
                    email: data.email,
                    accessToken: response.access_token,
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                    providerStatus: 'none',
                    providerApplication: { status: 'none', documents: {} }
                };
                setUser(newUser);
                setProviderStatus('none'); // Estado inicial para clientes
            } else {
                // Si solo recibimos mensaje de confirmación, mostrar mensaje
                setError(null);
                // Aquí podrías mostrar un mensaje de éxito o redirigir a login
            }
        } catch (err: any) {
            console.error('Error completo:', err);
            
            // Manejar diferentes tipos de errores
            if (err.detail && Array.isArray(err.detail)) {
                // Error de validación del backend
                const errorMessages = err.detail.map((e: any) => e.msg || e.message || 'Error de validación').join(', ');
                setError(errorMessages);
            } else if (err.detail) {
                // Error simple del backend
                setError(err.detail);
            } else if (err.message) {
                // Error de JavaScript
                setError(err.message);
            } else {
                // Error genérico
                setError('Error al registrar usuario');
            }
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = async () => {
        try {
            // Obtener access_token de localStorage para enviarlo en el header
            const accessToken = localStorage.getItem('access_token');
            
            if (accessToken) {
                // Llamar al endpoint de logout con el token en el header
                await authAPI.logout(accessToken);
                console.log('🍪 Refresh token cookie limpiada automáticamente');
            } else {
                console.warn('⚠️ No se encontró access_token para logout');
            }
            
            // Limpiar localStorage también
            localStorage.removeItem('access_token');
            console.log('💾 Access token limpiado de localStorage');
            
            setUser(null);
            setProviderStatus('none');
            setProviderApplication({ status: 'none', documents: {} });
        } catch (err) {
            console.error('Error al cerrar sesión:', err);
            // Aún así, limpiar el estado local aunque falle el logout del servidor
            localStorage.removeItem('access_token');
            setUser(null);
            setProviderStatus('none');
            setProviderApplication({ status: 'none', documents: {} });
        }
    };

    // Función para renovar token automáticamente
    const refreshToken = async () => {
        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                throw new Error('No hay refresh token');
            }

            console.log('🔄 Renovando token...');
            const response = await authAPI.refreshToken(refreshToken);
            
            // Actualizar tokens en localStorage
            localStorage.setItem('access_token', response.access_token);
            if (response.refresh_token) {
                localStorage.setItem('refresh_token', response.refresh_token);
            }

            // Actualizar usuario con nuevo token
            if (user) {
                setUser({ ...user, accessToken: response.access_token });
            }

            console.log('✅ Token renovado exitosamente');
            return response.access_token;
        } catch (error) {
            console.error('❌ Error al renovar token:', error);
            
            // No hacer logout automático en errores 500 del servidor
            if (error instanceof Error && (
                error.message.includes('500') || 
                error.message.includes('Error temporal del servidor') ||
                error.message.includes('Error interno del servidor')
            )) {
                console.log('⚠️ Error 500 en refresh, manteniendo sesión');
                // Lanzar un error específico para que useApiWithAuth lo maneje
                throw new Error('Error temporal del servidor. Por favor, intenta nuevamente.');
            }
            
            // Solo hacer logout en errores de autenticación reales (401, 403, etc.)
            if (error instanceof Error && (
                error.message.includes('401') ||
                error.message.includes('403') ||
                error.message.includes('Sesión expirada') ||
                error.message.includes('Token inválido')
            )) {
                console.log('🔐 Error de autenticación real, cerrando sesión');
                logout();
                throw error;
            }
            
            // Para otros errores, no hacer logout automático
            console.log('⚠️ Error en refresh, manteniendo sesión');
            throw error;
        }
    };

    const reloadUserProfile = async () => {
        console.log('🔄 Recargando perfil del usuario...');
        try {
            // Obtener access_token de localStorage
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                console.warn('⚠️ No se encontró access_token para recargar perfil');
                return;
            }
            
            // Agregar timeout para evitar esperas infinitas
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de conexión')), 5000)
            );

            const profilePromise = authAPI.getProfile(accessToken);
            const profile = await Promise.race([profilePromise, timeoutPromise]);
            console.log('👤 Perfil recargado:', profile);
            console.log('🔍 Campos disponibles:', Object.keys(profile));

            // Usar funciones helper para determinar rol, obtener estado de verificación y construir usuario
            const userRole = determineUserRole(profile);
            const { status: providerStatus, application: providerApplication } = 
                await getProviderVerificationStatus(accessToken);

            const updatedUser = buildUserFromProfile(
                profile,
                accessToken,
                userRole,
                providerStatus,
                providerApplication
            );

            console.log('✅ Usuario actualizado:', updatedUser);
            setUser(updatedUser);
            setProviderStatus(providerStatus);
            setProviderApplication(providerApplication);

        } catch (error) {
            console.error('❌ Error recargando perfil:', error);
            
            // Si es un error de CORS o timeout, no hacer nada para evitar bucles
            if (error instanceof Error && (
                error.message.includes('Timeout') || 
                error.message.includes('CORS') ||
                error.message.includes('Failed to fetch')
            )) {
                console.log('⚠️ Error de conexión detectado, manteniendo perfil actual');
                return;
            }
            
            // Para otros errores, limpiar el token si es necesario
            if (error instanceof Error && error.message.includes('401')) {
                console.log('🔐 Token inválido, limpiando sesión');
                localStorage.removeItem('access_token');
                setUser(null);
            }
        }
    };

    const updateProviderStatus = (status: ProviderStatus) => {
        setProviderStatus(status);
    };

    const updateProviderApplication = (application: ProviderApplicationStatus) => {
        setProviderApplication(application);
    };

    const submitProviderApplication = async (data: ProviderOnboardingData) => {
        if (user?.role === 'client') {
            setIsLoading(true);
            try {
                const accessToken = localStorage.getItem('access_token');
                if (!accessToken) {
                    throw new Error('No hay token de acceso');
                }

                // Usar funciones helper para procesar documentos y construir perfil_in
                const { documentos, nombres_tip_documento } = processUploadedDocuments(data.documents);
                const perfil_in = buildPerfilIn(data);

                // Enviar a la API
                await providersAPI.submitProviderApplication({
                    perfil_in: JSON.stringify(perfil_in),
                    documentos,
                    nombres_tip_documento,
                    comentario_solicitud: ''
                }, accessToken);
                
                // Usar función helper para actualizar el estado
                updateApplicationState(user.email);
                
            } catch (error) {
                console.error('Error enviando solicitud:', error);
                throw error;
            } finally {
                setIsLoading(false);
            }
        }
    };

    // Función helper para obtener el mapeo de tipos de documentos
    const getDocumentTypeMapping = (): Record<string, string> => {
        return {
            'ruc': 'Constancia de RUC',
            'cedula': 'Cédula MiPymes',
            'certificado': 'Certificado de Cumplimiento Tributario',
            'certificados_rubro': 'Certificados del Rubro',
        };
    };

    // Función helper para procesar documentos subidos
    const processUploadedDocuments = (documents: Record<string, any>): { documentos: File[]; nombres_tip_documento: string[] } => {
        const documentos: File[] = [];
        const nombres_tip_documento: string[] = [];
        const documentTypeMapping = getDocumentTypeMapping();

        for (const [key, doc] of Object.entries(documents)) {
            if (doc.status === 'uploaded' && doc.file) {
                documentos.push(doc.file);
                nombres_tip_documento.push(documentTypeMapping[key] || doc.name);
                console.log(`📄 Enviando documento ${key}: ${doc.file.name}`);
            } else if (doc.status === 'uploaded' && !doc.file) {
                console.log(`⚠️ Documento ${key} marcado como actualizable pero no se ha subido uno nuevo`);
            }
        }

        // Si no hay documentos nuevos para enviar, enviar al menos un documento vacío para evitar error 422
        if (documentos.length === 0) {
            console.log('⚠️ No hay documentos nuevos para enviar, creando documento vacío');
            const emptyFile = new File([''], 'empty.txt', { type: 'text/plain' });
            documentos.push(emptyFile);
            nombres_tip_documento.push('Constancia de RUC');
        }

        return { documentos, nombres_tip_documento };
    };

    // Función helper para construir el objeto perfil_in
    const buildPerfilIn = (data: ProviderOnboardingData) => {
        return {
            nombre_fantasia: data.company.tradeName,
            direccion: {
                departamento: data.address.department,
                ciudad: data.address.city,
                barrio: data.address.neighborhood,
                calle: data.address.street,
                numero: data.address.number,
                referencia: data.address.reference
            },
            sucursal: {
                nombre: data.branch.name,
                telefono: data.branch.phone,
                email: data.branch.email,
                usar_direccion_fiscal: data.branch.useFiscalAddress
            }
        };
    };

    // Función helper para actualizar el estado después del envío
    const updateApplicationState = (userEmail: string | undefined) => {
        const updatedApplication: ProviderApplicationStatus = {
            status: 'pending',
            submittedAt: new Date().toISOString(),
            documents: {}
        };
        
        setProviderApplication(updatedApplication);
        setProviderStatus('pending');
        
        if (userEmail) {
            localStorage.setItem(`providerStatus_${userEmail}`, 'pending');
            localStorage.setItem(`providerApplication_${userEmail}`, JSON.stringify(updatedApplication));
        }
    };

    // Función helper para obtener y validar el token de acceso
    const getAccessTokenForSubmission = (): string => {
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
            throw new Error('No hay token de acceso');
        }
        return accessToken;
    };

    const resubmitProviderApplication = async (data: ProviderOnboardingData) => {
        if (user?.role === 'client') {
            setIsLoading(true);
            try {
                const accessToken = getAccessTokenForSubmission();
                const { documentos, nombres_tip_documento } = processUploadedDocuments(data.documents);
                const perfil_in = buildPerfilIn(data);

                await providersAPI.submitProviderApplication({
                    perfil_in: JSON.stringify(perfil_in),
                    documentos,
                    nombres_tip_documento,
                    comentario_solicitud: ''
                }, accessToken);
                
                updateApplicationState(user.email);
                
            } catch (error) {
                console.error('Error reenviando solicitud:', error);
                throw error;
            } finally {
                setIsLoading(false);
            }
        }
    };

    const value: AuthContextType = useMemo(() => ({
        user,
        isAuthenticated: !!user,
        providerStatus,
        providerApplication,
        login,
        register,
        logout,
        refreshToken,
        reloadUserProfile,
        submitProviderApplication,
        resubmitProviderApplication,
        updateProviderStatus,
        updateProviderApplication,
        isLoading,
        error
    }), [
        user,
        providerStatus,
        providerApplication,
        login,
        register,
        logout,
        refreshToken,
        reloadUserProfile,
        submitProviderApplication,
        resubmitProviderApplication,
        updateProviderStatus,
        updateProviderApplication,
        isLoading,
        error
    ]);
    
    // Debug: verificar el estado del contexto
    console.log('🔍 AuthContext value actualizado:', {
        user: user ? 'Usuario presente' : 'Usuario null',
        isAuthenticated: !!user,
        isLoading: isLoading
    });

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export { AuthContext, AuthProvider };
