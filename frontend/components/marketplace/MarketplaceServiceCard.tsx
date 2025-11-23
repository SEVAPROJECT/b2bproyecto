
import React, { memo } from 'react';
import { StarIcon, BuildingStorefrontIcon, ClockIcon, LockClosedIcon } from '../icons';
import { BackendService, BackendCategory } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { API_CONFIG } from '../../config/api';

interface MarketplaceServiceCardProps {
    service: BackendService;
    category?: BackendCategory;
    onViewProviders: (serviceId: number) => void;
    onReservar: (service: BackendService) => void;
    isAuthenticated?: boolean;
}

const MarketplaceServiceCard: React.FC<MarketplaceServiceCardProps> = memo(({ service, category, onViewProviders, onReservar, isAuthenticated: propIsAuthenticated }) => {
    const { isAuthenticated: contextIsAuthenticated } = useAuth();
    const isAuthenticated = propIsAuthenticated ?? contextIsAuthenticated;
    
    // Debug: verificar autenticación (comentado para evitar spam)
    // console.log('🔐 Auth debug:', {
    //     contextIsAuthenticated: contextIsAuthenticated,
    //     propIsAuthenticated: propIsAuthenticated,
    //     finalIsAuthenticated: isAuthenticated
    // });
    
    // Debug: verificar estructura del servicio (comentado para evitar spam)
    // console.log('🃏 Service data:', {
    //     id: service.id_servicio,
    //     nombre: service.nombre,
    //     razon_social: service.razon_social,
    //     departamento: service.departamento,
    //     ciudad: service.ciudad,
    //     precio: service.precio,
    //     moneda: (service as any).moneda
    // });
    const getImageUrl = (imagePath: string | null) => {
        if (!imagePath) return null;
        
        // Si es una URL completa (Supabase Storage o iDrive), usarla directamente
        if (imagePath.startsWith('http')) {
            return imagePath;
        }
        
        // Si es una ruta local, construir URL completa
        const baseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
        return `${baseUrl}${imagePath}`;
    };

    // Función helper para obtener la moneda del servicio
    const getServiceCurrency = (service: BackendService): string => {
        // Primero intentar mapear por ID de moneda (más confiable)
        if (service.id_moneda) {
            switch (service.id_moneda) {
                case 1:
                    return 'GS';
                case 2:
                    return 'USD';
                case 3:
                    return 'BRL';
                case 4:
                case 8:
                    return 'ARS';
                default:
                    return 'GS';
            }
        }

        // Si no hay ID de moneda, intentar usar código ISO si está disponible
        // Nota: codigo_iso_moneda puede no estar en el tipo BackendService
        const serviceWithIso = service as BackendService & { codigo_iso_moneda?: string };
        if (serviceWithIso.codigo_iso_moneda) {
            return serviceWithIso.codigo_iso_moneda.trim();
        }

        // Si aún no hay moneda, asumir Guaraní
        return 'GS';
    };

    // Función helper para obtener el símbolo de la moneda
    const getCurrencySymbol = (currency: string): string => {
        if (currency === 'USD') return '$';
        if (currency === 'BRL') return 'R$';
        if (currency === 'ARS') return '$';
        return '₲';
    };

    // Función helper para formatear el precio según la moneda
    const formatPriceByCurrency = (price: number, currency: string): string => {
        const symbol = getCurrencySymbol(currency);
        if (currency === 'USD') {
            return `${symbol} ${price.toLocaleString('en-US')}`;
        }
        if (currency === 'BRL') {
            return `${symbol} ${price.toLocaleString('pt-BR')}`;
        }
        if (currency === 'ARS') {
            return `${symbol} ${price.toLocaleString('es-AR')}`;
        }
        return `${symbol} ${price.toLocaleString('es-PY')}`;
    };

    const formatPriceProfessional = (price: number, service: BackendService) => {
        const serviceCurrency = getServiceCurrency(service);
        return formatPriceByCurrency(price, serviceCurrency);
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

    return (
        <div className="service-card-uniform bg-white rounded-xl shadow-md border border-slate-200/80 overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-1 h-full flex flex-col">
            {/* Imagen del servicio - altura fija para uniformidad */}
            <div className="h-40 bg-gradient-to-br from-primary-100 to-primary-200 relative overflow-hidden flex-shrink-0">
                {service.imagen ? (
                    <img
                        src={getImageUrl(service.imagen)}
                        alt={`Imagen de ${service.nombre}`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const parent = target.parentElement;
                            if (parent) {
                                parent.innerHTML = `
                                    <div class="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary-100 to-primary-200">
                                        <svg class="w-16 h-16 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                        </svg>
                                    </div>
                                `;
                            }
                        }}
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <svg className="w-16 h-16 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                    </div>
                )}

                {/* Chip de categoría - estilo azul con blanco */}
                {category && (
                    <div className="absolute top-3 left-3">
                        <span className="px-3 py-1 bg-primary-600 text-white text-xs font-semibold rounded-full shadow-sm">
                            {category.nombre}
                        </span>
                    </div>
                )}
            </div>

            {/* Contenido - uniforme y bien distribuido */}
            <div className="card-content p-4 flex flex-col h-full">
                {/* Título - tamaño uniforme */}
                <h3 className="text-base font-semibold text-slate-900 mb-4 leading-tight">
                    {service.nombre}
                </h3>

                {/* Información de la empresa y ubicación - compacta y bien organizada */}
                <div className="mb-4 space-y-2">
                    {/* Empresa - línea compacta */}
                    <div className="flex items-center gap-2">
                        <div className="w-5 h-5 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <BuildingStorefrontIcon className="w-3 h-3 text-primary-600" />
                        </div>
                        <p className="text-sm font-medium text-slate-700 truncate">
                            {service.razon_social || 'Empresa verificada'}
                        </p>
                    </div>
                    
                    {/* Ubicación - línea compacta */}
                    <div className="flex items-center gap-1 text-xs text-slate-500">
                        {service.departamento && (
                            <span className="truncate">🗺️ {service.departamento}</span>
                        )}
                        {service.ciudad && service.departamento && (
                            <span>•</span>
                        )}
                        {service.ciudad && (
                            <span className="truncate">📍 {service.ciudad}</span>
                        )}
                        {!service.departamento && !service.ciudad && (
                            <span className="text-slate-400">Ubicación no especificada</span>
                        )}
                    </div>
                    
                    {/* Tiempo y estrellas - línea compacta */}
                    <div className="flex items-center justify-between text-xs text-slate-500">
                        <div className="flex items-center gap-1">
                            <ClockIcon className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">{getTimeAgo(service.created_at)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            {Array.from({ length: 5 }, (_, i) => (
                                <StarIcon key={i} className="w-3 h-3 text-slate-300" />
                            ))}
                            <span className="ml-1">(0)</span>
                        </div>
                    </div>
                </div>
                    
                {/* Precio y botón - sección fija en la parte inferior */}
                <div className="card-footer mt-auto space-y-3">
                    <div className="text-center">
                        <span className="text-lg font-bold text-primary-600">
                            Desde {service.precio ? formatPriceProfessional(service.precio, service) : '₲ 0'}
                        </span>
                    </div>

                    {/* Botón de acción - uniforme */}
                    {isAuthenticated ? (
                        <button
                            onClick={() => onReservar(service)}
                            className="w-full btn-blue touch-manipulation"
                        >
                            Reservar
                        </button>
                    ) : (
                        <button
                            onClick={() => onViewProviders(service.id_servicio)}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-200 transition-colors touch-manipulation"
                        >
                            <LockClosedIcon className="w-4 h-4" />
                            <span>Iniciar sesión para reservar</span>
                        </button>
                    )}
                </div>
            </div>

        </div>
    );
});

export default MarketplaceServiceCard;
