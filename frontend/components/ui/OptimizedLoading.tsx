import React from 'react';

interface OptimizedLoadingProps {
    message?: string;
    showProgress?: boolean;
    progress?: number;
}

const OptimizedLoading: React.FC<OptimizedLoadingProps> = ({ 
    message = 'Cargando...', 
    showProgress = false, 
    progress = 0 
}) => {
    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
                {/* Spinner estandarizado - mismo formato que categorías */}
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                
                {/* Mensaje principal estandarizado */}
                <p className="mt-4 text-gray-600">{message}</p>
                
                {/* Barra de progreso opcional */}
                {showProgress && (
                    <div className="mt-4 w-64 mx-auto">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                                className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                                style={{ width: `${progress}%` }}
                            ></div>
                        </div>
                        <p className="mt-2 text-sm text-gray-500">{progress}% completado</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default OptimizedLoading;