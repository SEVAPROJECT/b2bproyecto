import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { buildApiUrl } from '../../config/api';

interface Disponibilidad {
    id_disponibilidad: number;
    fecha_inicio: string;
    fecha_fin: string;
    disponible: boolean;
    precio_adicional?: number;
}

interface AvailabilityCalendarProps {
    serviceId: number;
    onDateSelect: (date: string, time: string) => void;
    selectedDate?: string;
    selectedTime?: string;
}

const AvailabilityCalendar: React.FC<AvailabilityCalendarProps> = ({
    serviceId,
    onDateSelect,
    selectedDate,
    selectedTime
}) => {
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [availableDates, setAvailableDates] = useState<Set<string>>(new Set());
    const [availableTimes, setAvailableTimes] = useState<Map<string, string[]>>(new Map());
    const [excepciones, setExcepciones] = useState<Map<string, { tipo: string; hora_inicio?: string; hora_fin?: string }>>(new Map());
    const [reservasConfirmadas, setReservasConfirmadas] = useState<Map<string, Array<{ hora_inicio: string; hora_fin: string }>>>(new Map());

    // Helper para convertir Date a string en formato YYYY-MM-DD sin cambio de zona horaria
    const formatDateToYYYYMMDD = (date: Date): string => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    // Helper para formatear fecha YYYY-MM-DD a DD/MM/YYYY sin conversión de zona horaria
    const formatDateToDDMMYYYY = (dateStr: string): string => {
        const [year, month, day] = dateStr.split('-');
        return `${day}/${month}/${year}`;
    };

    // Cargar disponibilidades y excepciones del servicio
    useEffect(() => {
        const loadDisponibilidades = async () => {
            try {
                setLoading(true);
                setError(null);
                
                // Cargar disponibilidades, excepciones y reservas confirmadas en paralelo
                const [disponibilidadesResponse, excepcionesResponse, reservasResponse] = await Promise.all([
                    fetch(buildApiUrl(`/disponibilidades/servicio/${serviceId}/disponibles`), {
                        headers: {
                            'Authorization': `Bearer ${user?.accessToken}`,
                            'Content-Type': 'application/json',
                        },
                    }),
                    fetch(buildApiUrl(`/disponibilidades/servicio/${serviceId}/excepciones`), {
                        headers: {
                            'Authorization': `Bearer ${user?.accessToken}`,
                            'Content-Type': 'application/json',
                        },
                    }),
                    fetch(buildApiUrl(`/reservas/servicio/${serviceId}/confirmadas`), {
                        headers: {
                            'Authorization': `Bearer ${user?.accessToken}`,
                            'Content-Type': 'application/json',
                        },
                    })
                ]);

                // Procesar disponibilidades
                if (!disponibilidadesResponse.ok) {
                    console.error(`❌ Error en respuesta: ${disponibilidadesResponse.status} ${disponibilidadesResponse.statusText}`);
                    if (disponibilidadesResponse.status === 404) {
                        console.log('ℹ️ No hay disponibilidades configuradas para este servicio');
                        setAvailableDates(new Set());
                        setAvailableTimes(new Map());
                    } else {
                        throw new Error(`Error ${disponibilidadesResponse.status}: ${disponibilidadesResponse.statusText}`);
                    }
                } else {
                    const data = await disponibilidadesResponse.json();
                    console.log(`📊 Datos recibidos: ${data.length} disponibilidades`);
                    
                    // Procesar fechas y horas disponibles
                    const dates = new Set<string>();
                    const timesMap = new Map<string, string[]>();

                    for (const disp of data) {
                        if (disp.disponible && disp.fecha_inicio) {
                            // Extraer fecha y hora directamente del string ISO sin conversión de zona horaria
                            const fechaStrRaw = String(disp.fecha_inicio);
                            
                            // Extraer fecha (YYYY-MM-DD) y hora (HH:MM) directamente del string ISO
                            // Formato esperado: "2025-12-22T11:00:00" o "2025-12-22T11:00:00Z" o "2025-12-22T11:00:00+00:00"
                            let fechaStr: string;
                            let horaStr: string;
                            
                            if (fechaStrRaw.includes('T')) {
                                const [fechaPart, horaPart] = fechaStrRaw.split('T');
                                fechaStr = fechaPart; // YYYY-MM-DD
                                
                                // Extraer hora (HH:MM) - puede venir como "11:00:00" o "11:00:00Z" o "11:00:00+00:00"
                                const horaPartClean = horaPart.split('+')[0].split('-')[0].split('Z')[0]; // Remover timezone
                                const [hora, minuto] = horaPartClean.split(':').map(Number);
                                
                                // Solo considerar horas completas (minutos = 0) para intervalos de 1 hora
                                if (!isNaN(hora) && !isNaN(minuto) && minuto === 0) {
                                    horaStr = `${String(hora).padStart(2, '0')}:00`;
                                    
                                    // Agregar fecha
                                    dates.add(fechaStr);
                                    
                                    // Agregar hora
                                    if (!timesMap.has(fechaStr)) {
                                        timesMap.set(fechaStr, []);
                                    }
                                    const times = timesMap.get(fechaStr);
                                    if (times && !times.includes(horaStr)) {
                                        times.push(horaStr);
                                    }
                                }
                            } else {
                                console.warn(`⚠️ Formato de fecha inesperado: ${fechaStrRaw}`);
                            }
                        }
                    }
                    
                    console.log(`✅ Fechas disponibles: ${dates.size}`);
                    console.log(`📊 Horas disponibles por fecha:`, Array.from(timesMap.entries()).map(([fecha, horas]) => ({ fecha, horas: horas.sort() })));
                    setAvailableDates(dates);
                    setAvailableTimes(timesMap);
                }

                // Procesar excepciones
                if (excepcionesResponse.ok) {
                    const excepcionesData = await excepcionesResponse.json();
                    console.log(`📊 Excepciones recibidas: ${excepcionesData.length}`);
                    
                    const excepcionesMap = new Map<string, { tipo: string; hora_inicio?: string; hora_fin?: string }>();
                    for (const exc of excepcionesData) {
                        // Extraer solo la fecha (YYYY-MM-DD) del string ISO
                        const fechaStr = exc.fecha.split('T')[0];
                        excepcionesMap.set(fechaStr, {
                            tipo: exc.tipo,
                            hora_inicio: exc.hora_inicio,
                            hora_fin: exc.hora_fin
                        });
                    }
                    setExcepciones(excepcionesMap);
                } else {
                    console.warn('⚠️ No se pudieron cargar excepciones');
                    setExcepciones(new Map());
                }
                
                // Procesar reservas confirmadas
                if (reservasResponse.ok) {
                    const reservasData = await reservasResponse.json();
                    const reservasMap = new Map<string, Array<{ hora_inicio: string; hora_fin: string }>>();
                    
                    for (const reserva of reservasData.reservas || []) {
                        const fechaStr = reserva.fecha.split('T')[0]; // Obtener solo la fecha (YYYY-MM-DD)
                        if (!reservasMap.has(fechaStr)) {
                            reservasMap.set(fechaStr, []);
                        }
                        const reservasFecha = reservasMap.get(fechaStr);
                        if (reserva.hora_inicio && reserva.hora_fin && reservasFecha) {
                            reservasFecha.push({
                                hora_inicio: reserva.hora_inicio.substring(0, 5), // HH:MM
                                hora_fin: reserva.hora_fin.substring(0, 5) // HH:MM
                            });
                        }
                    }
                    
                    setReservasConfirmadas(reservasMap);
                    console.log(`📊 Reservas confirmadas cargadas: ${reservasMap.size} fechas con reservas`);
                } else {
                    console.warn('⚠️ No se pudieron cargar reservas confirmadas');
                    setReservasConfirmadas(new Map());
                }
            } catch (err) {
                console.error('Error al cargar disponibilidades:', err);
                setError(err instanceof Error ? err.message : 'Error desconocido');
                // En caso de error, mostrar mensaje informativo
                setAvailableDates(new Set());
                setAvailableTimes(new Map());
                setExcepciones(new Map());
                setReservasConfirmadas(new Map());
            } finally {
                setLoading(false);
            }
        };

        if (serviceId && user) {
            loadDisponibilidades();
        }
    }, [serviceId, user]);

    // Generar opciones de fecha (próximos 30 días)
    const generateDateOptions = () => {
        const options = [];
        const today = new Date();
        
        for (let i = 0; i < 30; i++) {
            const date = new Date(today);
            date.setDate(today.getDate() + i);
            const dateStr = formatDateToYYYYMMDD(date);
            
            // Verificar si hay excepción para esta fecha
            const excepcion = excepciones.get(dateStr);
            
            // Si el día está cerrado, incluirlo en la lista con indicador
            if (excepcion && excepcion.tipo === 'cerrado') {
                const fechaLabel = date.toLocaleDateString('es-PY', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
                options.push({
                    value: dateStr,
                    label: `${fechaLabel} (Día cerrado)`,
                    esCerrado: true
                });
                continue;
            }
            
            // Si la fecha está disponible, incluirla en la lista
            if (availableDates.has(dateStr)) {
                const fechaLabel = date.toLocaleDateString('es-PY', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
                
                let labelConExcepcion = fechaLabel;
                
                // Agregar información de horario especial si existe
                if (excepcion && excepcion.tipo === 'horario_especial' && excepcion.hora_inicio && excepcion.hora_fin) {
                    labelConExcepcion = `${fechaLabel} (Horario especial: ${excepcion.hora_inicio} - ${excepcion.hora_fin})`;
                }
                
                options.push({
                    value: dateStr,
                    label: labelConExcepcion,
                    esCerrado: false
                });
            }
        }
        
        return options;
    };

    // Verificar si un horario está ocupado por una reserva confirmada
    const isHorarioOcupado = (date: string, hora: string): boolean => {
        const reservasFecha = reservasConfirmadas.get(date);
        if (!reservasFecha || reservasFecha.length === 0) {
            return false;
        }
        
        // Convertir hora a minutos para comparación
        const [horaH, horaM] = hora.split(':').map(Number);
        const horaMinutos = horaH * 60 + horaM;
        
        // Verificar si la hora se solapa con alguna reserva confirmada
        // El slot es de 1 hora (60 minutos)
        for (const reserva of reservasFecha) {
            const [inicioH, inicioM] = reserva.hora_inicio.split(':').map(Number);
            const [finH, finM] = reserva.hora_fin.split(':').map(Number);
            const inicioMinutos = inicioH * 60 + inicioM;
            const finMinutos = finH * 60 + finM;
            
            // Verificar solapamiento (el slot de 1 hora se solapa si empieza antes del fin de la reserva y termina después del inicio)
            if (horaMinutos < finMinutos && horaMinutos + 60 > inicioMinutos) {
                return true;
            }
        }
        
        return false;
    };

    // Generar opciones de hora para la fecha seleccionada basándose en el horario de trabajo del servicio
    const generateTimeOptions = (date: string) => {
        const excepcion = excepciones.get(date);
        
        // Si el día está cerrado, no mostrar horarios
        if (excepcion && excepcion.tipo === 'cerrado') {
            return [];
        }
        
        // Obtener las horas disponibles para esta fecha desde el backend (basadas en horario de trabajo)
        const horasDisponiblesBackend = availableTimes.get(date) || [];
        
        // Si hay horario especial, usar ese rango en lugar del horario normal
        if (excepcion && excepcion.tipo === 'horario_especial' && excepcion.hora_inicio && excepcion.hora_fin) {
            const horariosEspeciales = [];
            const [horaInicioH, horaInicioM] = excepcion.hora_inicio.split(':').map(Number);
            const [horaFinH, horaFinM] = excepcion.hora_fin.split(':').map(Number);
            
            let horaActual = horaInicioH * 60 + horaInicioM; // En minutos
            const horaFinMinutos = horaFinH * 60 + horaFinM;
            
            // Generar horarios cada 1 hora dentro del rango especial
            while (horaActual < horaFinMinutos) {
                const horas = Math.floor(horaActual / 60);
                const minutos = horaActual % 60;
                const horaStr = `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}`;
                
                // Solo agregar si no está ocupado por una reserva confirmada
                if (!isHorarioOcupado(date, horaStr)) {
                    horariosEspeciales.push({
                        value: horaStr,
                        label: horaStr
                    });
                }
                horaActual += 60; // Incrementar 1 hora
            }
            
            return horariosEspeciales;
        }
        
        // Si no hay excepción, usar las horas disponibles del backend (basadas en horario de trabajo)
        // Filtrar y formatear las horas disponibles, asegurando intervalos de 1 hora
        const horariosFiltrados: string[] = [];
        const horasSet = new Set<string>();
        
        // Procesar horas del backend y agrupar por hora completa (sin minutos)
        for (const horaBackend of horasDisponiblesBackend) {
            const [hora, minuto] = horaBackend.split(':').map(Number);
            // Solo considerar horas completas (minutos = 0) para intervalos de 1 hora
            if (minuto === 0) {
                const horaStr = `${String(hora).padStart(2, '0')}:00`;
                if (!horasSet.has(horaStr) && !isHorarioOcupado(date, horaStr)) {
                    horasSet.add(horaStr);
                    horariosFiltrados.push(horaStr);
                }
            }
        }
        
        // Ordenar las horas
        horariosFiltrados.sort();
        
        return horariosFiltrados.map(hora => ({
            value: hora,
            label: hora
        }));
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <span className="ml-2 text-slate-600">Cargando disponibilidades...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">⚠️ {error}</p>
            </div>
        );
    }

    const dateOptions = generateDateOptions();
    const timeOptions = selectedDate ? generateTimeOptions(selectedDate) : [];

    return (
        <div className="space-y-4">
            {/* Selector de Fecha */}
            <div className="space-y-2">
                <label htmlFor="date" className="block text-sm font-medium text-slate-700">
                    📅 Fecha disponible
                </label>
                <select
                    id="date"
                    value={selectedDate || ''}
                    onChange={(e) => {
                        const fechaSeleccionada = e.target.value;
                        const opcionSeleccionada = dateOptions.find(opt => opt.value === fechaSeleccionada);
                        
                        // Si el día está cerrado, mostrar mensaje y no permitir seleccionar
                        if (opcionSeleccionada && opcionSeleccionada.esCerrado) {
                            alert('⚠️ Este día está cerrado. No se pueden realizar reservas en esta fecha. Por favor, selecciona otra fecha.');
                            return;
                        }
                        
                        onDateSelect(fechaSeleccionada, '');
                    }}
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                >
                    <option value="">Selecciona una fecha</option>
                    {dateOptions.map(option => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </select>
                {dateOptions.length === 0 && !loading && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                        <p className="text-sm text-amber-800">
                            ⚠️ Este servicio no tiene disponibilidades configuradas. 
                        </p>
                        <p className="text-xs text-amber-700 mt-2">
                            El proveedor debe configurar horarios disponibles en su agenda.
                        </p>
                    </div>
                )}
            </div>

            {/* Selector de Hora */}
            {selectedDate && (() => {
                const excepcion = excepciones.get(selectedDate);
                const esDiaCerrado = excepcion && excepcion.tipo === 'cerrado';
                
                return (
                    <div className="space-y-2">
                        <label htmlFor="time" className="block text-sm font-medium text-slate-700">
                            🕐 Hora disponible
                        </label>
                        {esDiaCerrado ? (
                            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                <p className="text-sm text-red-800">
                                    ⚠️ Este día está cerrado. No se pueden realizar reservas en esta fecha.
                                </p>
                            </div>
                        ) : (
                            <>
                                <select
                                    id="time"
                                    value={selectedTime || ''}
                                    onChange={(e) => {
                                        const horaSeleccionada = e.target.value;
                                        
                                        // Validar que el horario no esté ocupado por una reserva confirmada
                                        if (horaSeleccionada && isHorarioOcupado(selectedDate, horaSeleccionada)) {
                                            alert(`⚠️ Este horario ya está reservado. Por favor, selecciona otro horario disponible.`);
                                            e.target.value = ''; // Limpiar la selección
                                            onDateSelect(selectedDate, ''); // Limpiar selección en el estado
                                            return;
                                        }
                                        
                                        // Validar si hay horario especial y la hora está fuera del rango
                                        if (excepcion && excepcion.tipo === 'horario_especial' && excepcion.hora_inicio && excepcion.hora_fin) {
                                            const [horaSelH, horaSelM] = horaSeleccionada.split(':').map(Number);
                                            const horaSelMinutos = horaSelH * 60 + horaSelM;
                                            
                                            const [horaInicioH, horaInicioM] = excepcion.hora_inicio.split(':').map(Number);
                                            const [horaFinH, horaFinM] = excepcion.hora_fin.split(':').map(Number);
                                            const horaInicioMinutos = horaInicioH * 60 + horaInicioM;
                                            const horaFinMinutos = horaFinH * 60 + horaFinM;
                                            
                                            // Validar que la hora esté dentro del rango del horario especial
                                            if (horaSelMinutos < horaInicioMinutos || horaSelMinutos >= horaFinMinutos) {
                                                alert(`⚠️ El horario seleccionado (${horaSeleccionada}) está fuera del rango de horario especial (${excepcion.hora_inicio} - ${excepcion.hora_fin}). Por favor, selecciona un horario dentro del rango permitido.`);
                                                // Resetear la selección
                                                onDateSelect(selectedDate, '');
                                                return;
                                            }
                                        }
                                        
                                        onDateSelect(selectedDate, horaSeleccionada);
                                    }}
                                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                                >
                                    <option value="">Selecciona una hora</option>
                                    {timeOptions.map(option => (
                                        <option key={option.value} value={option.value}>
                                            {option.label}
                                        </option>
                                    ))}
                                </select>
                                {excepcion && excepcion.tipo === 'horario_especial' && excepcion.hora_inicio && excepcion.hora_fin && (
                                    <p className="text-xs text-blue-600 mt-1">
                                        ℹ️ Horario especial: {excepcion.hora_inicio} - {excepcion.hora_fin}
                                    </p>
                                )}
                                {timeOptions.length === 0 && !esDiaCerrado && (
                                    <p className="text-sm text-amber-600">⚠️ No hay horarios disponibles para esta fecha</p>
                                )}
                            </>
                        )}
                    </div>
                );
            })()}

            {/* Información adicional */}
            {selectedDate && selectedTime && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-sm text-green-800">
                        ✅ Fecha y hora seleccionadas: {formatDateToDDMMYYYY(selectedDate)} a las {selectedTime}
                    </p>
                </div>
            )}
        </div>
    );
};

export default AvailabilityCalendar;
