import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface Reserva {
  id_reserva: number;
  id_servicio: number;
  id_usuario: string;
  descripcion: string;
  observacion?: string;
  fecha: string;
  estado: string;
  created_at: string;
  servicio?: {
    nombre: string;
    precio: number;
    imagen?: string;
  };
}

interface Disponibilidad {
  id_disponibilidad: number;
  id_servicio: number;
  fecha_inicio: string;
  fecha_fin: string;
  disponible: boolean;
  precio_adicional?: number;
  observaciones?: string;
}

const ReservasPage: React.FC = () => {
  const { user } = useAuth();
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [disponibilidades, setDisponibilidades] = useState<Disponibilidad[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'mis-reservas' | 'reservas-proveedor' | 'agenda'>('mis-reservas');

  // Usar la configuración centralizada de API
  const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000' 
    : 'https://backend-production-249d.up.railway.app';

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user, activeTab]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (activeTab === 'mis-reservas') {
        await loadMisReservas();
      } else if (activeTab === 'reservas-proveedor') {
        await loadReservasProveedor();
      } else if (activeTab === 'agenda') {
        await loadDisponibilidades();
      }
    } catch (err) {
      setError('Error al cargar los datos');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadMisReservas = async () => {
    if (!user) return;

    try {
      const response = await fetch(`${API_URL}/api/v1/reservas`, {
        headers: {
          'Authorization': `Bearer ${user.accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al cargar reservas');
      }

      const data = await response.json();
      setReservas(data);
    } catch (error) {
      console.error('Error al cargar reservas:', error);
      setError('Error al cargar las reservas');
    }
  };

  const loadReservasProveedor = async () => {
    if (!user) return;

    const response = await fetch(`${API_URL}/api/v1/reservas/proveedor`, {
      headers: {
        'Authorization': `Bearer ${user.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Error al cargar reservas del proveedor');
    }

    const data = await response.json();
    setReservas(data);
  };

  const loadDisponibilidades = async () => {
    if (!user) return;

    const response = await fetch(`${API_URL}/api/v1/disponibilidades`, {
      headers: {
        'Authorization': `Bearer ${user.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Error al cargar disponibilidades');
    }

    const data = await response.json();
    setDisponibilidades(data);
  };

  const actualizarEstadoReserva = async (reservaId: number, nuevoEstado: string) => {
    try {
      if (!user) return;

      const response = await fetch(`${API_URL}/api/v1/reservas/${reservaId}/estado?nuevo_estado=${nuevoEstado}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${user.accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al actualizar estado');
      }

      // Recargar datos
      await loadData();
    } catch (err) {
      setError('Error al actualizar el estado de la reserva');
      console.error('Error:', err);
    }
  };

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'pendiente':
        return 'bg-yellow-100 text-yellow-800';
      case 'confirmada':
        return 'bg-green-100 text-green-800';
      case 'cancelada':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando reservas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Reservas</h1>
          <p className="mt-2 text-gray-600">Administra tus reservas y disponibilidades</p>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('mis-reservas')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'mis-reservas'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Mis Reservas
            </button>
            <button
              onClick={() => setActiveTab('reservas-proveedor')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'reservas-proveedor'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Reservas de Mis Servicios
            </button>
            <button
              onClick={() => setActiveTab('agenda')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'agenda'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Mi Agenda
            </button>
          </nav>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Contenido de las tabs */}
        {activeTab === 'mis-reservas' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Mis Reservas
              </h3>
              {reservas.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No tienes reservas aún</p>
              ) : (
                <div className="space-y-4">
                  {reservas.map((reserva) => (
                    <div key={reserva.id_reserva} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="text-lg font-medium text-gray-900">
                            {reserva.servicio?.nombre || 'Servicio'}
                          </h4>
                          <p className="text-gray-600 mt-1">{reserva.descripcion}</p>
                          <p className="text-sm text-gray-500 mt-2">
                            Fecha: {formatFecha(reserva.fecha)}
                          </p>
                          {reserva.observacion && (
                            <p className="text-sm text-gray-500 mt-1">
                              Observación: {reserva.observacion}
                            </p>
                          )}
                        </div>
                        <div className="ml-4">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getEstadoColor(reserva.estado)}`}>
                            {reserva.estado}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'reservas-proveedor' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Reservas de Mis Servicios
              </h3>
              {reservas.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No hay reservas para tus servicios</p>
              ) : (
                <div className="space-y-4">
                  {reservas.map((reserva) => (
                    <div key={reserva.id_reserva} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="text-lg font-medium text-gray-900">
                            {reserva.servicio?.nombre || 'Servicio'}
                          </h4>
                          <p className="text-gray-600 mt-1">{reserva.descripcion}</p>
                          <p className="text-sm text-gray-500 mt-2">
                            Fecha: {formatFecha(reserva.fecha)}
                          </p>
                          {reserva.observacion && (
                            <p className="text-sm text-gray-500 mt-1">
                              Observación: {reserva.observacion}
                            </p>
                          )}
                        </div>
                        <div className="ml-4 flex flex-col items-end space-y-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getEstadoColor(reserva.estado)}`}>
                            {reserva.estado}
                          </span>
                          {reserva.estado === 'pendiente' && (
                            <div className="flex space-x-2">
                              <button
                                onClick={() => actualizarEstadoReserva(reserva.id_reserva, 'confirmada')}
                                className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                              >
                                Confirmar
                              </button>
                              <button
                                onClick={() => actualizarEstadoReserva(reserva.id_reserva, 'cancelada')}
                                className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                              >
                                Cancelar
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'agenda' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Mi Agenda
                </h3>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                  Agregar Disponibilidad
                </button>
              </div>
              {disponibilidades.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No tienes disponibilidades configuradas</p>
              ) : (
                <div className="space-y-4">
                  {disponibilidades.map((disponibilidad) => (
                    <div key={disponibilidad.id_disponibilidad} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="text-sm text-gray-500">
                            {formatFecha(disponibilidad.fecha_inicio)} - {formatFecha(disponibilidad.fecha_fin)}
                          </p>
                          {disponibilidad.precio_adicional && disponibilidad.precio_adicional > 0 && (
                            <p className="text-sm text-green-600 mt-1">
                              Precio adicional: ${disponibilidad.precio_adicional}
                            </p>
                          )}
                          {disponibilidad.observaciones && (
                            <p className="text-sm text-gray-500 mt-1">
                              {disponibilidad.observaciones}
                            </p>
                          )}
                        </div>
                        <div className="ml-4">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            disponibilidad.disponible ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {disponibilidad.disponible ? 'Disponible' : 'No disponible'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReservasPage;
