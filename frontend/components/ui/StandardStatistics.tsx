import React from 'react';
import { ClockIcon, CheckCircleIcon, XMarkIcon } from '../icons';

export interface Statistics {
    total: number;
    filtered: number;
    pending: number;
    approved: number;
    rejected: number;
}

interface StandardStatisticsProps {
    statistics: Statistics;
    showFiltered?: boolean;
    className?: string;
}

const StandardStatistics: React.FC<StandardStatisticsProps> = ({
    statistics,
    showFiltered = true,
    className = ''
}) => {
    return (
        <>
            {/* Estadísticas principales */}
            <div className={`grid grid-cols-1 md:grid-cols-4 gap-6 mb-8 ${className}`}>
                <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                    <div className="flex items-center">
                        <div className="p-2 bg-blue-100 rounded-lg">
                            <ClockIcon className="w-6 h-6 text-blue-600" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-500">Total</p>
                            <p className="text-2xl font-bold text-gray-900">{statistics.total}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                    <div className="flex items-center">
                        <div className="p-2 bg-yellow-100 rounded-lg">
                            <ClockIcon className="w-6 h-6 text-yellow-600" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-500">Pendientes</p>
                            <p className="text-2xl font-bold text-gray-900">{statistics.pending}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                    <div className="flex items-center">
                        <div className="p-2 bg-green-100 rounded-lg">
                            <CheckCircleIcon className="w-6 h-6 text-green-600" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-500">Aprobadas</p>
                            <p className="text-2xl font-bold text-gray-900">{statistics.approved}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                    <div className="flex items-center">
                        <div className="p-2 bg-red-100 rounded-lg">
                            <XMarkIcon className="w-6 h-6 text-red-600" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-500">Rechazadas</p>
                            <p className="text-2xl font-bold text-gray-900">{statistics.rejected}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Estadísticas de filtros */}
            {showFiltered && (
                <div className="bg-blue-50 p-4 rounded-lg mb-6">
                    <h3 className="text-lg font-medium text-blue-900 mb-2">📈 Estadísticas</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                            <span className="font-medium text-blue-800">Total:</span>
                            <span className="ml-2 text-blue-700">{statistics.total}</span>
                        </div>
                        <div>
                            <span className="font-medium text-blue-800">Filtrados:</span>
                            <span className="ml-2 text-blue-700">{statistics.filtered}</span>
                        </div>
                        <div>
                            <span className="font-medium text-blue-800">Pendientes:</span>
                            <span className="ml-2 text-blue-700">{statistics.pending}</span>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default StandardStatistics;
