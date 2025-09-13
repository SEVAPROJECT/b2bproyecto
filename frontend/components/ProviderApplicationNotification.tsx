import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { CheckCircleIcon, ExclamationCircleIcon, ClockIcon } from './icons';
import { useNavigate } from 'react-router-dom';
import Button from './ui/Button';

const ProviderApplicationNotification: React.FC = () => {
    const { providerStatus, providerApplication, user, reloadUserProfile } = useAuth();
    const navigate = useNavigate();
    
    // Solo mostrar para clientes con solicitudes de proveedor
    if (user?.role !== 'client' || providerStatus === 'none') return null;
    
    if (providerStatus === 'pending') {
        return (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                    <ClockIcon className="w-5 h-5 text-blue-500 mt-0.5 mr-3 flex-shrink-0" />
                    <div className="flex-1">
                        <h3 className="text-sm font-medium text-blue-800">Solicitud en revisión</h3>
                        <p className="text-sm text-blue-700 mt-1">
                            Tu solicitud para convertirte en proveedor está siendo revisada. 
                            Te notificaremos cuando se complete la revisión.
                        </p>
                        {providerApplication.submittedAt && (
                            <p className="text-xs text-blue-600 mt-2">
                                Enviada el {new Date(providerApplication.submittedAt).toLocaleDateString('es-ES')}
                            </p>
                        )}
                    </div>
                </div>
            </div>
        );
    }
    
    if (providerStatus === 'rejected') {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                    <ExclamationCircleIcon className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
                    <div className="flex-1">
                        <h3 className="text-sm font-medium text-red-800">Solicitud rechazada</h3>
                        <p className="text-sm text-red-700 mt-1">
                            Tu solicitud para convertirte en proveedor fue rechazada. 
                            Puedes corregir los problemas señalados y volver a enviar tu solicitud.
                        </p>
                        {providerApplication.rejectionReason && (
                            <div className="mt-3 p-3 bg-red-100 rounded-lg border border-red-200">
                                <p className="text-sm font-medium text-red-800 mb-1">Motivo del rechazo:</p>
                                <p className="text-sm text-red-700">{providerApplication.rejectionReason}</p>
                            </div>
                        )}
                        {providerApplication.reviewedAt && (
                            <p className="text-xs text-red-600 mt-2">
                                Revisado el {new Date(providerApplication.reviewedAt).toLocaleDateString('es-ES')}
                            </p>
                        )}
                        <div className="mt-3 flex space-x-2">
                            <Button 
                                variant="primary" 
                                size="sm" 
                                onClick={() => navigate('/dashboard/become-provider')}
                            >
                                Corregir y reenviar
                            </Button>
                            <Button 
                                variant="secondary" 
                                size="sm" 
                                onClick={async () => {
                                    try {
                                        if (user?.accessToken) {
                                            await reloadUserProfile();
                                            console.log('🔄 Estado actualizado');
                                        }
                                    } catch (error) {
                                        console.error('Error refrescando estado:', error);
                                    }
                                }}
                            >
                                🔄 Refrescar estado
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    if (providerStatus === 'approved') {
        return (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                    <CheckCircleIcon className="w-5 h-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                    <div className="flex-1">
                        <h3 className="text-sm font-medium text-green-800">¡Solicitud aprobada!</h3>
                        <p className="text-sm text-green-700 mt-1">
                            Tu solicitud para convertirte en proveedor fue aprobada. 
                            Ya puedes comenzar a ofrecer tus servicios.
                        </p>
                        {providerApplication.reviewedAt && (
                            <p className="text-xs text-green-600 mt-2">
                                Aprobado el {new Date(providerApplication.reviewedAt).toLocaleDateString('es-ES')}
                            </p>
                        )}
                        <div className="mt-3">
                            <Button 
                                variant="primary" 
                                size="sm" 
                                onClick={() => navigate('/dashboard')}
                            >
                                Ir al dashboard de proveedor
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    return null;
};

export default ProviderApplicationNotification;
