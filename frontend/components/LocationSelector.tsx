import React, { useState, useEffect, useRef } from 'react';
import { ChevronDownIcon } from './icons';

interface LocationSelectorProps<T extends { id: number; nombre: string }> {
    label: string;
    placeholder: string;
    options: T[];
    value: T | null;
    onChange: (option: T | null) => void;
    isLoading?: boolean;
    disabled?: boolean;
    error?: string;
    className?: string;
}

export const LocationSelector = <T extends { id: number; nombre: string }>({
    label,
    placeholder,
    options,
    value,
    onChange,
    isLoading = false,
    disabled = false,
    error,
    className = ''
}: LocationSelectorProps<T>) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filteredOptions, setFilteredOptions] = useState<T[]>(options);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Filtrar opciones basado en el término de búsqueda
    useEffect(() => {
        if (searchTerm.trim() === '') {
            setFilteredOptions(options);
        } else {
            const filtered = options.filter(option =>
                option.nombre.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setFilteredOptions(filtered);
        }
    }, [searchTerm, options]);

    // Cerrar dropdown cuando se hace clic fuera
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Actualizar searchTerm cuando cambia el valor seleccionado
    useEffect(() => {
        if (value) {
            setSearchTerm(value.nombre);
        } else {
            setSearchTerm('');
        }
    }, [value]);

    const handleSelect = (option: T) => {
        console.log('🎯 Seleccionando:', option.nombre);
        onChange(option);
        setIsOpen(false);
        setSearchTerm(option.nombre);
    };

    const handleKeyDown = (e: React.KeyboardEvent, option: T) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleSelect(option);
        }
    };

    const handleClear = () => {
        console.log('🧹 Limpiando selección');
        onChange(null);
        setSearchTerm('');
        setIsOpen(false);
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
        if (!isOpen) {
            setIsOpen(true);
        }
    };

    const handleInputFocus = () => {
        if (!disabled) {
            setIsOpen(true);
        }
    };

    return (
        <div className={`relative ${className}`}>
            <label className="block text-sm sm:text-base font-medium text-gray-700 mb-2">
                {label}
            </label>

            <div className="relative" ref={dropdownRef}>
                <div className="relative">
                    <input
                        type="text"
                        placeholder={placeholder}
                        value={searchTerm}
                        onChange={handleInputChange}
                        onFocus={handleInputFocus}
                        disabled={disabled}
                        className={`
                            w-full px-3 py-2 sm:px-4 sm:py-3 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                            transition-colors duration-200 text-sm sm:text-base
                            ${disabled ? 'bg-gray-100 cursor-not-allowed opacity-60' : 'bg-white hover:border-gray-400'}
                            ${error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300'}
                        `}
                    />

                    <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                        {isLoading ? (
                            <div className="loading-spinner"></div>
                        ) : (
                            <ChevronDownIcon
                                className={`h-4 w-4 sm:h-5 sm:w-5 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                            />
                        )}
                    </div>
                </div>

                {/* Dropdown con mejor responsive */}
                {isOpen && !disabled && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 sm:max-h-60 overflow-auto">
                        {filteredOptions.length === 0 ? (
                            <div className="px-3 py-3 sm:py-2 text-sm text-gray-500 text-center">
                                {searchTerm.trim() === '' ? 'No hay opciones disponibles' : 'No se encontraron coincidencias'}
                            </div>
                        ) : (
                            <div>
                                {filteredOptions.map((option) => (
                                    <div
                                        key={option.id}
                                        role="option"
                                        tabIndex={0}
                                        className="px-3 py-3 sm:py-2 text-sm cursor-pointer hover:bg-blue-50 hover:text-blue-900 transition-colors duration-150 touch-manipulation focus:outline-none focus:bg-blue-50 focus:ring-2 focus:ring-blue-500"
                                        onClick={() => handleSelect(option)}
                                        onKeyDown={(e) => handleKeyDown(e, option)}
                                        aria-selected={value?.id === option.id}
                                    >
                                        {option.nombre}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Botón para limpiar selección - mejor responsive */}
            {value && !disabled && (
                <button
                    type="button"
                    onClick={handleClear}
                    className="mt-2 text-sm sm:text-base text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded px-2 py-1 transition-colors duration-200"
                >
                    Limpiar selección
                </button>
            )}

            {/* Mensaje de error - mejor responsive */}
            {error && (
                <p className="mt-2 text-sm sm:text-base text-red-600 bg-red-50 px-3 py-2 rounded-md border border-red-200">
                    {error}
                </p>
            )}
        </div>
    );
};
