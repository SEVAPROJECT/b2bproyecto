import React, { ReactNode, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui';
import { HomeIcon, BuildingStorefrontIcon, UserCircleIcon, ArrowRightOnRectangleIcon, XMarkIcon } from '../icons';

// Icono de menú hamburguesa
const Bars3Icon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
);

interface MainLayoutProps {
    children: ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const handleLogout = async () => {
        await logout();
        navigate('/');
        setIsMobileMenuOpen(false);
    };

    const closeMobileMenu = () => {
        setIsMobileMenuOpen(false);
    };

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header */}
            <header className="bg-white/80 backdrop-blur-lg sticky top-0 z-40 w-full border-b border-slate-200/80">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <Link to="/" className="text-lg sm:text-xl md:text-2xl font-bold text-primary-600">SEVA EMPRESAS</Link>

                        {/* Desktop Navigation */}
                        <nav className="hidden md:flex items-center space-x-8">
                            <Link to="/" className="text-slate-600 hover:text-primary-600 transition-colors font-medium">Inicio</Link>
                            <Link to="/marketplace" className="text-slate-600 hover:text-primary-600 transition-colors font-medium">Marketplace</Link>
                        </nav>

                        {/* Desktop User Menu */}
                        <div className="hidden md:flex items-center space-x-2">
                            {user ? (
                                <>
                                    <div className="flex items-center space-x-2">
                                        <span className="text-sm text-slate-600">
                                            {user.role === 'admin' ? '⚙️ Admin' : 
                                             user.role === 'provider' ? '🏢 Proveedor' : '👤 Cliente'}
                                        </span>
                                        <Button to="/dashboard" variant="ghost">Mi Panel</Button>
                                        <Button onClick={handleLogout} variant="primary">Salir</Button>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <Button to="/login" variant="ghost">Iniciar sesión</Button>
                                    <Button to="/register" variant="primary">Crear cuenta</Button>
                                </>
                            )}
                        </div>

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                            className="md:hidden p-2 rounded-md text-slate-600 hover:text-primary-600 hover:bg-slate-100 transition-colors"
                            aria-label="Abrir menú"
                        >
                            {isMobileMenuOpen ? (
                                <XMarkIcon className="h-6 w-6" />
                            ) : (
                                <Bars3Icon className="h-6 w-6" />
                            )}
                        </button>
                    </div>

                    {/* Mobile Menu */}
                    {isMobileMenuOpen && (
                        <div className="md:hidden border-t border-slate-200/80 bg-white/95 backdrop-blur-lg">
                            <div className="px-4 py-4 space-y-4">
                                {/* Mobile Navigation */}
                                <nav className="space-y-2">
                                    <Link 
                                        to="/" 
                                        className="block px-3 py-2 text-slate-600 hover:text-primary-600 hover:bg-slate-50 rounded-md transition-colors font-medium"
                                        onClick={closeMobileMenu}
                                    >
                                        Inicio
                                    </Link>
                                    <Link 
                                        to="/marketplace" 
                                        className="block px-3 py-2 text-slate-600 hover:text-primary-600 hover:bg-slate-50 rounded-md transition-colors font-medium"
                                        onClick={closeMobileMenu}
                                    >
                                        Marketplace
                                    </Link>
                                </nav>

                                {/* Mobile User Menu */}
                                <div className="pt-4 border-t border-slate-200/80">
                                    {user ? (
                                        <div className="space-y-3">
                                            <div className="flex items-center space-x-2 px-3 py-2">
                                                <span className="text-sm text-slate-600">
                                                    {user.role === 'admin' ? '⚙️ Admin' : 
                                                     user.role === 'provider' ? '🏢 Proveedor' : '👤 Cliente'}
                                                </span>
                                            </div>
                                            <Link 
                                                to="/dashboard" 
                                                className="block w-full px-3 py-2 text-center text-slate-600 hover:text-primary-600 hover:bg-slate-50 rounded-md transition-colors font-medium border border-slate-300"
                                                onClick={closeMobileMenu}
                                            >
                                                Mi Panel
                                            </Link>
                                            <button 
                                                onClick={handleLogout}
                                                className="block w-full px-3 py-2 text-center text-white bg-primary-600 hover:bg-primary-700 rounded-md transition-colors font-medium"
                                            >
                                                Salir
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            <Link 
                                                to="/login" 
                                                className="block w-full px-3 py-2 text-center text-slate-600 hover:text-primary-600 hover:bg-slate-50 rounded-md transition-colors font-medium border border-slate-300"
                                                onClick={closeMobileMenu}
                                            >
                                                Iniciar sesión
                                            </Link>
                                            <Link 
                                                to="/register" 
                                                className="block w-full px-3 py-2 text-center text-white bg-primary-600 hover:bg-primary-700 rounded-md transition-colors font-medium"
                                                onClick={closeMobileMenu}
                                            >
                                                Crear cuenta
                                            </Link>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <main>
                {children}
            </main>

            {/* Footer */}
            <footer className="bg-slate-100 border-t border-slate-200">
                <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8 text-slate-500">
                     <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                        <div>
                            <h3 className="text-xl font-bold text-primary-600">SEVA EMPRESAS</h3>
                            <p className="mt-2 text-sm">Conectando empresas, potenciando el crecimiento en Paraguay.</p>
                        </div>
                        <div>
                            <h4 className="font-semibold text-slate-700">Explorar</h4>
                            <ul className="mt-2 space-y-1 text-sm">
                                <li><Link to="/marketplace" className="hover:text-primary-600">Marketplace</Link></li>
                                <li><Link to="/" className="hover:text-primary-600">Categorías</Link></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold text-slate-700">Nosotros</h4>
                            <ul className="mt-2 space-y-1 text-sm">
                                <li><Link to="/" className="hover:text-primary-600">Sobre Seva</Link></li>
                                <li><Link to="/" className="hover:text-primary-600">Términos y Condiciones</Link></li>
                                <li><Link to="/" className="hover:text-primary-600">Política de Privacidad</Link></li>
                            </ul>
                        </div>
                         <div>
                            <h4 className="font-semibold text-slate-700">Contacto</h4>
                            <ul className="mt-2 space-y-1 text-sm">
                                <li><a href="mailto:b2bseva.notificaciones@gmail.com" className="hover:text-primary-600">b2bseva.notificaciones@gmail.com</a></li>
                                <li>Asunción, Paraguay</li>
                            </ul>
                        </div>
                    </div>
                    <div className="mt-8 pt-6 border-t border-slate-200 text-center text-sm">
                        &copy; {new Date().getFullYear()} Seva Empresas. Todos los derechos reservados.
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default MainLayout;
