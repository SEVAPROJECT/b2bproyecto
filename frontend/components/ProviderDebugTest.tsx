import React, { useState } from 'react';
import { providersAPI } from '../services/api';

const ProviderDebugTest: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [debugInfo, setDebugInfo] = useState<string[]>([]);

  const addDebugInfo = (info: string) => {
    setDebugInfo(prev => [...prev, `${new Date().toLocaleTimeString()}: ${info}`]);
  };

  const testProviderAPI = async () => {
    setIsLoading(true);
    setMessage('');
    setError('');
    setDebugInfo([]);

    try {
      addDebugInfo('🔍 Iniciando prueba de API de proveedores...');
      
      const accessToken = localStorage.getItem('access_token');
      addDebugInfo(`🔑 Token encontrado: ${accessToken ? 'Sí' : 'No'}`);
      
      if (!accessToken) {
        setError('❌ No hay token de acceso. Debes iniciar sesión primero.');
        return;
      }

      // Verificar si el token parece válido
      if (!accessToken.includes('.')) {
        setError('❌ El token no tiene el formato correcto de JWT.');
        return;
      }

      addDebugInfo('✅ Token parece válido');

      // Crear un archivo de prueba
      const testFile = new File(['contenido de prueba'], 'test.txt', { type: 'text/plain' });
      addDebugInfo('📄 Archivo de prueba creado');

      const testData = {
        perfil_in: {
          nombre_fantasia: 'Empresa de Prueba Debug',
          direccion: {
            departamento: 'Central',
            ciudad: 'Asunción',
            barrio: 'Centro',
            calle: 'Test Debug',
            numero: '123',
            referencia: 'Prueba de debug'
          }
        },
        documentos: [testFile],
        nombres_tip_documento: ['RUC'],
        comentario_solicitud: 'Prueba de debug de conectividad'
      };

      addDebugInfo('📤 Preparando datos de prueba...');
      addDebugInfo(`📋 Datos: ${JSON.stringify(testData, null, 2)}`);

      addDebugInfo('🚀 Llamando a providersAPI.submitProviderApplication...');
      
      const result = await providersAPI.submitProviderApplication(testData, accessToken);
      
      addDebugInfo('✅ Llamada exitosa');
      setMessage(`✅ Éxito: ${result.message}`);
      
    } catch (err: any) {
      addDebugInfo(`❌ Error capturado: ${err.message || err.detail || 'Error desconocido'}`);
      console.error('Error en prueba:', err);
      setError(err.detail || err.message || 'Error desconocido');
    } finally {
      setIsLoading(false);
    }
  };

  const clearDebug = () => {
    setDebugInfo([]);
    setMessage('');
    setError('');
  };

  return (
    <div className="p-4 border rounded-lg bg-blue-50">
      <h3 className="text-lg font-semibold mb-4">🐛 Debug de API de Proveedores</h3>

      <div className="flex gap-2 mb-4">
        <button
          onClick={testProviderAPI}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {isLoading ? 'Probando...' : 'Probar API'}
        </button>
        
        <button
          onClick={clearDebug}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          Limpiar Debug
        </button>
      </div>

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

      {debugInfo.length > 0 && (
        <div className="mt-4">
          <h4 className="font-semibold mb-2">📋 Información de Debug:</h4>
          <div className="bg-gray-100 p-3 rounded max-h-60 overflow-y-auto">
            {debugInfo.map((info) => (
              <div key={info} className="text-sm font-mono mb-1">
                {info}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProviderDebugTest;
