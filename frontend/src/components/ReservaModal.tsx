import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface Servicio {
  id_servicio: number;
  nombre: string;
  descripcion: string;
  precio: number;
  imagen?: string;
  categoria?: {
    nombre: string;
  };
}

interface Disponibilidad {
  id_disponibilidad: number;
  fecha_inicio: string;
  fecha_fin: string;
  disponible: boolean;
  precio_adicional?: number;
  observaciones?: string;
}

interface ReservaModalProps {
  isOpen: boolean;
  onClose: () => void;
  servicio: Servicio | null;
  onReservaCreada: () => void;
}

const ReservaModal: React.FC<ReservaModalProps> = ({
  isOpen,
  onClose,
  servicio,
  onReservaCreada
}) => {
  const { user } = useAuth();
  const [disponibilidades, setDisponibilidades] = useState<Disponibilidad[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    descripcion: '',
    observacion: '',
    disponibilidad_id: ''
  });

  const API_URL = import.meta.env.VITE_API_URL || 'https://backend-production-249d.up.railway.app';

  useEffect(() => {
    if (isOpen && servicio) {
      loadDisponibilidades();
    }
  }, [isOpen, servicio]);

  const loadDisponibilidades = async () => {
    if (!servicio) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/v1/disponibilidades/servicio/${servicio.id_servicio}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al cargar disponibilidades');
      }

      const data = await response.json();
      setDisponibilidades(data);
    } catch (err) {
      setError('Error al cargar disponibilidades');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!servicio || !formData.disponibilidad_id) return;

    try {
      setLoading(true);
      setError(null);

      if (!user) {
        throw new Error('No hay sesión activa');
      }

      const disponibilidad = disponibilidades.find(d => d.id_disponibilidad.toString() === formData.disponibilidad_id);
      if (!disponibilidad) {
        throw new Error('Disponibilidad no encontrada');
      }

      const reservaData = {
        id_servicio: servicio.id_servicio,
        descripcion: formData.descripcion,
        observacion: formData.observacion || null,
        fecha: new Date(disponibilidad.fecha_inicio).toISOString().split('T')[0]
      };

      const response = await fetch(`${API_URL}/api/v1/reservas`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reservaData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear la reserva');
      }

      // Limpiar formulario
      setFormData({
        descripcion: '',
        observacion: '',
        disponibilidad_id: ''
      });

      onReservaCreada();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear la reserva');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calcularPrecioTotal = () => {
    if (!servicio || !formData.disponibilidad_id) return servicio?.precio || 0;
    
    const disponibilidad = disponibilidades.find(d => d.id_disponibilidad.toString() === formData.disponibilidad_id);
    if (!disponibilidad) return servicio.precio;
    
    return servicio.precio + (disponibilidad.precio_adicional || 0);
  };

  if (!isOpen || !servicio) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Reservar: {servicio.nombre}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Información del servicio */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Información del Servicio</h4>
              <p className="text-sm text-gray-600 mb-2">{servicio.descripcion}</p>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">
                  {servicio.categoria?.nombre}
                </span>
                <span className="font-medium text-gray-900">
                  ${servicio.precio}
                </span>
              </div>
            </div>

            {/* Selección de disponibilidad */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selecciona un horario disponible
              </label>
              {loading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-sm text-gray-600">Cargando horarios...</p>
                </div>
              ) : disponibilidades.length === 0 ? (
                <p className="text-sm text-gray-500 py-4 text-center">
                  No hay horarios disponibles para este servicio
                </p>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {disponibilidades.map((disponibilidad) => (
                    <label key={disponibilidad.id_disponibilidad} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="radio"
                        name="disponibilidad_id"
                        value={disponibilidad.id_disponibilidad}
                        checked={formData.disponibilidad_id === disponibilidad.id_disponibilidad.toString()}
                        onChange={(e) => setFormData({ ...formData, disponibilidad_id: e.target.value })}
                        className="mr-3"
                      />
                      <div className="flex-1">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-gray-900">
                            {formatFecha(disponibilidad.fecha_inicio)} - {formatFecha(disponibilidad.fecha_fin)}
                          </span>
                          {disponibilidad.precio_adicional && disponibilidad.precio_adicional > 0 && (
                            <span className="text-sm text-green-600">
                              +${disponibilidad.precio_adicional}
                            </span>
                          )}
                        </div>
                        {disponibilidad.observaciones && (
                          <p className="text-xs text-gray-500 mt-1">
                            {disponibilidad.observaciones}
                          </p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Descripción de la reserva */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descripción de la reserva *
              </label>
              <textarea
                value={formData.descripcion}
                onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                required
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe qué necesitas..."
              />
            </div>

            {/* Observaciones adicionales */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Observaciones adicionales
              </label>
              <textarea
                value={formData.observacion}
                onChange={(e) => setFormData({ ...formData, observacion: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Cualquier información adicional..."
              />
            </div>

            {/* Precio total */}
            {formData.disponibilidad_id && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-900">Precio total:</span>
                  <span className="text-lg font-bold text-blue-600">
                    ${calcularPrecioTotal()}
                  </span>
                </div>
              </div>
            )}

            {/* Botones */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading || !formData.disponibilidad_id || !formData.descripcion}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creando...' : 'Crear Reserva'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ReservaModal;
