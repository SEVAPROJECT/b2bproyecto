import React, { useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import AdminDashboardPage from '../admin/AdminDashboardPage';
import ProviderApplicationNotification from '../../components/ProviderApplicationNotification';

const DashboardPage: React.FC = () => {
    const { user, reloadUserProfile } = useAuth();

    // Recargar el perfil del usuario cuando se accede al dashboard
    useEffect(() => {
        if (user?.accessToken) {
            reloadUserProfile();
        }
    }, [user?.accessToken, reloadUserProfile]);

    return (
        <div>
            {/* Mostrar contenido basado en el rol del usuario */}
            {user?.role === 'admin' ? (
                <AdminDashboardPage />
            ) : (
                <div className="p-6">
                    {/* Solo mostrar notificación en el dashboard del cliente */}
                    {user?.role === 'client' && <ProviderApplicationNotification />}
                    
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-slate-900">
                            ¡Hola, {user?.name || 'Usuario'}!
                        </h1>
                        <p className="text-slate-600 mt-2">
                            Dashboard de {user?.role === 'provider' ? 'Proveedor' : 'Cliente'} - Resumen de tu actividad en la plataforma.
                        </p>
                    </div>
                    
                    <div className="bg-white p-8 rounded-xl shadow-md border border-slate-200">
                        <div className="text-center">
                            <h2 className="text-2xl font-bold text-slate-800 mb-4">
                                Bienvenido/a {user?.name || 'Usuario'}!
                            </h2>
                            <p className="text-slate-600">Gracias por usar nuestra plataforma de servicios empresariales.</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DashboardPage;
