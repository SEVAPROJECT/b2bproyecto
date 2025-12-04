// frontend/components/horario/HorarioTrabajoManager.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { buildApiUrl } from '../../config/api';
import { formatISODateToDDMMYYYY, parseLocalDate, formatDateToDDMMYYYY } from '../../utils/dateUtils';
import { 
  ClockIcon, 
  CalendarDaysIcon, 
  PlusIcon, 
  TrashIcon, 
  PencilIcon,
  CheckIcon
} from '../icons';

interface HorarioTrabajo {
  id_horario: number;
  id_proveedor: number;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  activo: boolean;
  created_at?: string;
}

interface ExcepcionHorario {
  id_excepcion: number;
  id_proveedor: number;
  fecha: string;
  tipo: 'cerrado' | 'horario_especial';
  hora_inicio?: string;
  hora_fin?: string;
  motivo?: string;
  created_at?: string;
}

const DIAS_SEMANA = [
  'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'
];

/**
 * Función helper para validar que la hora de inicio sea menor que la hora de fin
 * @param horaInicio - Hora de inicio en formato HH:MM
 * @param horaFin - Hora de fin en formato HH:MM
 * @returns Objeto con isValid (boolean) y errorMessage (string | null)
 */
const validateHorarioTimes = (horaInicio: string, horaFin: string): { isValid: boolean; errorMessage: string | null } => {
  if (!horaInicio || !horaFin) {
    return { isValid: false, errorMessage: 'Ambas horas son requeridas' };
  }

  const [horaInicioH, horaInicioM] = horaInicio.split(':').map(Number);
  const [horaFinH, horaFinM] = horaFin.split(':').map(Number);

  const inicioMinutos = horaInicioH * 60 + horaInicioM;
  const finMinutos = horaFinH * 60 + horaFinM;

  if (inicioMinutos >= finMinutos) {
    return {
      isValid: false,
      errorMessage: `La hora de inicio (${horaInicio}) debe ser menor que la hora de fin (${horaFin}). Por favor, verifica que el horario de inicio sea anterior al horario de fin.`
    };
  }

  return { isValid: true, errorMessage: null };
};


const HorarioTrabajoManager: React.FC = () => {
  const { user } = useAuth();
  const [horarios, setHorarios] = useState<HorarioTrabajo[]>([]);
  const [excepciones, setExcepciones] = useState<ExcepcionHorario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showExcepcionForm, setShowExcepcionForm] = useState(false);
  const [showConfiguracionCompleta, setShowConfiguracionCompleta] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [errorHorario, setErrorHorario] = useState<string | null>(null);
  const [errorExcepcion, setErrorExcepcion] = useState<string | null>(null);

  // Estados para el formulario de horario
  const [formData, setFormData] = useState({
    dia_semana: 0,
    hora_inicio: '09:00',
    hora_fin: '17:00',
    activo: true
  });

  // Estados para el formulario de excepción
  const [excepcionData, setExcepcionData] = useState({
    fecha: '',
    tipo: 'cerrado' as 'cerrado' | 'horario_especial',
    hora_inicio: '09:00',
    hora_fin: '17:00',
    motivo: ''
  });

  useEffect(() => {
    loadHorarios();
    loadExcepciones();
  }, []);

  const loadHorarios = async () => {
    try {
      const response = await fetch(buildApiUrl('/horario-trabajo/'), {
        headers: {
          'Authorization': `Bearer ${user?.accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setHorarios(data);
      } else {
        console.error('Error al cargar horarios:', response.status);
      }
    } catch (error) {
      console.error('Error al cargar horarios:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadExcepciones = async () => {
    try {
      const response = await fetch(buildApiUrl('/horario-trabajo/excepciones'), {
        headers: {
          'Authorization': `Bearer ${user?.accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setExcepciones(data);
      }
    } catch (error) {
      console.error('Error al cargar excepciones:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validar horarios antes de enviar
    const validation = validateHorarioTimes(formData.hora_inicio, formData.hora_fin);
    if (!validation.isValid) {
      setErrorHorario(validation.errorMessage);
      return;
    }
    
    setErrorHorario(null);
    
    try {
      const url = editingId 
        ? buildApiUrl(`/horario-trabajo/${editingId}`)
        : buildApiUrl('/horario-trabajo/');
      
      const method = editingId ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${user?.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        await loadHorarios();
        setShowForm(false);
        setEditingId(null);
        setErrorHorario(null);
        setFormData({ dia_semana: 0, hora_inicio: '09:00', hora_fin: '17:00', activo: true });
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        setErrorHorario(errorData.detail || 'Error al guardar horario');
        console.error('Error al guardar horario:', errorData);
        alert('Error al guardar horario: ' + (errorData.detail || 'Error desconocido'));
      }
    } catch (error) {
      setErrorHorario('Error de conexión. Por favor, intenta nuevamente.');
      console.error('Error al guardar horario:', error);
    }
  };

  const handleExcepcionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validar que se haya seleccionado una fecha
    if (!excepcionData.fecha) {
      setErrorExcepcion('Por favor, selecciona una fecha para la excepción.');
      return;
    }
    
    // Validar horarios si es horario_especial
    if (excepcionData.tipo === 'horario_especial') {
      const validation = validateHorarioTimes(excepcionData.hora_inicio, excepcionData.hora_fin);
      if (!validation.isValid) {
        setErrorExcepcion(validation.errorMessage);
        return;
      }
    }
    
    setErrorExcepcion(null);
    
    try {
      const response = await fetch(buildApiUrl('/horario-trabajo/excepciones'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(excepcionData),
      });

      if (response.ok) {
        await loadExcepciones();
        setShowExcepcionForm(false);
        setErrorExcepcion(null);
        setExcepcionData({ 
          fecha: '', 
          tipo: 'cerrado', 
          hora_inicio: '09:00', 
          hora_fin: '17:00', 
          motivo: '' 
        });
      } else {
        const errorData = await response.json();
        setErrorExcepcion(errorData.detail || 'Error al guardar excepción');
        console.error('Error al guardar excepción:', errorData);
      }
    } catch (error) {
      setErrorExcepcion('Error de conexión. Por favor, intenta nuevamente.');
      console.error('Error al guardar excepción:', error);
    }
  };

  const handleEdit = (horario: HorarioTrabajo) => {
    setFormData({
      dia_semana: horario.dia_semana,
      hora_inicio: horario.hora_inicio,
      hora_fin: horario.hora_fin,
      activo: horario.activo
    });
    setEditingId(horario.id_horario);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este horario?')) return;

    try {
      const response = await fetch(buildApiUrl(`/horario-trabajo/${id}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${user?.accessToken}`,
        },
      });

      if (response.ok || response.status === 204) {
        await loadHorarios();
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Error al eliminar horario:', errorData.detail || 'Error desconocido');
        alert('Error al eliminar horario: ' + (errorData.detail || 'Error desconocido'));
      }
    } catch (error) {
      console.error('Error al eliminar horario:', error);
      alert('Error al eliminar horario. Por favor, intenta nuevamente.');
    }
  };

  const handleDeleteExcepcion = async (id: number) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta excepción?')) return;

    try {
      console.log('🔍 [DELETE] Intentando eliminar excepción con ID:', id);
      const url = buildApiUrl(`/horario-trabajo/excepciones/${id}`);
      console.log('🔍 [DELETE] URL:', url);
      
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${user?.accessToken}`,
        },
      });

      console.log('🔍 [DELETE] Response status:', response.status);
      
      if (response.ok || response.status === 204) {
        await loadExcepciones();
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ [DELETE] Error al eliminar excepción:', errorData);
        console.error('❌ [DELETE] ID enviado:', id);
        alert('Error al eliminar excepción: ' + (errorData.detail || 'Error desconocido'));
      }
    } catch (error) {
      console.error('❌ [DELETE] Error al eliminar excepción:', error);
      alert('Error al eliminar excepción. Por favor, intenta nuevamente.');
    }
  };

  // Estado para la configuración completa
  const [configuracionCompleta, setConfiguracionCompleta] = useState(
    DIAS_SEMANA.map((nombreDia, index) => ({
      dia_semana: index,
      nombreDia: nombreDia,
      hora_inicio: index < 5 ? '09:00' : index === 5 ? '10:00' : '09:00', // Lunes-Viernes 9:00, Sábado 10:00, Domingo 9:00
      hora_fin: index < 5 ? '17:00' : index === 5 ? '14:00' : '17:00', // Lunes-Viernes 17:00, Sábado 14:00, Domingo 17:00
      activo: index < 6 // Lunes a Sábado activos por defecto, Domingo inactivo
    }))
  );

  const handleConfiguracionCompletaChange = (index: number, field: string, value: any) => {
    const nuevaConfiguracion = [...configuracionCompleta];
    nuevaConfiguracion[index] = {
      ...nuevaConfiguracion[index],
      [field]: value
    };
    setConfiguracionCompleta(nuevaConfiguracion);
  };


  const configurarHorarioCompleto = async () => {
    // Validar todos los horarios antes de enviar
    for (const horario of configuracionCompleta) {
      if (horario.activo) {
        const validation = validateHorarioTimes(horario.hora_inicio, horario.hora_fin);
        if (!validation.isValid) {
          alert(`Error en ${horario.nombreDia}: ${validation.errorMessage}`);
          return;
        }
      }
    }

    // Filtrar solo los horarios activos
    const horariosCompletos = configuracionCompleta
      .filter(h => h.activo)
      .map(({ nombreDia, ...horario }) => horario); // Remover nombreDia antes de enviar

    try {
      const response = await fetch(buildApiUrl('/horario-trabajo/configuracion-completa'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ horarios: horariosCompletos }),
      });

      if (response.ok) {
        await loadHorarios();
        setShowConfiguracionCompleta(false);
        alert('Horario completo configurado exitosamente');
      } else {
        const errorData = await response.json();
        alert(`Error al configurar horario completo: ${errorData.detail || 'Error desconocido'}`);
        console.error('Error al configurar horario completo:', errorData);
      }
    } catch (error) {
      console.error('Error al configurar horario completo:', error);
      alert(`Error de conexión: ${error instanceof Error ? error.message : 'Error desconocido'}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Mi Horario de Trabajo</h2>
          <p className="text-gray-600">Configura tu horario semanal. Aplica a todos tus servicios automáticamente.</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowConfiguracionCompleta(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center space-x-2"
          >
            <CheckIcon className="w-4 h-4" />
            <span>Configurar Horario Completo</span>
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Nuevo Horario</span>
          </button>
        </div>
      </div>

      {/* Formulario de Horario */}
      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">
            {editingId ? 'Editar Horario' : 'Nuevo Horario'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="dia_semana" className="block text-sm font-medium text-gray-700 mb-1">
                  Día de la Semana
                </label>
                <select
                  id="dia_semana"
                  value={formData.dia_semana}
                  onChange={(e) => setFormData({ ...formData, dia_semana: Number.parseInt(e.target.value) })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {DIAS_SEMANA.map((dia, index) => (
                    <option key={dia} value={index}>
                      {dia}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="activo" className="block text-sm font-medium text-gray-700 mb-1">
                  Activo
                </label>
                <select
                  id="activo"
                  value={formData.activo.toString()}
                  onChange={(e) => setFormData({ ...formData, activo: e.target.value === 'true' })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="true">Sí</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div>
                <label htmlFor="hora_inicio" className="block text-sm font-medium text-gray-700 mb-1">
                  Hora de Inicio
                </label>
                <input
                  id="hora_inicio"
                  type="time"
                  value={formData.hora_inicio}
                  onChange={(e) => {
                    const newHoraInicio = e.target.value;
                    setFormData({ ...formData, hora_inicio: newHoraInicio });
                    // Validar en tiempo real
                    if (formData.hora_fin) {
                      const validation = validateHorarioTimes(newHoraInicio, formData.hora_fin);
                      setErrorHorario(validation.isValid ? null : validation.errorMessage);
                    }
                  }}
                  className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errorHorario ? 'border-red-500' : 'border-gray-300'
                  }`}
                  required
                />
              </div>
              <div>
                <label htmlFor="hora_fin" className="block text-sm font-medium text-gray-700 mb-1">
                  Hora de Fin
                </label>
                <input
                  id="hora_fin"
                  type="time"
                  value={formData.hora_fin}
                  onChange={(e) => {
                    const newHoraFin = e.target.value;
                    setFormData({ ...formData, hora_fin: newHoraFin });
                    // Validar en tiempo real
                    if (formData.hora_inicio) {
                      const validation = validateHorarioTimes(formData.hora_inicio, newHoraFin);
                      setErrorHorario(validation.isValid ? null : validation.errorMessage);
                    }
                  }}
                  className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errorHorario ? 'border-red-500' : 'border-gray-300'
                  }`}
                  required
                />
              </div>
            </div>
            {errorHorario && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {errorHorario}
              </div>
            )}
            <div className="flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setFormData({ dia_semana: 0, hora_inicio: '09:00', hora_fin: '17:00', activo: true });
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                disabled={!!errorHorario}
              >
                {editingId ? 'Actualizar' : 'Crear'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Lista de Horarios */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold">Horarios Configurados</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {horarios.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <CalendarDaysIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No tienes horarios configurados</p>
              <p className="text-sm">Configura tu horario para que los clientes puedan hacer reservas</p>
            </div>
          ) : (
            horarios.map((horario) => (
              <div key={horario.id_horario} className="p-6 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <ClockIcon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {DIAS_SEMANA[horario.dia_semana]}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {horario.hora_inicio} - {horario.hora_fin}
                    </p>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      horario.activo 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {horario.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEdit(horario)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(horario.id_horario)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Excepciones */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold">Excepciones de Horario</h3>
          <button
            onClick={() => setShowExcepcionForm(true)}
            className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 flex items-center space-x-2"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Nueva Excepción</span>
          </button>
        </div>
        
        {showExcepcionForm && (
          <div className="p-6 border-b border-gray-200">
            <h4 className="text-md font-semibold mb-4">Nueva Excepción</h4>
            <form onSubmit={handleExcepcionSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="excepcion_fecha" className="block text-sm font-medium text-gray-700 mb-1">
                    Fecha
                  </label>
                  <input
                    id="excepcion_fecha"
                    type="date"
                    value={excepcionData.fecha}
                    onChange={(e) => setExcepcionData({ ...excepcionData, fecha: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="excepcion_tipo" className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo
                  </label>
                  <select
                    id="excepcion_tipo"
                    value={excepcionData.tipo}
                    onChange={(e) => {
                      const newTipo = e.target.value as 'cerrado' | 'horario_especial';
                      setExcepcionData({ ...excepcionData, tipo: newTipo });
                      // Limpiar error si cambia a "cerrado"
                      if (newTipo === 'cerrado') {
                        setErrorExcepcion(null);
                      } else if (newTipo === 'horario_especial') {
                        // Validar inmediatamente si ya hay horarios
                        if (excepcionData.hora_inicio && excepcionData.hora_fin) {
                          const validation = validateHorarioTimes(excepcionData.hora_inicio, excepcionData.hora_fin);
                          setErrorExcepcion(validation.isValid ? null : validation.errorMessage);
                        }
                      }
                    }}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="cerrado">Día Cerrado</option>
                    <option value="horario_especial">Horario Especial</option>
                  </select>
                </div>
                {excepcionData.tipo === 'horario_especial' && (
                  <>
                    <div>
                      <label htmlFor="excepcion_hora_inicio" className="block text-sm font-medium text-gray-700 mb-1">
                        Hora de Inicio <span className="text-red-500">*</span>
                      </label>
                      <input
                        id="excepcion_hora_inicio"
                        type="time"
                        value={excepcionData.hora_inicio}
                        onChange={(e) => {
                          const newHoraInicio = e.target.value;
                          setExcepcionData({ ...excepcionData, hora_inicio: newHoraInicio });
                          // Validar en tiempo real
                          if (excepcionData.hora_fin) {
                            const validation = validateHorarioTimes(newHoraInicio, excepcionData.hora_fin);
                            setErrorExcepcion(validation.isValid ? null : validation.errorMessage);
                          }
                        }}
                        className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                          errorExcepcion ? 'border-red-500' : 'border-gray-300'
                        }`}
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="excepcion_hora_fin" className="block text-sm font-medium text-gray-700 mb-1">
                        Hora de Fin <span className="text-red-500">*</span>
                      </label>
                      <input
                        id="excepcion_hora_fin"
                        type="time"
                        value={excepcionData.hora_fin}
                        onChange={(e) => {
                          const newHoraFin = e.target.value;
                          setExcepcionData({ ...excepcionData, hora_fin: newHoraFin });
                          // Validar en tiempo real
                          if (excepcionData.hora_inicio) {
                            const validation = validateHorarioTimes(excepcionData.hora_inicio, newHoraFin);
                            setErrorExcepcion(validation.isValid ? null : validation.errorMessage);
                          }
                        }}
                        className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                          errorExcepcion ? 'border-red-500' : 'border-gray-300'
                        }`}
                        required
                      />
                    </div>
                  </>
                )}
                <div className="md:col-span-2">
                  <label htmlFor="excepcion_motivo" className="block text-sm font-medium text-gray-700 mb-1">
                    Motivo (opcional)
                  </label>
                  <input
                    id="excepcion_motivo"
                    type="text"
                    value={excepcionData.motivo}
                    onChange={(e) => setExcepcionData({ ...excepcionData, motivo: e.target.value })}
                    placeholder="Ej: Vacaciones, Día festivo, etc."
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              {errorExcepcion && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {errorExcepcion}
                </div>
              )}
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowExcepcionForm(false);
                    setErrorExcepcion(null);
                    setExcepcionData({ 
                      fecha: '', 
                      tipo: 'cerrado', 
                      hora_inicio: '09:00', 
                      hora_fin: '17:00', 
                      motivo: '' 
                    });
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  disabled={!!errorExcepcion}
                >
                  Crear Excepción
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="divide-y divide-gray-200">
          {excepciones.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <p>No tienes excepciones configuradas</p>
            </div>
          ) : (
            excepciones.map((excepcion) => (
              <div key={excepcion.id_excepcion} className="p-6 flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">
                    {formatISODateToDDMMYYYY(excepcion.fecha)}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {excepcion.tipo === 'cerrado' 
                      ? 'Día cerrado' 
                      : `Horario especial: ${excepcion.hora_inicio} - ${excepcion.hora_fin}`
                    }
                  </p>
                  {excepcion.motivo && (
                    <p className="text-sm text-gray-500">{excepcion.motivo}</p>
                  )}
                </div>
                <button
                  onClick={() => handleDeleteExcepcion(excepcion.id_excepcion)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Modal de Configuración Completa */}
      {showConfiguracionCompleta && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-900">Configurar Horario Completo</h3>
              <button
                onClick={() => setShowConfiguracionCompleta(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="text-2xl">&times;</span>
              </button>
            </div>
            
            <p className="text-sm text-gray-600 mb-6">
              Configura los horarios para todos los días de la semana. Los horarios inactivos no se crearán.
            </p>

            <div className="space-y-4">
              {configuracionCompleta.map((horario, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={horario.activo}
                        onChange={(e) => handleConfiguracionCompletaChange(index, 'activo', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                      <span className="font-medium text-gray-900">{horario.nombreDia}</span>
                    </label>
                  </div>
                  
                  {horario.activo && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Hora de Inicio
                        </label>
                        <input
                          type="time"
                          value={horario.hora_inicio}
                          onChange={(e) => handleConfiguracionCompletaChange(index, 'hora_inicio', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Hora de Fin
                        </label>
                        <input
                          type="time"
                          value={horario.hora_fin}
                          onChange={(e) => handleConfiguracionCompletaChange(index, 'hora_fin', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowConfiguracionCompleta(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
              >
                Cancelar
              </button>
              <button
                onClick={configurarHorarioCompleto}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2"
              >
                <CheckIcon className="w-4 h-4" />
                <span>Guardar Configuración</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HorarioTrabajoManager;
