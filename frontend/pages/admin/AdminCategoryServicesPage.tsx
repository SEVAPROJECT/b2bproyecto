import React, { useState, useEffect, useContext } from 'react';
import { Link, useParams } from 'react-router-dom';
import { PlusIcon, XMarkIcon } from '../../components/icons';
import OptimizedLoading from '../../components/ui/OptimizedLoading';
import { BackendService, BackendCategory } from '../../types';
import { servicesAPI, categoriesAPI } from '../../services/api';
import { AuthContext } from '../../contexts/AuthContext';
import { API_CONFIG } from '../../config/api';

const AdminCategoryServicesPage: React.FC = () => {
    const { user } = useContext(AuthContext);
    const { categoryId } = useParams<{ categoryId: string }>();
    const [services, setServices] = useState<BackendService[]>([]);
    const [category, setCategory] = useState<BackendCategory | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [editingServiceId, setEditingServiceId] = useState<number | null>(null);
    const [editingService, setEditingService] = useState<Partial<BackendService>>({});
    const [showEditModal, setShowEditModal] = useState(false);
    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [isUploadingImage, setIsUploadingImage] = useState(false);

    useEffect(() => {
        if (categoryId) {
            loadServices();
        }
    }, [categoryId]);

    const handleEditService = (service: BackendService) => {
        setEditingServiceId(service.id_servicio);
        setEditingService({
            nombre: service.nombre,
            descripcion: service.descripcion,
            precio: service.precio,
            estado: service.estado,
            imagen: service.imagen
        });
        setImagePreview(service.imagen 
            ? (service.imagen.startsWith('http') 
                ? service.imagen 
                : `${API_CONFIG.BASE_URL.replace('/api/v1', '')}${service.imagen}`)
            : null);
        setSelectedImage(null);
        setShowEditModal(true);
    };

    const handleSaveServiceEdit = async () => {
        if (!editingServiceId || !editingService.nombre?.trim()) return;

        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            // Guardar el servicio original para poder revertir si falla
            const originalService = services.find(s => s.id_servicio === editingServiceId);
            if (!originalService) return;

            // Preparar datos del servicio
            const serviceData: any = {
                nombre: editingService.nombre.trim(),
                descripcion: editingService.descripcion?.trim() || '',
                precio: editingService.precio || 0,
                estado: editingService.estado || false
            };

            // Si hay una nueva imagen seleccionada, subirla primero
            if (selectedImage) {
                setIsUploadingImage(true);
                try {
                    const formData = new FormData();
                    formData.append('file', selectedImage);
                    
                    // Usar el mismo endpoint que Apporiginal.tsx
                    const apiBaseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
                    const uploadResponse = await fetch(`${apiBaseUrl}/api/v1/provider/services/upload-image`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        },
                        body: formData
                    });

                    if (uploadResponse.ok) {
                        const uploadResult = await uploadResponse.json();
                        serviceData.imagen = uploadResult.image_path; // Usar image_path como en Apporiginal.tsx
                    } else {
                        const errorData = await uploadResponse.json();
                        throw new Error(errorData.detail || 'Error al subir la imagen');
                    }
                } finally {
                    setIsUploadingImage(false);
                }
            } else if (editingService.imagen === null) {
                // Si se removió la imagen
                serviceData.imagen = null;
            }

            // Actualizar optimísticamente el estado local (sin recargar toda la página)
            setServices(prevServices =>
                prevServices.map(service =>
                    service.id_servicio === editingServiceId
                        ? {
                            ...service,
                            nombre: serviceData.nombre,
                            descripcion: serviceData.descripcion || '',
                            precio: serviceData.precio || 0,
                            estado: serviceData.estado || false,
                            imagen: serviceData.imagen !== undefined ? serviceData.imagen : service.imagen
                        }
                        : service
                )
            );

            await servicesAPI.updateService(editingServiceId, serviceData, accessToken);

            setSuccess('Servicio actualizado exitosamente');
            setShowEditModal(false);
            setEditingServiceId(null);
            setEditingService({});
            setSelectedImage(null);
            setImagePreview(null);
            // No recargar todos los servicios, ya actualizamos el estado local
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            // Revertir el cambio optimista si la API falla
            if (originalService) {
                setServices(prevServices =>
                    prevServices.map(service =>
                        service.id_servicio === editingServiceId
                            ? originalService
                            : service
                    )
                );
            }
            
            setError(err.detail || 'Error al actualizar servicio');
            setTimeout(() => setError(null), 3000);
        }
    };

    const handleToggleServiceStatus = async (serviceId: number, currentStatus: boolean) => {
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            const newStatus = !currentStatus;
            
            // Actualizar el estado optimísticamente
            setServices(prevServices =>
                prevServices.map(service =>
                    service.id_servicio === serviceId
                        ? { ...service, estado: newStatus }
                        : service
                )
            );

            // Llamar a la API para actualizar el estado
            await servicesAPI.updateServiceStatus(serviceId, newStatus, accessToken);
            
            setSuccess(`Servicio ${newStatus ? 'activado' : 'desactivado'} exitosamente`);
            setTimeout(() => setSuccess(null), 3000);

        } catch (err: any) {
            // Revertir el cambio si la API falla
            setServices(prevServices =>
                prevServices.map(service =>
                    service.id_servicio === serviceId
                        ? { ...service, estado: currentStatus }
                        : service
                )
            );

            setError(err.detail || 'Error al actualizar el estado del servicio');
            setTimeout(() => setError(null), 3000);
        }
    };

    const handleCancelEdit = () => {
        setShowEditModal(false);
        setEditingServiceId(null);
        setEditingService({});
        setSelectedImage(null);
        setImagePreview(null);
        setIsUploadingImage(false);
    };

    const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedImage(file);
            const reader = new FileReader();
            reader.onload = (e) => {
                setImagePreview(e.target?.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleRemoveImage = () => {
        setSelectedImage(null);
        setImagePreview(null);
        setEditingService({...editingService, imagen: null});
    };

    const loadServices = async () => {
        try {
            setLoading(true);
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken || !categoryId) return;

            // Cargar servicios de la categoría
            const servicesData = await servicesAPI.getServicesByCategory(Number.parseInt(categoryId), accessToken);
            setServices(servicesData);

            // Cargar información de la categoría
            const categoriesData = await categoriesAPI.getCategories(accessToken);
            const currentCategory = categoriesData.find(cat => cat.id_categoria === Number.parseInt(categoryId));
            setCategory(currentCategory || null);

        } catch (err: any) {
            setError(err.detail || 'Error al cargar servicios');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <OptimizedLoading 
                message="Cargando servicios..."
                showProgress={false}
            />
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900">
                                    Servicios de {category?.nombre || 'Categoría'}
                                </h1>
                                <p className="mt-1 text-sm text-gray-500">
                                    Gestiona los servicios disponibles en esta categoría
                                </p>
                            </div>
                            <Link
                                to="/dashboard/categories"
                                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                ← Volver a Categorías
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

                {/* Services Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {services.map((service) => (
                        <div key={service.id_servicio} className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                            <div className="p-6">
                                <div className="flex items-start space-x-4">
                                    {/* Service Image */}
                                    <div className="flex-shrink-0 w-20 h-20 bg-gray-100 rounded-xl border-2 border-gray-200 flex items-center justify-center overflow-hidden">
                                        {service.imagen ? (
                                            <img
                                                src={service.imagen.startsWith('http') 
                                                    ? service.imagen 
                                                    : `${API_CONFIG.BASE_URL.replace('/api/v1', '')}${service.imagen}`}
                                                alt={`Imagen de ${service.nombre}`}
                                                className="w-full h-full object-cover"
                                                onError={(e) => {
                                                    console.error('❌ Error cargando imagen del servicio:', {
                                                        servicioId: service.id_servicio,
                                                        imagen: service.imagen,
                                                        urlCompleta: service.imagen.startsWith('http') 
                                                            ? service.imagen 
                                                            : `${API_CONFIG.BASE_URL.replace('/api/v1', '')}${service.imagen}`
                                                    });
                                                    const target = e.target as HTMLImageElement;
                                                    target.style.display = 'none';
                                                    const placeholder = target.parentElement;
                                                    if (placeholder) {
                                                        placeholder.innerHTML = `
                                                            <div class="w-full h-full bg-gray-200 flex items-center justify-center">
                                                                <svg class="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                                                </svg>
                                                            </div>
                                                        `;
                                                    }
                                                }}
                                            />
                                        ) : (
                                            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                            </svg>
                                        )}
                                    </div>

                                    {/* Service Information */}
                                    <div className="flex-1 min-w-0">
                                        <h3 className="text-lg font-medium text-gray-900 truncate">{service.nombre}</h3>
                                        <p className="mt-1 text-sm text-gray-600 line-clamp-2">{service.descripcion}</p>
                                        <div className="mt-3 flex items-center justify-between">
                                            <span className="text-lg font-semibold text-gray-900">
                                                Gs. {service.precio ? service.precio.toLocaleString() : '0'}
                                            </span>
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                service.estado ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                            }`}>
                                                {service.estado ? 'Activo' : 'Inactivo'}
                                            </span>
                                        </div>
                                        <div className="mt-2 text-xs text-gray-500">
                                            Creado: {new Date(service.created_at).toLocaleDateString()}
                                        </div>
                                        {user?.role === 'admin' && (
                                            <div className="mt-3 space-y-2">
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={() => handleToggleServiceStatus(service.id_servicio, service.estado)}
                                                        className={`flex-1 text-xs px-3 py-2 rounded transition-colors ${
                                                            service.estado
                                                                ? 'bg-red-100 text-red-700 hover:bg-red-200 border border-red-300'
                                                                : 'bg-green-100 text-green-700 hover:bg-green-200 border border-green-300'
                                                        }`}
                                                    >
                                                        {service.estado ? (
                                                            <>
                                                                <XMarkIcon className="h-3 w-3 inline mr-1" />
                                                                Desactivar
                                                            </>
                                                        ) : (
                                                            <>
                                                                <PlusIcon className="h-3 w-3 inline mr-1" />
                                                                Activar
                                                            </>
                                                        )}
                                                    </button>
                                                </div>
                                                <button
                                                    onClick={() => handleEditService(service)}
                                                    className="w-full text-xs bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                >
                                                    Editar Servicio
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {(!services || services.length === 0) && (
                    <div className="text-center py-12">
                        <div className="w-20 h-20 bg-gray-100 rounded-xl border-2 border-gray-200 flex items-center justify-center mx-auto mb-4">
                            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No hay servicios</h3>
                        <p className="text-sm text-gray-500">No hay servicios publicados aún en esta categoría.</p>
                    </div>
                )}
            </div>

            {/* Edit Service Modal */}
            {showEditModal && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                        <div className="mt-3">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Editar Servicio</h3>
                            
                            <div className="space-y-4">
                                <div>
                                    <label htmlFor="serviceName" className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre del servicio
                                    </label>
                                    <input
                                        type="text"
                                        id="serviceName"
                                        value={editingService.nombre || ''}
                                        onChange={(e) => setEditingService({...editingService, nombre: e.target.value})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Nombre del servicio"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="serviceDescription" className="block text-sm font-medium text-gray-700 mb-2">
                                        Descripción
                                    </label>
                                    <textarea
                                        id="serviceDescription"
                                        value={editingService.descripcion || ''}
                                        onChange={(e) => setEditingService({...editingService, descripcion: e.target.value})}
                                        rows={3}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Descripción del servicio"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="servicePrice" className="block text-sm font-medium text-gray-700 mb-2">
                                        Precio (Gs.)
                                    </label>
                                    <input
                                        type="number"
                                        id="servicePrice"
                                        value={editingService.precio || 0}
                                        onChange={(e) => setEditingService({...editingService, precio: Number.parseFloat(e.target.value) || 0})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="0"
                                        min="0"
                                        step="1000"
                                    />
                                </div>

                                <div>
                                    <label className="flex items-center">
                                        <input
                                            type="checkbox"
                                            checked={editingService.estado || false}
                                            onChange={(e) => setEditingService({...editingService, estado: e.target.checked})}
                                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                        />
                                        <span className="ml-2 text-sm text-gray-700">Servicio activo</span>
                                    </label>
                                </div>

                                <div>
                                    <label htmlFor="serviceImage" className="block text-sm font-medium text-gray-700 mb-2">
                                        Imagen del servicio
                                    </label>
                                    
                                    {/* Vista previa de la imagen */}
                                    {imagePreview && (
                                        <div className="mb-3">
                                            <img
                                                src={imagePreview}
                                                alt="Vista previa"
                                                className="w-32 h-32 object-cover rounded-lg border border-gray-300"
                                            />
                                            <button
                                                type="button"
                                                onClick={handleRemoveImage}
                                                className="mt-2 text-xs text-red-600 hover:text-red-800"
                                            >
                                                Remover imagen
                                            </button>
                                        </div>
                                    )}
                                    
                                    <input
                                        type="file"
                                        id="serviceImage"
                                        accept="image/png,image/jpeg,image/jpg"
                                        onChange={handleImageSelect}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">
                                        Selecciona una nueva imagen para reemplazar la actual
                                    </p>
                                    <p className="text-xs text-gray-400 mt-1">
                                        (PNG/JPG, máximo 5MB)
                                    </p>
                                </div>
                            </div>

                            <div className="flex justify-end space-x-3 mt-6">
                                <button
                                    onClick={handleCancelEdit}
                                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleSaveServiceEdit}
                                    disabled={isUploadingImage}
                                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isUploadingImage ? 'Subiendo imagen...' : 'Guardar Cambios'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminCategoryServicesPage;
