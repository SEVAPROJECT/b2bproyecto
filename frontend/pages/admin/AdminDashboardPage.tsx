import React, { useState, useEffect, useRef } from 'react';
import { DashboardStatCard } from '../../components/ui';
import OptimizedLoading from '../../components/ui/OptimizedLoading';
import { UsersIcon, FolderIcon, BuildingStorefrontIcon, CheckCircleIcon } from '../../components/icons';
import { useAuth } from '../../contexts/AuthContext';
import { adminAPI } from '../../services/api';

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
        if (!user?.accessToken || user.role !== 'admin' || hasLoadedRef.current) {
            return;
        }

        const loadStats = async () => {
            hasLoadedRef.current = true; // Marcar como cargado

            try {
                console.log('🚀 Cargando estadísticas del dashboard por primera vez...');
                setIsLoading(true);

                // Carga ultra optimizada: todas las APIs en paralelo sin timeouts
                console.log('🚀 Carga ultra rápida del dashboard...');

                // Llamada optimizada usando adminAPI
                console.log('🔍 Obteniendo estadísticas del dashboard usando adminAPI...');
                const startTime = performance.now();
                
                const dashboardStats = await adminAPI.getDashboardStats(user.accessToken);

                const endTime = performance.now();
                const fetchTime = endTime - startTime;
                console.log(`⏱️ Tiempo de fetch: ${fetchTime.toFixed(2)}ms`);
                console.log('🔍 Datos recibidos del servidor:', dashboardStats);

                // Extraer datos del endpoint consolidado
                const totalUsers = dashboardStats.total_users || 0;
                const totalCategories = dashboardStats.total_categories || 0;
                const totalServices = dashboardStats.total_services || 0;
                const verificationRate = dashboardStats.verification_rate || 0;

                console.log('✅ Dashboard cargado:', { totalCategories, totalServices, totalUsers, verificationRate });

                setStats({
                    totalUsers,
                    totalCategories,
                    totalServices,
                    verificationRate
                });

                console.log('✅ Estadísticas cargadas:', { totalUsers, totalCategories, totalServices, verificationRate });

            } catch (error) {
                console.error('❌ Error obteniendo estadísticas del dashboard:', error);
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
                message={user ? 'Cargando dashboard...' : 'Cargando información del usuario...'}
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
