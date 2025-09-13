import React, { useState } from 'react';
import { AddressSelector } from './AddressSelector';
import { Departamento, Ciudad, Barrio } from '../services/locations';

export const AddressTestComponent: React.FC = () => {
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
    console.log('✅ Dirección seleccionada:', address);
    setSelectedAddress(address);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          🧪 Prueba del Selector de Dirección
        </h1>
        
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Selector de Dirección Simplificado
          </h2>
          
          <p className="text-gray-600 mb-4">
            <strong>Instrucciones de prueba:</strong>
          </p>
          <ol className="list-decimal list-inside text-gray-600 mb-6 space-y-2">
            <li>Selecciona un departamento</li>
            <li>Verifica que el departamento se mantiene seleccionado</li>
            <li>Selecciona una ciudad</li>
            <li>Verifica que tanto departamento como ciudad se mantienen</li>
            <li>Selecciona un barrio</li>
            <li>Verifica que todas las selecciones se mantienen</li>
          </ol>
          
          <AddressSelector
            onAddressChange={handleAddressChange}
            className="mb-6"
          />
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="text-lg font-medium text-blue-900 mb-2">
              📍 Dirección Seleccionada:
            </h3>
            <div className="text-sm text-blue-800 space-y-1">
              <p><strong>Departamento:</strong> {selectedAddress.departamento?.nombre || '❌ No seleccionado'}</p>
              <p><strong>Ciudad:</strong> {selectedAddress.ciudad?.nombre || '❌ No seleccionada'}</p>
              <p><strong>Barrio:</strong> {selectedAddress.barrio?.nombre || '❌ No seleccionado'}</p>
            </div>
          </div>

          <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <h4 className="text-md font-medium text-yellow-900 mb-2">
              🔍 Estado de la Prueba:
            </h4>
            <div className="text-sm text-yellow-800">
              {selectedAddress.departamento && selectedAddress.ciudad && selectedAddress.barrio ? (
                <p className="text-green-600 font-semibold">✅ ¡Éxito! Todas las selecciones se mantienen correctamente.</p>
              ) : selectedAddress.departamento && selectedAddress.ciudad ? (
                <p className="text-blue-600">🔄 En progreso: Falta seleccionar barrio.</p>
              ) : selectedAddress.departamento ? (
                <p className="text-blue-600">🔄 En progreso: Falta seleccionar ciudad.</p>
              ) : (
                <p className="text-gray-600">⏳ Esperando selección de departamento.</p>
              )}
            </div>
          </div>

          <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <h4 className="text-md font-medium text-gray-900 mb-2">
              📊 Debug Info:
            </h4>
            <div className="text-xs text-gray-600 space-y-1">
              <p><strong>Departamento ID:</strong> {selectedAddress.departamento?.id || 'N/A'}</p>
              <p><strong>Ciudad ID:</strong> {selectedAddress.ciudad?.id || 'N/A'}</p>
              <p><strong>Barrio ID:</strong> {selectedAddress.barrio?.id || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
