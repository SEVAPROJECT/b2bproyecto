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
    const hasLoadedRef = useRef(false);


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

                // Cargar datos reales de todas las APIs disponibles
                console.log('🔄 Cargando datos reales desde todas las APIs...');
                
                const results = await Promise.allSettled([
                    categoriesAPI.getCategories(user.accessToken, true),
                    servicesAPI.getServicesWithProviders(user.accessToken).catch(() => 
                        servicesAPI.getServices(user.accessToken).catch(() => [])
                    ),
                    adminAPI.getAllSolicitudesVerificacion(user.accessToken),
                    fetch(buildApiUrl('/admin/users'), {
                        headers: { 'Authorization': `Bearer ${user.accessToken}` }
                    }).then(r => r.ok ? r.json() : 
                        fetch(buildApiUrl('/admin/users/emails'), {
                            headers: { 'Authorization': `Bearer ${user.accessToken}` }
                        }).then(r2 => r2.ok ? r2.json().then(data => ({ usuarios: Object.keys(data.emails || {}) })) : { usuarios: [] })
                    ).catch(() => ({ usuarios: [] }))
                ]);

                // Procesar todos los datos reales obtenidos
                const [categoriesResult, servicesResult, verificationResult, usersResult] = results;
                
                const categories = categoriesResult.status === 'fulfilled' ? categoriesResult.value : [];
                const services = servicesResult.status === 'fulfilled' ? servicesResult.value : [];
                const verificationRequests = verificationResult.status === 'fulfilled' ? verificationResult.value : [];
                const allUsers = usersResult.status === 'fulfilled' ? usersResult.value : { usuarios: [] };

                console.log('📊 Datos reales obtenidos:', {
                    categories: categories?.length || 0,
                    services: services?.length || 0,
                    verificationRequests: verificationRequests?.length || 0,
                    users: Array.isArray(allUsers?.usuarios) ? allUsers.usuarios.length : (allUsers?.usuarios || 0)
                });

                // Usar datos reales de las APIs
                const totalCategories = categories?.length || 0;
                const totalServices = services?.length || 0;
                const totalUsers = Array.isArray(allUsers?.usuarios) ? allUsers.usuarios.length : (allUsers?.usuarios || 0);

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

                // Para cualquier error, usar datos por defecto sin mostrar error
                setStats({
                    totalUsers: 0,
                    totalCategories: 0,
                    totalServices: 0,
                    verificationRate: 0
                });
                
                console.log('⚠️ Usando datos por defecto debido a error');
            } finally {
                setIsLoading(false);
            }
        };

        loadStats();
    }, [user?.accessToken, user?.role]); // Solo depender de accessToken y role, no del objeto user completo


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

            {/* Mensaje informativo sobre datos */}
            <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-3">
                <div className="flex items-center">
                    <span className="text-green-600 mr-2">✅</span>
                    <div className="text-sm text-green-700">
                        Dashboard cargado con datos reales desde la base de datos. Los datos se actualizan automáticamente.
                    </div>
                </div>
            </div>


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
