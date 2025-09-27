import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { CalendarDaysIcon, ClockIcon, PlusIcon, TrashIcon, PencilIcon } from '../../components/icons';

interface Disponibilidad {
    id_disponibilidad?: number;
    id_servicio: number;
    fecha_inicio: string;
    fecha_fin: string;
    disponible: boolean;
    precio_adicional?: number;
    observaciones?: string;
    servicio_nombre?: string;
}

interface Servicio {
    id_servicio: number;
    nombre: string;
    descripcion: string;
    estado: boolean;
}

const ProviderAgendaPage: React.FC = () => {
    const { user } = useAuth();
    const [disponibilidades, setDisponibilidades] = useState<Disponibilidad[]>([]);
    const [servicios, setServicios] = useState<Servicio[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    const [formData, setFormData] = useState({
        id_servicio: '',
        fecha_inicio: '',
        fecha_fin: '',
        disponible: true,
        precio_adicional: 0,
        observaciones: ''
    });

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    // Cargar servicios del proveedor
    useEffect(() => {
        loadServicios();
    }, []);

    // Cargar disponibilidades cuando cambien los servicios
    useEffect(() => {
        if (servicios.length > 0) {
            loadDisponibilidades();
        }
    }, [servicios]);

    const loadServicios = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`${API_URL}/api/v1/provider/services`, {
                headers: {
                    'Authorization': `Bearer ${user?.accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Error al cargar servicios');
            }

            const data = await response.json();
            setServicios(data);
        } catch (err) {
            console.error('Error al cargar servicios:', err);
            setError(err instanceof Error ? err.message : 'Error desconocido');
        } finally {
            setLoading(false);
        }
    };

    const loadDisponibilidades = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // Cargar disponibilidades de todos los servicios
            const promises = servicios.map(servicio => 
                fetch(`${API_URL}/api/v1/disponibilidades/servicio/${servicio.id_servicio}`, {
                    headers: {
                        'Authorization': `Bearer ${user?.accessToken}`,
                        'Content-Type': 'application/json',
                    },
                }).then(res => res.json())
            );

            const results = await Promise.all(promises);
            const allDisponibilidades = results.flat().map(disp => ({
                ...disp,
                servicio_nombre: servicios.find(s => s.id_servicio === disp.id_servicio)?.nombre
            }));

            // Ordenar por fecha de inicio
            allDisponibilidades.sort((a, b) => 
                new Date(a.fecha_inicio).getTime() - new Date(b.fecha_inicio).getTime()
            );

            setDisponibilidades(allDisponibilidades);
        } catch (err) {
            console.error('Error al cargar disponibilidades:', err);
            setError(err instanceof Error ? err.message : 'Error desconocido');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!formData.id_servicio || !formData.fecha_inicio || !formData.fecha_fin) {
            setError('Por favor completa todos los campos requeridos');
            return;
        }

        try {
            setLoading(true);
            setError(null);

            const disponibilidadData = {
                id_servicio: parseInt(formData.id_servicio),
                fecha_inicio: new Date(formData.fecha_inicio).toISOString(),
                fecha_fin: new Date(formData.fecha_fin).toISOString(),
                disponible: formData.disponible,
                precio_adicional: formData.precio_adicional || 0,
                observaciones: formData.observaciones || null
            };

            const response = await fetch(`${API_URL}/api/v1/disponibilidades/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${user?.accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(disponibilidadData),
            });

            if (!response.ok) {
                throw new Error('Error al crear disponibilidad');
            }

            // Recargar disponibilidades
            await loadDisponibilidades();
            
            // Limpiar formulario
            setFormData({
                id_servicio: '',
                fecha_inicio: '',
                fecha_fin: '',
                disponible: true,
                precio_adicional: 0,
                observaciones: ''
            });
            setShowForm(false);
            
        } catch (err) {
            console.error('Error al crear disponibilidad:', err);
            setError(err instanceof Error ? err.message : 'Error desconocido');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('¿Estás seguro de que quieres eliminar esta disponibilidad?')) {
            return;
        }

        try {
            setLoading(true);
            setError(null);

            const response = await fetch(`${API_URL}/api/v1/disponibilidades/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${user?.accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Error al eliminar disponibilidad');
            }

            // Recargar disponibilidades
            await loadDisponibilidades();
            
        } catch (err) {
            console.error('Error al eliminar disponibilidad:', err);
            setError(err instanceof Error ? err.message : 'Error desconocido');
        } finally {
            setLoading(false);
        }
    };

    const formatDateTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString('es-PY', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-PY', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString('es-PY', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                                <CalendarDaysIcon className="h-8 w-8 text-primary-600" />
                                Mi Agenda
                            </h1>
                            <p className="mt-2 text-gray-600">
                                Gestiona la disponibilidad de todos tus servicios en una sola agenda
                            </p>
                        </div>
                        <button
                            onClick={() => setShowForm(!showForm)}
                            className="btn-blue flex items-center gap-2"
                        >
                            <PlusIcon className="h-5 w-5" />
                            Nueva Disponibilidad
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                        <p className="text-red-800">⚠️ {error}</p>
                    </div>
                )}

                {/* Formulario para agregar disponibilidad */}
                {showForm && (
                    <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8 shadow-sm">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <PlusIcon className="h-5 w-5" />
                            Nueva Disponibilidad
                        </h3>
                        
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Servicio *
                                    </label>
                                    <select
                                        required
                                        value={formData.id_servicio}
                                        onChange={(e) => setFormData(prev => ({ ...prev, id_servicio: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                    >
                                        <option value="">Seleccionar servicio</option>
                                        {servicios.filter(s => s.estado).map(servicio => (
                                            <option key={servicio.id_servicio} value={servicio.id_servicio}>
                                                {servicio.nombre}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Precio Adicional (opcional)
                                    </label>
                                    <input
                                        type="number"
                                        min="0"
                                        step="0.01"
                                        value={formData.precio_adicional}
                                        onChange={(e) => setFormData(prev => ({ ...prev, precio_adicional: parseFloat(e.target.value) || 0 }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Fecha y Hora de Inicio *
                                    </label>
                                    <input
                                        type="datetime-local"
                                        required
                                        value={formData.fecha_inicio}
                                        onChange={(e) => setFormData(prev => ({ ...prev, fecha_inicio: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Fecha y Hora de Fin *
                                    </label>
                                    <input
                                        type="datetime-local"
                                        required
                                        value={formData.fecha_fin}
                                        onChange={(e) => setFormData(prev => ({ ...prev, fecha_fin: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                    />
                                </div>
                            </div>
                            
                            <div>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={formData.disponible}
                                        onChange={(e) => setFormData(prev => ({ ...prev, disponible: e.target.checked }))}
                                        className="rounded"
                                    />
                                    <span className="text-sm font-medium text-gray-700">Disponible para reservas</span>
                                </label>
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Observaciones (opcional)
                                </label>
                                <textarea
                                    value={formData.observaciones}
                                    onChange={(e) => setFormData(prev => ({ ...prev, observaciones: e.target.value }))}
                                    rows={2}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                                    placeholder="Ej: Horario especial, condiciones especiales, etc."
                                />
                            </div>
                            
                            <div className="flex gap-2">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="btn-blue"
                                >
                                    {loading ? 'Guardando...' : 'Guardar'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowForm(false)}
                                    className="btn-gray"
                                >
                                    Cancelar
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Lista de disponibilidades */}
                {loading ? (
                    <div className="flex items-center justify-center p-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                        <span className="ml-2 text-gray-600">Cargando...</span>
                    </div>
                ) : disponibilidades.length === 0 ? (
                    <div className="text-center p-8 bg-white rounded-xl border border-gray-200">
                        <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No hay disponibilidades configuradas</h3>
                        <p className="mt-1 text-sm text-gray-500">Agrega disponibilidades para que los clientes puedan reservar tus servicios.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {disponibilidades.map((disp) => (
                            <div key={disp.id_disponibilidad} className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                                <div className="flex justify-between items-start">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-3">
                                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                                                disp.disponible 
                                                    ? 'bg-green-100 text-green-800' 
                                                    : 'bg-red-100 text-red-800'
                                            }`}>
                                                {disp.disponible ? 'Disponible' : 'No disponible'}
                                            </span>
                                            {disp.precio_adicional && disp.precio_adicional > 0 && (
                                                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                                                    +₲{disp.precio_adicional.toLocaleString()}
                                                </span>
                                            )}
                                            <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
                                                {disp.servicio_nombre}
                                            </span>
                                        </div>
                                        
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <p className="text-sm font-medium text-gray-500 mb-1">📅 Fecha</p>
                                                <p className="text-gray-900">{formatDate(disp.fecha_inicio)}</p>
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-gray-500 mb-1">🕐 Horario</p>
                                                <p className="text-gray-900">
                                                    {formatTime(disp.fecha_inicio)} - {formatTime(disp.fecha_fin)}
                                                </p>
                                            </div>
                                        </div>
                                        
                                        {disp.observaciones && (
                                            <div className="mt-3">
                                                <p className="text-sm font-medium text-gray-500 mb-1">📝 Observaciones</p>
                                                <p className="text-gray-700">{disp.observaciones}</p>
                                            </div>
                                        )}
                                    </div>
                                    
                                    <button
                                        onClick={() => handleDelete(disp.id_disponibilidad!)}
                                        className="text-red-600 hover:text-red-800 p-2 rounded-lg hover:bg-red-50 transition-colors"
                                        title="Eliminar disponibilidad"
                                    >
                                        <TrashIcon className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProviderAgendaPage;
