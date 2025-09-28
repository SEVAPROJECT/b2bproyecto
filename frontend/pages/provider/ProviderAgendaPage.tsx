import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import HorarioTrabajoManager from '../../components/horario/HorarioTrabajoManager';
import { CalendarDaysIcon } from '../../components/icons';

const ProviderAgendaPage: React.FC = () => {
    const { user } = useAuth();

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                                <CalendarDaysIcon className="h-8 w-8 text-primary-600" />
                                Mi Agenda
                            </h1>
                            <p className="mt-2 text-gray-600">
                                Configura tu horario de trabajo unificado para todos tus servicios
                            </p>
                        </div>
                    </div>
                </div>

                {/* Nuevo Sistema de Horario de Trabajo */}
                <HorarioTrabajoManager />
            </div>
        </div>
    );
};

export default ProviderAgendaPage;
