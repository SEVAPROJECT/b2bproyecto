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

    // Cargar disponibilidades del servicio
    useEffect(() => {
        const loadDisponibilidades = async () => {
            try {
                setLoading(true);
                setError(null);
                
                // Usar el endpoint correcto para disponibilidades disponibles
                const apiUrl = buildApiUrl(`/disponibilidades/servicio/${serviceId}/disponibles`);
                console.log(`🔍 Intentando cargar disponibilidades para servicio ${serviceId}`);
                console.log(`🔗 URL: ${apiUrl}`);
                
                const response = await fetch(apiUrl, {
                    headers: {
                        'Authorization': `Bearer ${user?.accessToken}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    console.error(`❌ Error en respuesta: ${response.status} ${response.statusText}`);
                    if (response.status === 404) {
                        // No hay disponibilidades configuradas para este servicio
                        console.log('ℹ️ No hay disponibilidades configuradas para este servicio');
                        setAvailableDates(new Set());
                        setAvailableTimes(new Map());
                        return;
                    }
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                console.log(`📊 Datos recibidos: ${data.length} disponibilidades`);
                console.log(`📋 Primeros 3 registros:`, data.slice(0, 3));
                
                // Procesar fechas y horas disponibles
                const dates = new Set<string>();
                const timesMap = new Map<string, string[]>();

                for (const disp of data) {
                    if (disp.disponible && disp.fecha_inicio) {
                        // Parsear fecha - puede venir con timezone o sin él
                        let fechaInicio: Date;
                        const fechaStrRaw = disp.fecha_inicio;
                        
                        // Si ya tiene timezone (termina con +00:00, -05:00, Z, etc.), parsear directamente
                        if (typeof fechaStrRaw === 'string') {
                            // Si no termina con Z ni tiene timezone, agregar Z para UTC
                            if (!fechaStrRaw.endsWith('Z') && !fechaStrRaw.includes('+') && !fechaStrRaw.includes('-', 10)) {
                                fechaInicio = new Date(fechaStrRaw + 'Z');
                            } else {
                                fechaInicio = new Date(fechaStrRaw);
                            }
                        } else {
                            fechaInicio = new Date(fechaStrRaw);
                        }
                        
                        // Validar que la fecha sea válida
                        if (isNaN(fechaInicio.getTime())) {
                            console.warn(`⚠️ Fecha inválida: ${fechaStrRaw}`);
                            continue;
                        }
                        
                        // Agregar fecha (usar función local sin conversión UTC)
                        const fechaStr = formatDateToYYYYMMDD(fechaInicio);
                        dates.add(fechaStr);
                        
                        // Agregar hora - usar hora local del datetime
                        const horaStr = fechaInicio.toTimeString().split(' ')[0].substring(0, 5);
                        if (!timesMap.has(fechaStr)) {
                            timesMap.set(fechaStr, []);
                        }
                        const times = timesMap.get(fechaStr);
                        if (times && !times.includes(horaStr)) {
                            times.push(horaStr);
                        }
                    }
                }
                
                console.log(`✅ Fechas disponibles: ${dates.size}`);
                console.log(`✅ Horarios por fecha:`, Array.from(timesMap.entries()).slice(0, 3));

                setAvailableDates(dates);
                setAvailableTimes(timesMap);
            } catch (err) {
                console.error('Error al cargar disponibilidades:', err);
                setError(err instanceof Error ? err.message : 'Error desconocido');
                // En caso de error, mostrar mensaje informativo
                setAvailableDates(new Set());
                setAvailableTimes(new Map());
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
            
            if (availableDates.has(dateStr)) {
                options.push({
                    value: dateStr,
                    label: date.toLocaleDateString('es-PY', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    })
                });
            }
        }
        
        return options;
    };

    // Generar opciones de hora para la fecha seleccionada
    const generateTimeOptions = (date: string) => {
        const times = availableTimes.get(date) || [];
        return times.map(time => ({
            value: time,
            label: time
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
                        onDateSelect(e.target.value, '');
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
            {selectedDate && (
                <div className="space-y-2">
                    <label htmlFor="time" className="block text-sm font-medium text-slate-700">
                        🕐 Hora disponible
                    </label>
                    <select
                        id="time"
                        value={selectedTime || ''}
                        onChange={(e) => {
                            onDateSelect(selectedDate, e.target.value);
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
                    {timeOptions.length === 0 && (
                        <p className="text-sm text-amber-600">⚠️ No hay horarios disponibles para esta fecha</p>
                    )}
                </div>
            )}

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
