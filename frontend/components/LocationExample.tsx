import React, { useState } from 'react';
import { LocationSelector } from './LocationSelector';
import { AddressSelector } from './AddressSelector';
import { locationsAPI, Departamento, Ciudad, Barrio } from '../services/locations';

export const LocationExample: React.FC = () => {
    const [selectedDepartamento, setSelectedDepartamento] = useState<Departamento | null>(null);
    const [selectedCiudad, setSelectedCiudad] = useState<Ciudad | null>(null);
    const [selectedBarrio, setSelectedBarrio] = useState<Barrio | null>(null);
    const [departamentos, setDepartamentos] = useState<Departamento[]>([]);
    const [ciudades, setCiudades] = useState<Ciudad[]>([]);
    const [barrios, setBarrios] = useState<Barrio[]>([]);

    // Cargar departamentos al montar el componente
    React.useEffect(() => {
        const loadDepartamentos = async () => {
            try {
                const data = await locationsAPI.getDepartamentos();
                setDepartamentos(data);
            } catch (error) {
                console.error('Error al cargar departamentos:', error);
            }
        };
        loadDepartamentos();
    }, []);

    // Cargar ciudades cuando se selecciona un departamento
    React.useEffect(() => {
        if (selectedDepartamento) {
            const loadCiudades = async () => {
                try {
                    const data = await locationsAPI.getCiudadesPorDepartamento(selectedDepartamento.id_departamento);
                    setCiudades(data);
                } catch (error) {
                    console.error('Error al cargar ciudades:', error);
                }
            };
            loadCiudades();
        } else {
            setCiudades([]);
        }
    }, [selectedDepartamento]);

    // Cargar barrios cuando se selecciona una ciudad
    React.useEffect(() => {
        if (selectedCiudad) {
            const loadBarrios = async () => {
                try {
                    const data = await locationsAPI.getBarriosPorCiudad(selectedCiudad.id_ciudad);
                    setBarrios(data);
                } catch (error) {
                    console.error('Error al cargar barrios:', error);
                }
            };
            loadBarrios();
        } else {
            setBarrios([]);
        }
    }, [selectedCiudad]);

    const handleAddressChange = (address: {
        departamento: Departamento | null;
        ciudad: Ciudad | null;
        barrio: Barrio | null;
    }) => {
        console.log('Dirección completa seleccionada:', address);
    };

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-8">
            <div className="text-center">
                <h1 className="text-3xl font-bold text-gray-900 mb-4">
                    Ejemplos de Componentes de Ubicación
                </h1>
                <p className="text-gray-600">
                    Diferentes formas de implementar la selección de ubicaciones
                </p>
            </div>

            {/* Ejemplo 1: Selectores individuales */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    1. Selectores Individuales
                </h2>
                <p className="text-gray-600 mb-4">
                    Cada selector funciona de forma independiente, útil cuando necesitas control total.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <LocationSelector<Departamento>
                        label="Departamento"
                        placeholder="Selecciona departamento..."
                        options={departamentos}
                        value={selectedDepartamento}
                        onChange={setSelectedDepartamento}
                    />
                    
                    <LocationSelector<Ciudad>
                        label="Ciudad"
                        placeholder={selectedDepartamento ? "Selecciona ciudad..." : "Primero departamento"}
                        options={ciudades}
                        value={selectedCiudad}
                        onChange={setSelectedCiudad}
                        disabled={!selectedDepartamento}
                    />
                    
                    <LocationSelector<Barrio>
                        label="Barrio"
                        placeholder={selectedCiudad ? "Selecciona barrio..." : "Primero ciudad"}
                        options={barrios}
                        value={selectedBarrio}
                        onChange={setSelectedBarrio}
                        disabled={!selectedCiudad}
                    />
                </div>

                {/* Información de selección */}
                <div className="mt-4 p-3 bg-gray-50 rounded">
                    <p className="text-sm text-gray-700">
                        <strong>Selección actual:</strong> {
                            selectedDepartamento?.nombre || 'Ninguno'
                        } → {
                            selectedCiudad?.nombre || 'Ninguna'
                        } → {
                            selectedBarrio?.nombre || 'Ninguno'
                        }
                    </p>
                </div>
            </div>

            {/* Ejemplo 2: Selector completo de dirección */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    2. Selector Completo de Dirección
                </h2>
                <p className="text-gray-600 mb-4">
                    Un solo componente que maneja toda la lógica de dependencias automáticamente.
                </p>
                
                <AddressSelector
                    onAddressChange={handleAddressChange}
                    className="mb-4"
                />
            </div>

            {/* Ejemplo 3: Uso en formulario */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    3. Uso en Formulario
                </h2>
                <p className="text-gray-600 mb-4">
                    Ejemplo de cómo integrar en un formulario de registro.
                </p>
                
                <form className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Nombre de la Empresa
                            </label>
                            <input
                                type="text"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="Mi Empresa S.A."
                            />
                        </div>
                        
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                RUC
                            </label>
                            <input
                                type="text"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="12345678-9"
                            />
                        </div>
                    </div>

                    {/* Selector de ubicación integrado */}
                    <div className="border-t pt-4">
                        <h3 className="text-lg font-medium text-gray-900 mb-3">Ubicación de la Empresa</h3>
                        <AddressSelector
                            onAddressChange={handleAddressChange}
                        />
                    </div>

                    <div className="flex justify-end space-x-3 pt-4">
                        <button
                            type="button"
                            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        >
                            Guardar Empresa
                        </button>
                    </div>
                </form>
            </div>

            {/* Información adicional */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-900 mb-2">
                    💡 Ventajas de estos componentes:
                </h4>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• <strong>Reutilizables:</strong> Se pueden usar en cualquier parte de la aplicación</li>
                    <li>• <strong>Consistentes:</strong> Misma experiencia de usuario en toda la app</li>
                    <li>• <strong>Mantenibles:</strong> Cambios centralizados en un solo lugar</li>
                    <li>• <strong>Accesibles:</strong> Cumplen con estándares de accesibilidad</li>
                    <li>• <strong>Responsivos:</strong> Se adaptan a diferentes tamaños de pantalla</li>
                </ul>
            </div>
        </div>
    );
};
