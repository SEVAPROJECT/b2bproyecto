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

                // Carga ultra optimizada: todas las APIs en paralelo sin timeouts
                console.log('🚀 Carga ultra rápida del dashboard...');

                // Ejecutar todas las llamadas en paralelo sin timeouts para máxima velocidad
                const apiCalls = [
                    categoriesAPI.getCategories(user.accessToken, true).catch(() => []),
                    servicesAPI.getServicesWithProviders(user.accessToken).catch(() =>
                        servicesAPI.getServices(user.accessToken).catch(() => [])
                    ),
                    adminAPI.getAllSolicitudesVerificacion(user.accessToken).catch(() => []),
                    fetch(buildApiUrl('/admin/users'), {
                        headers: { 'Authorization': `Bearer ${user.accessToken}` }
                    }).then(r => r.ok ? r.json() : { usuarios: 0 }).catch(() => ({ usuarios: 0 }))
                ];

                const results = await Promise.allSettled(apiCalls);

                // Procesamiento ultra rápido de resultados
                const [categoriesResult, servicesResult, verificationResult, usersResult] = results;

                const totalCategories = categoriesResult.status === 'fulfilled' ? (categoriesResult.value?.length || 0) : 0;
                const totalServices = servicesResult.status === 'fulfilled' ? (servicesResult.value?.length || 0) : 0;
                const verificationRequests = verificationResult.status === 'fulfilled' ? verificationResult.value : [];
                const totalUsers = usersResult.status === 'fulfilled' ? (usersResult.value?.usuarios?.length || usersResult.value?.usuarios || 0) : 0;

                console.log('✅ Dashboard cargado:', { totalCategories, totalServices, totalUsers });

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
                // Error silencioso, usar datos por defecto
                setStats({
                    totalUsers: 0,
                    totalCategories: 0,
                    totalServices: 0,
                    verificationRate: 0
                });
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
