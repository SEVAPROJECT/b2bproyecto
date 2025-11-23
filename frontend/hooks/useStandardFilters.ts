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
        // Función helper para obtener la fecha del item
        const getItemDate = (item: T): Date => {
            return new Date(
                item.created_at || 
                item.fecha_solicitud || 
                item.fecha_creacion || 
                new Date()
            );
        };

        // Función helper para verificar si el item pasa el filtro de fecha
        const matchesDateFilter = (item: T): boolean => {
            if (filters.dateFilter === 'all') {
                return true;
            }

            const itemDate = getItemDate(item);
            const now = new Date();
            
            switch (filters.dateFilter) {
                case 'today':
                    return itemDate.toDateString() === now.toDateString();
                case 'week': {
                    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    return itemDate >= weekAgo;
                }
                case 'month': {
                    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                    return itemDate >= monthAgo;
                }
                case 'year': {
                    const yearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
                    return itemDate >= yearAgo;
                }
                case 'custom': {
                    if (filters.customDate) {
                        const customDate = new Date(filters.customDate);
                        return itemDate.toDateString() === customDate.toDateString();
                    }
                    return true;
                }
                default:
                    return true;
            }
        };

        // Función helper para verificar si el item pasa el filtro de categoría
        const matchesCategoryFilter = (item: T): boolean => {
            if (filters.categoryFilter === 'all') {
                return true;
            }
            const itemCategoryId = item.id_categoria?.toString();
            return itemCategoryId === filters.categoryFilter;
        };

        // Función helper para verificar si el item pasa el filtro de empresa
        const matchesCompanyFilter = (item: T): boolean => {
            if (filters.companyFilter === 'all') {
                return true;
            }
            const itemCompany = item.nombre_empresa || item.razon_social;
            return itemCompany === filters.companyFilter;
        };

        // Función helper para verificar si el item pasa el filtro de estado
        const matchesStatusFilter = (item: T): boolean => {
            if (filters.statusFilter === 'all') {
                return true;
            }
            const itemStatus = item.estado_aprobacion || item.estado;
            return itemStatus === filters.statusFilter;
        };

        return itemsToFilter.filter(item => {
            return matchesDateFilter(item) &&
                   matchesCategoryFilter(item) &&
                   matchesCompanyFilter(item) &&
                   matchesStatusFilter(item);
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
