import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { MagnifyingGlassIcon, SparklesIcon, ExclamationCircleIcon } from '../icons';
import MarketplaceServiceCard from './MarketplaceServiceCard';
import ServiceReservationModal from './ServiceReservationModal';
import { BackendService, BackendCategory } from '../../types';
import { categoriesAPI, servicesAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

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
    const [dataVersion, setDataVersion] = useState(Date.now()); // Para forzar recarga
    const dataLoadedRef = useRef(false); // Para evitar cargas duplicadas
    
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


    // Función para construir filtros del backend
    const buildBackendFilters = useCallback(() => {
        const filters: any = {};
        
        console.log('🔍 buildBackendFilters ejecutándose con:', {
            currencyFilter,
            priceRange,
            categoryFilter,
            departmentFilter,
            cityFilter,
            searchQuery,
            dateFilter,
            ratingFilter
        });
        
        // Filtro por moneda (si está seleccionada)
        if (currencyFilter !== 'all') {
            filters.currency = currencyFilter;
            console.log('💰 Agregando filtro de moneda:', currencyFilter);
        }
        
        // Filtro por precio (solo si el usuario ha cambiado el rango desde el inicial)
        const isPriceFilterActive = priceRange[0] > 0 || priceRange[1] < 1000000000;
        if (isPriceFilterActive) {
            if (priceRange[0] > 0) {
                filters.min_price = priceRange[0];
                console.log('💰 Agregando precio mínimo:', priceRange[0]);
            }
            if (priceRange[1] < 1000000000) {
                filters.max_price = priceRange[1];
                console.log('💰 Agregando precio máximo:', priceRange[1]);
            }
        }
        
        // Filtro por categoría
        if (categoryFilter !== 'all') {
            filters.category_id = parseInt(categoryFilter);
            console.log('📂 Agregando filtro de categoría:', categoryFilter);
        }
        
        // Filtro por departamento
        if (departmentFilter !== 'all') {
            filters.department = departmentFilter;
            console.log('🏢 Agregando filtro de departamento:', departmentFilter);
        }
        
        // Filtro por ciudad
        if (cityFilter !== 'all') {
            filters.city = cityFilter;
            console.log('🏙️ Agregando filtro de ciudad:', cityFilter);
        }
        
        // Filtro por búsqueda
        if (searchQuery.trim()) {
            filters.search = searchQuery.trim();
            console.log('🔍 Agregando filtro de búsqueda:', searchQuery);
        }
        
        // Filtro por fecha (si está seleccionado)
        if (dateFilter !== 'all') {
            const today = new Date();
            let dateFrom: string | undefined;
            let dateTo: string | undefined;
            
            switch (dateFilter) {
                case 'today':
                    dateFrom = today.toISOString().split('T')[0];
                    dateTo = today.toISOString().split('T')[0];
                    break;
                case 'week':
                    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                    dateFrom = weekAgo.toISOString().split('T')[0];
                    dateTo = today.toISOString().split('T')[0];
                    break;
                case 'month':
                    const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
                    dateFrom = monthAgo.toISOString().split('T')[0];
                    dateTo = today.toISOString().split('T')[0];
                    break;
                case 'custom':
                    if (customDateRange.start && customDateRange.end) {
                        dateFrom = customDateRange.start;
                        dateTo = customDateRange.end;
                    }
                    break;
            }
            
            if (dateFrom) {
                filters.date_from = dateFrom;
                console.log('📅 Agregando filtro de fecha desde:', dateFrom);
            }
            if (dateTo) {
                filters.date_to = dateTo;
                console.log('📅 Agregando filtro de fecha hasta:', dateTo);
            }
        }
        
        // Filtro por calificación (si está seleccionada)
        if (ratingFilter > 0) {
            filters.min_rating = ratingFilter;
            console.log('⭐ Agregando filtro de calificación mínima:', ratingFilter);
        }
        
        console.log('🔍 Filtros construidos:', filters);
        console.log('🔍 ¿Filtro de precio activo?', isPriceFilterActive);
        return filters;
    }, [currencyFilter, priceRange, categoryFilter, departmentFilter, cityFilter, searchQuery, dateFilter, ratingFilter, customDateRange]);

    // Cargar datos iniciales con paginación del backend
    const loadInitialData = useCallback(async () => {
        console.log('🚀 Iniciando loadInitialData...');
        // Removido: if (dataLoadedRef.current) return; // Evitar cargas duplicadas
        
        try {
            console.log('🔄 Estableciendo isLoading = true');
            setIsLoading(true);
            setError(null);
            
            // Intentar llamadas reales a la API del backend con paginación
            try {
                console.log('Intentando cargar datos reales de la API con paginación...');
                
                // Calcular offset basado en la página actual
                const offset = (currentPage - 1) * itemsPerPage;
                
                // Obtener token de autenticación si está disponible
                const accessToken = user?.accessToken || localStorage.getItem('access_token');
                console.log(`🔄 Carga inicial con offset ${offset}, limit ${itemsPerPage}`);
                
                // Construir filtros del backend
                const filters = buildBackendFilters();
                console.log('🔍 Filtros del backend:', filters);
                
                // Usar el nuevo endpoint filtrado que maneja filtros del lado del servidor
                const [filteredResponse, categoriesData] = await Promise.all([
                    servicesAPI.getFilteredServices(itemsPerPage, offset, accessToken, filters),
                    categoriesAPI.getCategories(undefined, true) // Solo categorías activas
                ]);

                console.log('📊 Respuesta del endpoint filtrado:', filteredResponse);
                console.log('📊 Servicios cargados del backend (filtrados):', filteredResponse.services.length);
                console.log('📊 Total de servicios disponibles:', filteredResponse.pagination.total);
                
                // Actualizar estados
                console.log('🔄 Actualizando estados...');
                console.log('📊 filteredResponse.pagination.total:', filteredResponse.pagination.total);
                console.log('📊 filteredResponse.services.length:', filteredResponse.services.length);
                console.log('📊 categoriesData.length:', categoriesData.length);
                
                setTotalServices(filteredResponse.pagination.total);
                setServices(filteredResponse.services);
                setCategories(categoriesData);
                setUsingMockData(false);
                
                console.log('✅ Datos filtrados del servidor aplicados correctamente');
            } catch (apiError) {
                console.error('❌ Error con API real:', apiError);
                setError('No se pudo conectar con el servidor. Por favor, verifica que el backend esté funcionando.');
                setServices([]);
                setCategories([]);
                setUsingMockData(false);
                return;
            }
            
        } catch (err) {
            console.error('Error cargando datos:', err);
            setError('Error al cargar los datos. Por favor, intentá nuevamente.');
        } finally {
            console.log('🔄 Finalizando loadInitialData - estableciendo isLoading = false');
            setIsLoading(false);
            dataLoadedRef.current = true;
            console.log('✅ loadInitialData completado');
        }
    }, [buildBackendFilters, currentPage, itemsPerPage, user]); // Agregar dependencias necesarias


    // Función para cargar una página específica (optimizada)
    const loadPage = useCallback(async (page: number) => {
        console.log(`🔄 loadPage ejecutándose para página ${page}`);
        
        // Evitar cargar la misma página
        if (page === currentPage) {
            console.log(`⚠️ Ya estás en la página ${page}, evitando recarga`);
            return;
        }
        
        try {
            // Solo mostrar loading en los botones, no en toda la interfaz
            setIsLoadingPage(true);
            const offset = (page - 1) * itemsPerPage;
            
            // Obtener token de autenticación si está disponible
            const accessToken = user?.accessToken || localStorage.getItem('access_token');
            console.log(`🔄 Cargando página ${page} con offset ${offset}, limit ${itemsPerPage}`);
            
            // Construir filtros para la página
            const filters = buildBackendFilters();
            console.log('🔍 Filtros para página:', filters);
            
            // Usar el nuevo endpoint filtrado para cargar la página
            const filteredResponse = await servicesAPI.getFilteredServices(itemsPerPage, offset, accessToken, filters);
            
            // Actualizar servicios y página de forma atómica
            setServices(filteredResponse.services);
            setCurrentPage(filteredResponse.pagination.page);
            setTotalServices(filteredResponse.pagination.total);
            console.log(`📄 Página ${page} cargada: ${filteredResponse.services.length} servicios, total: ${filteredResponse.pagination.total}`);
        } catch (error) {
            console.error('❌ Error cargando página:', error);
            setError('Error cargando la página. Inténtalo de nuevo.');
        } finally {
            // Reducir el tiempo de loading para que sea menos notorio
            setTimeout(() => setIsLoadingPage(false), 100);
        }
    }, [itemsPerPage, user, buildBackendFilters, currentPage]);

    useEffect(() => {
        console.log('🎯 useEffect ejecutándose - llamando loadInitialData');
        loadInitialData();
    }, []); // Solo ejecutar una vez al montar

    // Función optimizada para recargar solo los datos filtrados (sin resetear página)
    const reloadFilteredData = useCallback(async () => {
        console.log('🔄 Recargando datos filtrados (sin resetear página)...');
        
        try {
            setIsLoadingFilters(true); // Loading específico para filtros
            const offset = (currentPage - 1) * itemsPerPage;
            const accessToken = user?.accessToken || localStorage.getItem('access_token');
            const filters = buildBackendFilters();
            
            console.log(`🔄 Recarga filtrada con offset ${offset}, limit ${itemsPerPage}`);
            
            const filteredResponse = await servicesAPI.getFilteredServices(itemsPerPage, offset, accessToken, filters);
            
            setServices(filteredResponse.services);
            setTotalServices(filteredResponse.pagination.total);
            // NO resetear currentPage - mantener la página actual
            console.log(`📄 Datos filtrados recargados: ${filteredResponse.services.length} servicios, total: ${filteredResponse.pagination.total}`);
            
        } catch (error) {
            console.error('❌ Error recargando datos filtrados:', error);
            setError('Error aplicando filtros. Inténtalo de nuevo.');
        } finally {
            setIsLoadingFilters(false);
        }
    }, [currentPage, itemsPerPage, user, buildBackendFilters]);

    // Recargar datos cuando cambien los filtros (con debounce inteligente)
    useEffect(() => {
        // Solo recargar si hay filtros activos
        const hasActiveFilters = currencyFilter !== 'all' || 
                                priceRange[0] > 0 || 
                                priceRange[1] < 1000000000 ||
                                categoryFilter !== 'all' ||
                                departmentFilter !== 'all' ||
                                cityFilter !== 'all' ||
                                searchQuery.trim() !== '' ||
                                dateFilter !== 'all' ||
                                ratingFilter > 0;
        
        if (hasActiveFilters) {
            console.log('🔄 Filtros activos detectados, aplicando debounce inteligente...');
            
            // Debounce inteligente: más corto para filtros inmediatos, más largo para slider
            const isSliderChange = priceRange[0] > 0 || priceRange[1] < 1000000000;
            const debounceTime = isSliderChange ? 500 : 100; // 500ms para slider, 100ms para otros filtros
            
            const timeoutId = setTimeout(() => {
                console.log(`🔄 Ejecutando recarga filtrada después de ${debounceTime}ms...`);
                reloadFilteredData();
            }, debounceTime);
            
            return () => clearTimeout(timeoutId);
        }
    }, [currencyFilter, priceRange, categoryFilter, departmentFilter, cityFilter, searchQuery, dateFilter, ratingFilter, reloadFilteredData]);

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

    // Función para búsqueda con IA usando Weaviate
    const handleAISearch = useCallback(async () => {
        if (!searchQuery.trim()) {
            alert('Por favor, ingresa un término de búsqueda para usar la IA');
            return;
        }

        setIsAISearching(true);
        setError(null);

        try {
            // Detectar entorno para la URL de la API
            const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
                ? 'http://localhost:8000' 
                : 'https://backend-production-249d.up.railway.app';

            console.log('🤖 Iniciando búsqueda con IA:', searchQuery);
            console.log('🔗 API_URL:', API_URL);

            // Llamar al endpoint correcto de búsqueda de Weaviate
            const response = await fetch(`${API_URL}/api/v1/weaviate/search-public?query=${encodeURIComponent(searchQuery)}&limit=10`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('🤖 Resultados de IA:', data);

            if (data.results && data.results.length > 0) {
                // Convertir resultados de Weaviate al formato esperado
                const aiServices = data.results.map((result: any) => ({
                    id_servicio: result.id_servicio,
                    nombre: result.nombre,
                    descripcion: result.descripcion,
                    precio: result.precio,
                    categoria: result.categoria,
                    empresa: result.empresa,
                    // Agregar campos requeridos con valores por defecto
                    id_categoria: 1, // Valor por defecto
                    razon_social: result.empresa,
                    departamento: '',
                    ciudad: '',
                    codigo_iso_moneda: 'GS',
                    simbolo_moneda: '₲',
                    id_moneda: 1,
                    created_at: new Date().toISOString(),
                    estado: 'activo'
                }));

                // Actualizar servicios con resultados de IA
                setServices(aiServices);
                setTotalServices(aiServices.length);
                setCurrentPage(1);
                
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
    }, [searchQuery]);

    // Función para manejar contacto con proveedor
    const handleContactProvider = useCallback((serviceId: number) => {
        if (!isAuthenticated) {
            window.location.href = '/login#/login';
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

    // Función para cuando se crea una reserva
    const handleReservaCreada = useCallback(() => {
        // Aquí podrías mostrar una notificación de éxito
        console.log('Reserva creada exitosamente');
    }, []);

    // Filtrar servicios
    const filteredServices = useMemo(() => {
        console.log('🔍 filteredServices useMemo ejecutándose');
        console.log('📊 Estado actual:', {
            servicesLength: services.length,
            totalServices: totalServices,
            itemsPerPage: itemsPerPage
        });
        
        // TEMPORAL: Aplicar filtros locales para que funcionen los filtros de precio
        // TODO: Implementar filtros del backend para mantener paginación
        console.log('🔄 Aplicando filtros locales (temporal)');
        console.log('📊 Servicios del backend:', services.length, 'Total disponible:', totalServices);
        
        // Eliminar duplicados basándose en el ID del servicio
        const uniqueServices = services.filter((service, index, self) => 
            index === self.findIndex(s => s.id_servicio === service.id_servicio)
        );
        
        let filtered = [...uniqueServices];
        console.log('🔍 Aplicando filtros locales - Servicios iniciales:', services.length, 'Únicos:', uniqueServices.length);
        console.log('🎯 Filtros activos:', {
            currencyFilter,
            departmentFilter,
            cityFilter,
            priceFilter,
            categoryFilter
        });

        // Filtro por precio válido (excluir solo servicios sin precio, permitir precio 0)
        const beforePriceFilter = filtered.length;
        filtered = filtered.filter(service => {
            const price = service.precio;
            const hasValidPrice = price !== null && price !== undefined;
            
            if (!hasValidPrice) {
                console.log(`❌ Servicio "${service.nombre}" excluido por precio inválido:`, {
                    precio: price,
                    tipo: typeof price,
                    es_null: price === null,
                    es_undefined: price === undefined
                });
            }
            
            return hasValidPrice;
        });
        console.log(`💰 Filtro precio válido: ${beforePriceFilter} → ${filtered.length} servicios (excluidos ${beforePriceFilter - filtered.length} sin precio válido)`);

        // Filtro por búsqueda
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            const beforeSearch = filtered.length;
            filtered = filtered.filter(service =>
                service.nombre.toLowerCase().includes(query) ||
                service.descripcion.toLowerCase().includes(query) ||
                (service.razon_social && service.razon_social.toLowerCase().includes(query))
            );
            console.log(`🔎 Búsqueda "${searchQuery}": ${beforeSearch} → ${filtered.length} servicios`);
        }

        // Filtro por categoría
        if (categoryFilter !== 'all') {
            filtered = filtered.filter(service => 
                service.id_categoria.toString() === categoryFilter
            );
        }

        // Filtro por calificación
        if (ratingFilter > 0) {
            // TODO: Implementar filtro por calificación real
            filtered = filtered.filter(service => true); // Placeholder
        }

        // Filtro por departamento y ciudad
        if (departmentFilter !== 'all') {
            const beforeDept = filtered.length;
            filtered = filtered.filter(service => {
                const serviceDept = service.departamento || '';
                const matches = serviceDept === departmentFilter;
                console.log(`🏛️ Servicio "${service.nombre}" - Departamento: "${serviceDept}" (filtrando: "${departmentFilter}") - Match: ${matches}`);
                return matches;
            });
            console.log(`🏛️ Filtro departamento "${departmentFilter}": ${beforeDept} → ${filtered.length} servicios`);
        }

        // Filtro por ciudad (solo si hay departamento seleccionado)
        if (cityFilter !== 'all' && departmentFilter !== 'all') {
            const beforeCity = filtered.length;
            filtered = filtered.filter(service => {
                const serviceCity = service.ciudad || '';
                const matches = serviceCity === cityFilter;
                console.log(`🏙️ Servicio "${service.nombre}" - Ciudad: "${serviceCity}" (filtrando: "${cityFilter}") - Match: ${matches}`);
                return matches;
            });
            console.log(`🏙️ Filtro ciudad "${cityFilter}": ${beforeCity} → ${filtered.length} servicios`);
        }

        // Filtro por moneda
        if (currencyFilter !== 'all') {
            console.log('🔍 Filtrando por moneda:', currencyFilter);
            console.log('📊 Servicios antes del filtro de moneda:', filtered.length);
            console.log('💰 Ejemplos de monedas en servicios:', filtered.slice(0, 3).map(s => ({
                nombre: s.nombre,
                codigo_iso_moneda: s.codigo_iso_moneda,
                simbolo_moneda: s.simbolo_moneda,
                id_moneda: s.id_moneda,
                precio: s.precio
            })));

            const beforeCurrency = filtered.length;
            filtered = filtered.filter(service => {
                // Priorizar el mapeo por ID de moneda sobre el código ISO (más confiable)
                let serviceCurrency = null;

                console.log(`🔍 Procesando servicio "${service.nombre}":`, {
                    original_codigo_iso: `"${service.codigo_iso_moneda}"`,
                    id_moneda: service.id_moneda
                });

                // Primero intentar mapear por ID de moneda (más confiable)
                if (service.id_moneda) {
                    switch (service.id_moneda) {
                        case 1: // Guaraní
                            serviceCurrency = 'GS';
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
                        case 8: // Peso Argentino (otro ID)
                            serviceCurrency = 'ARS';
                            break;
                        default:
                            serviceCurrency = 'GS'; // Fallback a Guaraní
                    }
                    console.log(`🔄 Mapeo por ID aplicado: ${service.id_moneda} → ${serviceCurrency}`);
                }

                // Si no hay ID de moneda, usar código ISO limpio como fallback
                if (!serviceCurrency && service.codigo_iso_moneda) {
                    serviceCurrency = service.codigo_iso_moneda.trim();
                    console.log(`🔄 Fallback a código ISO limpio: "${service.codigo_iso_moneda}" → "${serviceCurrency}"`);
                }

                // Si aún no hay moneda, asumir Guaraní
                if (!serviceCurrency) {
                    serviceCurrency = 'GS';
                    console.log(`🔄 Fallback final: null → GS`);
                }

                const matches = serviceCurrency === currencyFilter;

                if (!matches) {
                    console.log(`❌ Servicio "${service.nombre}" no coincide:`, {
                        service_moneda: serviceCurrency,
                        filtro_moneda: currencyFilter,
                        original_codigo_iso: service.codigo_iso_moneda,
                        id_moneda: service.id_moneda,
                        precio: service.precio,
                        mapeo_aplicado: service.id_moneda ? 'por_id' : 'codigo_iso_limpio'
                    });
                } else {
                    console.log(`✅ Servicio "${service.nombre}" coincide:`, {
                        service_moneda: serviceCurrency,
                        filtro_moneda: currencyFilter,
                        id_moneda: service.id_moneda,
                        mapeo_aplicado: service.id_moneda ? 'por_id' : 'codigo_iso_limpio'
                    });
                }

                return matches;
            });

            console.log('📊 Servicios después del filtro de moneda:', filtered.length);
        }

        // Filtro por precio (aplicar siempre)
        const beforePrice = filtered.length;
        console.log(`💰 Aplicando filtro de precio: rango ${priceRange[0]} - ${priceRange[1]}, servicios antes: ${beforePrice}`);
        filtered = filtered.filter(service => {
            const price = service.precio || 0;
            // Si el rango máximo es 0, no mostrar ningún servicio (filtro activo)
            if (priceRange[1] === 0) {
                console.log(`💰 Servicio "${service.nombre}" - Precio: ${price}, Rango máximo es 0, excluido`);
                return false;
            }
            const matches = price >= priceRange[0] && price <= priceRange[1];
            console.log(`💰 Servicio "${service.nombre}" - Precio: ${price}, Rango: ${priceRange[0]}-${priceRange[1]}, Match: ${matches}`);
            return matches;
        });
        console.log(`💰 Filtro precio por rango: ${priceRange[0]} - ${priceRange[1]}: ${beforePrice} → ${filtered.length} servicios`);

        // Filtro por fecha
        if (dateFilter !== 'all') {
            const now = new Date();
            filtered = filtered.filter(service => {
                const serviceDate = new Date(service.created_at);
                const diffInMs = now.getTime() - serviceDate.getTime();
                const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
                
                switch (dateFilter) {
                    case 'recent':
                        return true; // No filtrar por fecha, solo ordenar
                    case 'oldest':
                        return true; // No filtrar, solo cambiar orden
                    case '7days':
                        return diffInDays <= 7;
                    case '30days':
                        return diffInDays <= 30;
                    case '12months':
                        return diffInDays <= 365;
                    case 'custom':
                        if (customDateRange.start && customDateRange.end) {
                            const startDate = new Date(customDateRange.start);
                            const endDate = new Date(customDateRange.end);
                            return serviceDate >= startDate && serviceDate <= endDate;
                        }
                        return true;
                    default:
                        return true;
                }
            });
        }

        // Ordenar por fecha
        filtered.sort((a, b) => {
            const dateA = new Date(a.created_at).getTime();
            const dateB = new Date(b.created_at).getTime();
            if (dateFilter === 'oldest') {
                return dateA - dateB; // Más antiguos primero
            } else {
                return dateB - dateA; // Más recientes primero (por defecto)
            }
        });

        return filtered;
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
        // NUEVO: Si estamos usando el endpoint filtrado del servidor, usar totalServices
        if (totalServices > 0) {
            const pages = Math.ceil(totalServices / itemsPerPage);
            console.log('📄 Calculando páginas con servidor filtrado:', {
                totalServices,
                itemsPerPage,
                totalPages: pages
            });
            return pages;
        }
        
        // Fallback: Si no hay paginación del backend, usar filtros locales
        const hasActiveFilters = priceRange[0] > 0 || priceRange[1] < 1000000000 || 
                                currencyFilter !== 'all' || 
                                categoryFilter !== 'all' || 
                                departmentFilter !== 'all' || 
                                cityFilter !== 'all' ||
                                searchQuery.trim() !== '';
        
        if (hasActiveFilters) {
            const pages = Math.ceil(filteredServices.length / itemsPerPage);
            console.log('📄 Calculando páginas con filtros locales:', {
                filteredServices: filteredServices.length,
                itemsPerPage,
                totalPages: pages
            });
            return pages;
        }
        
        // Si no hay filtros activos, usar paginación del backend
        const pages = Math.ceil(totalServices / itemsPerPage);
        console.log('📄 Calculando páginas del backend:', {
            totalServices,
            itemsPerPage,
            totalPages: pages
        });
        return pages;
    }, [filteredServices.length, totalServices, itemsPerPage, priceRange, currencyFilter, categoryFilter, departmentFilter, cityFilter, searchQuery]);

    // Resetear filtros
    const resetFilters = useCallback(() => {
        setSearchQuery('');
        setDateFilter('all');
        setCategoryFilter('all');
        setRatingFilter(0);
        setCurrencyFilter('all');
        setPriceFilter('all');
        setPriceRange([0, 1000000000]);
        setDepartmentFilter('all');
        setCityFilter('all');
        setCurrentPage(1);
    }, []);

    // Estados de loading y error
    if (isLoading) {
        return (
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
    }

    if (error) {
        return (
            <div className="bg-slate-50 min-h-screen">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="bg-white p-8 rounded-xl shadow-md border border-slate-200/80">
                        <div className="text-center py-12">
                            <ExclamationCircleIcon className="mx-auto h-12 w-12 text-red-400" />
                            <h3 className="mt-2 text-lg font-semibold text-slate-800">Error al cargar</h3>
                            <p className="mt-1 text-sm text-slate-500">{error}</p>
                            <button
                                onClick={loadInitialData}
                                className="mt-4 btn-blue touch-manipulation"
                            >
                                <span>Reintentar</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-slate-50 min-h-screen">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="max-w-7xl mx-auto">
                    {/* Encabezado mejorado para móviles */}
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
                    
                    {/* Barra de búsqueda mejorada */}
                    <div className="mt-6 space-y-4">
                        {/* Input de búsqueda principal */}
                        <div className="relative">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                placeholder="Buscar servicios profesionales..."
                                className="w-full pl-11 pr-4 py-2.5 sm:py-3 rounded-lg border-2 border-slate-300 focus:ring-primary-500 focus:border-primary-500 transition text-sm sm:text-base"
                                disabled={isSearching}
                            />
                            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-slate-400" />
                        </div>

                        {/* Botones de búsqueda - uniformes y bien distribuidos */}
                        <div className="flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={handleSearch}
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
                                onClick={handleAISearch}
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
                                <label className="block text-xs font-medium text-slate-700">Fecha</label>
                                <select
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
                                    onChange={(e) => setRatingFilter(parseInt(e.target.value))}
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
                    {currencyFilter !== 'all' ? (
                        <div className="mt-3 p-3 sm:p-4 bg-primary-50 rounded-lg border border-primary-200">
                            <div className="space-y-3">
                                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                                    <label className="block text-xs sm:text-sm font-medium text-slate-700">
                                        Precio en {currencyFilter === 'GS' ? 'Guaraníes' : currencyFilter === 'USD' ? 'Dólares' : currencyFilter === 'BRL' ? 'Reales' : 'Pesos'}
                                    </label>
                                    <span className="text-xs sm:text-sm font-semibold text-primary-600">
                                        Hasta {currencyFilter === 'GS' ?
                                            `₲ ${priceRange[1].toLocaleString('es-PY')}` :
                                            currencyFilter === 'USD' ?
                                                `$ ${priceRange[1].toLocaleString('en-US')}` :
                                                currencyFilter === 'BRL' ?
                                                    `R$ ${priceRange[1].toLocaleString('pt-BR')}` :
                                                    `$ ${priceRange[1].toLocaleString('es-AR')}`
                                        }
                                    </span>
                                </div>

                                <div className="space-y-2">
                                    <input
                                        type="range"
                                        min="0"
                                        max="1000000000"
                                        step="1000000"
                                        value={priceRange[1]}
                                        onChange={(e) => setPriceRange([0, parseInt(e.target.value)])}
                                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer slider-thumb"
                                        style={{
                                            background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(priceRange[1] / 1000000000) * 100}%, #e2e8f0 ${(priceRange[1] / 1000000000) * 100}%, #e2e8f0 100%)`
                                        }}
                                    />
                                    <div className="flex justify-between text-xs text-slate-500">
                                        <span>{currencyFilter === 'GS' ? '₲' : currencyFilter === 'USD' ? '$' : currencyFilter === 'BRL' ? 'R$' : '$'} 0</span>
                                        <span>{currencyFilter === 'GS' ?
                                            '₲ 1.000.000.000' :
                                            currencyFilter === 'USD' ?
                                                '$ 1,000,000,000' :
                                                currencyFilter === 'BRL' ?
                                                    'R$ 1.000.000.000' :
                                                    '$ 1.000.000.000'
                                        }</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                            <p className="text-xs text-slate-600 text-center">
                                💡 Para filtrar por precio, primero selecciona una moneda arriba
                            </p>
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
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                    onClick={() => setShowAdvancedFilters(false)}
                >
                    <div
                        className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-xl font-semibold text-slate-900">Filtros Avanzados</h2>
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
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Departamento
                                    </label>
                                    <select
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
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Ciudad
                                    </label>
                                    <select
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
                    </div>
                </div>
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
