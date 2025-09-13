import React, { useState, useEffect, useContext } from 'react';
import { BuildingStorefrontIcon, PlusCircleIcon } from '../../components/icons';
import { AuthContext } from '../../contexts/AuthContext';
import { categoriesAPI, servicesAPI, serviceRequestsAPI } from '../../services/api';
import { BackendCategory, BackendService, ServiceRequestIn } from '../../types';

const ProviderExploreCategoriesPage: React.FC = () => {
    const { user } = useContext(AuthContext);
    const [categories, setCategories] = useState<BackendCategory[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<BackendCategory | null>(null);
    const [services, setServices] = useState<BackendService[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingServices, setLoadingServices] = useState(false);
    const [submittingRequest, setSubmittingRequest] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showRequestForm, setShowRequestForm] = useState(false);
    const [newServiceName, setNewServiceName] = useState('');
    const [newServiceDescription, setNewServiceDescription] = useState('');
    const [success, setSuccess] = useState<string | null>(null);

    useEffect(() => {
        loadCategories();
    }, []);

    const loadCategories = async () => {
        try {
            setLoading(true);
            const data = await categoriesAPI.getCategories();
            setCategories(data);
        } catch (err: any) {
            setError(err.detail || 'Error al cargar categorías');
        } finally {
            setLoading(false);
        }
    };

    const loadServicesByCategory = async (categoryId: number) => {
        try {
            setLoadingServices(true);
            setServices([]);
            const data = await servicesAPI.getServicesByCategory(categoryId);
            setServices(data);
        } catch (err: any) {
            setError(err.detail || 'Error al cargar servicios');
        } finally {
            setLoadingServices(false);
        }
    };

    const handleCategorySelect = (category: BackendCategory) => {
        setSelectedCategory(category);
        setServices([]);
        loadServicesByCategory(category.id_categoria);
    };

    const handleRequestNewService = async () => {
        if (!selectedCategory || !newServiceName.trim() || !newServiceDescription.trim()) return;

        try {
            setSubmittingRequest(true);
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            await serviceRequestsAPI.proposeService({
                nombre_servicio: newServiceName.trim(),
                descripcion: newServiceDescription.trim(),
                id_categoria: selectedCategory.id_categoria,
                comentario_admin: null
            }, accessToken);

            setSuccess('Solicitud de servicio enviada exitosamente');
            setNewServiceName('');
            setNewServiceDescription('');
            setShowRequestForm(false);
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.detail || 'Error al enviar solicitud');
            setTimeout(() => setError(null), 3000);
        } finally {
            setSubmittingRequest(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Cargando categorías...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-6">
                    <h1 className="text-3xl font-bold text-gray-900">Explorar Categorías</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Explora las categorías disponibles y solicita nuevos servicios si no encuentras lo que buscas
                        </p>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Messages */}
                {error && (
                    <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
                        <div className="text-sm text-red-700">{error}</div>
                    </div>
                )}
                {success && (
                    <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4">
                        <div className="text-sm text-green-700">{success}</div>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Categories List */}
                    <div className="lg:col-span-1">
                        <div className="bg-white shadow rounded-lg">
                            <div className="p-6">
                                <h2 className="text-lg font-medium text-gray-900 mb-4">Categorías Disponibles</h2>
                                <div className="space-y-2">
                                    {categories.map((category) => (
                                        <button
                                            key={category.id_categoria}
                                            onClick={() => handleCategorySelect(category)}
                                            className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                                                selectedCategory?.id_categoria === category.id_categoria
                                                    ? 'bg-blue-50 border-blue-300 text-blue-700'
                                                    : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                                            }`}
                                        >
                                            <div className="font-medium">{category.nombre}</div>
                                            <div className="text-sm text-gray-500">
                                                {category.estado ? 'Activo' : 'Inactivo'}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Services List */}
                    <div className="lg:col-span-2">
                        {selectedCategory ? (
                            <div className="bg-white shadow rounded-lg">
                                <div className="p-6">
                                    <div className="flex items-center justify-between mb-6">
                                        <div>
                                            <h2 className="text-xl font-medium text-gray-900">
                                                Servicios en {selectedCategory.nombre}
                                            </h2>
                                            <p className="text-sm text-gray-500 mt-1">
                                                Servicios disponibles en esta categoría
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => setShowRequestForm(true)}
                                            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                        >
                                            <PlusCircleIcon className="h-5 w-5 mr-2" />
                                            Solicitar Nuevo Servicio
                                        </button>
                                    </div>

                                    {loadingServices ? (
                                        <div className="flex items-center justify-center py-8">
                                            <div className="text-center">
                                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                                                <p className="mt-2 text-sm text-gray-600">Cargando servicios...</p>
                                            </div>
                                        </div>
                                    ) : services.length > 0 ? (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {services.map((service) => (
                                                <div key={service.id_servicio} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200">
                                                    <h3 className="font-medium text-gray-900 mb-2">{service.nombre}</h3>
                                                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">{service.descripcion}</p>
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-semibold text-blue-600">
                                                            Gs. {service.precio.toLocaleString()}
                                                        </span>
                                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                                            service.estado ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                        }`}>
                                                            {service.estado ? 'Disponible' : 'No disponible'}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-center py-8">
                                            <BuildingStorefrontIcon className="mx-auto h-12 w-12 text-gray-400" />
                                            <h3 className="mt-2 text-sm font-medium text-gray-900">No hay servicios</h3>
                                            <p className="mt-1 text-sm text-gray-500">
                                                No hay servicios disponibles en esta categoría aún.
                                            </p>
                                            <button
                                                onClick={() => setShowRequestForm(true)}
                                                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                                            >
                                                <PlusCircleIcon className="h-5 w-5 mr-2" />
                                                Solicitar Primer Servicio
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="bg-white shadow rounded-lg">
                                <div className="p-12 text-center">
                                    <BuildingStorefrontIcon className="mx-auto h-12 w-12 text-gray-400" />
                                    <h3 className="mt-2 text-sm font-medium text-gray-900">Selecciona una categoría</h3>
                                    <p className="mt-1 text-sm text-gray-500">
                                        Elige una categoría del panel izquierdo para ver los servicios disponibles
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Request New Service Modal */}
            {showRequestForm && selectedCategory && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
                    <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-auto">
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    Solicitar Nuevo Servicio
                                </h3>
                                <button
                                    onClick={() => {
                                        setShowRequestForm(false);
                                        setNewServiceName('');
                                        setNewServiceDescription('');
                                    }}
                                    className="text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                            
                            <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                                <p className="text-sm text-blue-800">
                                    <span className="font-medium">Categoría:</span> {selectedCategory.nombre}
                                </p>
                    </div>

                            <div className="space-y-4">
                                <div>
                                    <label htmlFor="serviceName" className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre del servicio *
                                    </label>
                                    <input
                                        type="text"
                                        id="serviceName"
                                        value={newServiceName}
                                        onChange={(e) => setNewServiceName(e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                                        placeholder="Ej: Diseño de logos, Consultoría..."
                                        maxLength={100}
                                    />
                                    <p className="text-xs text-gray-500 mt-1">{newServiceName.length}/100 caracteres</p>
                                </div>
                                <div>
                                    <label htmlFor="serviceDescription" className="block text-sm font-medium text-gray-700 mb-2">
                                        Descripción del servicio *
                                    </label>
                                    <textarea
                                        id="serviceDescription"
                                        value={newServiceDescription}
                                        onChange={(e) => setNewServiceDescription(e.target.value)}
                                        rows={4}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors resize-none"
                                        placeholder="Describe detalladamente el servicio que ofreces..."
                                        maxLength={500}
                                    />
                                    <p className="text-xs text-gray-500 mt-1">{newServiceDescription.length}/500 caracteres</p>
                                </div>
                            </div>
                            
                            <div className="flex justify-end space-x-3 mt-6">
                                <button
                                    onClick={() => {
                                        setShowRequestForm(false);
                                        setNewServiceName('');
                                        setNewServiceDescription('');
                                    }}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleRequestNewService}
                                    disabled={!newServiceName.trim() || !newServiceDescription.trim() || submittingRequest}
                                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md transition-colors flex items-center"
                                >
                                    {submittingRequest ? (
                                        <>
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                            Enviando...
                                        </>
                                    ) : (
                                        'Enviar Solicitud'
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProviderExploreCategoriesPage;
