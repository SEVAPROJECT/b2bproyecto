import React, { useState } from 'react';
import { ClockIcon, UserCircleIcon, StarIcon } from '../icons';
import { BackendService, BackendCategory } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import AvailabilityCalendar from './AvailabilityCalendar';
import { formatPriceProfessional, getTimeAgo, getServiceImageUrl, formatPriceByCurrency, getServiceCurrency } from '../../utils/formatting';
import { buildApiUrl } from '../../config/api';

interface ServiceReservationModalProps {
    isOpen: boolean;
    onClose: () => void;
    service: BackendService | null;
    category?: BackendCategory;
}

const ServiceReservationModal: React.FC<ServiceReservationModalProps> = ({ isOpen, onClose, service, category }) => {
    const { user, isAuthenticated } = useAuth();
    const [reservationData, setReservationData] = useState({
        date: '',
        time: '',
        observations: ''
    });

    if (!isOpen || !service) return null;

    const formatTarifaPrice = (monto: number, service: BackendService) => {
        const serviceCurrency = getServiceCurrency(service);
        return formatPriceByCurrency(monto, serviceCurrency);
    };

    // Función helper para validar los datos de entrada
    const validateReservationData = (): boolean => {
        if (!service || !reservationData.date || !reservationData.time) {
            alert('Por favor selecciona una fecha y hora disponible');
            return false;
        }
        if (!isAuthenticated || !user) {
            alert('Debes estar autenticado para crear una reserva');
            return false;
        }
        return true;
    };

    // Función helper para construir los datos de la reserva
    const buildReservationData = () => {
        return {
            id_servicio: Number.parseInt(service.id_servicio.toString(), 10),
            descripcion: reservationData.observations || `Reserva para ${service.nombre}`,
            observacion: reservationData.observations || null,
            fecha: reservationData.date,
            hora_inicio: reservationData.time || null
        };
    };

    // Función helper para extraer el mensaje de error de la respuesta
    const extractErrorMessage = async (response: Response): Promise<string> => {
        let errorMessage = 'Error al crear la reserva';
        
        try {
            const errorData = await response.json();
            console.log('🔍 [FRONTEND] Error del backend:', errorData);
            
            if (typeof errorData === 'string') {
                return errorData;
            }
            
            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    return errorData.detail.map(err => err.msg || err.message || err).join(', ');
                }
                return errorData.detail;
            }
            
            if (errorData.message) {
                return errorData.message;
            }
            
            if (errorData.error) {
                return errorData.error;
            }
            
            return JSON.stringify(errorData);
        } catch {
            console.log('🔍 [FRONTEND] No se pudo parsear error JSON');
            try {
                const errorText = await response.text();
                if (errorText) {
                    return errorText;
                }
            } catch {
                console.log('🔍 [FRONTEND] No se pudo obtener texto de error');
            }
        }
        
        return errorMessage;
    };

    // Función helper para realizar la petición HTTP
    const createReservationRequest = async (reservaData: any): Promise<Response> => {
        const API_URL = buildApiUrl('/reservas/crear');
        console.log('🔍 [FRONTEND] API_URL:', API_URL);
        console.log('🔍 [FRONTEND] Datos a enviar:', reservaData);
        console.log('🔍 [FRONTEND] AccessToken:', user.accessToken ? 'Presente' : 'No presente');
        console.log('🔍 [FRONTEND] Enviando petición POST...');
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${user.accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(reservaData),
        });
        
        console.log('🔍 [FRONTEND] Respuesta recibida:', response.status, response.statusText);
        return response;
    };

    // Función helper para manejar la respuesta exitosa
    const handleSuccessResponse = async (response: Response) => {
        const result = await response.json();
        console.log('✅ [FRONTEND] Reserva creada exitosamente:', result);
        alert('Reserva creada exitosamente. El proveedor se pondrá en contacto contigo.');
        onClose();
    };

    // Función helper para manejar errores
    const handleError = (error: unknown) => {
        console.error('❌ [FRONTEND] Error al crear reserva:', error);
        console.log('❌ [FRONTEND] ========== FIN CREAR RESERVA CON ERROR ==========');
        
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido al crear la reserva';
        alert(`Error al crear la reserva: ${errorMessage}\n\nPor favor intenta nuevamente.`);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        console.log('🔍 [FRONTEND] ========== INICIO CREAR RESERVA ==========');
        console.log('🔍 [FRONTEND] Service:', service);
        console.log('🔍 [FRONTEND] ReservationData:', reservationData);
        console.log('🔍 [FRONTEND] User:', user);
        console.log('🔍 [FRONTEND] IsAuthenticated:', isAuthenticated);
        
        if (!validateReservationData()) {
            return;
        }

        try {
            const reservaData = buildReservationData();
            const response = await createReservationRequest(reservaData);

            if (!response.ok) {
                const errorMessage = await extractErrorMessage(response);
                throw new Error(`Error ${response.status}: ${errorMessage}`);
            }

            await handleSuccessResponse(response);
        } catch (error) {
            handleError(error);
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
                                        src={getServiceImageUrl(service.imagen) || undefined} 
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
                                    <span>Descripción del Servicio</span>
                                </h2>
                                <p className="text-slate-700 leading-relaxed">{service.descripcion}</p>
                            </div>

                            {/* SECCIÓN: INFORMACIÓN DEL PROVEEDOR */}
                            <div className="bg-white border border-slate-200 rounded-xl p-6">
                                <h2 className="text-xl font-semibold text-slate-900 mb-6 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-primary-600 rounded-full"></span>
                                    <span>Información del Proveedor</span>
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
                                    <span>Precios y Tarifas</span>
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
                                    <span>Reservar Servicio</span>
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