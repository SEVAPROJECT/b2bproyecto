import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Layouts
import { MainLayout, DashboardLayout } from '../components/layouts';

// Pages
import HomePage from '../pages/HomePage';
import { LoginPage, RegisterPage } from '../pages/auth';
import { DashboardPage } from '../pages/dashboard';
import { MarketplacePage } from '../components/marketplace';

// Admin Pages
import {
    AdminUsersPage,
    AdminServicesPage,
    AdminCategoriesPage,
    AdminPendingRequestsPage,
    AdminServiceRequestsPage
} from '../components/admin';
import AdminCategoryRequestsPage from '../components/admin/AdminCategoryRequestsPage';

// Service Pages (extraídas de Apporiginal.tsx)
import ServiceDetailPage from '../pages/ServiceDetailPage';
import ResetPasswordPage from '../pages/auth/ResetPasswordPage';
import ReservationsPage from '../pages/ReservationsPage';
import ManageProfilePage from '../pages/ManageProfilePage';
import ProviderAgendaPage from '../pages/provider/ProviderAgendaPage';
import ProviderOnboardingPage from '../pages/provider/ProviderOnboardingPage';
import AdminVerificationsPage from '../components/admin/AdminVerificationsPage';

// Test Components
// import DateTestComponent from '../docs/DateTestComponent'; // Comentado: solo para pruebas locales
import AdminReportsPage from '../pages/admin/AdminReportsPage';
import AdminCategoryServicesPage from '../pages/admin/AdminCategoryServicesPage';
import ProviderExploreCategoriesPage from '../pages/provider/ProviderExploreCategoriesPage';
import ProviderMyRequestsPage from '../pages/provider/ProviderMyRequestsPage';
import ProviderMyServicesPage from '../pages/provider/ProviderMyServicesPage';
import UserReportsPage from '../pages/UserReportsPage';

// Protected Route Components
interface ProtectedRouteProps {
    children: React.ReactNode;
    adminOnly?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, adminOnly = false }) => {
    const { user, isLoading } = useAuth();

    // Mostrar loading mientras se verifica la autenticación
    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Verificando sesión...</p>
                </div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (adminOnly && user.role !== 'admin') {
        return <Navigate to="/dashboard" replace />;
    }

    return <>{children}</>;
};

interface ProviderRouteProps {
    children: React.ReactNode;
}

const ProviderRoute: React.FC<ProviderRouteProps> = ({ children }) => {
    const { user, isLoading } = useAuth();

    // Mostrar loading mientras se verifica la autenticación
    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Verificando sesión...</p>
                </div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // Si el usuario no tiene rol de provider, pero tiene accessToken, 
    // asumir que es provider para evitar redirección en errores 500
    if (user.role !== 'provider') {
        console.log('⚠️ Usuario no tiene rol de provider, pero manteniendo acceso para evitar redirección');
        // No redirigir si hay problemas de autenticación
        if (user.accessToken) {
            console.log('🔑 Usuario tiene accessToken, permitiendo acceso');
            return <>{children}</>;
        }
        return <Navigate to="/dashboard" replace />;
    }

    return <>{children}</>;
};

interface AdminRouteProps {
    children: React.ReactNode;
}

const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
    const { user, isLoading } = useAuth();

    // Mostrar loading mientras se verifica la autenticación
    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Verificando sesión...</p>
                </div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (user.role !== 'admin') {
        return <Navigate to="/dashboard" replace />;
    }

    return <>{children}</>;
};

const AppRoutes: React.FC = () => {
    const { user, isLoading } = useAuth();

    const renderHomeContent = () => {
        if (isLoading) {
            return (
                <div className="flex items-center justify-center min-h-screen">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p className="text-gray-600">Verificando sesión...</p>
                    </div>
                </div>
            );
        }
        if (user) {
            return <Navigate to="/dashboard" replace />;
        }
        return <HomePage />;
    };

    return (
        <Routes>
            {/* Public Routes */}
            <Route path="/" element={
                <MainLayout>
                    {renderHomeContent()}
                </MainLayout>
            } />

            <Route path="/service/:id" element={<ServiceDetailPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            
            {/* Ruta de prueba temporal - Comentada para producción */}
            {/* <Route path="/test-dates" element={<DateTestComponent />} /> */}

            <Route path="/marketplace" element={
                <MainLayout>
                    <MarketplacePage />
                </MainLayout>
            } />

            {/* Protected Routes */}
            <Route path="/dashboard" element={
                <ProtectedRoute>
                    <DashboardLayout>
                        <Outlet />
                    </DashboardLayout>
                </ProtectedRoute>
            }>
                   <Route index element={<DashboardPage />} />
                   <Route path="marketplace" element={<MarketplacePage />} />
                   <Route path="reservations" element={<ReservationsPage />} />
                   <Route path="profile" element={<ManageProfilePage />} />
                   <Route path="my-reports" element={<UserReportsPage />} />
                   <Route path="become-provider" element={<ProviderOnboardingPage />} />
                   {/* Rutas de administrador */}
                   <Route path="verifications" element={<AdminRoute><AdminVerificationsPage /></AdminRoute>} />
                   <Route path="users" element={<AdminRoute><AdminUsersPage /></AdminRoute>} />
                   <Route path="reports" element={<AdminRoute><AdminReportsPage /></AdminRoute>} />
                   <Route path="categories" element={<AdminRoute><AdminCategoriesPage /></AdminRoute>} />
                   <Route path="categories/:categoryId/services" element={<AdminRoute><AdminCategoryServicesPage /></AdminRoute>} />
                   <Route path="service-requests" element={<AdminRoute><AdminServiceRequestsPage /></AdminRoute>} />
                   <Route path="category-requests" element={<AdminRoute><AdminCategoryRequestsPage /></AdminRoute>} />
                   <Route path="explore-categories" element={<ProviderRoute><ProviderExploreCategoriesPage /></ProviderRoute>} />
                   <Route path="my-requests" element={<ProviderRoute><ProviderMyRequestsPage /></ProviderRoute>} />
                   <Route path="my-services" element={<ProviderRoute><ProviderMyServicesPage /></ProviderRoute>} />
                   <Route path="agenda" element={<ProviderRoute><ProviderAgendaPage /></ProviderRoute>} />
                </Route>

            {/* Admin Routes */}
            <Route path="/admin/categories" element={
                <ProtectedRoute adminOnly>
                    <DashboardLayout>
                        <AdminCategoriesPage />
                    </DashboardLayout>
                </ProtectedRoute>
            } />

            <Route path="/admin/users" element={
                <ProtectedRoute adminOnly>
                    <DashboardLayout>
                        <AdminUsersPage />
                    </DashboardLayout>
                </ProtectedRoute>
            } />

            <Route path="/admin/services" element={
                <ProtectedRoute adminOnly>
                    <DashboardLayout>
                        <AdminServicesPage />
                    </DashboardLayout>
                </ProtectedRoute>
            } />

            <Route path="/admin/pending-requests" element={
                <ProtectedRoute adminOnly>
                    <DashboardLayout>
                        <AdminPendingRequestsPage />
                    </DashboardLayout>
                </ProtectedRoute>
            } />

            <Route path="/admin/service-requests" element={
                <ProtectedRoute adminOnly>
                    <DashboardLayout>
                        <AdminServiceRequestsPage />
                    </DashboardLayout>
                </ProtectedRoute>
            } />

            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
};

export default AppRoutes;
