import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { providerServicesAPI } from '../../services/api';
import { CalendarDaysIcon, ClockIcon, PlusIcon, TrashIcon, PencilIcon, CheckIcon, XMarkIcon } from '../../components/icons';

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

interface HorarioBase {
    dias_semana: string[];
    hora_inicio: string;
    hora_fin: string;
    duracion_sesion: number;
    descanso_entre_sesiones: number;
}

interface PlantillaHorario {
    id: string;
    nombre: string;
    descripcion: string;
    icono: string;
    color: string;
    horario: HorarioBase;
}

const ProviderAgendaPage: React.FC = () => {
    const { user } = useAuth();
    const [disponibilidades, setDisponibilidades] = useState<Disponibilidad[]>([]);
    const [servicios, setServicios] = useState<Servicio[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [vista, setVista] = useState<'configuracion' | 'calendario' | 'excepciones'>('configuracion');
    const [serviciosSeleccionados, setServiciosSeleccionados] = useState<number[]>([]);
    const [creandoHorario, setCreandoHorario] = useState(false);
    const [horarioBase, setHorarioBase] = useState<HorarioBase>({
        dias_semana: [],
        hora_inicio: '09:00',
        hora_fin: '17:00',
        duracion_sesion: 60,
        descanso_entre_sesiones: 15
    });

    const [formData, setFormData] = useState({
        id_servicio: '',
        fecha_inicio: '',
        fecha_fin: '',
        disponible: true,
        precio_adicional: 0,
        observaciones: ''
    });

    const API_URL = import.meta.env.VITE_API_URL || 'https://backend-production-249d.up.railway.app';

    // Plantillas predefinidas de horarios
    const plantillasHorario: PlantillaHorario[] = [
        {
            id: 'oficina',
            nombre: 'Oficina Estándar',
            descripcion: 'Horario de oficina tradicional de lunes a viernes',
            icono: '🏢',
            color: 'blue',
            horario: {
                dias_semana: ['lunes', 'martes', 'miércoles', 'jueves', 'viernes'],
                hora_inicio: '09:00',
                hora_fin: '17:00',
                duracion_sesion: 60,
                descanso_entre_sesiones: 15
            }
        },
        {
            id: 'consultas',
            nombre: 'Consultas Médicas',
            descripcion: 'Horario para consultas médicas con citas programadas',
            icono: '🏥',
            color: 'green',
            horario: {
                dias_semana: ['lunes', 'martes', 'miércoles', 'jueves', 'viernes'],
                hora_inicio: '08:00',
                hora_fin: '18:00',
                duracion_sesion: 30,
                descanso_entre_sesiones: 10
            }
        },
        {
            id: 'tienda',
            nombre: 'Tienda Comercial',
            descripcion: 'Horario comercial extendido incluyendo fines de semana',
            icono: '🛍️',
            color: 'purple',
            horario: {
                dias_semana: ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'],
                hora_inicio: '10:00',
                hora_fin: '20:00',
                duracion_sesion: 45,
                descanso_entre_sesiones: 15
            }
        }
    ];

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
            
            console.log(`🔍 Cargando servicios usando providerServicesAPI`);
            
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                console.log('❌ No hay token de acceso');
                setError('No hay token de acceso');
                setServicios([]);
                return;
            }

            const data = await providerServicesAPI.getProviderServices(accessToken);
            console.log(`✅ Servicios cargados: ${data.length} servicios`);
            
            if (data.length === 0) {
                console.log('⚠️ No hay servicios disponibles, pero manteniendo sesión');
                setError('No hay servicios disponibles. Por favor, crea un servicio primero en "Mis Servicios".');
            }
            
            setServicios(data);
        } catch (err) {
            console.error('❌ Error al cargar servicios:', err);
            
            // No hacer logout en errores de red o servidor
            if (err instanceof Error && (
                err.message.includes('Error temporal del servidor') ||
                err.message.includes('Error 500') ||
                err.message.includes('Error 401') ||
                err.message.includes('Failed to fetch')
            )) {
                console.log('⚠️ Error de servidor detectado, manteniendo sesión');
                setError('Error temporal del servidor. Por favor, intenta nuevamente.');
                setServicios([]);
            } else {
                setError(err instanceof Error ? err.message : 'Error desconocido');
                setServicios([]);
            }
        } finally {
            setLoading(false);
        }
    };

    const loadDisponibilidades = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                console.log('❌ No hay token de acceso para cargar disponibilidades');
                setDisponibilidades([]);
                return;
            }

            console.log('🔍 Cargando disponibilidades optimizado para', servicios.length, 'servicios');
            
            // Optimización: Cargar disponibilidades de todos los servicios con una sola petición
            try {
                const response = await fetch(`${API_URL}/api/v1/disponibilidades/proveedor`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json',
                    },
                });

                console.log(`🔍 Respuesta disponibilidades proveedor:`, response.status);

                if (!response.ok) {
                    if (response.status === 404) {
                        console.log(`⚠️ No hay disponibilidades para el proveedor`);
                        setDisponibilidades([]);
                        return;
                    }
                    if (response.status === 401 || response.status === 500) {
                        console.log(`⚠️ Error 401/500 para disponibilidades proveedor, devolviendo array vacío`);
                        setDisponibilidades([]);
                        return;
                    }
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }

                const disponibilidadesData = await response.json();
                const allDisponibilidades = disponibilidadesData.map((disp: any) => ({
                    ...disp,
                    servicio_nombre: servicios.find(s => s.id_servicio === disp.id_servicio)?.nombre
                }));

                // Ordenar por fecha de inicio
                allDisponibilidades.sort((a: any, b: any) => 
                    new Date(a.fecha_inicio).getTime() - new Date(b.fecha_inicio).getTime()
                );

                console.log(`✅ Disponibilidades cargadas: ${allDisponibilidades.length} disponibilidades`);
                setDisponibilidades(allDisponibilidades);
            } catch (error) {
                console.error('❌ Error cargando disponibilidades del proveedor:', error);
                // Fallback: cargar disponibilidades de forma individual si el endpoint optimizado falla
                console.log('🔄 Intentando carga individual como fallback...');
                await loadDisponibilidadesIndividual();
            }
        } catch (err) {
            console.error('Error al cargar disponibilidades:', err);
            
            // No hacer logout en errores de red o servidor
            if (err instanceof Error && (
                err.message.includes('Error temporal del servidor') ||
                err.message.includes('Error 500') ||
                err.message.includes('Error 401') ||
                err.message.includes('Failed to fetch')
            )) {
                console.log('⚠️ Error de servidor en disponibilidades, manteniendo sesión');
                setError('Error temporal del servidor. Por favor, intenta nuevamente.');
            } else {
                setError(err instanceof Error ? err.message : 'Error desconocido');
            }
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

            console.log('🔍 Creando disponibilidad:', disponibilidadData);
            
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                throw new Error('No hay token de acceso');
            }

            const response = await fetch(`${API_URL}/api/v1/disponibilidades/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(disponibilidadData),
            });

            console.log('🔍 Respuesta crear disponibilidad:', response.status, response.statusText);

            if (!response.ok) {
                if (response.status === 401 || response.status === 500) {
                    console.log('⚠️ Error 401/500 al crear disponibilidad, no haciendo logout');
                    throw new Error('Error temporal del servidor. Por favor, intenta nuevamente.');
                }
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

            console.log('🔍 Eliminando disponibilidad:', id);
            
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                throw new Error('No hay token de acceso');
            }

            const response = await fetch(`${API_URL}/api/v1/disponibilidades/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log('🔍 Respuesta eliminar disponibilidad:', response.status, response.statusText);

            if (!response.ok) {
                if (response.status === 401 || response.status === 500) {
                    console.log('⚠️ Error 401/500 al eliminar disponibilidad, no haciendo logout');
                    throw new Error('Error temporal del servidor. Por favor, intenta nuevamente.');
                }
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

    // Función de fallback para cargar disponibilidades individualmente
    const loadDisponibilidadesIndividual = async () => {
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            // Cargar solo los primeros 3 servicios para evitar sobrecarga
            const serviciosLimitados = servicios.slice(0, 3);
            console.log('🔍 Cargando disponibilidades individuales para:', serviciosLimitados.map(s => s.id_servicio));
            
            const promises = serviciosLimitados.map(async servicio => {
                try {
                    const response = await fetch(`${API_URL}/api/v1/disponibilidades/servicio/${servicio.id_servicio}`, {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${accessToken}`,
                            'Content-Type': 'application/json',
                        },
                    });

                    if (!response.ok) {
                        if (response.status === 404) {
                            return [];
                        }
                        return [];
                    }

                    return await response.json();
                } catch (error) {
                    console.error(`❌ Error cargando disponibilidades para servicio ${servicio.id_servicio}:`, error);
                    return [];
                }
            });

            const results = await Promise.all(promises);
            const allDisponibilidades = results.flat().map((disp: any) => ({
                ...disp,
                servicio_nombre: servicios.find(s => s.id_servicio === disp.id_servicio)?.nombre
            }));

            allDisponibilidades.sort((a: any, b: any) => 
                new Date(a.fecha_inicio).getTime() - new Date(b.fecha_inicio).getTime()
            );

            console.log(`✅ Disponibilidades cargadas (fallback): ${allDisponibilidades.length} disponibilidades`);
            setDisponibilidades(allDisponibilidades);
        } catch (error) {
            console.error('❌ Error en fallback de disponibilidades:', error);
            setDisponibilidades([]);
        }
    };

    // Aplicar plantilla de horario
    const aplicarPlantilla = (plantilla: PlantillaHorario) => {
        setHorarioBase(plantilla.horario);
        console.log('🎯 Plantilla aplicada:', plantilla.nombre);
    };

    // Seleccionar todos los servicios
    const seleccionarTodosLosServicios = () => {
        const todosLosIds = servicios.filter(s => s.estado).map(s => s.id_servicio);
        setServiciosSeleccionados(todosLosIds);
        console.log('✅ Todos los servicios seleccionados:', todosLosIds.length);
    };

    // Crear horario base para los próximos 7 días (optimizado)
    const crearHorarioBase = async () => {
        if (serviciosSeleccionados.length === 0) {
            setError('Por favor selecciona al menos un servicio');
            return;
        }

        if (horarioBase.dias_semana.length === 0) {
            setError('Por favor selecciona al menos un día de la semana');
            return;
        }

        // Límite de seguridad: máximo 5 servicios y 7 días
        if (serviciosSeleccionados.length > 5) {
            setError('Por seguridad, selecciona máximo 5 servicios para crear el horario automático');
            return;
        }

        try {
            setCreandoHorario(true);
            setError(null);

            console.log('🚀 Creando horario para', serviciosSeleccionados.length, 'servicios');
            console.log('📅 Días:', horarioBase.dias_semana);
            console.log('🕐 Horario:', horarioBase.hora_inicio, '-', horarioBase.hora_fin);

            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                throw new Error('No hay token de acceso');
            }

            // Crear disponibilidades para los próximos 7 días (optimizado)
            const disponibilidadesACrear = [];
            const hoy = new Date();
            
            for (let i = 0; i < 7; i++) { // Reducido de 30 a 7 días
                const fecha = new Date(hoy);
                fecha.setDate(hoy.getDate() + i);
                
                const diaSemana = fecha.toLocaleDateString('es-PY', { weekday: 'long' });
                
                if (horarioBase.dias_semana.includes(diaSemana)) {
                    // Crear sesiones para este día
                    const horaInicio = new Date(fecha);
                    const [hora, minuto] = horarioBase.hora_inicio.split(':');
                    horaInicio.setHours(parseInt(hora), parseInt(minuto), 0, 0);
                    
                    const horaFin = new Date(fecha);
                    const [horaF, minutoF] = horarioBase.hora_fin.split(':');
                    horaFin.setHours(parseInt(horaF), parseInt(minutoF), 0, 0);
                    
                    // Crear sesiones cada duracion_sesion + descanso_entre_sesiones
                    let horaActual = new Date(horaInicio);
                    while (horaActual < horaFin) {
                        const horaSesionFin = new Date(horaActual);
                        horaSesionFin.setMinutes(horaSesionFin.getMinutes() + horarioBase.duracion_sesion);
                        
                        if (horaSesionFin <= horaFin) {
                            for (const idServicio of serviciosSeleccionados) {
                                disponibilidadesACrear.push({
                                    id_servicio: idServicio,
                                    fecha_inicio: horaActual.toISOString(),
                                    fecha_fin: horaSesionFin.toISOString(),
                                    disponible: true,
                                    precio_adicional: 0,
                                    observaciones: `Horario automático - ${horarioBase.duracion_sesion}min`
                                });
                            }
                        }
                        
                        // Siguiente sesión
                        horaActual.setMinutes(horaActual.getMinutes() + horarioBase.duracion_sesion + horarioBase.descanso_entre_sesiones);
                    }
                }
            }

            console.log(`📊 Creando ${disponibilidadesACrear.length} disponibilidades (optimizado)`);

            // Crear disponibilidades en lotes más pequeños (5 en lugar de 10)
            const lotes = [];
            for (let i = 0; i < disponibilidadesACrear.length; i += 5) {
                lotes.push(disponibilidadesACrear.slice(i, i + 5));
            }

            let creadas = 0;
            let errores = 0;
            
            for (const lote of lotes) {
                const promises = lote.map(async (disp) => {
                    try {
                        const response = await fetch(`${API_URL}/api/v1/disponibilidades/`, {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${accessToken}`,
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(disp),
                        });

                        if (response.ok) {
                            creadas++;
                        } else {
                            errores++;
                            console.error('Error creando disponibilidad:', response.status, response.statusText);
                        }
                    } catch (error) {
                        errores++;
                        console.error('Error creando disponibilidad:', error);
                    }
                });

                await Promise.all(promises);
                
                // Pausa más larga entre lotes para evitar sobrecarga
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            console.log(`✅ Creadas ${creadas} disponibilidades, ${errores} errores`);
            
            if (creadas > 0) {
                // Recargar disponibilidades
                await loadDisponibilidades();
                
                // Limpiar selección
                setServiciosSeleccionados([]);
                setVista('calendario');
                
                setError(null);
            } else {
                setError('No se pudieron crear las disponibilidades. El servidor puede estar sobrecargado. Intenta con menos servicios.');
            }
            
        } catch (err) {
            console.error('Error creando horario:', err);
            setError(err instanceof Error ? err.message : 'Error desconocido');
        } finally {
            setCreandoHorario(false);
        }
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
                                Configura tu horario de trabajo y gestiona la disponibilidad de todos tus servicios
                            </p>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                        <p className="text-red-800">⚠️ {error}</p>
                    </div>
                )}

                {/* Navegación por pestañas */}
                <div className="mb-8">
                    <div className="border-b border-gray-200">
                        <nav className="-mb-px flex space-x-8">
                            <button
                                onClick={() => setVista('configuracion')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                    vista === 'configuracion'
                                        ? 'border-primary-500 text-primary-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                            >
                                ⚙️ Configuración Rápida
                            </button>
                            <button
                                onClick={() => setVista('calendario')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                    vista === 'calendario'
                                        ? 'border-primary-500 text-primary-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                            >
                                📅 Vista Calendario
                            </button>
                            <button
                                onClick={() => setVista('excepciones')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                    vista === 'excepciones'
                                        ? 'border-primary-500 text-primary-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                            >
                                🚫 Gestionar Excepciones
                            </button>
                        </nav>
                    </div>
                </div>

                {/* Contenido de las pestañas */}
                {vista === 'configuracion' && (
                    <div className="space-y-8">
                        {/* Paso 1: Seleccionar Plantilla */}
                        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">1️⃣ Selecciona una Plantilla</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {plantillasHorario.map((plantilla) => (
                                    <button
                                        key={plantilla.id}
                                        onClick={() => aplicarPlantilla(plantilla)}
                                        className={`p-4 rounded-lg border-2 transition-all hover:shadow-md ${
                                            horarioBase.dias_semana.length > 0 && 
                                            horarioBase.dias_semana.join(',') === plantilla.horario.dias_semana.join(',')
                                                ? 'border-primary-500 bg-primary-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                        }`}
                                    >
                                        <div className="text-2xl mb-2">{plantilla.icono}</div>
                                        <h4 className="font-medium text-gray-900">{plantilla.nombre}</h4>
                                        <p className="text-sm text-gray-600 mt-1">{plantilla.descripcion}</p>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Paso 2: Personalizar Horario */}
                        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">2️⃣ Personaliza tu Horario</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Días de la Semana
                                    </label>
                                    <div className="space-y-2">
                                        {['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'].map((dia) => (
                                            <label key={dia} className="flex items-center">
                                                <input
                                                    type="checkbox"
                                                    checked={horarioBase.dias_semana.includes(dia)}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setHorarioBase(prev => ({
                                                                ...prev,
                                                                dias_semana: [...prev.dias_semana, dia]
                                                            }));
                                                        } else {
                                                            setHorarioBase(prev => ({
                                                                ...prev,
                                                                dias_semana: prev.dias_semana.filter(d => d !== dia)
                                                            }));
                                                        }
                                                    }}
                                                    className="rounded mr-3"
                                                />
                                                <span className="text-sm text-gray-700 capitalize">{dia}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Hora de Inicio
                                        </label>
                                        <input
                                            type="time"
                                            value={horarioBase.hora_inicio}
                                            onChange={(e) => setHorarioBase(prev => ({ ...prev, hora_inicio: e.target.value }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Hora de Fin
                                        </label>
                                        <input
                                            type="time"
                                            value={horarioBase.hora_fin}
                                            onChange={(e) => setHorarioBase(prev => ({ ...prev, hora_fin: e.target.value }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Duración de Sesión (minutos)
                                        </label>
                                        <input
                                            type="number"
                                            min="15"
                                            max="240"
                                            value={horarioBase.duracion_sesion}
                                            onChange={(e) => setHorarioBase(prev => ({ ...prev, duracion_sesion: parseInt(e.target.value) }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Descanso entre Sesiones (minutos)
                                        </label>
                                        <input
                                            type="number"
                                            min="0"
                                            max="60"
                                            value={horarioBase.descanso_entre_sesiones}
                                            onChange={(e) => setHorarioBase(prev => ({ ...prev, descanso_entre_sesiones: parseInt(e.target.value) }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Paso 3: Seleccionar Servicios */}
                        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">3️⃣ Selecciona los Servicios</h3>
                            <div className="mb-4">
                                <button
                                    onClick={seleccionarTodosLosServicios}
                                    className="btn-blue flex items-center gap-2"
                                >
                                    <CheckIcon className="h-4 w-4" />
                                    Seleccionar Todos
                                </button>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {servicios.filter(s => s.estado).map((servicio) => (
                                    <label key={servicio.id_servicio} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                                        <input
                                            type="checkbox"
                                            checked={serviciosSeleccionados.includes(servicio.id_servicio)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setServiciosSeleccionados(prev => [...prev, servicio.id_servicio]);
                                                } else {
                                                    setServiciosSeleccionados(prev => prev.filter(id => id !== servicio.id_servicio));
                                                }
                                            }}
                                            className="rounded mr-3"
                                        />
                                        <div>
                                            <div className="font-medium text-gray-900">{servicio.nombre}</div>
                                            <div className="text-sm text-gray-600">{servicio.descripcion}</div>
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Botón de Creación */}
                        <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl border border-primary-200 p-6">
                            <div className="text-center">
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">🚀 Crear mi Horario Automáticamente</h3>
                                <p className="text-gray-600 mb-2">
                                    Se crearán disponibilidades para los próximos 7 días según tu configuración
                                </p>
                                <div className="text-sm text-amber-600 bg-amber-50 px-3 py-2 rounded-lg mb-4">
                                    ⚠️ <strong>Límite de seguridad:</strong> Máximo 5 servicios para evitar sobrecarga del servidor
                                </div>
                                <button
                                    onClick={crearHorarioBase}
                                    disabled={creandoHorario || serviciosSeleccionados.length === 0 || serviciosSeleccionados.length > 5}
                                    className="btn-blue text-lg px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {creandoHorario ? (
                                        <>
                                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                                            Creando Horario...
                                        </>
                                    ) : (
                                        '🚀 Crear mi horario automáticamente'
                                    )}
                                </button>
                                {serviciosSeleccionados.length > 5 && (
                                    <p className="text-red-600 text-sm mt-2">
                                        Selecciona máximo 5 servicios para crear el horario automático
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {vista === 'calendario' && (
                    <div className="space-y-6">
                        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">📅 Vista de Calendario</h3>
                            {loading ? (
                                <div className="flex items-center justify-center p-8">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                                    <span className="ml-2 text-gray-600">Cargando disponibilidades...</span>
                                </div>
                            ) : disponibilidades.length === 0 ? (
                                <div className="text-center p-8">
                                    <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" />
                                    <h3 className="mt-2 text-sm font-medium text-gray-900">No hay disponibilidades</h3>
                                    <p className="mt-1 text-sm text-gray-500">
                                        Configura tu horario en la pestaña "Configuración Rápida"
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {disponibilidades.map((disp) => (
                                        <div key={disp.id_disponibilidad} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                            <div className="flex justify-between items-start">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-3 mb-2">
                                                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                                                            disp.disponible 
                                                                ? 'bg-green-100 text-green-800' 
                                                                : 'bg-red-100 text-red-800'
                                                        }`}>
                                                            {disp.disponible ? 'Disponible' : 'No disponible'}
                                                        </span>
                                                        <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                                                            {disp.servicio_nombre}
                                                        </span>
                                                    </div>
                                                    
                                                    <div className="text-sm text-gray-600">
                                                        <p>📅 {formatDate(disp.fecha_inicio)}</p>
                                                        <p>🕐 {formatTime(disp.fecha_inicio)} - {formatTime(disp.fecha_fin)}</p>
                                                        {disp.observaciones && (
                                                            <p>📝 {disp.observaciones}</p>
                                                        )}
                                                    </div>
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
                )}

                {vista === 'excepciones' && (
                    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">🚫 Gestionar Excepciones</h3>
                        <div className="text-center p-8">
                            <XMarkIcon className="mx-auto h-12 w-12 text-gray-400" />
                            <h3 className="mt-2 text-sm font-medium text-gray-900">Próximamente</h3>
                            <p className="mt-1 text-sm text-gray-500">
                                Aquí podrás gestionar días festivos, vacaciones y excepciones especiales
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProviderAgendaPage;
