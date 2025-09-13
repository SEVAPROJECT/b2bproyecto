import React from 'react';

interface AlertProps {
    children: React.ReactNode;
    variant?: 'error' | 'warning' | 'info';
    className?: string;
}

const Alert: React.FC<AlertProps> = ({ children, variant = 'info', className = '' }) => {
    const baseClasses = 'p-4 rounded-lg my-4 border text-sm font-medium';
    const variantClasses = {
        error: 'bg-red-50 border-red-200 text-red-800',
        warning: 'bg-amber-50 border-amber-200 text-amber-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800',
    };

    // Asegurar que children sea un string válido
    const displayContent = typeof children === 'string' ? children : 
                          typeof children === 'object' && children !== null ? 
                          JSON.stringify(children) : 'Error desconocido';

    return (
        <div className={`${baseClasses} ${variantClasses[variant]} ${className}`} role="alert">
            {displayContent}
        </div>
    );
};

export default Alert;
