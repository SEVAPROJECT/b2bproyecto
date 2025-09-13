import React, { useState } from 'react';
import { providersAPI } from '../services/api';

const ProviderTest: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const testProviderAPI = async () => {
    setIsLoading(true);
    setMessage('');
    setError('');

    try {
      const accessToken = localStorage.getItem('access_token');
      console.log('🔍 Token encontrado:', accessToken ? 'Sí' : 'No');
      console.log('🔍 Token completo:', accessToken);
      
      if (!accessToken) {
        setError('No hay token de acceso. Debes iniciar sesión primero.');
        return;
      }
      
      // Verificar si el token parece válido (tiene el formato correcto)
      if (!accessToken.includes('.')) {
        setError('El token no tiene el formato correcto de JWT.');
        return;
      }

      // Crear un archivo de prueba
      const testFile = new File(['contenido de prueba'], 'test.txt', { type: 'text/plain' });

      const result = await providersAPI.submitProviderApplication({
        perfil_in: {
          nombre_fantasia: 'Empresa de Prueba',
          direccion: {
            departamento: 'Central',
            ciudad: 'Asunción',
            barrio: 'Centro',
            calle: 'Test',
            numero: '123',
            referencia: 'Prueba'
          }
        },
        documentos: [testFile],
        nombres_tip_documento: ['RUC'],
        comentario_solicitud: 'Prueba de conexión'
      }, accessToken);

      setMessage(`Éxito: ${result.message}`);
    } catch (err: any) {
      console.error('Error en prueba:', err);
      setError(err.detail || 'Error desconocido');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-4">Prueba de Conexión con API de Proveedores</h3>
      
      <button
        onClick={testProviderAPI}
        disabled={isLoading}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
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

export default ProviderTest;
