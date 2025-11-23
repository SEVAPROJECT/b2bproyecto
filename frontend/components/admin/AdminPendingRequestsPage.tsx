import React, { useState, useEffect } from 'react';
import { ClipboardDocumentListIcon, EyeIcon, CheckCircleIcon, XCircleIcon } from '../icons';

const AdminPendingRequestsPage: React.FC = () => {
    const [requests, setRequests] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadRequests();
    }, []);

    const loadRequests = async () => {
        try {
            setIsLoading(true);
            setError(null);
            // Implementar llamada a la API
            // const data = await requestsAPI.getPendingRequests(token);
            // setRequests(data);

            // Datos de ejemplo por ahora
            setRequests([
                {
                    id: 1,
                    type: 'provider_registration',
                    user: 'Juan Pérez',
                    company: 'Empresa XYZ',
                    status: 'pending',
                    createdAt: '2024-01-15'
                }
            ]);
        } catch (err) {
            console.error('Error cargando solicitudes:', err);
            setError('Error al cargar las solicitudes');
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Cargando solicitudes pendientes...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">Solicitudes Pendientes</h1>
                    <p className="mt-2 text-gray-600">Gestiona las solicitudes de registro y otros procesos pendientes</p>
                </div>

                {error && (
                    <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
                        <div className="text-sm text-red-700">{error}</div>
                    </div>
                )}

                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                    <ul className="divide-y divide-gray-200">
                        {requests.length > 0 ? (
                            requests.map((request) => (
                                <li key={request.id}>
                                    <div className="px-4 py-4 sm:px-6">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0">
                                                    <ClipboardDocumentListIcon className="h-8 w-8 text-yellow-400" />
                                                </div>
                                                <div className="ml-4">
                                                    <div className="text-sm font-medium text-gray-900">
                                                        {request.user} - {request.company}
                                                    </div>
                                                    <div className="text-sm text-gray-500">
                                                        Tipo: {request.type} | Fecha: {request.createdAt}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex space-x-2">
                                                <button className="inline-flex items-center px-3 py-1 border border-transparent rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700">
                                                    <CheckCircleIcon className="w-4 h-4 mr-1" />
                                                    Aprobar
                                                </button>
                                                <button className="inline-flex items-center px-3 py-1 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50">
                                                    <XCircleIcon className="w-4 h-4 mr-1" />
                                                    Rechazar
                                                </button>
                                                <button className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                                                    <EyeIcon className="w-4 h-4 mr-1" />
                                                    Ver Detalles
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </li>
                            ))
                        ) : (
                            <li>
                                <div className="px-4 py-8 text-center">
                                    <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400" />
                                    <h3 className="mt-2 text-sm font-medium text-gray-900">No hay solicitudes pendientes</h3>
                                    <p className="mt-1 text-sm text-gray-500">Todas las solicitudes han sido procesadas.</p>
                                </div>
                            </li>
                        )}
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default AdminPendingRequestsPage;
