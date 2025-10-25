import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { buildApiUrl, getJsonHeaders } from '../config/api';

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
  const [showModal, setShowModal] = useState(false);
  const [modalData, setModalData] = useState<{reservaId: number, accion: string, observacion: string} | null>(null);
  const [filtroEstado, setFiltroEstado] = useState<string>('todos');
  const [filtroFecha, setFiltroFecha] = useState<string>('');
  const [busqueda, setBusqueda] = useState<string>('');
  const [accionLoading, setAccionLoading] = useState<number | null>(null);
  const [mensajeExito, setMensajeExito] = useState<string | null>(null);
  const [sincronizando, setSincronizando] = useState(false);

  // Debug: Verificar que el componente se está cargando
  console.log('🔍 ReservasPage cargado - activeTab:', activeTab);

  // Usar la configuración centralizada de API

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
      const response = await fetch(buildApiUrl('/reservas/mis-reservas'), {
        headers: getJsonHeaders(),
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

    const response = await fetch(buildApiUrl('/reservas/reservas-proveedor'), {
      headers: getJsonHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error al cargar reservas del proveedor');
    }

    const data = await response.json();
    setReservas(data);
  };

  const loadDisponibilidades = async () => {
    if (!user) return;

    const response = await fetch(buildApiUrl('/disponibilidades'), {
      headers: getJsonHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error al cargar disponibilidades');
    }

    const data = await response.json();
    setDisponibilidades(data);
  };

  const actualizarEstadoReserva = async (reservaId: number, nuevoEstado: string, observacion?: string) => {
    try {
      if (!user) return;

      setAccionLoading(reservaId);
      setError(null);

      // Usar endpoint específico para cancelación
      const endpoint = nuevoEstado === 'cancelada' ? `/reservas/${reservaId}/cancelar` : `/reservas/${reservaId}/estado`;
      const body = nuevoEstado === 'cancelada' 
        ? { motivo: observacion || '' }
        : { nuevo_estado: nuevoEstado, observacion: observacion || '' };

      const response = await fetch(buildApiUrl(endpoint), {
        method: 'PUT',
        headers: getJsonHeaders(),
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al actualizar estado');
      }

      const result = await response.json();
      console.log('Estado actualizado:', result);

      // Mensaje específico para cancelación
      if (nuevoEstado === 'cancelada') {
        setMensajeExito('✅ Reserva cancelada - Los cambios se sincronizarán automáticamente');
      } else {
        setMensajeExito(`Reserva ${nuevoEstado} exitosamente`);
      }
      setTimeout(() => setMensajeExito(null), 5000);

      // Refetch inmediato para sincronización
      setSincronizando(true);
      await loadData();
      setSincronizando(false);
      setShowModal(false);
      setModalData(null);
    } catch (err) {
      setError('Error al actualizar el estado de la reserva');
      console.error('Error:', err);
    } finally {
      setAccionLoading(null);
    }
  };

  const handleAccionReserva = (reservaId: number, accion: string) => {
    // Validaciones previas
    if (accionLoading === reservaId) {
      return; // Ya está procesando
    }
    
    setModalData({
      reservaId,
      accion,
      observacion: ''
    });
    setShowModal(true);
  };

  const confirmarAccion = () => {
    if (!modalData) return;
    
    // Validaciones del modal
    if (modalData.accion === 'cancelada' && !modalData.observacion.trim()) {
      setError('Debés ingresar un motivo para cancelar la reserva');
      return;
    }
    
    if (modalData.accion === 'rechazado' && !modalData.observacion.trim()) {
      setError('Es recomendable agregar una observación al rechazar una reserva');
      return;
    }
    
    if (modalData.accion === 'concluido' && !modalData.observacion.trim()) {
      setError('Es recomendable agregar una observación al marcar como concluido');
      return;
    }
    
    actualizarEstadoReserva(modalData.reservaId, modalData.accion, modalData.observacion);
  };

  const filtrarReservas = (reservas: Reserva[]) => {
    return reservas.filter(reserva => {
      // Filtro por estado
      if (filtroEstado !== 'todos' && reserva.estado !== filtroEstado) {
        return false;
      }
      
      // Filtro por fecha
      if (filtroFecha && reserva.fecha !== filtroFecha) {
        return false;
      }
      
      // Filtro por búsqueda
      if (busqueda && !reserva.descripcion.toLowerCase().includes(busqueda.toLowerCase()) &&
          !(reserva.servicio?.nombre || '').toLowerCase().includes(busqueda.toLowerCase())) {
        return false;
      }
      
      return true;
    });
  };

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'pendiente':
        return 'bg-yellow-100 text-yellow-800';
      case 'aprobado':
        return 'bg-green-100 text-green-800';
      case 'rechazado':
        return 'bg-red-100 text-red-800';
      case 'concluido':
        return 'bg-blue-100 text-blue-800';
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
        
        {/* Debug: Mostrar información de las pestañas */}
        <div className="mb-4 p-4 bg-yellow-100 border border-yellow-300 rounded-md">
          <h4 className="font-medium text-yellow-800">Debug - Pestañas:</h4>
          <p className="text-sm text-yellow-700">Active Tab: {activeTab}</p>
          <p className="text-sm text-yellow-700">User: {user?.email || 'No user'}</p>
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

        {mensajeExito && (
          <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4 animate-fade-in">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Éxito</h3>
                <div className="mt-2 text-sm text-green-700">{mensajeExito}</div>
              </div>
            </div>
          </div>
        )}

        {/* Indicador de sincronización */}
        {sincronizando && (
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-md p-4 animate-fade-in">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-3"></div>
              <div className="text-sm text-blue-700">
                Sincronizando cambios con el servidor...
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
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Reservas de Mis Servicios
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setFiltroEstado('todos')}
                    className={`px-3 py-1 rounded text-sm ${
                      filtroEstado === 'todos' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Todos
                  </button>
                  <button
                    onClick={() => setFiltroEstado('pendiente')}
                    className={`px-3 py-1 rounded text-sm ${
                      filtroEstado === 'pendiente' 
                        ? 'bg-yellow-600 text-white' 
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Pendientes
                  </button>
                  <button
                    onClick={() => setFiltroEstado('aprobado')}
                    className={`px-3 py-1 rounded text-sm ${
                      filtroEstado === 'aprobado' 
                        ? 'bg-green-600 text-white' 
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Aprobadas
                  </button>
                  <button
                    onClick={() => setFiltroEstado('rechazado')}
                    className={`px-3 py-1 rounded text-sm ${
                      filtroEstado === 'rechazado' 
                        ? 'bg-red-600 text-white' 
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Rechazadas
                  </button>
                  <button
                    onClick={() => setFiltroEstado('concluido')}
                    className={`px-3 py-1 rounded text-sm ${
                      filtroEstado === 'concluido' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Concluidas
                  </button>
                </div>
              </div>
              
              {/* Controles de búsqueda y filtros */}
              <div className="mb-4 flex space-x-4">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Buscar por descripción o servicio..."
                    value={busqueda}
                    onChange={(e) => setBusqueda(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <input
                    type="date"
                    value={filtroFecha}
                    onChange={(e) => setFiltroFecha(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  onClick={() => {
                    setFiltroEstado('todos');
                    setFiltroFecha('');
                    setBusqueda('');
                  }}
                  className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
                >
                  Limpiar
                </button>
              </div>
              
              {/* Contador de resultados */}
              {reservas.length > 0 && (
                <div className="mb-4 text-sm text-gray-600">
                  Mostrando {filtrarReservas(reservas).length} de {reservas.length} reservas
                  {filtroEstado !== 'todos' && ` (filtradas por estado: ${filtroEstado})`}
                  {busqueda && ` (búsqueda: "${busqueda}")`}
                  {filtroFecha && ` (fecha: ${filtroFecha})`}
                </div>
              )}
              
              {reservas.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No hay reservas para tus servicios</p>
              ) : filtrarReservas(reservas).length === 0 ? (
                <p className="text-gray-500 text-center py-8">No hay reservas que coincidan con los filtros aplicados</p>
              ) : (
                <div className="space-y-4">
                  {filtrarReservas(reservas).map((reserva) => (
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
                                onClick={() => handleAccionReserva(reserva.id_reserva, 'aprobado')}
                                disabled={accionLoading === reserva.id_reserva}
                                className={`bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition-all duration-200 ${
                                  accionLoading === reserva.id_reserva 
                                    ? 'opacity-50 cursor-not-allowed' 
                                    : 'hover:scale-105'
                                }`}
                              >
                                {accionLoading === reserva.id_reserva ? (
                                  <span className="flex items-center">
                                    <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Procesando...
                                  </span>
                                ) : (
                                  'Aceptar'
                                )}
                              </button>
                              <button
                                onClick={() => handleAccionReserva(reserva.id_reserva, 'cancelada')}
                                disabled={accionLoading === reserva.id_reserva}
                                className={`bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition-all duration-200 ${
                                  accionLoading === reserva.id_reserva 
                                    ? 'opacity-50 cursor-not-allowed' 
                                    : 'hover:scale-105'
                                }`}
                              >
                                {accionLoading === reserva.id_reserva ? (
                                  <span className="flex items-center">
                                    <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Procesando...
                                  </span>
                                ) : (
                                  'Cancelar'
                                )}
                              </button>
                            </div>
                          )}
                          {reserva.estado === 'aprobado' && (
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleAccionReserva(reserva.id_reserva, 'concluido')}
                                disabled={accionLoading === reserva.id_reserva}
                                className={`bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-all duration-200 ${
                                  accionLoading === reserva.id_reserva 
                                    ? 'opacity-50 cursor-not-allowed' 
                                    : 'hover:scale-105'
                                }`}
                              >
                                {accionLoading === reserva.id_reserva ? (
                                  <span className="flex items-center">
                                    <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Procesando...
                                  </span>
                                ) : (
                                  'Marcar como Concluido'
                                )}
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

        {/* Modal de confirmación */}
        {showModal && modalData && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {modalData.accion === 'aprobado' ? 'Aprobar Reserva' : 
                   modalData.accion === 'rechazado' ? 'Rechazar Reserva' : 
                   modalData.accion === 'cancelada' ? 'Cancelar Reserva' :
                   modalData.accion === 'concluido' ? 'Marcar como Concluido' : 'Confirmar Acción'}
                </h3>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {modalData.accion === 'cancelada' ? 'Motivo de cancelación (obligatorio)' : 
                     modalData.accion === 'rechazado' || modalData.accion === 'concluido' ? 'Observación (recomendado)' : 
                     'Observación (opcional)'}:
                  </label>
                  <textarea
                    value={modalData.observacion}
                    onChange={(e) => setModalData({...modalData, observacion: e.target.value})}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                      modalData.accion === 'cancelada' && !modalData.observacion.trim()
                        ? 'border-red-300 focus:ring-red-500'
                        : (modalData.accion === 'rechazado' || modalData.accion === 'concluido') && !modalData.observacion.trim()
                        ? 'border-yellow-300 focus:ring-yellow-500'
                        : 'border-gray-300 focus:ring-blue-500'
                    }`}
                    rows={3}
                    placeholder={
                      modalData.accion === 'cancelada'
                        ? 'Debés ingresar un motivo para cancelar la reserva...'
                        : modalData.accion === 'rechazado' 
                        ? 'Explica por qué rechazas esta reserva...'
                        : modalData.accion === 'concluido'
                        ? 'Describe cómo se completó el servicio...'
                        : 'Agrega una observación sobre esta acción...'
                    }
                  />
                  {modalData.accion === 'cancelada' && !modalData.observacion.trim() && (
                    <p className="mt-1 text-sm text-red-600">
                      ❌ Debés ingresar un motivo para cancelar la reserva
                    </p>
                  )}
                  {(modalData.accion === 'rechazado' || modalData.accion === 'concluido') && !modalData.observacion.trim() && (
                    <p className="mt-1 text-sm text-yellow-600">
                      ⚠️ Es recomendable agregar una observación para esta acción
                    </p>
                  )}
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      setShowModal(false);
                      setModalData(null);
                    }}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={confirmarAccion}
                    className={`px-4 py-2 text-white rounded-md ${
                      modalData.accion === 'rechazado' || modalData.accion === 'cancelada' ? 'bg-red-600 hover:bg-red-700' :
                      modalData.accion === 'aprobado' ? 'bg-green-600 hover:bg-green-700' :
                      'bg-blue-600 hover:bg-blue-700'
                    }`}
                  >
                    {modalData.accion === 'aprobado' ? 'Aprobar' : 
                     modalData.accion === 'rechazado' ? 'Rechazar' : 
                     modalData.accion === 'cancelada' ? 'Cancelar' :
                     modalData.accion === 'concluido' ? 'Marcar como Concluido' : 'Confirmar'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReservasPage;
