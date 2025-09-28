import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface Disponibilidad {
    id_disponibilidad?: number;
    id_servicio: number;
    fecha_inicio: string;
    fecha_fin: string;
    disponible: boolean;
    precio_adicional?: number;
    observaciones?: string;
}

interface AvailabilityManagerProps {
    servicioId: number;
    servicioNombre: string;
}

const AvailabilityManager: React.FC<AvailabilityManagerProps> = ({ servicioId, servicioNombre }) => {
    const { user } = useAuth();
    const [disponibilidades, setDisponibilidades] = useState<Disponibilidad[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    const [formData, setFormData] = useState({
        fecha_inicio: '',
        fecha_fin: '',
        disponible: true,
        precio_adicional: 0,
        observaciones: ''
    });

    const API_URL = import.meta.env.VITE_API_URL || 'https://backend-production-249d.up.railway.app';

    // Cargar disponibilidades del servicio
    useEffect(() => {
        loadDisponibilidades();
    }, [servicioId]);

    const loadDisponibilidades = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`${API_URL}/api/v1/disponibilidades/servicio/${servicioId}`, {
                headers: {
                    'Authorization': `Bearer ${user?.accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Error al cargar disponibilidades');
            }

            const data = await response.json();
            setDisponibilidades(data);
        } catch (err) {
            console.error('Error al cargar disponibilidades:', err);
            setError(err instanceof Error ? err.message : 'Error desconocido');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        try {
            setLoading(true);
            setError(null);

            const disponibilidadData = {
                id_servicio: servicioId,
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

    return (
        <div className="bg-white border border-slate-200 rounded-xl p-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-900">
                    📅 Disponibilidades - {servicioNombre}
                </h3>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="btn-blue text-sm"
                >
                    {showForm ? 'Cancelar' : '+ Agregar Disponibilidad'}
                </button>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                    <p className="text-red-800">⚠️ {error}</p>
                </div>
            )}

            {/* Formulario para agregar disponibilidad */}
            {showForm && (
                <form onSubmit={handleSubmit} className="bg-slate-50 border border-slate-200 rounded-lg p-4 mb-6">
                    <h4 className="font-medium text-slate-900 mb-4">Nueva Disponibilidad</h4>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Fecha y Hora de Inicio
                            </label>
                            <input
                                type="datetime-local"
                                required
                                value={formData.fecha_inicio}
                                onChange={(e) => setFormData(prev => ({ ...prev, fecha_inicio: e.target.value }))}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                            />
                        </div>
                        
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Fecha y Hora de Fin
                            </label>
                            <input
                                type="datetime-local"
                                required
                                value={formData.fecha_fin}
                                onChange={(e) => setFormData(prev => ({ ...prev, fecha_fin: e.target.value }))}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                            />
                        </div>
                        
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Precio Adicional (opcional)
                            </label>
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={formData.precio_adicional}
                                onChange={(e) => setFormData(prev => ({ ...prev, precio_adicional: parseFloat(e.target.value) || 0 }))}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                            />
                        </div>
                        
                        <div>
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={formData.disponible}
                                    onChange={(e) => setFormData(prev => ({ ...prev, disponible: e.target.checked }))}
                                    className="rounded"
                                />
                                <span className="text-sm font-medium text-slate-700">Disponible</span>
                            </label>
                        </div>
                    </div>
                    
                    <div className="mt-4">
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Observaciones (opcional)
                        </label>
                        <textarea
                            value={formData.observaciones}
                            onChange={(e) => setFormData(prev => ({ ...prev, observaciones: e.target.value }))}
                            rows={2}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                            placeholder="Ej: Horario especial, condiciones especiales, etc."
                        />
                    </div>
                    
                    <div className="flex gap-2 mt-4">
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
            )}

            {/* Lista de disponibilidades */}
            {loading ? (
                <div className="flex items-center justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                    <span className="ml-2 text-slate-600">Cargando...</span>
                </div>
            ) : disponibilidades.length === 0 ? (
                <div className="text-center p-8">
                    <p className="text-slate-500">No hay disponibilidades configuradas para este servicio.</p>
                    <p className="text-sm text-slate-400 mt-2">Agrega disponibilidades para que los clientes puedan reservar.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {disponibilidades.map((disp) => (
                        <div key={disp.id_disponibilidad} className="bg-white border border-slate-200 rounded-lg p-4">
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                            disp.disponible 
                                                ? 'bg-green-100 text-green-800' 
                                                : 'bg-red-100 text-red-800'
                                        }`}>
                                            {disp.disponible ? 'Disponible' : 'No disponible'}
                                        </span>
                                        {disp.precio_adicional && disp.precio_adicional > 0 && (
                                            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                                                +₲{disp.precio_adicional.toLocaleString()}
                                            </span>
                                        )}
                                    </div>
                                    
                                    <div className="text-sm text-slate-600">
                                        <p><strong>Inicio:</strong> {formatDateTime(disp.fecha_inicio)}</p>
                                        <p><strong>Fin:</strong> {formatDateTime(disp.fecha_fin)}</p>
                                        {disp.observaciones && (
                                            <p><strong>Observaciones:</strong> {disp.observaciones}</p>
                                        )}
                                    </div>
                                </div>
                                
                                <button
                                    onClick={() => handleDelete(disp.id_disponibilidad!)}
                                    className="text-red-600 hover:text-red-800 text-sm font-medium"
                                >
                                    Eliminar
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AvailabilityManager;
