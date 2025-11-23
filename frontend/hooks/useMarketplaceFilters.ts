import { useState, useCallback, useMemo } from 'react';


export interface MarketplaceFilters {
    searchQuery: string;
    dateFilter: string;
    categoryFilter: string;
    ratingFilter: number;
    currencyFilter: string;
    priceFilter: string;
    priceRange: [number, number];
    departmentFilter: string;
    cityFilter: string;
    customDateRange: { start: string; end: string };
}

const DEFAULT_FILTERS: MarketplaceFilters = {
    searchQuery: '',
    dateFilter: 'all',
    categoryFilter: 'all',
    ratingFilter: 0,
    currencyFilter: 'all',
    priceFilter: 'all',
    priceRange: [0, 1000000000],
    departmentFilter: 'all',
    cityFilter: 'all',
    customDateRange: { start: '', end: '' }
};

export const useMarketplaceFilters = () => {
    const [filters, setFilters] = useState<MarketplaceFilters>(DEFAULT_FILTERS);

    const setSearchQuery = useCallback((value: string) => {
        setFilters(prev => ({ ...prev, searchQuery: value }));
    }, []);

    const setDateFilter = useCallback((value: string) => {
        setFilters(prev => ({ ...prev, dateFilter: value }));
    }, []);

    const setCategoryFilter = useCallback((value: string) => {
        setFilters(prev => ({ ...prev, categoryFilter: value }));
    }, []);

    const setRatingFilter = useCallback((value: number) => {
        setFilters(prev => ({ ...prev, ratingFilter: value }));
    }, []);

    const setCurrencyFilter = useCallback((value: string) => {
        setFilters(prev => ({ ...prev, currencyFilter: value }));
    }, []);

    const setPriceFilter = useCallback((value: string) => {
        setFilters(prev => ({ ...prev, priceFilter: value }));
    }, []);

    const setPriceRange = useCallback((value: [number, number]) => {
        setFilters(prev => ({ ...prev, priceRange: value }));
    }, []);

    const setDepartmentFilter = useCallback((value: string) => {
        setFilters(prev => ({ ...prev, departmentFilter: value }));
    }, []);

    const setCityFilter = useCallback((value: string) => {
        setFilters(prev => ({ ...prev, cityFilter: value }));
    }, []);

    const setCustomDateRange = useCallback((value: { start: string; end: string }) => {
        setFilters(prev => ({ ...prev, customDateRange: value }));
    }, []);

    const resetFilters = useCallback(() => {
        setFilters(DEFAULT_FILTERS);
    }, []);

    const hasActiveFilters = useMemo(() => {
        return filters.currencyFilter !== 'all' ||
            filters.priceRange[0] > 0 ||
            filters.priceRange[1] < 1000000000 ||
            filters.categoryFilter !== 'all' ||
            filters.departmentFilter !== 'all' ||
            filters.cityFilter !== 'all' ||
            filters.searchQuery.trim() !== '' ||
            filters.dateFilter !== 'all' ||
            filters.ratingFilter > 0;
    }, [filters]);

    return {
        filters,
        setSearchQuery,
        setDateFilter,
        setCategoryFilter,
        setRatingFilter,
        setCurrencyFilter,
        setPriceFilter,
        setPriceRange,
        setDepartmentFilter,
        setCityFilter,
        setCustomDateRange,
        resetFilters,
        hasActiveFilters
    };
};


