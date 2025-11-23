import { BackendService } from '../types';

export interface FilterParams {
    currencyFilter: string;
    priceRange: [number, number];
    categoryFilter: string;
    departmentFilter: string;
    cityFilter: string;
    searchQuery: string;
    dateFilter: string;
    ratingFilter: number;
    customDateRange: { start: string; end: string };
}

const applyCurrencyFilter = (filters: Record<string, any>, currencyFilter: string): void => {
    if (currencyFilter !== 'all') {
        filters.currency = currencyFilter;
    }
};

const applyPriceFilter = (filters: Record<string, any>, priceRange: [number, number]): void => {
    const isPriceFilterActive = priceRange[0] > 0 || priceRange[1] < 1000000000;
    if (!isPriceFilterActive) return;

    if (priceRange[0] > 0) {
        filters.min_price = priceRange[0];
    }
    if (priceRange[1] < 1000000000) {
        filters.max_price = priceRange[1];
    }
};

const applyCategoryFilter = (filters: Record<string, any>, categoryFilter: string): void => {
    if (categoryFilter !== 'all') {
        filters.category_id = parseInt(categoryFilter);
    }
};

const applyLocationFilters = (filters: Record<string, any>, departmentFilter: string, cityFilter: string): void => {
    if (departmentFilter !== 'all') {
        filters.department = departmentFilter;
    }
    if (cityFilter !== 'all') {
        filters.city = cityFilter;
    }
};

const applySearchFilter = (filters: Record<string, any>, searchQuery: string): void => {
    if (searchQuery.trim()) {
        filters.search = searchQuery.trim();
    }
};

const applyDateFilter = (filters: Record<string, any>, dateFilter: string, customDateRange: { start: string; end: string }): void => {
    if (dateFilter === 'all') return;

    const dateFilters = getDateFilters(dateFilter, customDateRange);
    if (dateFilters.dateFrom) {
        filters.date_from = dateFilters.dateFrom;
    }
    if (dateFilters.dateTo) {
        filters.date_to = dateFilters.dateTo;
    }
};

const applyRatingFilter = (filters: Record<string, any>, ratingFilter: number): void => {
    if (ratingFilter > 0) {
        filters.min_rating = ratingFilter;
    }
};

export const buildBackendFilters = (params: FilterParams): Record<string, any> => {
    const filters: Record<string, any> = {};
    const {
        currencyFilter,
        priceRange,
        categoryFilter,
        departmentFilter,
        cityFilter,
        searchQuery,
        dateFilter,
        ratingFilter,
        customDateRange
    } = params;

    applyCurrencyFilter(filters, currencyFilter);
    applyPriceFilter(filters, priceRange);
    applyCategoryFilter(filters, categoryFilter);
    applyLocationFilters(filters, departmentFilter, cityFilter);
    applySearchFilter(filters, searchQuery);
    applyDateFilter(filters, dateFilter, customDateRange);
    applyRatingFilter(filters, ratingFilter);

    return filters;
};

const getDateFilters = (dateFilter: string, customDateRange: { start: string; end: string }) => {
    const today = new Date();
    let dateFrom: string | undefined;
    let dateTo: string | undefined;

    switch (dateFilter) {
        case 'today':
            dateFrom = today.toISOString().split('T')[0];
            dateTo = today.toISOString().split('T')[0];
            break;
        case 'week': {
            const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
            dateFrom = weekAgo.toISOString().split('T')[0];
            dateTo = today.toISOString().split('T')[0];
            break;
        }
        case 'month': {
            const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
            dateFrom = monthAgo.toISOString().split('T')[0];
            dateTo = today.toISOString().split('T')[0];
            break;
        }
        case 'custom':
            if (customDateRange.start && customDateRange.end) {
                dateFrom = customDateRange.start;
                dateTo = customDateRange.end;
            }
            break;
    }

    return { dateFrom, dateTo };
};

const getServiceCurrency = (service: BackendService): string => {
    if (service.id_moneda) {
        switch (service.id_moneda) {
            case 1: return 'GS';
            case 2: return 'USD';
            case 3: return 'BRL';
            case 4:
            case 8: return 'ARS';
            default: return 'GS';
        }
    }
    if (service.codigo_iso_moneda) {
        return service.codigo_iso_moneda.trim();
    }
    return 'GS';
};

const matchesSearchQuery = (service: BackendService, query: string): boolean => {
    if (!query.trim()) return true;
    const lowerQuery = query.toLowerCase();
    return service.nombre.toLowerCase().includes(lowerQuery) ||
        service.descripcion.toLowerCase().includes(lowerQuery) ||
        (service.razon_social?.toLowerCase().includes(lowerQuery) ?? false);
};

const matchesCategory = (service: BackendService, categoryFilter: string): boolean => {
    if (categoryFilter === 'all') return true;
    return service.id_categoria.toString() === categoryFilter;
};

const matchesDepartment = (service: BackendService, departmentFilter: string): boolean => {
    if (departmentFilter === 'all') return true;
    return (service.departamento || '') === departmentFilter;
};

const matchesCity = (service: BackendService, cityFilter: string, departmentFilter: string): boolean => {
    if (cityFilter === 'all' || departmentFilter === 'all') return true;
    return (service.ciudad || '') === cityFilter;
};

const matchesCurrency = (service: BackendService, currencyFilter: string): boolean => {
    if (currencyFilter === 'all') return true;
    return getServiceCurrency(service) === currencyFilter;
};

const matchesPriceRange = (service: BackendService, priceRange: [number, number]): boolean => {
    const price = service.precio || 0;
    if (priceRange[1] === 0) return false;
    return price >= priceRange[0] && price <= priceRange[1];
};

const matchesDateFilter = (service: BackendService, dateFilter: string, customDateRange: { start: string; end: string }): boolean => {
    if (dateFilter === 'all') return true;

    const now = new Date();
    const serviceDate = new Date(service.created_at);
    const diffInMs = now.getTime() - serviceDate.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

    switch (dateFilter) {
        case 'recent':
        case 'oldest':
            return true;
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
};

const hasValidPrice = (service: BackendService): boolean => {
    return service.precio !== null && service.precio !== undefined;
};

export const filterServices = (services: BackendService[], params: FilterParams): BackendService[] => {
    // Eliminar duplicados
    const uniqueServices = services.filter((service, index, self) =>
        index === self.findIndex(s => s.id_servicio === service.id_servicio)
    );

    // Aplicar filtros
    let filtered = uniqueServices.filter(hasValidPrice);

    if (params.searchQuery.trim()) {
        filtered = filtered.filter(service => matchesSearchQuery(service, params.searchQuery));
    }

    filtered = filtered.filter(service => matchesCategory(service, params.categoryFilter));
    filtered = filtered.filter(service => matchesDepartment(service, params.departmentFilter));
    filtered = filtered.filter(service => matchesCity(service, params.cityFilter, params.departmentFilter));
    filtered = filtered.filter(service => matchesCurrency(service, params.currencyFilter));
    filtered = filtered.filter(service => matchesPriceRange(service, params.priceRange));
    filtered = filtered.filter(service => matchesDateFilter(service, params.dateFilter, params.customDateRange));

    // Ordenar por fecha
    filtered.sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        if (params.dateFilter === 'oldest') {
            return dateA - dateB;
        }
        return dateB - dateA;
    });

    return filtered;
};


