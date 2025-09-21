import React, { useState, useEffect, useRef } from 'react';
import { DashboardStatCard } from '../../components/ui';
import OptimizedLoading from '../../components/ui/OptimizedLoading';
import { UsersIcon, FolderIcon, BuildingStorefrontIcon, CheckCircleIcon } from '../../components/icons';
import { useAuth } from '../../contexts/AuthContext';
import { categoriesAPI, servicesAPI, adminAPI } from '../../services/api';
import { API_CONFIG, buildApiUrl } from '../../config/api';

const AdminDashboardPage: React.FC = () => {
    const { user } = useAuth();
    const [stats, setStats] = useState({
        totalUsers: 0,
        totalCategories: 0,
        totalServices: 0,
        verificationRate: 0
    });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const hasLoadedRef = useRef(false);
    const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);


    useEffect(() => {
        // Solo ejecutar si el usuario es admin y no hemos cargado aún
        if (!user || !user.accessToken || user.role !== 'admin' || hasLoadedRef.current) {
            return;
        }

        const loadStats = async () => {
            hasLoadedRef.current = true; // Marcar como cargado

            try {
                console.log('🚀 Cargando estadísticas del dashboard por primera vez...');
                setIsLoading(true);
                setError(null);

                // Optimización: Usar Promise.allSettled para mejor manejo de errores
                // y reducir timeout a 8 segundos para mejor UX
                const timeoutPromise = new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Timeout')), 8000)
                );

                const apiBaseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');

                const statsPromise = Promise.allSettled([
                    categoriesAPI.getCategories(user.accessToken, true),
                    servicesAPI.getServices(user.accessToken),
                    adminAPI.getAllSolicitudesVerificacion(user.accessToken),
                    // Usar el mismo endpoint que AdminUsersPage
                    //fetch(buildApiUrl('/admin/users'), {
                        //headers: { 'Authorization': `Bearer ${user.//accessToken}` }
                    //}).then(r => r.ok ? r.json() : { usuarios: [] })
                    fetch(`${apiBaseUrl}/api/v1/admin/users'`, {
                        headers: { 'Authorization': `Bearer ${user.accessToken}` }
                    }).then(r => r.ok ? r.json() : { usuarios: [] })
                ]);

                const results = await Promise.race([
                    statsPromise,
                    timeoutPromise.then(() => { throw new Error('Timeout'); })
                ]);

                // Procesar resultados con fallbacks
                const [categoriesResult, servicesResult, verificationResult, usersResult] = results;
                
                const categories = categoriesResult.status === 'fulfilled' ? categoriesResult.value : [];
                const services = servicesResult.status === 'fulfilled' ? servicesResult.value : [];
                const verificationRequests = verificationResult.status === 'fulfilled' ? verificationResult.value : [];
                const allUsers = usersResult.status === 'fulfilled' ? usersResult.value : { usuarios: [] };

                // Procesar datos
                const totalCategories = categories?.length || 0;
                const totalServices = services?.length || 0;
                
                // Obtener usuarios del mismo endpoint que AdminUsersPage
                const totalUsers = allUsers?.usuarios?.length || 0;

                // Debug: ver qué valores llegan para verificación
                console.log('🔍 Solicitudes de verificación completas:', verificationRequests);
                console.log('🔍 Estados encontrados:', verificationRequests?.map(req => ({
                    id: req.id_verificacion,
                    estado: req.estado_aprobacion,
                    email: req.email_contacto,
                    todos_los_campos: Object.keys(req)
                })));

                // Filtrar las aprobadas (según datos de la tabla: 7 aprobadas)
                const approvedRequests = verificationRequests?.filter((req: any) => {
                    const estado = req.estado_aprobacion || req.estado || req.status || req.state;
                    console.log(`🔍 Revisando solicitud ${req.id_verificacion}: estado="${estado}"`);
                    return estado === 'aprobada' || estado === 'approved' || estado === 'aceptada';
                }).length || 0;

                const totalRequests = verificationRequests?.length || 0;
                // Calcular tasa de verificación: aprobadas / total * 100
                const verificationRate = totalRequests > 0 ? Math.round((approvedRequests / totalRequests) * 100) : 0;

                console.log(`📊 Verificación - Aprobadas: ${approvedRequests}, Total: ${totalRequests}, Tasa: ${verificationRate}%`);
                console.log(`👥 Usuarios reales obtenidos: ${totalUsers}`);

                setStats({
                    totalUsers,
                    totalCategories,
                    totalServices,
                    verificationRate
                });

                console.log('✅ Estadísticas cargadas:', { totalUsers, totalCategories, totalServices, verificationRate });
                console.log('🔍 DIAGNÓSTICO COMPLETO:');
                console.log('- Total solicitudes:', totalRequests);
                console.log('- Solicitudes aprobadas:', approvedRequests);
                console.log('- Tasa calculada:', verificationRate + '%');
                console.log('- Array de solicitudes:', verificationRequests);

            } catch (error) {
                console.error('❌ Error cargando estadísticas:', error);

                // Fallback: usar datos mock si las APIs fallan
                console.log('⚠️ Usando datos de respaldo...');
                setStats({
                    totalUsers: 0,
                    totalCategories: 0,
                    totalServices: 0,
                    verificationRate: 0
                });
                
                // Solo mostrar error si es un error real de conexión, no un timeout
                if (error instanceof Error && error.message === 'Timeout') {
                    setError('La conexión está tardando más de lo esperado. Intenta recargar la página.');
                } else {
                    setError('Error al cargar los datos. Verifica tu conexión.');
                }
                
                // Limpiar el error después de 10 segundos para permitir reintentos
                if (retryTimeoutRef.current) {
                    clearTimeout(retryTimeoutRef.current);
                }
                retryTimeoutRef.current = setTimeout(() => {
                    setError(null);
                    hasLoadedRef.current = false; // Permitir reintento
                }, 10000);
            } finally {
                setIsLoading(false);
            }
        };

        loadStats();
    }, [user?.accessToken, user?.role]); // Solo depender de accessToken y role, no del objeto user completo

    // Cleanup timeout al desmontar el componente
    useEffect(() => {
        return () => {
            if (retryTimeoutRef.current) {
                clearTimeout(retryTimeoutRef.current);
            }
        };
    }, []);

    // Mostrar loading optimizado mientras se carga
    if (!user || isLoading) {
        return (
            <OptimizedLoading 
                message={!user ? 'Cargando información del usuario...' : 'Cargando dashboard...'}
                showProgress={false}
            />
        );
    }

    // Verificar permisos
    if (user.role !== 'admin') {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-red-600 text-2xl">🚫</span>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">Acceso Denegado</h1>
                    <p className="text-gray-600">Solo los administradores pueden acceder a esta página.</p>
                </div>
            </div>
        );
    }

    return (
        <div>
            <div className="bg-white shadow rounded-lg p-6 mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900"> Bienvenido/a {user?.name || 'Administrador'}</h1>
                    <p className="mt-1 text-sm text-gray-500">Gestiona la plataforma y monitorea el rendimiento de SEVA Empresas.</p>
                </div>
            </div>

            {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
                    <div className="flex items-center justify-between">
                        <div className="text-sm text-red-700">{error}</div>
                        <button
                            onClick={() => {
                                setError(null);
                                hasLoadedRef.current = false;
                                setIsLoading(true);
                                // Trigger reload by updating a dependency
                                window.location.reload();
                            }}
                            className="ml-4 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
                        >
                            Reintentar
                        </button>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-8">
                <DashboardStatCard
                    title="Usuarios Totales"
                    value={isLoading ? "..." : stats.totalUsers.toString()}
                    icon={<UsersIcon className="w-6 h-6"/>}
                    change=""
                />
                <DashboardStatCard
                    title="Categorías Totales"
                    value={isLoading ? "..." : stats.totalCategories.toString()}
                    icon={<FolderIcon className="w-6 h-6"/>}
                    change=""
                />
                <DashboardStatCard
                    title="Servicios Totales"
                    value={isLoading ? "..." : stats.totalServices.toString()}
                    icon={<BuildingStorefrontIcon className="w-6 h-6"/>}
                    change=""
                />
                <DashboardStatCard
                    title="Tasa de Verificación"
                    value={isLoading ? "..." : `${stats.verificationRate}%`}
                    icon={<CheckCircleIcon className="w-6 h-6"/>}
                    change=""
                />
            </div>
        </div>
    );
};

export default AdminDashboardPage;
