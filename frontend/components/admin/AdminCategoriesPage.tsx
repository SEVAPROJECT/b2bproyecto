import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { BuildingStorefrontIcon, PlusCircleIcon } from '../icons';
import OptimizedLoading from '../ui/OptimizedLoading';
import { BackendCategory } from '../../types';
import { categoriesAPI } from '../../services/api';
import { AuthContext } from '../../contexts/AuthContext';

const AdminCategoriesPage: React.FC = () => {
    const { user } = useContext(AuthContext);
    const [categories, setCategories] = useState<BackendCategory[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newCategoryName, setNewCategoryName] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
    const [editingCategoryName, setEditingCategoryName] = useState('');

    useEffect(() => {
        loadCategories();
    }, []);

    const loadCategories = async () => {
        try {
            setLoading(true);
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            // Los administradores ven todas las categorías (activas e inactivas)
            // Los otros usuarios solo ven las activas
            const activeOnly = user?.role !== 'admin';
            const data = await categoriesAPI.getCategories(accessToken, activeOnly);
            setCategories(data);
        } catch (err: any) {
            setError(err.detail || 'Error al cargar categorías');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateCategory = async () => {
        if (!newCategoryName.trim()) return;

        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            await categoriesAPI.createCategory({
                nombre: newCategoryName.trim(),
                estado: true
            }, accessToken);

            setSuccess('Categoría creada exitosamente');
            setNewCategoryName('');
            setShowCreateForm(false);
            loadCategories();
            setTimeout(() => setSuccess(null), 13000);
        } catch (err: any) {
            setError(err.detail || 'Error al crear categoría');
            setTimeout(() => setError(null), 3000);
        }
    };

    const handleEditCategory = (categoryId: number, currentName: string) => {
        setEditingCategoryId(categoryId);
        setEditingCategoryName(currentName);
    };

    const handleSaveCategoryEdit = async () => {
        if (!editingCategoryName.trim() || !editingCategoryId) return;

        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            await categoriesAPI.updateCategory(editingCategoryId, {
                nombre: editingCategoryName.trim()
            }, accessToken);

            setSuccess('Categoría actualizada exitosamente');
            setEditingCategoryId(null);
            setEditingCategoryName('');
            loadCategories();
            setTimeout(() => setSuccess(null), 13000);
        } catch (err: any) {
            setError(err.detail || 'Error al actualizar categoría');
            setTimeout(() => setError(null), 3000);
        }
    };

    const handleCancelEdit = () => {
        setEditingCategoryId(null);
        setEditingCategoryName('');
    };

    const handleToggleCategoryStatus = async (categoryId: number, currentStatus: boolean) => {
        // Optimistic update: cambiar el estado local inmediatamente
        const newStatus = !currentStatus;
        setCategories(prevCategories =>
            prevCategories.map(cat =>
                cat.id_categoria === categoryId
                    ? { ...cat, estado: newStatus }
                    : cat
            )
        );

        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                // Revertir el cambio si no hay token
                setCategories(prevCategories =>
                    prevCategories.map(cat =>
                        cat.id_categoria === categoryId
                            ? { ...cat, estado: currentStatus }
                            : cat
                    )
                );
                return;
            }

            await categoriesAPI.updateCategory(categoryId, {
                estado: newStatus
            }, accessToken);

            setSuccess(`Categoría ${newStatus ? 'activada' : 'desactivada'} exitosamente`);
            setTimeout(() => setSuccess(null), 11500);

        } catch (err: any) {
            // Revertir el cambio si la API falla
            setCategories(prevCategories =>
                prevCategories.map(cat =>
                    cat.id_categoria === categoryId
                        ? { ...cat, estado: currentStatus }
                        : cat
                )
            );

            setError(err.detail || 'Error al actualizar categoría');
            setTimeout(() => setError(null), 3000);
        }
    };

    if (loading) {
        return (
            <OptimizedLoading 
                message="Cargando categorías..."
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
                                <h1 className="text-3xl font-bold text-gray-900">Gestión de Categorías</h1>
                                <p className="mt-1 text-sm text-gray-500">
                                    Administra las categorías de servicios disponibles en la plataforma
                                </p>
                            </div>
                            <button
                                onClick={() => setShowCreateForm(true)}
                                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                <PlusCircleIcon className="h-5 w-5 mr-2" />
                                Nueva Categoría
                            </button>
                        </div>
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

                {/* Categories Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {categories.map((category) => (
                        <div key={category.id_categoria} className="bg-white overflow-hidden shadow rounded-lg">
                            <div className="p-6">
                                <div className="flex items-center">
                                    <div className="flex-shrink-0">
                                        <BuildingStorefrontIcon className="h-8 w-8 text-gray-400" />
                                    </div>
                                    <div className="ml-4 flex-1">
                                        {editingCategoryId === category.id_categoria ? (
                                            <div className="space-y-2">
                                                <input
                                                    type="text"
                                                    value={editingCategoryName}
                                                    onChange={(e) => setEditingCategoryName(e.target.value)}
                                                    className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    placeholder="Nombre de la categoría"
                                                />
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={handleSaveCategoryEdit}
                                                        className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                                                    >
                                                        Guardar
                                                    </button>
                                                    <button
                                                        onClick={handleCancelEdit}
                                                        className="text-xs bg-gray-600 text-white px-2 py-1 rounded hover:bg-gray-700"
                                                    >
                                                        Cancelar
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <>
                                                <h3 className="text-lg font-medium text-gray-900">{category.nombre}</h3>
                                                <p className="text-sm text-gray-500">
                                                    Estado: {category.estado ? 'Activo' : 'Inactivo'}
                                                </p>
                                                <p className="text-xs text-gray-400 mt-1">
                                                    Creado: {new Date(category.created_at).toLocaleDateString()}
                                                </p>
                                            </>
                                        )}
                                    </div>
                                </div>
                                <div className="mt-4 flex items-center justify-between">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        category.estado
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-red-100 text-red-800'
                                    }`}>
                                        {category.estado ? 'Activo' : 'Inactivo'}
                                    </span>
                                    <div className="flex items-center space-x-3">
                                        <Link
                                            to={`/dashboard/categories/${category.id_categoria}/services`}
                                            className="text-blue-600 hover:text-blue-500 text-sm font-medium"
                                        >
                                            Ver servicios →
                                        </Link>
                                        {editingCategoryId !== category.id_categoria && (
                                            <button
                                                onClick={() => handleEditCategory(category.id_categoria, category.nombre)}
                                                className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                                            >
                                                Editar
                                            </button>
                                        )}
                                        <button
                                            onClick={() => handleToggleCategoryStatus(category.id_categoria, category.estado)}
                                            className={`inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded ${
                                                category.estado
                                                    ? 'text-red-700 bg-red-100 hover:bg-red-200'
                                                    : 'text-green-700 bg-green-100 hover:bg-green-200'
                                            } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500`}
                                        >
                                            {category.estado ? 'Desactivar' : 'Activar'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {categories.length === 0 && (
                    <div className="text-center py-12">
                        <BuildingStorefrontIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay categorías</h3>
                        <p className="mt-1 text-sm text-gray-500">Comienza creando tu primera categoría.</p>
                    </div>
                )}
            </div>

            {/* Create Category Modal */}
            {showCreateForm && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                        <div className="mt-3">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Nueva Categoría</h3>
                            <div className="mb-4">
                                <label htmlFor="categoryName" className="block text-sm font-medium text-gray-700 mb-2">
                                    Nombre de la categoría
                                </label>
                                <input
                                    type="text"
                                    id="categoryName"
                                    value={newCategoryName}
                                    onChange={(e) => setNewCategoryName(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Ej: Catering, Transporte, Salud..."
                                />
                            </div>
                            <div className="flex justify-end space-x-3">
                                <button
                                    onClick={() => {
                                        setShowCreateForm(false);
                                        setNewCategoryName('');
                                    }}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleCreateCategory}
                                    disabled={!newCategoryName.trim()}
                                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 rounded-md"
                                >
                                    Crear
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminCategoriesPage;
