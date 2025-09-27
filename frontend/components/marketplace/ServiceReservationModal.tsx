import React, { useState } from 'react';
import { ClockIcon, UserCircleIcon, StarIcon } from '../icons';
import { BackendService, BackendCategory, TarifaServicio } from '../../types';
import AvailabilityCalendar from './AvailabilityCalendar';

interface ServiceReservationModalProps {
    isOpen: boolean;
    onClose: () => void;
    service: BackendService | null;
    category?: BackendCategory;
}

const ServiceReservationModal: React.FC<ServiceReservationModalProps> = ({ isOpen, onClose, service, category }) => {
    const [reservationData, setReservationData] = useState({
        date: '',
        time: '',
        observations: ''
    });

    if (!isOpen || !service) return null;

    const getImageUrl = (imagePath: string | null) => {
        if (!imagePath) return null;
        const baseUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
        return `${baseUrl}${imagePath}`;
    };

    const getTimeAgo = (dateString: string) => {
        const now = new Date();
        const publishDate = new Date(dateString);
        const diffInMs = now.getTime() - publishDate.getTime();
        const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
        
        if (diffInDays === 0) return 'hoy';
        if (diffInDays === 1) return 'hace 1 día';
        if (diffInDays < 7) return `hace ${diffInDays} días`;
        if (diffInDays < 30) {
            const weeks = Math.floor(diffInDays / 7);
            return weeks === 1 ? 'hace 1 semana' : `hace ${weeks} semanas`;
        }
        if (diffInDays < 365) {
            const months = Math.floor(diffInDays / 30);
            return months === 1 ? 'hace 1 mes' : `hace ${months} meses`;
        }
        const years = Math.floor(diffInDays / 365);
        return years === 1 ? 'hace 1 año' : `hace ${years} años`;
    };

    const formatPriceProfessional = (price: number, service: BackendService) => {
        // Usar la lógica de mapeo de moneda de la versión original
        let serviceCurrency = null;

        // Primero intentar mapear por ID de moneda (más confiable)
        if (service.id_moneda) {
            switch (service.id_moneda) {
                case 1: // Guaraní
                    serviceCurrency = 'PYG';
                    break;
                case 2: // Dólar
                    serviceCurrency = 'USD';
                    break;
                case 3: // Real
                    serviceCurrency = 'BRL';
                    break;
                case 4: // Peso Argentino
                    serviceCurrency = 'ARS';
                    break;
                default:
                    serviceCurrency = 'PYG'; // Fallback a Guaraní
            }
        }

        // Si no hay ID de moneda, usar código ISO limpio como fallback
        if (!serviceCurrency && service.codigo_iso_moneda) {
            serviceCurrency = service.codigo_iso_moneda.trim();
        }

        // Si aún no hay moneda, asumir Guaraní
        if (!serviceCurrency) {
            serviceCurrency = 'PYG';
        }

        const currencySymbol = serviceCurrency === 'USD' ? '$' :
                              serviceCurrency === 'BRL' ? 'R$' :
                              serviceCurrency === 'ARS' ? '$' : '₲';

        if (serviceCurrency === 'USD') {
            return `${currencySymbol} ${price.toLocaleString('en-US')}`;
        } else if (serviceCurrency === 'BRL') {
            return `${currencySymbol} ${price.toLocaleString('pt-BR')}`;
        } else if (serviceCurrency === 'ARS') {
            return `${currencySymbol} ${price.toLocaleString('es-AR')}`;
        } else {
            return `${currencySymbol} ${price.toLocaleString('es-PY')}`;
        }
    };

    const formatTarifaPrice = (monto: number, service: BackendService) => {
        // Usar la misma lógica de mapeo de moneda
        let serviceCurrency = null;

        if (service.id_moneda) {
            switch (service.id_moneda) {
                case 1: serviceCurrency = 'PYG'; break;
                case 2: serviceCurrency = 'USD'; break;
                case 3: serviceCurrency = 'BRL'; break;
                case 4: serviceCurrency = 'ARS'; break;
                default: serviceCurrency = 'PYG';
            }
        }

        if (!serviceCurrency && service.codigo_iso_moneda) {
            serviceCurrency = service.codigo_iso_moneda.trim();
        }

        if (!serviceCurrency) {
            serviceCurrency = 'PYG';
        }

        const currencySymbol = serviceCurrency === 'USD' ? '$' :
                              serviceCurrency === 'BRL' ? 'R$' :
                              serviceCurrency === 'ARS' ? '$' : '₲';

        if (serviceCurrency === 'USD') {
            return `${currencySymbol} ${monto.toLocaleString('en-US')}`;
        } else if (serviceCurrency === 'BRL') {
            return `${currencySymbol} ${monto.toLocaleString('pt-BR')}`;
        } else if (serviceCurrency === 'ARS') {
            return `${currencySymbol} ${monto.toLocaleString('es-AR')}`;
        } else {
            return `${currencySymbol} ${monto.toLocaleString('es-PY')}`;
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!service || !reservationData.date || !reservationData.time) {
            alert('Por favor selecciona una fecha y hora disponible');
            return;
        }

        try {
               const API_URL = import.meta.env.VITE_API_URL || 'https://backend-production-ee3b.up.railway.app';
            
            // Crear la reserva
            const reservaData = {
                id_servicio: service.id_servicio,
                descripcion: reservationData.observations || `Reserva para ${service.nombre}`,
                observacion: reservationData.observations || null,
                fecha: reservationData.date
            };

            const response = await fetch(`${API_URL}/api/v1/reservas`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(reservaData),
            });

            if (!response.ok) {
                throw new Error('Error al crear la reserva');
            }

            const result = await response.json();
            console.log('Reserva creada:', result);
            
            alert('Reserva creada exitosamente. El proveedor se pondrá en contacto contigo.');
            onClose();
        } catch (error) {
            console.error('Error al crear reserva:', error);
            alert('Error al crear la reserva. Por favor intenta nuevamente.');
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-7xl w-full max-h-[95vh] overflow-y-auto">
                <div className="p-8">
                    {/* ENCABEZADO PROFESIONAL */}
                    <div className="flex justify-between items-start mb-8">
                        <div className="flex-1">
                            <h1 className="text-3xl font-bold text-slate-900 mb-4">{service.nombre}</h1>
                            <div className="flex items-center gap-4">
                                {category && (
                                    <span className="px-4 py-2 bg-primary-600 text-white rounded-full font-medium text-sm">
                                        {category.nombre}
                                    </span>
                                )}
                                <span className="flex items-center gap-2 text-sm text-slate-600">
                                    <ClockIcon className="w-4 h-4" />
                                    Publicado {getTimeAgo(service.created_at)}
                                </span>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-slate-400 hover:text-slate-600 text-3xl ml-4 p-2 hover:bg-slate-100 rounded-full transition-colors"
                        >
                            ✕
                        </button>
                    </div>

                    {/* CONTENIDO PRINCIPAL - DISTRIBUCIÓN EN DOS COLUMNAS */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* COLUMNA IZQUIERDA - INFORMACIÓN DEL SERVICIO Y PROVEEDOR */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* IMAGEN DESTACADA DEL SERVICIO */}
                            {service.imagen && (
                                <div className="relative">
                                    <img 
                                        src={getImageUrl(service.imagen)} 
                                        alt={service.nombre}
                                        className="w-full h-64 object-cover rounded-xl shadow-lg"
                                        onError={(e) => {
                                            const target = e.target as HTMLImageElement;
                                            target.style.display = 'none';
                                        }}
                                    />
                                </div>
                            )}

                            {/* SECCIÓN: DESCRIPCIÓN DEL SERVICIO */}
                            <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
                                <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-primary-600 rounded-full"></span>
                                    Descripción del Servicio
                                </h2>
                                <p className="text-slate-700 leading-relaxed">{service.descripcion}</p>
                            </div>

                            {/* SECCIÓN: INFORMACIÓN DEL PROVEEDOR */}
                            <div className="bg-white border border-slate-200 rounded-xl p-6">
                                <h2 className="text-xl font-semibold text-slate-900 mb-6 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-primary-600 rounded-full"></span>
                                    Información del Proveedor
                                </h2>
                                
                                {/* Avatar y nombre del proveedor */}
                                <div className="flex items-start gap-4 mb-6">
                                    <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg flex-shrink-0">
                                        <UserCircleIcon className="w-8 h-8 text-white" />
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="text-lg font-semibold text-slate-900 mb-4">
                                            {service.nombre_contacto || 'Contacto disponible'}
                                        </h3>
                                        
                                        {/* Lista organizada de información del proveedor */}
                                        <div className="space-y-3">
                                            <div className="flex items-center gap-3">
                                                <span className="text-slate-500">🏢</span>
                                                <span className="text-slate-700">
                                                    <span className="font-medium">Empresa:</span> {service.razon_social || 'Información disponible al contactar'}
                                                </span>
                                            </div>
                                            
                                            {service.departamento && (
                                                <div className="flex items-center gap-3">
                                                    <span className="text-slate-500">🗺️</span>
                                                    <span className="text-slate-700">
                                                        <span className="font-medium">Departamento:</span> {service.departamento}
                                                    </span>
                                                </div>
                                            )}
                                            
                                            {service.ciudad && (
                                                <div className="flex items-center gap-3">
                                                    <span className="text-slate-500">📍</span>
                                                    <span className="text-slate-700">
                                                        <span className="font-medium">Ciudad:</span> {service.ciudad}
                                                    </span>
                                                </div>
                                            )}
                                            
                                            {service.barrio && (
                                                <div className="flex items-center gap-3">
                                                    <span className="text-slate-500">🏘️</span>
                                                    <span className="text-slate-700">
                                                        <span className="font-medium">Barrio:</span> {service.barrio}
                                                    </span>
                                                </div>
                                            )}
                                            
                                            <div className="flex items-center gap-3">
                                                <span className="text-slate-500">✅</span>
                                                <span className="text-slate-700">
                                                    <span className="font-medium">Estado:</span> 
                                                    <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                                                        service.estado ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                    }`}>
                                                        {service.estado ? 'Activo' : 'Inactivo'}
                                                    </span>
                                                </span>
                                            </div>
                                            
                                            <div className="flex items-center gap-3">
                                                <span className="text-slate-500">📊</span>
                                                <span className="text-slate-700">
                                                    <span className="font-medium">Reservas completadas:</span> 
                                                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                                                        0
                                                    </span>
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Calificación destacada */}
                                <div className="border-t border-slate-200 pt-4">
                                    <div className="flex items-center gap-3">
                                        <div className="flex items-center gap-1">
                                            {Array.from({ length: 5 }, (_, i) => (
                                                <StarIcon key={i} className="w-5 h-5 text-amber-400" />
                                            ))}
                                        </div>
                                        <span className="text-slate-700 font-medium">5.0 (0 reseñas)</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* COLUMNA DERECHA - PRECIOS Y FORMULARIO */}
                        <div className="lg:col-span-1 space-y-6">
                            {/* SECCIÓN: PRECIOS Y TARIFAS */}
                            <div className="bg-gradient-to-br from-primary-50 to-blue-50 border border-primary-200 rounded-xl p-6">
                                <h2 className="text-xl font-semibold text-slate-900 mb-6 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-primary-600 rounded-full"></span>
                                    Precios y Tarifas
                                </h2>
                                
                                <div className="space-y-6">
                                    {/* Precio principal destacado */}
                                    <div className="text-center bg-white rounded-lg p-6 border border-primary-200">
                                        <span className="text-3xl font-bold text-primary-600">
                                            Desde {service.precio ? formatPriceProfessional(service.precio, service) : '₲ 0'}
                                        </span>
                                    </div>
                                    
                                    {/* Tarifas específicas si existen */}
                                    {service.tarifas && service.tarifas.length > 0 && (
                                        <div className="bg-white rounded-lg p-4 border border-slate-200">
                                            <h4 className="font-medium text-slate-900 mb-4">Tarifas Específicas</h4>
                                            <div className="space-y-3">
                                                {service.tarifas.map((tarifa) => (
                                                    <div key={tarifa.id_tarifa_servicio} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                                                        <div className="flex justify-between items-start mb-2">
                                                            <div className="flex-1">
                                                                <p className="font-medium text-slate-900 text-sm">{tarifa.descripcion}</p>
                                                                {tarifa.nombre_tipo_tarifa && (
                                                                    <span className="inline-block px-2 py-1 bg-primary-100 text-primary-700 text-xs font-medium rounded-full mt-1">
                                                                        {tarifa.nombre_tipo_tarifa}
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <div className="text-right ml-4">
                                                                <span className="font-bold text-primary-600 text-lg">
                                                                    {formatTarifaPrice(tarifa.monto, service)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center justify-between text-xs text-slate-500">
                                                            <span>
                                                                📅 {new Date(tarifa.fecha_inicio).toLocaleDateString('es-PY')}
                                                                {tarifa.fecha_fin && ` - ${new Date(tarifa.fecha_fin).toLocaleDateString('es-PY')}`}
                                                            </span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Detalle de tarifas adicionales si no hay tarifas específicas */}
                                    {(!service.tarifas || service.tarifas.length === 0) && (
                                        <div className="bg-white rounded-lg p-4 border border-slate-200">
                                            <h4 className="font-medium text-slate-900 mb-2">Tarifas adicionales</h4>
                                            <p className="text-sm text-slate-600">
                                                Presupuesto personalizado según requerimientos específicos del proyecto
                                            </p>
                                        </div>
                                    )}
                                    
                                    {/* Nota informativa */}
                                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                        <p className="text-sm text-blue-800 text-center">
                                            💡 Los precios finales se acuerdan según el alcance del trabajo
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN: FORMULARIO DE RESERVA */}
                            <div className="bg-white border border-slate-200 rounded-xl p-6">
                                <h2 className="text-xl font-semibold text-slate-900 mb-6 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-primary-600 rounded-full"></span>
                                    Reservar Servicio
                                </h2>

                                <form onSubmit={handleSubmit} className="w-full space-y-5">
                                    {/* Calendario inteligente con disponibilidades */}
                                    <AvailabilityCalendar
                                        serviceId={service.id_servicio}
                                        onDateSelect={(date, time) => {
                                            setReservationData(prev => ({ 
                                                ...prev, 
                                                date, 
                                                time 
                                            }));
                                        }}
                                        selectedDate={reservationData.date}
                                        selectedTime={reservationData.time}
                                    />

                                    <div className="space-y-2">
                                        <label htmlFor="observations" className="block text-sm font-medium text-slate-700">
                                            📝 Observaciones (opcional)
                                        </label>
                                        <textarea
                                            id="observations"
                                            rows={4}
                                            value={reservationData.observations}
                                            onChange={(e) => setReservationData(prev => ({ ...prev, observations: e.target.value }))}
                                            placeholder="Describe los detalles específicos del servicio que necesitas..."
                                            className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none transition-colors duration-200"
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        className="w-full btn-blue touch-manipulation"
                                        disabled={!reservationData.date || !reservationData.time}
                                    >
                                        🚀 Reservar
                                    </button>
                                </form>

                                {/* Nota de confianza */}
                                <div className="mt-6 text-center">
                                    <p className="text-xs text-slate-500">
                                        El proveedor se pondrá en contacto contigo en las próximas 24 horas
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ServiceReservationModal;