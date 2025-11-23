import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { MagnifyingGlassIcon, SparklesIcon, ExclamationCircleIcon } from '../icons';
import MarketplaceServiceCard from './MarketplaceServiceCard';
import ServiceReservationModal from './ServiceReservationModal';
import { BackendService, BackendCategory } from '../../types';
import { categoriesAPI, servicesAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { buildBackendFilters, filterServices } from '../../utils/marketplaceFilters';
import { buildApiUrl } from '../../config/api';
import { locationsAPI } from '../../services/locations';

// Función helper para calcular el offset de paginación
const calculateOffset = (page: number, itemsPerPage: number): number => {
    return (page - 1) * itemsPerPage;
};

// Función helper para obtener el token de acceso
const getAccessToken = (user: any): string | undefined => {
    return user?.accessToken || localStorage.getItem('access_token') || undefined;
};

// Interfaz para los setters de estado
interface DataStateSetters {
    setTotalServices: (value: number) => void;
    setServices: (services: BackendService[]) => void;
    setCategories: (categories: BackendCategory[]) => void;
    setUsingMockData: (value: boolean) => void;
    setCurrentPage: (page: number) => void;
}

// Interfaz para los datos de respuesta
interface UpdateDataStatesParams {
    setters: DataStateSetters;
    filteredResponse: any;
    categoriesData: BackendCategory[];
    page?: number;
}

// Función helper para actualizar estados después de cargar datos
const updateDataStates = (params: UpdateDataStatesParams) => {
    const { setters, filteredResponse, categoriesData, page } = params;
    setters.setTotalServices(filteredResponse.pagination.total);
    setters.setServices(filteredResponse.services);
    setters.setCategories(categoriesData);
    setters.setUsingMockData(false);
    if (page !== undefined) {
        setters.setCurrentPage(page);
    }
};

// Función helper para verificar si hay filtros activos
const hasActiveFilters = (
    priceRange: number[],
    currencyFilter: string,
    categoryFilter: string,
    departmentFilter: string,
    cityFilter: string,
    searchQuery: string
): boolean => {
    return priceRange[0] > 0 || 
           priceRange[1] < 1000000000 || 
           currencyFilter !== 'all' || 
           categoryFilter !== 'all' || 
           departmentFilter !== 'all' || 
           cityFilter !== 'all' ||
           searchQuery.trim() !== '';
};

// Función helper para calcular el total de páginas con servidor filtrado
const calculateTotalPagesWithServer = (totalServices: number, itemsPerPage: number): number => {
    return Math.ceil(totalServices / itemsPerPage);
};

// Función helper para calcular el total de páginas con filtros locales
const calculateTotalPagesWithLocalFilters = (filteredServicesLength: number, itemsPerPage: number): number => {
    return Math.ceil(filteredServicesLength / itemsPerPage);
};

// Función helper para convertir resultados de IA al formato esperado
const convertAIResultsToServices = (results: any[]): BackendService[] => {
    return results.map((result: any) => ({
        id_servicio: result.id_servicio,
        nombre: result.nombre,
        descripcion: result.descripcion,
        precio: result.precio,
        categoria: result.categoria,
        empresa: result.empresa,
        id_categoria: 1,
        razon_social: result.empresa,
        departamento: '',
        ciudad: '',
        codigo_iso_moneda: 'GS',
        simbolo_moneda: '₲',
        id_moneda: 1,
        created_at: new Date().toISOString(),
        estado: 'activo'
    }));
};

// Función helper para determinar el tiempo de debounce según el tipo de cambio
const getDebounceTime = (priceRange: number[]): number => {
    const isSliderChange = priceRange[0] > 0 || priceRange[1] < 1000000000;
    return isSliderChange ? 500 : 100;
};

// Componente para el estado de carga
const LoadingState: React.FC = () => (
    <div className="bg-slate-50 min-h-screen">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                    <p className="mt-4 text-slate-600">Cargando servicios...</p>
                </div>
            </div>
        </div>
    </div>
);

// Componente para el estado de error
interface ErrorStateProps {
    error: string;
    onRetry: () => void;
}

const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry }) => (
    <div className="bg-slate-50 min-h-screen">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="bg-white p-8 rounded-xl shadow-md border border-slate-200/80">
                <div className="text-center py-12">
                    <ExclamationCircleIcon className="mx-auto h-12 w-12 text-red-400" />
                    <h3 className="mt-2 text-lg font-semibold text-slate-800">Error al cargar</h3>
                    <p className="mt-1 text-sm text-slate-500">{error}</p>
                    <button onClick={onRetry} className="mt-4 btn-blue touch-manipulation">
                        <span>Reintentar</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
);

// Componente para la barra de búsqueda
interface SearchBarProps {
    searchQuery: string;
    isSearching: boolean;
    isAISearching: boolean;
    onSearchQueryChange: (value: string) => void;
    onSearch: () => void;
    onAISearch: () => void;
}

const SearchBar: React.FC<SearchBarProps> = ({
    searchQuery,
    isSearching,
    isAISearching,
    onSearchQueryChange,
    onSearch,
    onAISearch
}) => (
    <div className="mt-6 space-y-4">
        <div className="relative">
            <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchQueryChange(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                placeholder="Buscar servicios profesionales..."
                className="w-full pl-11 pr-4 py-2.5 sm:py-3 rounded-lg border-2 border-slate-300 focus:ring-primary-500 focus:border-primary-500 transition text-sm sm:text-base"
                disabled={isSearching}
            />
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-slate-400" />
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
            <button
                onClick={onSearch}
                disabled={isSearching || isAISearching}
                className="flex-1 sm:flex-initial btn-blue disabled:opacity-50 touch-manipulation"
            >
                {isSearching ? (
                    <div className="flex items-center justify-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Buscando...</span>
                    </div>
                ) : (
                    <div className="flex items-center justify-center gap-2">
                        <MagnifyingGlassIcon className="w-4 h-4 flex-shrink-0" />
                        <span>Buscar servicio</span>
                    </div>
                )}
            </button>
            <button
                onClick={onAISearch}
                disabled={isSearching || isAISearching}
                className="flex-1 sm:flex-initial btn-purple disabled:opacity-50 touch-manipulation"
            >
                {isAISearching ? (
                    <div className="flex items-center justify-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Procesando IA...</span>
                    </div>
                ) : (
                    <div className="flex items-center justify-center gap-2">
                        <SparklesIcon className="w-4 h-4 flex-shrink-0" />
                        <span>Buscar con IA</span>
                    </div>
                )}
            </button>
        </div>
    </div>
);

// Componente para el encabezado
interface HeaderProps {
    usingMockData: boolean;
    dataVersion: number;
}

const Header: React.FC<HeaderProps> = ({ usingMockData, dataVersion }) => (
    <div className="text-center sm:text-left mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
            <h1 className="text-3xl font-bold text-gray-900">
                Servicios profesionales de calidad
            </h1>
            {usingMockData && (
                <div className="flex items-center gap-2 px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-medium">
                    <span>⚠️</span>
                    <span>Datos de prueba v{dataVersion}</span>
                </div>
            )}
        </div>
        <p className="mt-1 text-sm text-gray-500">
            Explorá categorías, filtrá por fecha y encontrá los servicios ideales para hacer crecer tu negocio. Todo en un solo lugar.
        </p>
    </div>
);

const MarketplacePage: React.FC = () => {
    const { isAuthenticated, user } = useAuth();
    
    // Debug: verificar autenticación en MarketplacePage
    console.log('🔐 MarketplacePage Auth debug:', {
        user: user,
        isAuthenticated: isAuthenticated
    });
    
    // Estados principales
    const [services, setServices] = useState<BackendService[]>([]);
    const [categories, setCategories] = useState<BackendCategory[]>([]);
    const [departments, setDepartments] = useState<string[]>([]);
    const [cities, setCities] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isSearching, setIsSearching] = useState(false);
    const [usingMockData, setUsingMockData] = useState(false);
    const dataVersion = Date.now(); // Versión estática para mostrar en el header
    const dataLoadedRef = useRef(false); // Para evitar cargas duplicadas
    const reloadFilteredDataRef = useRef<((page?: number, showFullLoading?: boolean) => Promise<void>) | null>(null);
    const getBackendFiltersRef = useRef<(() => Record<string, any>) | null>(null);
    
    // Estados para paginación del backend
    const [totalServices, setTotalServices] = useState<number>(0);
    const [isLoadingPage, setIsLoadingPage] = useState(false);
    const [isLoadingFilters, setIsLoadingFilters] = useState(false);

    // Estados de filtros
    const [searchQuery, setSearchQuery] = useState('');
    const [dateFilter, setDateFilter] = useState('all');
    const [categoryFilter, setCategoryFilter] = useState('all');
    const [ratingFilter, setRatingFilter] = useState(0);
    const [currencyFilter, setCurrencyFilter] = useState('all');
    const [priceFilter, setPriceFilter] = useState('all');
    const [priceRange, setPriceRange] = useState([0, 1000000000]);
    const [sliderValue, setSliderValue] = useState(1000000000); // Estado temporal para mostrar el valor mientras se arrastra
    
    // Sincronizar sliderValue con priceRange[1] cuando cambia priceRange externamente (solo si no viene del slider)
    const isSliderDraggingRef = useRef(false);
    
    useEffect(() => {
        if (!isSliderDraggingRef.current) {
            setSliderValue(priceRange[1]);
        }
    }, [priceRange[1]]);
    
    // Estados de filtros avanzados
    const [departmentFilter, setDepartmentFilter] = useState('all');
    const [cityFilter, setCityFilter] = useState('all');
    const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
    
    // Estados para rango personalizado de fechas
    const [customDateRange, setCustomDateRange] = useState({ start: '', end: '' });
    const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
    
    // Estados de paginación
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 5; // Cambiado de 12 a 5 servicios por página

    // Estados para modal de reserva
    const [showServiceReservationModal, setShowServiceReservationModal] = useState(false);
    const [showServiceDetail, setShowServiceDetail] = useState(false);
    const [selectedService, setSelectedService] = useState<BackendService | null>(null);

    // Estados separados para búsquedas
    const [isAISearching, setIsAISearching] = useState(false);

    // Ref para el dialog de filtros avanzados
    const advancedFiltersDialogRef = useRef<HTMLDialogElement>(null);


    // Función para construir filtros del backend (usando helper)
    const getBackendFilters = useCallback(() => {
        try {
            return buildBackendFilters({
                currencyFilter,
                priceRange,
                categoryFilter,
                departmentFilter,
                cityFilter,
                searchQuery,
                dateFilter,
                ratingFilter,
                customDateRange
            });
        } catch (error) {
            console.error('❌ Error construyendo filtros del backend:', error);
            // Retornar objeto vacío en caso de error
            return {};
        }
    }, [currencyFilter, priceRange, categoryFilter, departmentFilter, cityFilter, searchQuery, dateFilter, ratingFilter, customDateRange]);

    // Mantener referencia actualizada de getBackendFilters
    useEffect(() => {
        getBackendFiltersRef.current = getBackendFilters;
    }, [getBackendFilters]);

    // Cargar departamentos y ciudades para los filtros avanzados
    useEffect(() => {
        const loadDepartmentsAndCities = async () => {
            try {
                const departamentosData = await locationsAPI.getDepartamentos();
                // Convertir a array de strings (nombres) para los filtros
                setDepartments(departamentosData.map(dept => dept.nombre));
            } catch (error) {
                console.error('❌ Error cargando departamentos para filtros:', error);
                // Mantener array vacío si falla la carga
            }
        };
        loadDepartmentsAndCities();
    }, []);

    // Cargar ciudades cuando se selecciona un departamento
    useEffect(() => {
        const loadCitiesForDepartment = async () => {
            if (departmentFilter === 'all') {
                setCities([]);
                return;
            }

            try {
                // Buscar el departamento por nombre para obtener el ID
                const departamentosData = await locationsAPI.getDepartamentos();
                const departamento = departamentosData.find(d => d.nombre === departmentFilter);
                
                if (departamento) {
                    const ciudadesData = await locationsAPI.getCiudadesPorDepartamento(departamento.id_departamento);
                    // Convertir a array de strings (nombres) para los filtros
                    setCities(ciudadesData.map(ciudad => ciudad.nombre));
                } else {
                    setCities([]);
                }
            } catch (error) {
                console.error('❌ Error cargando ciudades para filtros:', error);
                setCities([]);
            }
        };
        loadCitiesForDepartment();
    }, [departmentFilter]);

    // Función helper para cargar datos de la API
    const fetchDataFromAPI = useCallback(async (pageToUse: number) => {
        const offset = calculateOffset(pageToUse, itemsPerPage);
        const accessToken = getAccessToken(user);
        const filters = getBackendFiltersRef.current ? getBackendFiltersRef.current() : {};
        
        const [filteredResponse, categoriesData] = await Promise.all([
            servicesAPI.getFilteredServices(itemsPerPage, offset, accessToken, filters),
            categoriesAPI.getCategories(undefined, true)
        ]);
        
        return { filteredResponse, categoriesData };
    }, [itemsPerPage, user]);

    // Función helper para manejar errores de API
    const handleAPIError = useCallback((apiError: any) => {
        console.error('❌ Error con API real:', apiError);
        setError('No se pudo conectar con el servidor. Por favor, verifica que el backend esté funcionando.');
        setServices([]);
        setCategories([]);
        setUsingMockData(false);
    }, []);

    // Cargar datos iniciales con paginación del backend
    const loadInitialData = useCallback(async (page?: number) => {
        const pageToUse = page ?? currentPage;
        console.log('🚀 Iniciando loadInitialData...', { page: pageToUse });
        
        try {
            setIsLoading(true);
            setError(null);
            
            try {
                const { filteredResponse, categoriesData } = await fetchDataFromAPI(pageToUse);
                
                updateDataStates({
                    setters: {
                        setTotalServices,
                        setServices,
                        setCategories,
                        setUsingMockData,
                        setCurrentPage
                    },
                    filteredResponse,
                    categoriesData,
                    page
                });
                
                console.log('✅ Datos filtrados del servidor aplicados correctamente');
            } catch (apiError) {
                handleAPIError(apiError);
                return;
            }
            
        } catch (err) {
            console.error('Error cargando datos:', err);
            setError('Error al cargar los datos. Por favor, intentá nuevamente.');
        } finally {
            setIsLoading(false);
            dataLoadedRef.current = true;
            console.log('✅ loadInitialData completado');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentPage, itemsPerPage, user, fetchDataFromAPI, handleAPIError]); // No incluir getBackendFilters para evitar bucles

    // Función helper para establecer el estado de loading apropiado
    const setLoadingState = useCallback((showFullLoading: boolean) => {
        if (showFullLoading) {
            setIsLoading(true);
        } else {
            setIsLoadingFilters(true);
        }
    }, []);

    // Función helper para limpiar el estado de loading apropiado
    const clearLoadingState = useCallback((showFullLoading: boolean) => {
        if (showFullLoading) {
            setIsLoading(false);
        } else {
            setIsLoadingFilters(false);
        }
    }, []);

    // Función helper para actualizar servicios después de recargar
    const updateServicesAfterReload = useCallback((filteredResponse: any, page?: number) => {
        setServices(filteredResponse.services);
        setTotalServices(filteredResponse.pagination.total);
        if (page !== undefined) {
            setCurrentPage(page);
        }
    }, []);

    // Función optimizada para recargar solo los datos filtrados (sin loading completo)
    const reloadFilteredData = useCallback(async (page?: number, showFullLoading: boolean = false) => {
        const pageToUse = page ?? currentPage;
        console.log('🔄 Recargando datos filtrados...', { page: pageToUse, showFullLoading });
        
        try {
            setLoadingState(showFullLoading);
            
            const offset = calculateOffset(pageToUse, itemsPerPage);
            const accessToken = getAccessToken(user);
            const filters = getBackendFiltersRef.current ? getBackendFiltersRef.current() : {};
            
            const filteredResponse = await servicesAPI.getFilteredServices(itemsPerPage, offset, accessToken, filters);
            
            updateServicesAfterReload(filteredResponse, page);
            console.log(`📄 Datos filtrados recargados: ${filteredResponse.services.length} servicios, total: ${filteredResponse.pagination.total}`);
            
        } catch (error) {
            console.error('❌ Error recargando datos filtrados:', error);
            setError('Error aplicando filtros. Inténtalo de nuevo.');
        } finally {
            clearLoadingState(showFullLoading);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentPage, itemsPerPage, user, setLoadingState, clearLoadingState, updateServicesAfterReload]); // No incluir getBackendFilters para evitar bucles

    // Mantener referencia actualizada de reloadFilteredData
    useEffect(() => {
        reloadFilteredDataRef.current = reloadFilteredData;
    }, [reloadFilteredData]);

    // Función para cargar una página específica (optimizada)
    const loadPage = useCallback(async (page: number) => {
        console.log(`🔄 loadPage ejecutándose para página ${page}`);
        
        // Evitar cargar la misma página
        if (page === currentPage) {
            console.log(`⚠️ Ya estás en la página ${page}, evitando recarga`);
            return;
        }
        
        // Usar reloadFilteredData con la página específica y loading de página
        setIsLoadingPage(true);
        try {
            await reloadFilteredData(page, false);
        } catch (error) {
            console.error('❌ Error cargando página:', error);
            setError('Error cargando la página. Inténtalo de nuevo.');
        } finally {
            setTimeout(() => setIsLoadingPage(false), 100);
        }
    }, [currentPage, reloadFilteredData]);

    useEffect(() => {
        console.log('🎯 useEffect ejecutándose - llamando loadInitialData');
        // Usar una función async inmediata para manejar el error
        (async () => {
            try {
                await loadInitialData();
            } catch (error) {
                console.error('❌ Error en loadInitialData desde useEffect:', error);
                setError('Error al cargar los datos iniciales. Por favor, intentá nuevamente.');
                setIsLoading(false);
            }
        })();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Solo ejecutar una vez al montar

    // Recargar datos cuando cambien los filtros (con debounce inteligente)
    // NOTA: No incluir reloadFilteredData en dependencias para evitar bucles con paginación
    useEffect(() => {
        // No ejecutar en el montaje inicial - solo cuando cambian los filtros después de la carga inicial
        if (!dataLoadedRef.current) {
            console.log('⏭️ Saltando recarga de filtros en montaje inicial');
            return;
        }
        
        // Verificar que reloadFilteredDataRef esté disponible
        if (!reloadFilteredDataRef.current) {
            console.log('⏭️ reloadFilteredDataRef no está disponible aún, saltando...');
            return;
        }
        
        console.log('🔄 Filtros cambiaron, recargando datos...');
        
        const debounceTime = getDebounceTime(priceRange);
        
        const timeoutId = setTimeout(() => {
            console.log(`🔄 Ejecutando recarga después de ${debounceTime}ms...`);
            
            console.log('🔄 Recargando datos desde página 1 (sin loading completo)...');
            const reloadFn = reloadFilteredDataRef.current;
            if (reloadFn) {
                reloadFn(1, false).catch((error) => {
                    console.error('❌ Error en reloadFilteredData desde useEffect:', error);
                });
            }
        }, debounceTime);
        
        return () => clearTimeout(timeoutId);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currencyFilter, priceRange, categoryFilter, departmentFilter, cityFilter, searchQuery, dateFilter, ratingFilter]);

    // Aplicar filtros automáticamente cuando cambien
    // TEMPORALMENTE DESHABILITADO PARA EVITAR BUCLE INFINITO
    // useEffect(() => {
    //     if (dataLoadedRef.current) {
    //         console.log('🔄 Filtros cambiaron, aplicando automáticamente...');
    //         applyFilters();
    //     }
    // }, [currencyFilter, priceRange, applyFilters]);

    // Efecto para aplicar filtros automáticamente cuando cambien
    // TEMPORALMENTE DESHABILITADO PARA DEBUGGING
    // useEffect(() => {
    //     // Solo aplicar filtros si ya se cargaron los datos iniciales
    //     if (dataLoadedRef.current && totalServices > 0) {
    //         console.log('🔄 Filtros cambiaron, aplicando automáticamente...');
    //         applyFilters();
    //     }
    // }, [searchQuery, categoryFilter, departmentFilter, cityFilter, currencyFilter, priceRange, dateFilter, applyFilters]);


    // Función para manejar búsqueda normal (filtros del backend)
    const handleSearch = useCallback(() => {
        setIsSearching(true);
        // Recargar datos con filtros aplicados
        reloadFilteredData().finally(() => {
            setIsSearching(false);
        });
    }, [reloadFilteredData]);

    // Función helper para realizar la búsqueda en Weaviate
    const searchWeaviate = useCallback(async (query: string) => {
        const weaviateSearchUrl = buildApiUrl('/weaviate/search-public');
        const response = await fetch(`${weaviateSearchUrl}?query=${encodeURIComponent(query)}&limit=10`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }, []);

    // Función helper para actualizar servicios con resultados de IA
    const updateServicesWithAIResults = useCallback((aiServices: BackendService[]) => {
        setServices(aiServices);
        setTotalServices(aiServices.length);
        setCurrentPage(1);
    }, []);

    // Función para búsqueda con IA usando Weaviate
    const handleAISearch = useCallback(async () => {
        if (!searchQuery.trim()) {
            alert('Por favor, ingresa un término de búsqueda para usar la IA');
            return;
        }

        setIsAISearching(true);
        setError(null);

        try {
            console.log('🤖 Iniciando búsqueda con IA:', searchQuery);

            const data = await searchWeaviate(searchQuery);
            console.log('🤖 Resultados de IA:', data);

            if (data.results && data.results.length > 0) {
                const aiServices = convertAIResultsToServices(data.results);
                updateServicesWithAIResults(aiServices);
                console.log('✅ Búsqueda con IA completada:', aiServices.length, 'servicios encontrados');
            } else {
                console.log('⚠️ No se encontraron resultados con IA');
                setServices([]);
                setTotalServices(0);
            }

        } catch (error) {
            console.error('❌ Error en búsqueda con IA:', error);
            setError('Error en la búsqueda con IA. Inténtalo de nuevo.');
        } finally {
            setIsAISearching(false);
        }
    }, [searchQuery, searchWeaviate, updateServicesWithAIResults]);

    // Función para manejar contacto con proveedor
    const handleContactProvider = useCallback((serviceId: number) => {
        if (!isAuthenticated) {
            globalThis.location.href = '/login#/login';
            return;
        }
        
        const service = services.find(s => s.id_servicio === serviceId);
        if (service) {
            setSelectedService(service);
            setShowServiceDetail(true);
        }
    }, [services, isAuthenticated]);

    // Función para formatear fechas
    const formatDateShortLocal = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-PY', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    };

    // Función para obtener fecha de hoy
    const getTodayDateString = () => {
        return new Date().toISOString().split('T')[0];
    };

    // Función para manejar cambio de fecha de inicio
    const handleStartDateChange = (startDate: string) => {
        setCustomDateRange(prev => ({ ...prev, start: startDate }));
    };

    // Función para manejar cambio de fecha de fin
    const handleEndDateChange = (endDate: string) => {
        setCustomDateRange(prev => ({ ...prev, end: endDate }));
    };

    // Función para manejar reserva
    const handleReservar = useCallback((service: BackendService) => {
        setSelectedService(service);
        setShowServiceReservationModal(true);
    }, []);

    // Función para cerrar modal de reserva
    const handleCloseServiceReservationModal = useCallback(() => {
        setShowServiceReservationModal(false);
        setSelectedService(null);
    }, []);

    // Función helper para obtener el nombre de la moneda
    const getCurrencyName = useCallback((currency: string): string => {
        if (currency === 'GS') return 'Guaraníes';
        if (currency === 'USD') return 'Dólares';
        if (currency === 'BRL') return 'Reales';
        return 'Pesos';
    }, []);

    // Función helper para formatear el precio según la moneda
    const formatPriceByCurrency = useCallback((price: number, currency: string): string => {
        if (currency === 'GS') {
            return `₲ ${price.toLocaleString('es-PY')}`;
        }
        if (currency === 'USD') {
            return `$ ${price.toLocaleString('en-US')}`;
        }
        if (currency === 'BRL') {
            return `R$ ${price.toLocaleString('pt-BR')}`;
        }
        return `$ ${price.toLocaleString('es-AR')}`;
    }, []);

    // Función helper para obtener el símbolo de la moneda
    const getCurrencySymbol = useCallback((currency: string): string => {
        if (currency === 'GS') return '₲';
        if (currency === 'USD') return '$';
        if (currency === 'BRL') return 'R$';
        return '$';
    }, []);

    // Función helper para obtener el precio máximo formateado según la moneda
    const getMaxPriceFormatted = useCallback((currency: string): string => {
        if (currency === 'GS') return '₲ 1.000.000.000';
        if (currency === 'USD') return '$ 1,000,000,000';
        if (currency === 'BRL') return 'R$ 1.000.000.000';
        return '$ 1.000.000.000';
    }, []);

    // Filtrar servicios (usando función helper)
    const filteredServices = useMemo(() => {
        try {
            console.log('🔍 filteredServices useMemo ejecutándose');
            console.log('📊 Estado actual:', {
                servicesLength: services.length,
                totalServices: totalServices,
                itemsPerPage: itemsPerPage
            });
            
            // Usar función helper para filtrar servicios
            return filterServices(services, {
                currencyFilter,
                priceRange,
                categoryFilter,
                departmentFilter,
                cityFilter,
                searchQuery,
                dateFilter,
                ratingFilter,
                customDateRange
            });
        } catch (error) {
            console.error('❌ Error en filteredServices:', error);
            // En caso de error, retornar servicios sin filtrar
            return services;
        }
    }, [services, searchQuery, categoryFilter, ratingFilter, departmentFilter, cityFilter, currencyFilter, priceRange, dateFilter, customDateRange]);

    // Paginación
    const paginatedServices = useMemo(() => {
        console.log('📄 paginatedServices useMemo ejecutándose');
        console.log('📊 Estado para paginación:', {
            servicesLength: services.length,
            totalServices: totalServices,
            currentPage: currentPage,
            itemsPerPage: itemsPerPage
        });
        
        // NUEVO: Si estamos usando el endpoint filtrado del servidor, NO aplicar filtros locales
        // Los servicios ya vienen filtrados y paginados del servidor
        if (totalServices > 0) {
            console.log('📄 Usando servicios filtrados del servidor (sin filtros locales)');
            console.log('📊 Servicios del servidor:', services.length);
            return services; // Usar directamente los servicios del servidor
        }
        
        // Fallback: Si no hay paginación del backend, usar filtros locales
        console.log('📄 Sin paginación del backend - usando filtros locales');
        const startIndex = (currentPage - 1) * itemsPerPage;
        const paginated = filteredServices.slice(startIndex, startIndex + itemsPerPage);
        console.log('📄 Paginación local - Servicios filtrados:', filteredServices.length, 'Paginados:', paginated.length);
        return paginated;
    }, [services, filteredServices, currentPage, itemsPerPage, totalServices]);

    // Calcular total de páginas basado en servicios filtrados cuando hay filtros activos
    const totalPages = useMemo(() => {
        if (totalServices > 0) {
            return calculateTotalPagesWithServer(totalServices, itemsPerPage);
        }
        
        const hasFilters = hasActiveFilters(
            priceRange,
            currencyFilter,
            categoryFilter,
            departmentFilter,
            cityFilter,
            searchQuery
        );
        
        if (hasFilters) {
            return calculateTotalPagesWithLocalFilters(filteredServices.length, itemsPerPage);
        }
        
        return calculateTotalPagesWithServer(totalServices, itemsPerPage);
    }, [filteredServices.length, totalServices, itemsPerPage, priceRange, currencyFilter, categoryFilter, departmentFilter, cityFilter, searchQuery]);

    // Memoizar el texto formateado del precio para asegurar actualización en tiempo real
    const formattedMaxPrice = useMemo(() => {
        return formatPriceByCurrency(sliderValue, currencyFilter);
    }, [sliderValue, currencyFilter, formatPriceByCurrency]);

    // Resetear filtros
    const resetFilters = useCallback(() => {
        setSearchQuery('');
        setDateFilter('all');
        setCategoryFilter('all');
        setRatingFilter(0);
        setCurrencyFilter('all');
        setPriceFilter('all');
        setPriceRange([0, 1000000000]);
        setSliderValue(1000000000);
        setDepartmentFilter('all');
        setCityFilter('all');
        setCurrentPage(1);
    }, []);

    // Estados de loading y error
    if (isLoading) {
        return <LoadingState />;
    }

    if (error) {
        return <ErrorState error={error} onRetry={loadInitialData} />;
    }

    return (
        <div className="bg-slate-50 min-h-screen">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="max-w-7xl mx-auto">
                    <Header usingMockData={usingMockData} dataVersion={dataVersion} />
                    
                    <SearchBar
                        searchQuery={searchQuery}
                        isSearching={isSearching}
                        isAISearching={isAISearching}
                        onSearchQueryChange={setSearchQuery}
                        onSearch={handleSearch}
                        onAISearch={handleAISearch}
                    />

                    {/* Filtros compactos - diseño optimizado para dar más espacio a las tarjetas */}
                    <div className="mt-4 bg-primary-50 rounded-lg p-3 sm:p-4 border border-primary-200">
                        {/* Título y controles principales - más compactos */}
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                            <h3 className="text-base font-semibold text-primary-800">Filtros</h3>
                            <div className="flex gap-2">
                                <button
                                    onClick={resetFilters}
                                    className="btn-uniform btn-secondary touch-manipulation text-xs sm:text-sm px-3 py-2"
                                >
                                    <span>Limpiar</span>
                                </button>
                                <button
                                    onClick={() => setShowAdvancedFilters(true)}
                                    className="btn-uniform btn-secondary touch-manipulation text-xs sm:text-sm px-3 py-2"
                                >
                                    <svg className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                                    </svg>
                                    <span>Más</span>
                                </button>
                            </div>
                        </div>

                        {/* Filtros principales - diseño más compacto y horizontal */}
                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                            {/* Filtro de fecha - compacto */}
                            <div className="space-y-1">
                                <label htmlFor="filter-date" className="block text-xs font-medium text-slate-700">Fecha</label>
                                <select
                                    id="filter-date"
                                    value={dateFilter}
                                    onChange={(e) => {
                                        setDateFilter(e.target.value);
                                        if (e.target.value === 'custom') {
                                            setShowCustomDatePicker(true);
                                        } else {
                                            setShowCustomDatePicker(false);
                                            setCustomDateRange({ start: '', end: '' });
                                        }
                                    }}
                                    className={`w-full px-2 py-1.5 border rounded-md focus:ring-primary-500 focus:border-primary-500 transition-colors text-xs ${
                                        dateFilter === 'custom' && customDateRange.start && customDateRange.end
                                            ? 'border-primary-500 bg-primary-50'
                                            : 'border-slate-300'
                                    }`}
                                >
                                    <option value="all">Todos</option>
                                    <option value="recent">Recientes</option>
                                    <option value="7days">7 días</option>
                                    <option value="30days">30 días</option>
                                    <option value="custom">
                                        {dateFilter === 'custom' && customDateRange.start && customDateRange.end
                                            ? `📅 ${formatDateShortLocal(customDateRange.start)} - ${formatDateShortLocal(customDateRange.end)}`
                                            : 'Personalizado'
                                        }
                                    </option>
                                </select>
                            </div>

                            {/* Filtro de categoría - compacto */}
                            <div className="space-y-1">
                                <label className="block text-xs font-medium text-slate-700">Categoría</label>
                                <select
                                    value={categoryFilter}
                                    onChange={(e) => setCategoryFilter(e.target.value)}
                                    className="w-full px-2 py-1.5 border border-slate-300 rounded-md focus:ring-primary-500 focus:border-primary-500 transition-colors text-xs"
                                >
                                    <option value="all">Todas</option>
                                    {categories.map(category => (
                                        <option key={category.id_categoria} value={category.id_categoria.toString()}>
                                            {category.nombre}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Filtro de calificación - compacto */}
                            <div className="space-y-1">
                                <label className="block text-xs font-medium text-slate-700">Calificación</label>
                                <select
                                    value={ratingFilter}
                                    onChange={(e) => setRatingFilter(Number.parseInt(e.target.value))}
                                    className="w-full px-2 py-1.5 border border-slate-300 rounded-md focus:ring-primary-500 focus:border-primary-500 transition-colors text-xs"
                                >
                                    <option value={0}>Cualquiera</option>
                                    {[4, 5, 6, 7, 8, 9, 10].map(rating => (
                                        <option key={rating} value={rating}>
                                            {rating}+ ⭐
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Filtro de moneda - compacto */}
                            <div className="space-y-1">
                                <label className="block text-xs font-medium text-slate-700">Moneda</label>
                                <select
                                    value={currencyFilter}
                                    onChange={(e) => setCurrencyFilter(e.target.value)}
                                    className="w-full px-2 py-1.5 border border-slate-300 rounded-md focus:ring-primary-500 focus:border-primary-500 transition-colors text-xs"
                                >
                                    <option value="all">Todas</option>
                                    <option value="GS">₲ Guaraní</option>
                                    <option value="USD">$ Dólar</option>
                                    <option value="BRL">R$ Real</option>
                                    <option value="ARS">$ Peso</option>
                                </select>
                            </div>

                        </div>

                        {/* Selector de rango personalizado de fechas - más compacto */}
                        {showCustomDatePicker && (
                            <div className="mt-3 bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                                <div className="flex items-center justify-between mb-3">
                                    <label className="block text-sm font-medium text-slate-700">
                                        📅 Rango personalizado
                                    </label>
                                    <button
                                        onClick={() => {
                                            setDateFilter('all');
                                            setShowCustomDatePicker(false);
                                            setCustomDateRange({ start: '', end: '' });
                                        }}
                                        className="text-slate-400 hover:text-slate-600 text-lg p-1"
                                    >
                                        ✕
                                    </button>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium text-slate-700">Desde</label>
                                        <input
                                            type="date"
                                            value={customDateRange.start}
                                            onChange={(e) => handleStartDateChange(e.target.value)}
                                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 transition-colors"
                                            max={getTodayDateString()}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium text-slate-700">Hasta</label>
                                        <input
                                            type="date"
                                            value={customDateRange.end}
                                            onChange={(e) => handleEndDateChange(e.target.value)}
                                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 transition-colors"
                                            min={customDateRange.start || undefined}
                                            max={getTodayDateString()}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Rango de precios - más compacto */}
                    {currencyFilter === 'all' ? null : (
                        <div className="mt-3 p-3 sm:p-4 bg-primary-50 rounded-lg border border-primary-200">
                            <div className="space-y-3">
                                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                                    <label className="block text-xs sm:text-sm font-medium text-slate-700">
                                        Precio en {getCurrencyName(currencyFilter)}
                                    </label>
                                    <span className="text-xs sm:text-sm font-semibold text-primary-600" key={`price-${sliderValue}`}>
                                        Hasta {formattedMaxPrice}
                                    </span>
                                </div>

                                <div className="space-y-2">
                                    <input
                                        type="range"
                                        min="0"
                                        max="1000000000"
                                        step="1000000"
                                        value={sliderValue}
                                        onInput={(e) => {
                                            const target = e.target as HTMLInputElement;
                                            const newValue = Number.parseInt(target.value, 10);
                                            isSliderDraggingRef.current = true;
                                            setSliderValue(() => newValue);
                                        }}
                                        onChange={(e) => {
                                            const target = e.target as HTMLInputElement;
                                            const newValue = Number.parseInt(target.value, 10);
                                            isSliderDraggingRef.current = true;
                                            setSliderValue(() => newValue);
                                        }}
                                        onMouseDown={() => {
                                            isSliderDraggingRef.current = true;
                                        }}
                                        onMouseUp={(e) => {
                                            const target = e.target as HTMLInputElement;
                                            const newValue = Number.parseInt(target.value, 10);
                                            isSliderDraggingRef.current = false;
                                            setPriceRange([0, newValue]);
                                        }}
                                        onTouchStart={() => {
                                            isSliderDraggingRef.current = true;
                                        }}
                                        onTouchEnd={(e) => {
                                            const target = e.target as HTMLInputElement;
                                            const newValue = Number.parseInt(target.value, 10);
                                            isSliderDraggingRef.current = false;
                                            setPriceRange([0, newValue]);
                                        }}
                                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer slider-thumb"
                                        style={{
                                            background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(sliderValue / 1000000000) * 100}%, #e2e8f0 ${(sliderValue / 1000000000) * 100}%, #e2e8f0 100%)`
                                        }}
                                    />
                                    <div className="flex justify-between text-xs text-slate-500">
                                        <span>{getCurrencySymbol(currencyFilter)} 0</span>
                                        <span>{getMaxPriceFormatted(currencyFilter)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Resultados - más espacio para las tarjetas */}
                    <div className="mt-4 sm:mt-6">
                        {/* Chips de filtros activos - más compactos */}
                        {(departmentFilter !== 'all' || cityFilter !== 'all') && (
                            <div className="mb-3 sm:mb-4">
                                <h4 className="text-xs font-medium text-slate-700 mb-2">Filtros aplicados:</h4>
                                <div className="flex flex-wrap gap-2">
                                    {departmentFilter !== 'all' && (
                                        <div className="flex items-center gap-1 px-2 py-1 bg-primary-100 text-primary-800 rounded-full text-xs font-medium">
                                            <span>🗺️ {departmentFilter}</span>
                                            <button
                                                onClick={() => {
                                                    setDepartmentFilter('all');
                                                    setCityFilter('all');
                                                }}
                                                className="text-primary-600 hover:text-primary-800 ml-1 p-0.5 hover:bg-primary-200 rounded-full transition-colors"
                                                aria-label="Remover filtro de departamento"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    )}
                                    {cityFilter !== 'all' && (
                                        <div className="flex items-center gap-1 px-2 py-1 bg-primary-100 text-primary-800 rounded-full text-xs font-medium">
                                            <span>📍 {cityFilter}</span>
                                            <button
                                                onClick={() => setCityFilter('all')}
                                                className="text-primary-600 hover:text-primary-800 ml-1 p-0.5 hover:bg-primary-200 rounded-full transition-colors"
                                                aria-label="Remover filtro de ciudad"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                        
                        {/* 
                            ========================================
                            BARRA DE ESTADÍSTICAS DE RESULTADOS
                            ========================================
                            
                            Esta sección muestra información clave sobre los resultados:
                            1. Cantidad de servicios encontrados (paginados)
                            2. Información de paginación (página actual / total)
                            3. Diseño responsivo (diferente en móvil y desktop)
                            
                            Variables importantes:
                            - paginatedServices.length: Servicios en la página actual
                            - filteredServices.length: Total de servicios filtrados
                            - currentPage: Página actual (1, 2, 3...)
                            - totalPages: Total de páginas disponibles
                            - itemsPerPage: Servicios por página (12)
                            
                            COMENTADO: Esta barra está deshabilitada temporalmente
                        */}
                        {/* 
                        <div className="mb-4 sm:mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 bg-white rounded-lg border border-primary-200 shadow-sm">
                            <div className="flex items-center gap-4">
                                <div className="text-center sm:text-left">
                                    <p className="text-xl sm:text-2xl font-bold text-primary-600">
                                        {paginatedServices.length}
                                    </p>
                                    <p className="text-sm text-primary-500 font-medium">servicios encontrados</p>
                                </div>
                                {filteredServices.length > itemsPerPage && (
                                    <div className="hidden sm:block text-center bg-primary-50 px-4 py-2 rounded-lg border border-primary-200">
                                        <p className="text-lg font-bold text-primary-700">{currentPage}</p>
                                        <p className="text-sm text-primary-600 font-medium">de {totalPages}</p>
                                    </div>
                                )}
                            </div>

                            <div className="sm:hidden text-center">
                                <div className="inline-flex items-center bg-primary-50 px-3 py-1 rounded-full border border-primary-200">
                                    <p className="text-sm text-primary-600 font-medium">
                                        Página {currentPage} de {totalPages}
                                    </p>
                                </div>
                            </div>
                        </div>
                        */}


                        {/* Estados vacíos - más compactos */}
                        {filteredServices.length === 0 && (
                            <div className="text-center py-8">
                                <MagnifyingGlassIcon className="mx-auto h-10 w-10 text-primary-400" />
                                <h3 className="mt-2 text-base font-semibold text-primary-800">
                                    No encontramos resultados
                                </h3>
                                <p className="mt-1 text-xs text-primary-500">
                                    Probá ajustar los filtros o términos de búsqueda.
                                </p>
                                {/* Botón "Limpiar filtros" comentado */}
                                {/* <button
                                    onClick={resetFilters}
                                    className="mt-3 btn-blue touch-manipulation"
                                >
                                    <span>Limpiar filtros</span>
                                </button> */}
                            </div>
                        )}

                        {/* Grid de servicios - optimizado para móviles */}
                        {(() => {
                            console.log('🎨 Renderizando grid de servicios');
                            console.log('📊 Estado del renderizado:', {
                                paginatedServicesLength: paginatedServices.length,
                                filteredServicesLength: filteredServices.length,
                                servicesLength: services.length,
                                totalServices: totalServices,
                                currentPage: currentPage,
                                isLoading: isLoading,
                                error: error
                            });
                            console.log('🔍 ¿Debe mostrar servicios?', paginatedServices.length > 0);
                            return paginatedServices.length > 0;
                        })() && (
                            <>
                                {/* Grid responsivo optimizado para más espacio */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3 sm:gap-4">
                                    {paginatedServices.map(service => (
                                        <div key={service.id_servicio} className="transform transition-transform duration-200 hover:scale-[1.02]">
                                            <MarketplaceServiceCard 
                                                service={service} 
                                                category={categories.find(c => c.id_categoria === service.id_categoria)}
                                                onViewProviders={handleContactProvider}
                                                onReservar={handleReservar}
                                                isAuthenticated={isAuthenticated}
                                            />
                                        </div>
                                    ))}
                                </div>

                                {/* Paginación mejorada */}
                                {totalPages > 1 && (
                                    <div className="mt-6 sm:mt-8">
                                        {/* Paginación completa para desktop */}
                                        <div className="hidden sm:flex justify-center">
                                            <nav className="flex items-center gap-3">
                                                <button
                                                    onClick={() => loadPage(Math.max(1, currentPage - 1))}
                                                    disabled={currentPage === 1 || isLoadingPage}
                                                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50 hover:border-slate-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
                                                >
                                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                                    </svg>
                                                    {isLoadingPage ? '⏳' : 'Anterior'}
                                                </button>
                                                
                                                <div className="flex items-center gap-2">
                                                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                        const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                                                        if (pageNum > totalPages) return null;
                                                        
                                                        return (
                                                        <button
                                                            key={pageNum}
                                                            onClick={() => loadPage(pageNum)}
                                                            disabled={isLoadingPage}
                                                            className={`px-4 py-2 text-sm font-medium border rounded-lg transition-all duration-150 min-w-[44px] disabled:opacity-50 disabled:cursor-not-allowed ${
                                                                currentPage === pageNum
                                                                    ? 'bg-primary-600 text-white border-primary-600 shadow-md'
                                                                    : 'text-slate-600 border-slate-300 hover:bg-slate-50 hover:border-slate-400'
                                                            }`}
                                                        >
                                                            {isLoadingPage && currentPage === pageNum ? '⏳' : pageNum}
                                                        </button>
                                                        );
                                                    })}
                                                </div>
                                                
                                                <button
                                                    onClick={() => loadPage(Math.min(totalPages, currentPage + 1))}
                                                    disabled={currentPage === totalPages || isLoadingPage}
                                                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50 hover:border-slate-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
                                                >
                                                    {isLoadingPage ? '⏳' : 'Siguiente'}
                                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                                    </svg>
                                                </button>
                                            </nav>
                                        </div>

                                        {/* Paginación simplificada para móviles */}
                                        <div className="sm:hidden flex justify-center">
                                            <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg p-2 shadow-sm">
                                                <button
                                                    onClick={() => loadPage(Math.max(1, currentPage - 1))}
                                                    disabled={currentPage === 1 || isLoadingPage}
                                                    className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                                                >
                                                    {isLoadingPage ? '⏳' : '←'}
                                                </button>
                                                <div className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-50 rounded-md min-w-[80px] text-center">
                                                    {isLoadingPage ? 'Cargando...' : `${currentPage} de ${totalPages}`}
                                                </div>
                                                <button
                                                    onClick={() => loadPage(Math.min(totalPages, currentPage + 1))}
                                                    disabled={currentPage === totalPages || isLoadingPage}
                                                    className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                                                >
                                                    {isLoadingPage ? '⏳' : '→'}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Modal de filtros avanzados */}
            {showAdvancedFilters && (
                <dialog
                    ref={advancedFiltersDialogRef}
                    open
                    aria-modal="true"
                    aria-labelledby="filtros-avanzados-title"
                    className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border-0 p-0 backdrop:bg-black backdrop:bg-opacity-50"
                    onCancel={(e) => {
                        e.preventDefault();
                        setShowAdvancedFilters(false);
                    }}
                >
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h2 id="filtros-avanzados-title" className="text-xl font-semibold text-slate-900">Filtros Avanzados</h2>
                                <button
                                    onClick={() => setShowAdvancedFilters(false)}
                                    className="text-slate-400 hover:text-slate-600 text-2xl"
                                >
                                    ✕
                                </button>
                            </div>

                            <div className="space-y-6">
                                {/* Filtro por departamento */}
                                <div>
                                    <label htmlFor="filter-department" className="block text-sm font-medium text-slate-700 mb-2">
                                        Departamento
                                    </label>
                                    <select
                                        id="filter-department"
                                        value={departmentFilter}
                                        onChange={(e) => {
                                            setDepartmentFilter(e.target.value);
                                            // Resetear ciudad cuando cambia el departamento
                                            if (e.target.value === 'all') {
                                                setCityFilter('all');
                                            }
                                        }}
                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                                    >
                                        <option value="all">Todos los departamentos</option>
                                        {departments.map(dept => (
                                            <option key={dept} value={dept}>{dept}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Filtro por ciudad */}
                                <div>
                                    <label htmlFor="filter-city" className="block text-sm font-medium text-slate-700 mb-2">
                                        Ciudad
                                    </label>
                                    <select
                                        id="filter-city"
                                        value={cityFilter}
                                        onChange={(e) => setCityFilter(e.target.value)}
                                        disabled={departmentFilter === 'all'}
                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 disabled:bg-slate-100 disabled:cursor-not-allowed"
                                    >
                                        <option value="all">
                                            {departmentFilter === 'all' ? 'Selecciona un departamento primero' : 'Todas las ciudades'}
                                        </option>
                                        {cities.map(city => (
                                            <option key={city} value={city}>{city}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="mt-8 flex gap-3">
                                <button
                                    onClick={() => {
                                        setDepartmentFilter('all');
                                        setCityFilter('all');
                                        setShowAdvancedFilters(false);
                                    }}
                                    className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                                >
                                    Limpiar
                                </button>
                                <button
                                    onClick={() => setShowAdvancedFilters(false)}
                                    className="flex-1 btn-blue touch-manipulation"
                                >
                                    <span>Cerrar filtros</span>
                                </button>
                            </div>
                        </div>
                    </dialog>
            )}

            {/* Modal de reserva del servicio */}
            {showServiceDetail && (
                <ServiceReservationModal
                    isOpen={showServiceDetail}
                    onClose={() => setShowServiceDetail(false)}
                    service={selectedService}
                    category={selectedService ? categories.find(c => c.id_categoria === selectedService.id_categoria) : undefined}
                />
            )}

            {/* Modal de reserva */}
            {showServiceReservationModal && (
                <ServiceReservationModal
                    isOpen={showServiceReservationModal}
                    onClose={handleCloseServiceReservationModal}
                    service={selectedService}
                    category={selectedService ? categories.find(c => c.id_categoria === selectedService.id_categoria) : undefined}
                />
            )}
        </div>
    );
};

export default MarketplacePage;
