import React, { useState, useEffect } from 'react';
import { ExclamationCircleIcon, EyeIcon, EyeSlashIcon } from '../icons';
import { BackendService, BackendCategory } from '../../types';
import { servicesAPI, categoriesAPI } from '../../services/api';
import { formatPriceProfessional, getTimeAgo } from '../../utils/formatting';

const AdminServicesPage: React.FC = () => {
    const [services, setServices] = useState<BackendService[]>([]);
    const [categories, setCategories] = useState<BackendCategory[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [categoryFilter, setCategoryFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('all');
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 10;

    const loadData = async () => {
        try {
            setIsLoading(true);
            setError(null);
            const [servicesData, categoriesData] = await Promise.all([
                servicesAPI.getAll(),
                categoriesAPI.getAll()
            ]);
            setServices(servicesData);
            setCategories(categoriesData);
        } catch (err) {
            console.error('Error cargando datos:', err);
            setError('Error al cargar los datos. Por favor, intentá nuevamente.');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const filteredServices = services.filter(service => {
        const matchesSearch = service.nombre.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            service.descripcion.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            (service.razon_social?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
        const matchesCategory = categoryFilter === 'all' || service.id_categoria.toString() === categoryFilter;
        const matchesStatus = statusFilter === 'all' || 
                            (statusFilter === 'active' && service.estado) ||
                            (statusFilter === 'inactive' && !service.estado);
        return matchesSearch && matchesCategory && matchesStatus;
    });

    const paginatedServices = filteredServices.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    const totalPages = Math.ceil(filteredServices.length / itemsPerPage);

    const handleToggleServiceStatus = async (serviceId: number, currentStatus: boolean) => {
        try {
            // Implementar lógica para cambiar estado del servicio
            console.log('Cambiando estado del servicio:', serviceId, !currentStatus);
            
        } catch (err) {
            console.error('Error actualizando servicio:', err);
        }
    };

    if (isLoading) {
        return (
            <div className="bg-slate-50 min-h-screen">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-center min-h-[400px]">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                            <p className="mt-4 text-slate-600">Cargando servicios...</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-slate-50 min-h-screen">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="bg-white p-8 rounded-xl shadow-md border border-slate-200/80">
                        <div className="text-center py-12">
                            <ExclamationCircleIcon className="mx-auto h-12 w-12 text-red-400" />
                            <h3 className="mt-2 text-lg font-semibold text-slate-800">Error al cargar</h3>
                            <p className="mt-1 text-sm text-slate-500">{error}</p>
                            <button
                                onClick={loadData}
                                className="mt-4 btn-blue touch-manipulation"
                            >
                                <span>Reintentar</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-slate-50 min-h-screen">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="max-w-7xl mx-auto">
                    {/* Encabezado */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-slate-900 mb-2">Gestión de Servicios</h1>
                        <p className="text-slate-600">Administrá los servicios publicados en la plataforma</p>
                    </div>

                    {/* Filtros */}
                    <div className="bg-white p-6 rounded-xl shadow-md border border-slate-200/80 mb-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label htmlFor="search-services" className="block text-sm font-medium text-slate-700 mb-2">
                                    Buscar servicios
                                </label>
                                <input
                                    id="search-services"
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Buscar por nombre, descripción o empresa..."
                                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>
                            <div>
                                <label htmlFor="filter-category-services" className="block text-sm font-medium text-slate-700 mb-2">
                                    Filtrar por categoría
                                </label>
                                <select
                                    id="filter-category-services"
                                    value={categoryFilter}
                                    onChange={(e) => setCategoryFilter(e.target.value)}
                                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                >
                                    <option value="all">Todas las categorías</option>
                                    {categories.map(category => (
                                        <option key={category.id_categoria} value={category.id_categoria.toString()}>
                                            {category.nombre}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label htmlFor="filter-status-services" className="block text-sm font-medium text-slate-700 mb-2">
                                    Filtrar por estado
                                </label>
                                <select
                                    id="filter-status-services"
                                    value={statusFilter}
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                >
                                    <option value="all">Todos los estados</option>
                                    <option value="active">Activos</option>
                                    <option value="inactive">Inactivos</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Tabla de servicios */}
                    <div className="bg-white rounded-xl shadow-md border border-slate-200/80 overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-slate-200">
                                <thead className="bg-slate-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                            Servicio
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                            Categoría
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                            Proveedor
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                            Precio
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                            Fecha de publicación
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                            Estado
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                            Acciones
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-slate-200">
                                    {paginatedServices.map((service) => {
                                        const category = categories.find(c => c.id_categoria === service.id_categoria);
                                        return (
                                            <tr key={service.id_servicio} className="hover:bg-slate-50">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center">
                                                        <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                                                            <span className="text-primary-600 font-semibold text-sm">
                                                                {service.nombre.charAt(0).toUpperCase()}
                                                            </span>
                                                        </div>
                                                        <div className="ml-4">
                                                            <div className="text-sm font-medium text-slate-900">
                                                                {service.nombre}
                                                            </div>
                                                            <div className="text-sm text-slate-500 max-w-xs truncate">
                                                                {service.descripcion}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                                                        {category?.nombre || 'Sin categoría'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm text-slate-900">
                                                        {service.razon_social || 'Sin empresa'}
                                                    </div>
                                                    <div className="text-sm text-slate-500">
                                                        {service.nombre_contacto || 'Sin contacto'}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                                                    {service.precio ? formatPriceProfessional(service.precio, service) : 'No especificado'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                                                    {getTimeAgo(service.created_at)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                        service.estado ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                    }`}>
                                                        {service.estado ? 'Activo' : 'Inactivo'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                    <button
                                                        onClick={() => handleToggleServiceStatus(service.id_servicio, service.estado)}
                                                        className={`mr-3 ${
                                                            service.estado 
                                                                ? 'text-green-600 hover:text-green-900' 
                                                                : 'text-red-600 hover:text-red-900'
                                                        }`}
                                                    >
                                                        {service.estado ? (
                                                            <EyeIcon className="w-4 h-4" />
                                                        ) : (
                                                            <EyeSlashIcon className="w-4 h-4" />
                                                        )}
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>

                        {/* Paginación */}
                        {totalPages > 1 && (
                            <div className="bg-white px-4 py-3 border-t border-slate-200 sm:px-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex-1 flex justify-between sm:hidden">
                                        <button
                                            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                            disabled={currentPage === 1}
                                            className="relative inline-flex items-center px-4 py-2 border border-slate-300 text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            Anterior
                                        </button>
                                        <button
                                            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                            disabled={currentPage === totalPages}
                                            className="ml-3 relative inline-flex items-center px-4 py-2 border border-slate-300 text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            Siguiente
                                        </button>
                                    </div>
                                    <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                                        <div>
                                            <p className="text-sm text-slate-700">
                                                Mostrando{' '}
                                                <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span>
                                                {' '}a{' '}
                                                <span className="font-medium">
                                                    {Math.min(currentPage * itemsPerPage, filteredServices.length)}
                                                </span>
                                                {' '}de{' '}
                                                <span className="font-medium">{filteredServices.length}</span>
                                                {' '}resultados
                                            </p>
                                        </div>
                                        <div>
                                            <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                                                <button
                                                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                                    disabled={currentPage === 1}
                                                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-slate-300 bg-white text-sm font-medium text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                                >
                                                    Anterior
                                                </button>
                                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                    const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                                                    if (pageNum > totalPages) return null;
                                                    
                                                    return (
                                                        <button
                                                            key={pageNum}
                                                            onClick={() => setCurrentPage(pageNum)}
                                                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                                                currentPage === pageNum
                                                                    ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                                                                    : 'bg-white border-slate-300 text-slate-500 hover:bg-slate-50'
                                                            }`}
                                                        >
                                                            {pageNum}
                                                        </button>
                                                    );
                                                })}
                                                <button
                                                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                                    disabled={currentPage === totalPages}
                                                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-slate-300 bg-white text-sm font-medium text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                                >
                                                    Siguiente
                                                </button>
                                            </nav>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminServicesPage;
