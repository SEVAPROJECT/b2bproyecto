// frontend/components/horario/HorarioTrabajoManager.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { buildApiUrl } from '../../config/api';
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

const HorarioTrabajoManager: React.FC = () => {
  const { user } = useAuth();
  const [horarios, setHorarios] = useState<HorarioTrabajo[]>([]);
  const [excepciones, setExcepciones] = useState<ExcepcionHorario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showExcepcionForm, setShowExcepcionForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

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
        setFormData({ dia_semana: 0, hora_inicio: '09:00', hora_fin: '17:00', activo: true });
      } else {
        const errorData = await response.json();
        console.error('Error al guardar horario:', errorData);
      }
    } catch (error) {
      console.error('Error al guardar horario:', error);
    }
  };

  const handleExcepcionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
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
        setExcepcionData({ 
          fecha: '', 
          tipo: 'cerrado', 
          hora_inicio: '09:00', 
          hora_fin: '17:00', 
          motivo: '' 
        });
      } else {
        const errorData = await response.json();
        console.error('Error al guardar excepción:', errorData);
      }
    } catch (error) {
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

      if (response.ok) {
        await loadHorarios();
      } else {
        console.error('Error al eliminar horario');
      }
    } catch (error) {
      console.error('Error al eliminar horario:', error);
    }
  };

  const configurarHorarioCompleto = async () => {
    const horariosCompletos = [];
    
    // Crear horarios para toda la semana
    for (let dia = 0; dia < 7; dia++) {
      if (dia < 5) { // Lunes a Viernes
        horariosCompletos.push({
          dia_semana: dia,
          hora_inicio: '09:00',
          hora_fin: '17:00',
          activo: true
        });
      } else if (dia === 5) { // Sábado
        horariosCompletos.push({
          dia_semana: dia,
          hora_inicio: '10:00',
          hora_fin: '14:00',
          activo: true
        });
      }
      // Domingo no se agrega (no trabaja)
    }

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
        alert('Horario completo configurado exitosamente');
      } else {
        const errorData = await response.json();
        console.error('Error al configurar horario completo:', errorData);
      }
    } catch (error) {
      console.error('Error al configurar horario completo:', error);
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
            onClick={configurarHorarioCompleto}
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
                  onChange={(e) => setFormData({ ...formData, hora_inicio: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                  onChange={(e) => setFormData({ ...formData, hora_fin: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>
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
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
                    onChange={(e) => setExcepcionData({ ...excepcionData, tipo: e.target.value as 'cerrado' | 'horario_especial' })}
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
                        Hora de Inicio
                      </label>
                      <input
                        id="excepcion_hora_inicio"
                        type="time"
                        value={excepcionData.hora_inicio}
                        onChange={(e) => setExcepcionData({ ...excepcionData, hora_inicio: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label htmlFor="excepcion_hora_fin" className="block text-sm font-medium text-gray-700 mb-1">
                        Hora de Fin
                      </label>
                      <input
                        id="excepcion_hora_fin"
                        type="time"
                        value={excepcionData.hora_fin}
                        onChange={(e) => setExcepcionData({ ...excepcionData, hora_fin: e.target.value })}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowExcepcionForm(false);
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
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
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
                    {new Date(excepcion.fecha).toLocaleDateString()}
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
                  onClick={() => {/* Implementar eliminación */}}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default HorarioTrabajoManager;
