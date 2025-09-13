import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { servicesAPI } from '../services/api';
import { BackendService } from '../types';
import { MainLayout } from '../components/layouts';
import { StarIcon, MapPinIcon, ClockIcon, UserCircleIcon } from '../components/icons';

const ServiceDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [service, setService] = useState<BackendService | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (id) {
            loadService();
        }
    }, [id]);

    const loadService = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('access_token');
            if (!token) {
                setError('No autorizado');
                return;
            }

            const serviceData = await servicesAPI.getServiceById(parseInt(id!), token);
            setService(serviceData);
        } catch (err: any) {
            setError(err.message || 'Error al cargar el servicio');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <MainLayout>
                <div className="min-h-screen flex items-center justify-center">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Cargando servicio...</p>
                    </div>
                </div>
            </MainLayout>
        );
    }

    if (error || !service) {
        return (
            <MainLayout>
                <div className="min-h-screen flex items-center justify-center">
                    <div className="text-center">
                        <div className="text-red-600">
                            <h2 className="text-xl font-semibold mb-2">Error</h2>
                            <p>{error || 'Servicio no encontrado'}</p>
                            <button
                                onClick={() => navigate('/marketplace')}
                                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                            >
                                Volver al marketplace
                            </button>
                        </div>
                    </div>
                </div>
            </MainLayout>
        );
    }

    return (
        <MainLayout>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-white shadow-lg rounded-lg overflow-hidden">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
                        <h1 className="text-3xl font-bold">{service.nombre}</h1>
                        <p className="mt-2 text-blue-100">{service.descripcion}</p>
                    </div>

                    <div className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Imagen y precio */}
                            <div>
                                <div className="bg-gray-100 rounded-lg p-4 mb-6">
                                    <h3 className="text-lg font-semibold mb-4">Información del Servicio</h3>
                                    <div className="text-3xl font-bold text-green-600 mb-4">
                                        Gs. {service.precio?.toLocaleString() || 'Consultar'}
                                    </div>
                                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                                        <div className="flex items-center">
                                            <ClockIcon className="w-4 h-4 mr-1" />
                                            <span>Disponible</span>
                                        </div>
                                        <div className="flex items-center">
                                            <StarIcon className="w-4 h-4 mr-1" />
                                            <span>4.5 (120 reseñas)</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Botón de contacto */}
                                <button className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                                    Contactar Proveedor
                                </button>
                            </div>

                            {/* Información del proveedor */}
                            <div>
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <h3 className="text-lg font-semibold mb-4">Proveedor</h3>
                                    <div className="flex items-center space-x-3 mb-4">
                                        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                                            <UserCircleIcon className="w-6 h-6 text-blue-600" />
                                        </div>
                                        <div>
                                            <h4 className="font-medium">{service.razon_social || 'Proveedor'}</h4>
                                            <p className="text-sm text-gray-600">Servicio verificado</p>
                                        </div>
                                    </div>

                                    <div className="space-y-2 text-sm">
                                        <div className="flex items-center text-gray-600">
                                            <MapPinIcon className="w-4 h-4 mr-2" />
                                            <span>{service.ciudad || 'Ciudad no especificada'}</span>
                                        </div>
                                        <div className="text-gray-600">
                                            <span className="font-medium">Estado:</span> {service.estado ? 'Activo' : 'Inactivo'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </MainLayout>
    );
};

export default ServiceDetailPage;
