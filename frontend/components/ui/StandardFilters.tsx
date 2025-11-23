import React, { useState, useCallback } from 'react';

export interface FilterConfig {
    dateFilter: string;
    categoryFilter: string;
    companyFilter: string;
    statusFilter: string;
    customDate: string;
}

export interface FilterOptions {
    categories?: Array<{ id: string | number; name: string }>;
    companies?: string[];
    statuses?: Array<{ value: string; label: string }>;
    showDateFilter?: boolean;
    showCategoryFilter?: boolean;
    showCompanyFilter?: boolean;
    showStatusFilter?: boolean;
    customDateLabel?: string;
}

interface StandardFiltersProps {
    filters: FilterConfig;
    onFiltersChange: (filters: FilterConfig) => void;
    onResetFilters: () => void;
    options: FilterOptions;
    className?: string;
}

const StandardFilters: React.FC<StandardFiltersProps> = ({
    filters,
    onFiltersChange,
    onResetFilters,
    options,
    className = ''
}) => {
    const [showCustomDate, setShowCustomDate] = useState(false);

    const handleFilterChange = useCallback((key: keyof FilterConfig, value: string) => {
        onFiltersChange({ ...filters, [key]: value });
        
        // Mostrar/ocultar fecha personalizada
        if (key === 'dateFilter') {
            setShowCustomDate(value === 'custom');
            if (value !== 'custom') {
                onFiltersChange({ ...filters, dateFilter: value, customDate: '' });
            }
        }
    }, [filters, onFiltersChange]);

    return (
        <div className={`bg-white p-6 rounded-lg shadow border border-gray-200 ${className}`}>
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">📋 Filtrar</h2>
                <button
                    onClick={onResetFilters}
                    className="text-sm text-blue-600 hover:text-blue-800"
                >
                    🔄 Limpiar Filtros
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Filtro por fecha */}
                {options.showDateFilter !== false && (
                    <div>
                        <label htmlFor="filter-date-standard" className="block text-sm font-medium text-gray-700 mb-2">📅 Fecha</label>
                        <select
                            id="filter-date-standard"
                            value={filters.dateFilter}
                            onChange={(e) => handleFilterChange('dateFilter', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">Todas las fechas</option>
                            <option value="today">Hoy</option>
                            <option value="week">Esta semana</option>
                            <option value="month">Este mes</option>
                            <option value="year">Este año</option>
                            <option value="custom">Fecha específica</option>
                        </select>
                    </div>
                )}

                {/* Filtro por categoría */}
                {options.showCategoryFilter !== false && options.categories && (
                    <div>
                        <label htmlFor="filter-category-standard" className="block text-sm font-medium text-gray-700 mb-2">📂 Categoría</label>
                        <select
                            id="filter-category-standard"
                            value={filters.categoryFilter}
                            onChange={(e) => handleFilterChange('categoryFilter', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">Todas las categorías</option>
                            {options.categories.map(category => (
                                <option key={category.id} value={category.id.toString()}>
                                    {category.name}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Filtro por empresa */}
                {options.showCompanyFilter !== false && options.companies && (
                    <div>
                        <label htmlFor="filter-company-standard" className="block text-sm font-medium text-gray-700 mb-2">📊 Empresa</label>
                        <select
                            id="filter-company-standard"
                            value={filters.companyFilter}
                            onChange={(e) => handleFilterChange('companyFilter', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">Todas las empresas</option>
                            {options.companies.map(company => (
                                <option key={company} value={company}>
                                    {company}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Filtro por estado */}
                {options.showStatusFilter !== false && options.statuses && (
                    <div>
                        <label htmlFor="filter-status-standard" className="block text-sm font-medium text-gray-700 mb-2">Estado</label>
                        <select
                            id="filter-status-standard"
                            value={filters.statusFilter}
                            onChange={(e) => handleFilterChange('statusFilter', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">Todos los estados</option>
                            {options.statuses.map(status => (
                                <option key={status.value} value={status.value}>
                                    {status.label}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Fecha personalizada */}
                {showCustomDate && (
                    <div>
                        <label htmlFor="filter-custom-date-standard" className="block text-sm font-medium text-gray-700 mb-2">
                            {options.customDateLabel || 'Fecha específica'}
                        </label>
                        <input
                            id="filter-custom-date-standard"
                            type="date"
                            value={filters.customDate}
                            onChange={(e) => handleFilterChange('customDate', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

export default StandardFilters;
