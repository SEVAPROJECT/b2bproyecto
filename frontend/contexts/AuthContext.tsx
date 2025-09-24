import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AuthContextType, User, ProviderApplicationStatus, UserRole } from '../types/auth';
import { ProviderOnboardingData } from '../types/provider';
import { authAPI, providersAPI, adminAPI } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [providerStatus, setProviderStatus] = useState<'none' | 'pending' | 'approved' | 'rejected'>('none');
    const [providerApplication, setProviderApplication] = useState<ProviderApplicationStatus>({
        status: 'none',
        documents: {}
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Verificar si hay un usuario logueado al cargar la app
    useEffect(() => {
        const loadUser = async () => {
            console.log('🚀 Iniciando carga automática del usuario...');
            try {
                const accessToken = localStorage.getItem('access_token');
                if (!accessToken) {
                    console.log('❌ No hay token de acceso');
                    setIsLoading(false);
                    return;
                }

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

                // Validación robusta de roles como en Apporiginal.tsx
                let userRole: UserRole = 'client';
                
                // Verificar si tiene rol de admin en el backend (solución para mayúsculas/minúsculas)
                if (profile.roles && Array.isArray(profile.roles)) {
                    const rolesLower = profile.roles.map((role: string) => role.toLowerCase());
                    console.log('🎭 Roles en minúsculas:', rolesLower);
                    
                    if (rolesLower.includes('admin') || rolesLower.includes('administrador')) {
                        userRole = 'admin';
                        console.log('Usuario es ADMIN (verificado en backend)');
                    } else if (rolesLower.includes('provider') || rolesLower.includes('proveedor')) {
                        userRole = 'provider';
                        console.log('🏢 Usuario es PROVIDER (verificado en backend)');
                    } else {
                        console.log('👤 Usuario es CLIENT (verificado en backend)');
                    }
                } else {
                    console.log('⚠️ No se encontraron roles en el perfil:', profile);
                }
                
                // Obtener el estado actual de la solicitud de verificación
                let providerStatus: 'none' | 'pending' | 'approved' | 'rejected' = 'none';
                let providerApplication: ProviderApplicationStatus = { status: 'none', documents: {} };
                
                try {
                    const verificationStatus = await authAPI.getVerificacionEstado(accessToken);
                    console.log('📋 Estado de verificación al cargar:', verificationStatus);
                    
                    if (verificationStatus.estado) {
                        const estado = verificationStatus.estado as 'none' | 'pending' | 'approved' | 'rejected';
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
                    // Usar valores por defecto si no se puede obtener el estado
                }

                const newUser: User = {
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
                
                console.log('👤 Usuario configurado:', newUser);
                setUser(newUser);
                setProviderStatus(newUser.providerStatus);
                setProviderApplication(newUser.providerApplication);
            } catch (err: any) {
                console.error('❌ Error cargando usuario:', err);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
            } finally {
                setIsLoading(false);
            }
        };

        loadUser();
    }, []); // Sin dependencias para ejecutar solo una vez

    const login = async (email: string, password: string) => {
        try {
            setIsLoading(true);
            setError(null);

            // Llamada real a la API
            const response = await authAPI.signIn({ email, password });

            // Obtener datos reales del usuario desde el backend
            const profile = await authAPI.getProfile(response.access_token);

            // Validación robusta de roles como en Apporiginal.tsx
            let userRole: UserRole = 'client';
            
            // Verificar si tiene rol de admin en el backend (solución para mayúsculas/minúsculas)
            if (profile.roles && Array.isArray(profile.roles)) {
                const rolesLower = profile.roles.map((role: string) => role.toLowerCase());
                console.log('🎭 Roles en minúsculas:', rolesLower);
                
                if (rolesLower.includes('admin') || rolesLower.includes('administrador')) {
                    userRole = 'admin';
                    console.log('Usuario es ADMIN (verificado en backend)');
                } else if (rolesLower.includes('provider') || rolesLower.includes('proveedor')) {
                    userRole = 'provider';
                    console.log('🏢 Usuario es PROVIDER (verificado en backend)');
                } else {
                    console.log('👤 Usuario es CLIENT (verificado en backend)');
                }
            } else {
                console.log('⚠️ No se encontraron roles en el perfil:', profile);
            }

            // Mapear el perfil a la estructura User
            const userData: User = {
                id: profile.id || 1,
                name: profile.nombre_persona || profile.nombre || profile.first_name || profile.name || profile.email?.split('@')[0] || 'Usuario',
                email: profile.email || profile.correo,
                role: userRole,
                companyName: profile.nombre_empresa || profile.razon_social || profile.company_name || '',
                createdAt: profile.created_at || new Date().toISOString(),
                updatedAt: profile.updated_at || new Date().toISOString(),
                providerStatus: profile.provider_status || 'none',
                providerApplication: profile.provider_application || { status: 'none', documents: {} },
                foto_perfil: profile.foto_perfil || null
            };

            localStorage.setItem('access_token', response.access_token);
            setUser(userData);
            setProviderStatus(userData.providerStatus);
            setProviderApplication(userData.providerApplication);

            // Login exitoso sin refresco de pantalla
            console.log('✅ Login exitoso, datos actualizados sin refresco de pantalla');

        } catch (err: any) {
            // Manejar específicamente el error de cuenta inactiva
            const errorMessage = err.detail || err.message || 'Error al iniciar sesión';
            
            if (errorMessage.includes('inactiva') || errorMessage.includes('inactive') || 
                errorMessage.includes('desactivada') || errorMessage.includes('desactivado')) {
                setError('Tu cuenta está inactiva. Por favor, contacta al administrador en b2bseva.notificaciones@gmail.com para más detalles.');
            } else {
                setError(errorMessage);
            }
            throw err;
        } finally {
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
            localStorage.removeItem('access_token');
            setUser(null);
            setProviderStatus('none');
            setProviderApplication({ status: 'none', documents: {} });
        } catch (err) {
            console.error('Error al cerrar sesión:', err);
        }
    };

    const reloadUserProfile = async () => {
        console.log('🔄 Recargando perfil del usuario...');
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                console.log('❌ No hay token para recargar perfil');
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

            // Usar la misma lógica que en loadUser
            let userRole: UserRole = 'client';
            if (profile.roles && Array.isArray(profile.roles)) {
                const rolesLower = profile.roles.map((role: string) => role.toLowerCase());
                if (rolesLower.includes('admin') || rolesLower.includes('administrador')) {
                    userRole = 'admin';
                } else if (rolesLower.includes('provider') || rolesLower.includes('proveedor')) {
                    userRole = 'provider';
                }
            }

            // Obtener el estado actual de la solicitud de verificación
            let providerStatus: 'none' | 'pending' | 'approved' | 'rejected' = 'none';
            let providerApplication: ProviderApplicationStatus = { status: 'none', documents: {} };
            
            try {
                const verificationStatus = await authAPI.getVerificacionEstado(accessToken);
                console.log('📋 Estado de verificación:', verificationStatus);
                
                if (verificationStatus.estado) {
                    const estado = verificationStatus.estado as 'none' | 'pending' | 'approved' | 'rejected';
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
                console.log('⚠️ No se pudo obtener estado de verificación:', verificationError);
                // Usar valores por defecto si no se puede obtener el estado
            }

            const updatedUser: User = {
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

    const updateProviderStatus = (status: 'none' | 'pending' | 'approved' | 'rejected') => {
        setProviderStatus(status);
    };

    const updateProviderApplication = (application: ProviderApplicationStatus) => {
        setProviderApplication(application);
    };

    const submitProviderApplication = async (data: ProviderOnboardingData) => {
        if (user && user.role === 'client') {
            setIsLoading(true);
            try {
                const accessToken = localStorage.getItem('access_token');
                if (!accessToken) {
                    throw new Error('No hay token de acceso');
                }

                // Preparar datos para la API
                const documentos: File[] = [];
                const nombres_tip_documento: string[] = [];
                
                // Mapear documentos a nombres de tipo (usando nombres en lugar de IDs)
                const documentTypeMapping: Record<string, string> = {
                    'ruc': 'Constancia de RUC',
                    'patente': 'Patente Comercial',
                    'contrato': 'Cédula de Identidad del Representante',
                    'balance': 'Constitución de la Empresa',
                    'certificado': 'Certificado de Cumplimiento Tributario',
                    'certificaciones': 'Certificado de Calidad',
                    'certificados_rubro': 'Certificaciones del Rubro',
                };

                // Procesar documentos subidos
                Object.entries(data.documents).forEach(([key, doc]) => {
                    if (doc.status === 'uploaded' && doc.file) {
                        documentos.push(doc.file);
                        nombres_tip_documento.push(documentTypeMapping[key] || doc.name);
                    }
                });

                const perfil_in = {
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

                // Enviar a la API
                await providersAPI.submitProviderApplication({
                    perfil_in: JSON.stringify(perfil_in),
                    documentos,
                    nombres_tip_documento,
                    comentario_solicitud: ''
                }, accessToken);
                
                const newApplication: ProviderApplicationStatus = {
                    status: 'pending',
                    submittedAt: new Date().toISOString(),
                    documents: {}
                };
                
                setProviderApplication(newApplication);
                setProviderStatus('pending');
                
                // Persistir en localStorage
                if (user.email) {
                    localStorage.setItem(`providerStatus_${user.email}`, 'pending');
                    localStorage.setItem(`providerApplication_${user.email}`, JSON.stringify(newApplication));
                }
                
            } catch (error) {
                console.error('Error enviando solicitud:', error);
                throw error;
            } finally {
                setIsLoading(false);
            }
        }
    };

    const resubmitProviderApplication = async (data: ProviderOnboardingData) => {
        if (user && user.role === 'client') {
            setIsLoading(true);
            try {
                const accessToken = localStorage.getItem('access_token');
                if (!accessToken) {
                    throw new Error('No hay token de acceso');
                }

                // Preparar datos para la API
                const documentos: File[] = [];
                const nombres_tip_documento: string[] = [];
                
                // Mapear documentos a nombres de tipo (usando nombres en lugar de IDs)
                const documentTypeMapping: Record<string, string> = {
                    'ruc': 'Constancia de RUC',
                    'patente': 'Patente Comercial',
                    'contrato': 'Cédula de Identidad del Representante',
                    'balance': 'Constitución de la Empresa',
                    'certificado': 'Certificado de Cumplimiento Tributario',
                    'certificaciones': 'Certificado de Calidad',
                    'certificados_rubro': 'Certificaciones del Rubro',
                };

                // Procesar documentos subidos (nuevos y actualizados)
                Object.entries(data.documents).forEach(([key, doc]) => {
                    if (doc.status === 'uploaded' && doc.file) {
                        // Documento nuevo o actualizado
                        documentos.push(doc.file);
                        nombres_tip_documento.push(documentTypeMapping[key] || doc.name);
                        console.log(`📄 Enviando documento ${key}: ${doc.file.name}`);
                    } else if (doc.status === 'uploaded' && !doc.file) {
                        // Documento existente que puede ser actualizado pero no se ha subido uno nuevo
                        console.log(`⚠️ Documento ${key} marcado como actualizable pero no se ha subido uno nuevo`);
                    }
                });

                // Si no hay documentos nuevos para enviar, enviar al menos un documento vacío para evitar error 422
                if (documentos.length === 0) {
                    console.log('⚠️ No hay documentos nuevos para enviar, creando documento vacío');
                    // Crear un archivo vacío temporal
                    const emptyFile = new File([''], 'empty.txt', { type: 'text/plain' });
                    documentos.push(emptyFile);
                    nombres_tip_documento.push('Constancia de RUC'); // Tipo por defecto
                }

                const perfil_in = {
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

                // Enviar a la API
                await providersAPI.submitProviderApplication({
                    perfil_in: JSON.stringify(perfil_in),
                    documentos,
                    nombres_tip_documento,
                    comentario_solicitud: ''
                }, accessToken);
                
                const updatedApplication: ProviderApplicationStatus = {
                    status: 'pending',
                    submittedAt: new Date().toISOString(),
                    documents: {}
                };
                
                setProviderApplication(updatedApplication);
                setProviderStatus('pending');
                
                // Persistir en localStorage
                if (user.email) {
                    localStorage.setItem(`providerStatus_${user.email}`, 'pending');
                    localStorage.setItem(`providerApplication_${user.email}`, JSON.stringify(updatedApplication));
                }
                
            } catch (error) {
                console.error('Error reenviando solicitud:', error);
                throw error;
            } finally {
                setIsLoading(false);
            }
        }
    };

    const value: AuthContextType = {
        user,
        isAuthenticated: !!user,
        providerStatus,
        providerApplication,
        login,
        register,
        logout,
        reloadUserProfile,
        submitProviderApplication,
        resubmitProviderApplication,
        updateProviderStatus,
        updateProviderApplication,
        isLoading,
        error
    };

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

export { AuthContext };
