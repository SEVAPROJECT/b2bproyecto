import { useState, useCallback, useMemo } from 'react';
import { FilterConfig } from '../components/ui/StandardFilters';

export interface FilterableItem {
    created_at?: string;
    fecha_solicitud?: string;
    fecha_creacion?: string;
    id_categoria?: string | number;
    nombre_categoria?: string;
    nombre_empresa?: string;
    razon_social?: string;
    estado_aprobacion?: string;
    estado?: string;
    [key: string]: any;
}

export const useStandardFilters = <T extends FilterableItem>(
    items: T[],
    initialFilters: Partial<FilterConfig> = {}
) => {
    const [filters, setFilters] = useState<FilterConfig>({
        dateFilter: 'all',
        categoryFilter: 'all',
        companyFilter: 'all',
        statusFilter: 'all',
        customDate: '',
        ...initialFilters
    });

    // Función para filtrar items
    const filterItems = useCallback((itemsToFilter: T[]) => {
        return itemsToFilter.filter(item => {
            // Filtro por fecha
            if (filters.dateFilter !== 'all') {
                const itemDate = new Date(
                    item.created_at || 
                    item.fecha_solicitud || 
                    item.fecha_creacion || 
                    new Date()
                );
                const now = new Date();
                
                switch (filters.dateFilter) {
                    case 'today':
                        if (itemDate.toDateString() !== now.toDateString()) return false;
                        break;
                    case 'week':
                        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        if (itemDate < weekAgo) return false;
                        break;
                    case 'month':
                        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                        if (itemDate < monthAgo) return false;
                        break;
                    case 'year':
                        const yearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
                        if (itemDate < yearAgo) return false;
                        break;
                    case 'custom':
                        if (filters.customDate) {
                            const customDate = new Date(filters.customDate);
                            if (itemDate.toDateString() !== customDate.toDateString()) return false;
                        }
                        break;
                }
            }

            // Filtro por categoría
            if (filters.categoryFilter !== 'all') {
                const itemCategoryId = item.id_categoria?.toString();
                if (itemCategoryId !== filters.categoryFilter) return false;
            }

            // Filtro por empresa
            if (filters.companyFilter !== 'all') {
                const itemCompany = item.nombre_empresa || item.razon_social;
                if (itemCompany !== filters.companyFilter) return false;
            }

            // Filtro por estado
            if (filters.statusFilter !== 'all') {
                const itemStatus = item.estado_aprobacion || item.estado;
                if (itemStatus !== filters.statusFilter) return false;
            }

            return true;
        });
    }, [filters]);

    // Items filtrados
    const filteredItems = useMemo(() => {
        return filterItems(items);
    }, [items, filterItems]);

    // Estadísticas
    const statistics = useMemo(() => {
        const total = items.length;
        const filtered = filteredItems.length;
        const pending = items.filter(item => {
            const status = item.estado_aprobacion || item.estado;
            return status === 'pendiente';
        }).length;
        const approved = items.filter(item => {
            const status = item.estado_aprobacion || item.estado;
            return status === 'aprobada' || status === 'aprobado';
        }).length;
        const rejected = items.filter(item => {
            const status = item.estado_aprobacion || item.estado;
            return status === 'rechazada' || status === 'rechazado';
        }).length;

        return { total, filtered, pending, approved, rejected };
    }, [items, filteredItems]);

    // Opciones para los filtros
    const filterOptions = useMemo(() => {
        // Categorías únicas
        const categories = [...new Set(
            items
                .map(item => ({
                    id: item.id_categoria,
                    name: item.nombre_categoria || `Categoría ${item.id_categoria}`
                }))
                .filter(cat => cat.id)
        )];

        // Empresas únicas
        const companies = [...new Set(
            items
                .map(item => item.nombre_empresa || item.razon_social)
                .filter(Boolean)
        )].sort();

        // Estados únicos
        const statuses = [
            { value: 'pendiente', label: 'Pendiente' },
            { value: 'aprobada', label: 'Aprobada' },
            { value: 'rechazada', label: 'Rechazada' }
        ];

        return {
            categories,
            companies,
            statuses
        };
    }, [items]);

    // Función para resetear filtros
    const resetFilters = useCallback(() => {
        setFilters({
            dateFilter: 'all',
            categoryFilter: 'all',
            companyFilter: 'all',
            statusFilter: 'all',
            customDate: ''
        });
    }, []);

    // Función para actualizar filtros
    const updateFilters = useCallback((newFilters: FilterConfig) => {
        setFilters(newFilters);
    }, []);

    return {
        filters,
        filteredItems,
        statistics,
        filterOptions,
        resetFilters,
        updateFilters
    };
};
