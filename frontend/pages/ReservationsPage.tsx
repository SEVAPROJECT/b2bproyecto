import React, { useState, useEffect } from 'react';
import { CalendarDaysIcon, ClockIcon, MapPinIcon, UserCircleIcon } from '../components/icons';

const ReservationsPage: React.FC = () => {
    const [reservations, setReservations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadReservations();
    }, []);

    const loadReservations = async () => {
        setLoading(true);
        // Simular carga de datos
        setTimeout(() => {
            setReservations([]);
            setLoading(false);
        }, 1000);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Cargando reservas...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">Mis Reservas</h1>
                    <p className="mt-2 text-gray-600">Gestiona tus reservas de servicios</p>
                </div>

                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                    <ul className="divide-y divide-gray-200">
                        {reservations.length > 0 ? (
                            reservations.map((reservation) => (
                                <li key={reservation.id}>
                                    <div className="px-4 py-4 sm:px-6">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0">
                                                    <CalendarDaysIcon className="h-8 w-8 text-blue-400" />
                                                </div>
                                                <div className="ml-4">
                                                    <div className="text-sm font-medium text-gray-900">
                                                        {reservation.service}
                                                    </div>
                                                    <div className="text-sm text-gray-500">
                                                        Proveedor: {reservation.provider}
                                                    </div>
                                                    <div className="text-sm text-gray-500">
                                                        Fecha: {reservation.date} | Hora: {reservation.time}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center space-x-2">
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                    reservation.status === 'confirmed'
                                                        ? 'bg-green-100 text-green-800'
                                                        : 'bg-yellow-100 text-yellow-800'
                                                }`}>
                                                    {reservation.status === 'confirmed' ? 'Confirmada' : 'Pendiente'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </li>
                            ))
                        ) : (
                            <li>
                                <div className="px-4 py-8 text-center">
                                    <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" />
                                    <h3 className="mt-2 text-sm font-medium text-gray-900">No hay reservas</h3>
                                    <p className="mt-1 text-sm text-gray-500">Aún no has realizado ninguna reserva.</p>
                                </div>
                            </li>
                        )}
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default ReservationsPage;
