import React, { ReactNode, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
    HomeIcon,
    BuildingStorefrontIcon,
    CalendarDaysIcon,
    UserCircleIcon,
    ArrowRightOnRectangleIcon,
    ChartBarIcon,
    UsersIcon,
    BriefcaseIcon,
    FolderIcon,
    ClipboardDocumentListIcon,
    ClipboardDocumentIcon,
    MagnifyingGlassIcon,
    CheckCircleIcon,
    PlusCircleIcon,
    SparklesIcon,
    WrenchScrewdriverIcon,
    ClockIcon,
    ExclamationCircleIcon
} from '../icons';

interface DashboardLayoutProps {
    children: ReactNode;
}

// Icono de menú hamburguesa
const Bars3Icon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
);

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
    const { user, logout, providerStatus, providerApplication } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    const toggleSidebar = () => {
        setIsSidebarOpen(!isSidebarOpen);
    };

    const closeSidebar = () => {
        setIsSidebarOpen(false);
    };

    const isActive = (path: string) => {
        return location.pathname === path;
    };

    const navigation = user?.role === 'admin' ? [
        { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
        { name: 'Marketplace', href: '/dashboard/marketplace', icon: MagnifyingGlassIcon },
        { name: 'Solicitudes Pendientes', href: '/dashboard/verifications', icon: CheckCircleIcon },
        { name: 'Solicitudes de Servicios', href: '/dashboard/service-requests', icon: PlusCircleIcon },
        { name: 'Solicitudes de Categorías', href: '/dashboard/category-requests', icon: FolderIcon },
        { name: 'Categorías', href: '/dashboard/categories', icon: BuildingStorefrontIcon },
        { name: 'Usuarios', href: '/dashboard/users', icon: UsersIcon },
        { name: 'Reportes', href: '/dashboard/reports', icon: ChartBarIcon },
    ] : user?.role === 'provider' ? [
        { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
        { name: 'Marketplace', href: '/dashboard/marketplace', icon: MagnifyingGlassIcon },
        { name: 'Explorar Categorías', href: '/dashboard/explore-categories', icon: BuildingStorefrontIcon },
        { name: 'Mis Solicitudes', href: '/dashboard/my-requests', icon: PlusCircleIcon },
        { name: 'Mis Servicios', href: '/dashboard/my-services', icon: BriefcaseIcon },
        { name: 'Mis Reservas', href: '/dashboard/reservations', icon: CalendarDaysIcon },
    ] : [
        { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
        { name: 'Marketplace', href: '/dashboard/marketplace', icon: MagnifyingGlassIcon },
        { name: 'Mis Reservas', href: '/dashboard/reservations', icon: CalendarDaysIcon },
    ];

    // Agregar "Mi Perfil" al final para todos los roles
    const clientNavigation = [...navigation];
    clientNavigation.push({ name: 'Mi Perfil', href: '/dashboard/profile', icon: UserCircleIcon });

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Mobile Header */}
            <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white shadow-lg z-50 flex items-center justify-between px-4">
                <button
                    onClick={toggleSidebar}
                    className="p-2 rounded-md text-slate-600 hover:text-primary-600 hover:bg-slate-100 transition-colors"
                    aria-label="Abrir menú"
                >
                    <Bars3Icon className="h-6 w-6" />
                </button>
                <Link to="/" className="text-lg font-bold text-primary-600">SEVA EMPRESAS</Link>
                <div className="w-10"></div> {/* Spacer para centrar el logo */}
            </div>

            {/* Sidebar */}
            <div className={`fixed inset-y-0 left-0 w-64 bg-white shadow-lg z-40 transform transition-transform duration-300 ease-in-out ${
                isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
            } lg:translate-x-0`}>
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="h-16 flex items-center justify-between px-6 border-b border-slate-200">
                        <Link to="/" className="text-lg sm:text-xl font-bold text-primary-600">SEVA EMPRESAS</Link>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-6 space-y-2">
                        {clientNavigation.map((item) => {
                            const Icon = item.icon;
                            const isDisabled = item.href === '#';
                            return (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                                        isDisabled
                                            ? 'text-slate-400 cursor-not-allowed bg-blue-50'
                                            : isActive(item.href)
                                            ? 'bg-primary-100 text-primary-700'
                                            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                                    }`}
                                    onClick={isDisabled ? (e) => e.preventDefault() : closeSidebar}
                                >
                                    <Icon className="w-5 h-5" />
                                    <span className="font-medium">{item.name}</span>
                                </Link>
                            );
                        })}
                    </nav>

                    {/* Botón Convertirme en Proveedor para clientes */}
                    {user?.role === 'client' && (
                        <div className="px-3 sm:px-4 pb-4">
                            {providerStatus === 'none' && (
                                <Link
                                    to="/dashboard/become-provider"
                                    className="flex items-center space-x-2 sm:space-x-3 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg transition-colors bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700"
                                    onClick={closeSidebar}
                                >
                                    <WrenchScrewdriverIcon className="w-4 h-4 sm:w-5 sm:h-5" />
                                    <span className="text-xs sm:text-sm font-medium">Convertirme en Proveedor</span>
                                </Link>
                            )}
                            {providerStatus === 'pending' && (
                                <div className="flex items-center space-x-2 sm:space-x-3 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg bg-blue-50 text-blue-700 border border-blue-200">
                                    <ClockIcon className="w-4 h-4 sm:w-5 sm:h-5" />
                                    <span className="text-xs sm:text-sm font-medium">Solicitud en Revisión</span>
                                </div>
                            )}
                            {providerStatus === 'rejected' && (
                                <Link
                                    to="/dashboard/become-provider"
                                    className="flex items-center space-x-2 sm:space-x-3 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg transition-colors bg-red-50 text-red-700 hover:bg-red-100 border border-red-200"
                                    onClick={closeSidebar}
                                >
                                    <ExclamationCircleIcon className="w-4 h-4 sm:w-5 sm:h-5" />
                                    <span className="text-xs sm:text-sm font-medium">Corregir Solicitud</span>
                                </Link>
                            )}
                        </div>
                    )}

                    {/* User Info */}
                    <div className="p-3 sm:p-4 border-t border-slate-200">
                        <div className="flex items-center space-x-2 sm:space-x-3 mb-3">
                            <div className="w-7 h-7 sm:w-8 sm:h-8 bg-primary-100 rounded-full flex items-center justify-center overflow-hidden flex-shrink-0">
                                {user?.foto_perfil ? (
                                    <img
                                        src={user.foto_perfil.startsWith('/') 
                                            ? `http://localhost:8000${user.foto_perfil}` 
                                            : user.foto_perfil}
                                        alt="Foto de perfil"
                                        className="w-full h-full object-cover"
                                        onError={(e) => {
                                            // Si hay error cargando la imagen, mostrar el ícono por defecto
                                            const target = e.target as HTMLImageElement;
                                            target.style.display = 'none';
                                            const parent = target.parentElement;
                                            if (parent) {
                                                const fallback = document.createElement('div');
                                                fallback.className = 'w-full h-full flex items-center justify-center';
                                                fallback.innerHTML = '<svg class="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>';
                                                parent.appendChild(fallback);
                                            }
                                        }}
                                    />
                                ) : (
                                    <UserCircleIcon className="w-5 h-5 text-primary-600" />
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-xs sm:text-sm font-medium text-slate-900 truncate">
                                    {user?.name}
                                </p>
                                <p className="text-xs text-slate-500 truncate">
                                    {user?.email}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                            <ArrowRightOnRectangleIcon className="w-3 h-3 sm:w-4 sm:h-4" />
                            <span>Cerrar Sesión</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="lg:pl-64 pt-16 lg:pt-0">
                <div className="min-h-screen">
                    {children}
                </div>
            </div>

            {/* Overlay para móviles */}
            {isSidebarOpen && (
                <div 
                    className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
                    onClick={closeSidebar}
                />
            )}
        </div>
    );
};

export default DashboardLayout;
