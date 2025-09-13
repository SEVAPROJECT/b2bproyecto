import React, { useState } from 'react';

const ConnectionTest: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const testConnection = async () => {
    setIsLoading(true);
    setMessage('');
    setError('');

    try {
      // Detectar la URL base automáticamente
      const getApiBaseUrl = (): string => {
        if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
          const backendUrl = (window as any).__ENV__?.VITE_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}:8000`;
          return `${backendUrl}/api/v1`;
        }
        return 'http://localhost:8000/api/v1';
      };

      const API_BASE_URL = getApiBaseUrl();
      console.log('🔗 Probando conexión a:', API_BASE_URL);

      // Probar endpoint simple
      const response = await fetch(`${API_BASE_URL}/providers/test`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 Respuesta de prueba:', response.status, response.statusText);

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setMessage(`✅ Conexión exitosa: ${result.message}`);
    } catch (err: any) {
      console.error('❌ Error de conexión:', err);
      setError(`❌ Error de conexión: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 border rounded-lg bg-yellow-50">
      <h3 className="text-lg font-semibold mb-4">🔍 Prueba de Conexión con Backend</h3>
      
      <button
        onClick={testConnection}
        disabled={isLoading}
        className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
      >
        {isLoading ? 'Probando...' : 'Probar Conexión'}
      </button>

      {message && (
        <div className="mt-4 p-3 bg-green-100 text-green-800 rounded">
          {message}
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-800 rounded">
          {error}
        </div>
      )}
    </div>
  );
};

export default ConnectionTest;
