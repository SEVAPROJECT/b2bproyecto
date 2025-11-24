import React, { useState } from 'react';

interface CalificacionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CalificacionData) => void;
  tipo: 'cliente' | 'proveedor';
  reservaId: number;
  loading?: boolean;
}

interface CalificacionData {
  puntaje: number;
  comentario: string;
  satisfaccion_nps?: number;
}

const CalificacionModal: React.FC<CalificacionModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  tipo,
  reservaId,
  loading = false
}) => {
  const [puntaje, setPuntaje] = useState(0);
  const [comentario, setComentario] = useState('');
  const [satisfaccionNps, setSatisfaccionNps] = useState(0);
  const [errors, setErrors] = useState<{[key: string]: string}>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validaciones
    const newErrors: {[key: string]: string} = {};
    
    if (puntaje === 0) {
      newErrors.puntaje = 'Seleccioná un puntaje';
    }
    
    if (!comentario.trim()) {
      newErrors.comentario = 'El comentario es obligatorio';
    }
    
    if (tipo === 'cliente' && satisfaccionNps === 0) {
      newErrors.satisfaccion_nps = 'Seleccioná una puntuación NPS';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    // Enviar datos
    const data: CalificacionData = {
      puntaje,
      comentario: comentario.trim(),
      satisfaccion_nps: tipo === 'cliente' ? satisfaccionNps : undefined
    };
    
    onSubmit(data);
  };

  const handleClose = () => {
    setPuntaje(0);
    setComentario('');
    setSatisfaccionNps(0);
    setErrors({});
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {tipo === 'cliente' 
              ? 'Calificá tu experiencia con este servicio'
              : 'Calificá al cliente de esta reserva'
            }
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-2xl"
            disabled={loading}
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Puntaje con estrellas */}
          <div>
            <label htmlFor="puntaje-estrellas" className="block text-sm font-medium text-gray-700 mb-2">
              ⭐ Puntaje (1-5 estrellas)
            </label>
            <div id="puntaje-estrellas" className="flex space-x-1" role="group" aria-label="Seleccionar puntaje de 1 a 5 estrellas">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setPuntaje(star)}
                  className="focus:outline-none"
                  disabled={loading}
                  aria-label={`${star} estrella${star > 1 ? 's' : ''}`}
                >
                  {star <= puntaje ? (
                    <span className="text-3xl text-yellow-400">⭐</span>
                  ) : (
                    <span className="text-3xl text-gray-300 hover:text-yellow-400">☆</span>
                  )}
                </button>
              ))}
            </div>
            {errors.puntaje && (
              <p className="mt-1 text-sm text-red-600">{errors.puntaje}</p>
            )}
          </div>

          {/* Comentario */}
          <div>
            <label htmlFor="comentario-calificacion" className="block text-sm font-medium text-gray-700 mb-2">
              💬 Comentario
            </label>
            <textarea
              id="comentario-calificacion"
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              rows={3}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.comentario ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Contanos tu experiencia..."
              disabled={loading}
            />
            {errors.comentario && (
              <p className="mt-1 text-sm text-red-600">{errors.comentario}</p>
            )}
          </div>

          {/* NPS solo para cliente */}
          {tipo === 'cliente' && (
            <div>
              <label htmlFor="nps-calificacion" className="block text-sm font-medium text-gray-700 mb-2">
                📊 NPS - ¿Qué tan probable es que recomiendes este servicio a otras personas? (1-10)
              </label>
              <div id="nps-calificacion" className="flex space-x-2" role="group" aria-label="Seleccionar puntuación NPS de 1 a 10">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setSatisfaccionNps(num)}
                    className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                      num <= satisfaccionNps
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-blue-100'
                    }`}
                    disabled={loading}
                    aria-label={`Puntuación NPS ${num}`}
                  >
                    {num}
                  </button>
                ))}
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Muy improbable</span>
                <span>Muy probable</span>
              </div>
              {errors.satisfaccion_nps && (
                <p className="mt-1 text-sm text-red-600">{errors.satisfaccion_nps}</p>
              )}
            </div>
          )}

          {/* Botones */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              disabled={loading}
            >
              {loading ? 'Enviando...' : 'Enviar Calificación'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CalificacionModal;
