import React, { useState } from 'react';
import { AddressSelector } from './AddressSelector';
import { Departamento, Ciudad, Barrio } from '../services/locations';

export const AddressTest: React.FC = () => {
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
    console.log('Dirección seleccionada:', address);
    setSelectedAddress(address);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          Prueba del Selector de Dirección
        </h1>
        
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Selector de Dirección
          </h2>
          
          <AddressSelector
            onAddressChange={handleAddressChange}
            className="mb-6"
          />
          
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Dirección Seleccionada:
            </h3>
            <div className="text-sm text-gray-700">
              <p><strong>Departamento:</strong> {selectedAddress.departamento?.nombre || 'No seleccionado'}</p>
              <p><strong>Ciudad:</strong> {selectedAddress.ciudad?.nombre || 'No seleccionada'}</p>
              <p><strong>Barrio:</strong> {selectedAddress.barrio?.nombre || 'No seleccionado'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
