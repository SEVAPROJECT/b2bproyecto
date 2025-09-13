import React, { useState } from 'react';
import { AddressSelector } from './AddressSelector';
import { Departamento, Ciudad, Barrio } from '../services/locations';

export const LocationDemo: React.FC = () => {
    const [selectedAddress, setSelectedAddress] = useState<{
        departamento: Departamento | null;
        ciudad: Ciudad | null;
        barrio: Barrio | null;
    }>({
        departamento: null,
        ciudad: null,
        barrio: null
    });

    const handleAddressChange = (address: {
        departamento: Departamento | null;
        ciudad: Ciudad | null;
        barrio: Barrio | null;
    }) => {
        setSelectedAddress(address);
        console.log('Dirección seleccionada:', address);
    };

    return (
        <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Selector de Ubicaciones
                </h2>
                <p className="text-gray-600">
                    Selecciona tu ubicación usando los selectores desplegables con búsqueda en tiempo real.
                </p>
            </div>

            {/* Selector de ubicaciones */}
            <AddressSelector
                onAddressChange={handleAddressChange}
                className="mb-6"
            />

            {/* Información de la selección */}
            <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Ubicación Seleccionada:
                </h3>
                
                {!selectedAddress.departamento && !selectedAddress.ciudad && !selectedAddress.barrio ? (
                    <p className="text-gray-500 italic">
                        No se ha seleccionado ninguna ubicación
                    </p>
                ) : (
                    <div className="space-y-2">
                        {selectedAddress.departamento && (
                            <div className="flex items-center space-x-2">
                                <span className="text-sm font-medium text-gray-700">Departamento:</span>
                                <span className="text-sm text-gray-900 bg-blue-100 px-2 py-1 rounded">
                                    {selectedAddress.departamento.nombre}
                                </span>
                            </div>
                        )}
                        
                        {selectedAddress.ciudad && (
                            <div className="flex items-center space-x-2">
                                <span className="text-sm font-medium text-gray-700">Ciudad:</span>
                                <span className="text-sm text-gray-900 bg-green-100 px-2 py-1 rounded">
                                    {selectedAddress.ciudad.nombre}
                                </span>
                            </div>
                        )}
                        
                        {selectedAddress.barrio && (
                            <div className="flex items-center space-x-2">
                                <span className="text-sm font-medium text-gray-700">Barrio:</span>
                                <span className="text-sm text-gray-900 bg-purple-100 px-2 py-1 rounded">
                                    {selectedAddress.barrio.nombre}
                                </span>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Instrucciones de uso */}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="text-sm font-semibold text-blue-900 mb-2">
                    💡 Cómo usar:
                </h4>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Escribe en cualquier campo para buscar opciones específicas</li>
                    <li>• Los campos se habilitan secuencialmente según tu selección</li>
                    <li>• Puedes limpiar cualquier selección con el botón "Limpiar selección"</li>
                    <li>• La búsqueda es en tiempo real y filtra las opciones automáticamente</li>
                </ul>
            </div>
        </div>
    );
};
