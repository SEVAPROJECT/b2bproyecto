import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { buildApiUrl, getJsonHeaders } from '../config/api';

// Tipos
export interface Calificacion {
    puntaje: number;
    comentario: string;
    nps?: number;
}

export interface Reserva {
    id_reserva: number;
    id_servicio: number;
    id_usuario: string;
    descripcion: string;
    observacion: string | null;
    fecha: string;
    hora_inicio: string | null;
    hora_fin: string | null;
    estado: string;
    created_at: string;
    updated_at: string;
    nombre_servicio: string;
    descripcion_servicio: string;
    precio_servicio: number;
    imagen_servicio: string | null;
    nombre_empresa: string;
    razon_social: string;
    id_perfil: number;
    nombre_contacto: string;
    email_contacto: string | null;
    telefono_contacto: string | null;
    nombre_categoria: string | null;
    simbolo_moneda?: string | null;
    codigo_iso_moneda?: string | null;
    ya_calificado_por_cliente?: boolean;
    ya_calificado_por_proveedor?: boolean;
    calificacion_cliente?: Calificacion | null;
    calificacion_proveedor?: Calificacion | null;
}

export interface PaginationInfo {
    total: number;
    page: number;
    limit: number;
    offset: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
}

interface ReservasResponse {
    reservas: Reserva[];
    pagination: PaginationInfo;
}

export type TabType = 'mis-reservas' | 'reservas-proveedor' | 'agenda';

export const useReservations = () => {
    const { user } = useAuth();
    const [reservas, setReservas] = useState<Reserva[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [pagination, setPagination] = useState<PaginationInfo>({
        total: 0,
        page: 1,
        limit: 20,
        offset: 0,
        total_pages: 0,
        has_next: false,
        has_prev: false
    });

    // Estados de filtros
    const [searchFilter, setSearchFilter] = useState('');
    const [nombreServicio, setNombreServicio] = useState('');
    const [nombreEmpresa, setNombreEmpresa] = useState('');
    const [fechaDesde, setFechaDesde] = useState('');
    const [fechaHasta, setFechaHasta] = useState('');
    const [estadoFilter, setEstadoFilter] = useState('all');
    const [nombreContacto, setNombreContacto] = useState('');
    const [showFilters, setShowFilters] = useState(false);

    // Estados para las pestañas
    const [activeTab, setActiveTab] = useState<TabType>('mis-reservas');

    // Estados para modales y acciones
    const [showModal, setShowModal] = useState(false);
    const [modalData, setModalData] = useState<{reservaId: number, accion: string, observacion: string} | null>(null);
    const [accionLoading, setAccionLoading] = useState<number | null>(null);
    const [mensajeExito, setMensajeExito] = useState<string | null>(null);
    const [sincronizando, setSincronizando] = useState(false);
    const [showCalificacionModal, setShowCalificacionModal] = useState(false);
    const [calificacionReservaId, setCalificacionReservaId] = useState<number | null>(null);
    const [calificacionLoading, setCalificacionLoading] = useState(false);

    // Configurar pestaña inicial según el rol del usuario
    useEffect(() => {
        if (!user?.role) return; // Esperar a que el usuario esté cargado
        
        // Solo cambiar el tab si es necesario y no está ya en el correcto
        if (user.role === 'provider' && activeTab === 'mis-reservas') {
            console.log('🔍 [useReservations] Cambiando tab de mis-reservas a reservas-proveedor para proveedor');
            setActiveTab('reservas-proveedor');
            // Limpiar reservas cuando cambiamos el tab para evitar mostrar datos incorrectos
            setReservas([]);
        } else if (user.role !== 'provider' && activeTab !== 'mis-reservas') {
            console.log('🔍 [useReservations] Cambiando tab a mis-reservas para cliente');
            setActiveTab('mis-reservas');
            // Limpiar reservas cuando cambiamos el tab para evitar mostrar datos incorrectos
            setReservas([]);
        }
    }, [user?.role, activeTab]); // Incluir activeTab para detectar cuando cambia

    // Cargar reservas
    const loadReservas = useCallback(async (page: number = 1) => {
        if (!user?.accessToken) return;

        try {
            setLoading(true);
            setError(null);
            // Limpiar reservas antes de cargar nuevas para evitar mostrar datos mezclados
            setReservas([]);

            // Validar fechas antes de enviar
            if (fechaDesde && fechaHasta && fechaDesde > fechaHasta) {
                setError('La fecha "hasta" debe ser mayor o igual a la fecha "desde"');
                setLoading(false);
                return;
            }

            // Construir query params
            const params = new URLSearchParams();
            const limit = 20; // Usar valor fijo en lugar de pagination.limit
            params.append('limit', limit.toString());
            params.append('offset', ((page - 1) * limit).toString());

            if (searchFilter.trim()) params.append('search', searchFilter.trim());
            if (nombreServicio.trim()) params.append('nombre_servicio', nombreServicio.trim());
            if (nombreEmpresa.trim()) params.append('nombre_empresa', nombreEmpresa.trim());
            if (fechaDesde) params.append('fecha_desde', fechaDesde);
            if (fechaHasta) params.append('fecha_hasta', fechaHasta);
            if (estadoFilter !== 'all') {
                params.append('estado', estadoFilter);
            }
            if (nombreContacto.trim()) params.append('nombre_contacto', nombreContacto.trim());

            // Validar que el tab sea correcto para el rol del usuario
            if (user.role === 'provider' && activeTab === 'mis-reservas') {
                console.log('🔍 [useReservations] ERROR: Proveedor intentando acceder a mis-reservas, cancelando carga');
                setReservas([]);
                setLoading(false);
                return;
            }
            
            if (user.role !== 'provider' && activeTab === 'reservas-proveedor') {
                console.log('🔍 [useReservations] ERROR: Cliente intentando acceder a reservas-proveedor, cancelando carga');
                setReservas([]);
                setLoading(false);
                return;
            }
            
            // Determinar qué endpoint usar según la pestaña activa
            let endpoint = '';
            if (activeTab === 'mis-reservas') {
                endpoint = '/reservas/mis-reservas';
            } else if (activeTab === 'reservas-proveedor') {
                endpoint = '/reservas/reservas-proveedor';
            } else {
                // Para agenda, no cargar reservas
                setReservas([]);
                setLoading(false);
                return;
            }

            const urlConParams = `${buildApiUrl(endpoint)}?${params.toString()}`;
            
            console.log(`🔍 [useReservations] Cargando reservas desde: ${endpoint}`);
            console.log(`🔍 [useReservations] ActiveTab: ${activeTab}, User Role: ${user?.role}`);
            console.log(`🔍 [useReservations] URL: ${urlConParams}`);

            const response = await fetch(urlConParams, {
                headers: getJsonHeaders(),
            });

            if (!response.ok) {
                throw new Error('Error al cargar reservas');
            }

            const data = await response.json();

            // Mapeo simplificado para el endpoint de prueba
            const reservasData = data.reservas || data || [];
            
            console.log(`🔍 [useReservations] Datos recibidos del backend:`, {
                endpoint,
                activeTab,
                totalReservas: reservasData.length,
                reservas: reservasData.map((r: any) => ({ id: r.id_reserva, servicio: r.nombre_servicio, empresa: r.nombre_empresa }))
            });
            
            const reservasMapeadas = reservasData.map((reserva: any) => ({
                id_reserva: reserva.id_reserva,
                nombre_servicio: reserva.nombre_servicio || reserva.servicio?.nombre || 'Servicio sin nombre',
                nombre_empresa: reserva.nombre_empresa || reserva.servicio?.empresa || 'Empresa sin nombre',
                fecha: reserva.fecha,
                estado: reserva.estado,
                descripcion: reserva.descripcion,
                observacion: reserva.observacion || '',
                hora_inicio: reserva.hora_inicio,
                hora_fin: reserva.hora_fin,
                nombre_contacto: reserva.nombre_contacto || 'No especificado',
                email_contacto: reserva.email_contacto || null,
                precio_servicio: reserva.precio_servicio || reserva.servicio?.precio || 0,
                imagen_servicio: reserva.imagen_servicio || reserva.servicio?.imagen,
                nombre_categoria: reserva.nombre_categoria || reserva.servicio?.categoria || 'Sin categoría',
                simbolo_moneda: reserva.simbolo_moneda || '₲',
                codigo_iso_moneda: reserva.codigo_iso_moneda || 'GS',
                ya_calificado_por_cliente: reserva.ya_calificado_por_cliente || false,
                ya_calificado_por_proveedor: reserva.ya_calificado_por_proveedor || false,
                calificacion_cliente: reserva.calificacion_cliente,
                calificacion_proveedor: reserva.calificacion_proveedor,
                id_servicio: reserva.id_servicio,
                id_usuario: reserva.id_usuario,
                descripcion_servicio: reserva.descripcion_servicio || '',
                razon_social: reserva.razon_social || '',
                id_perfil: reserva.id_perfil || 0,
                telefono_contacto: reserva.telefono_contacto || null,
                created_at: reserva.created_at || '',
                updated_at: reserva.updated_at || ''
            }));

            console.log(`🔍 [useReservations] Reservas mapeadas: ${reservasMapeadas.length}`);
            setReservas(reservasMapeadas);
            const limitValue = data.pagination?.limit || 20;
            setPagination({
                total: data.pagination?.total || data.total || reservasData.length,
                page: data.pagination?.page || page,
                limit: limitValue,
                offset: data.pagination?.offset || ((page - 1) * limitValue),
                total_pages: data.pagination?.total_pages || Math.ceil((data.pagination?.total || data.total || reservasData.length) / limitValue),
                has_next: data.pagination?.has_next || false,
                has_prev: data.pagination?.has_prev || false
            });
        } catch (error) {
            console.error('Error al cargar reservas:', error);
            setError('Error al cargar las reservas. Por favor, inténtalo de nuevo.');
        } finally {
            setLoading(false);
        }
    }, [user, searchFilter, nombreServicio, nombreEmpresa, fechaDesde, fechaHasta, estadoFilter, nombreContacto, activeTab]);

    // Cargar al montar y cuando cambien filtros o pestaña
    useEffect(() => {
        // Solo cargar si el usuario está autenticado y el tab es válido para su rol
        if (!user?.accessToken) return;
        
        // Para proveedores, solo cargar si el tab es 'reservas-proveedor' o 'agenda'
        if (user.role === 'provider' && activeTab === 'mis-reservas') {
            console.log('🔍 [useReservations] Saltando carga: proveedor no debe ver mis-reservas');
            return;
        }
        
        // Para clientes, solo cargar si el tab es 'mis-reservas'
        if (user.role !== 'provider' && activeTab !== 'mis-reservas') {
            console.log('🔍 [useReservations] Saltando carga: cliente solo debe ver mis-reservas');
            return;
        }
        
        console.log(`🔍 [useReservations] Ejecutando loadReservas para tab: ${activeTab}, rol: ${user.role}`);
        loadReservas(1);
    }, [searchFilter, nombreServicio, nombreEmpresa, fechaDesde, fechaHasta, estadoFilter, nombreContacto, activeTab, loadReservas, user?.accessToken, user?.role]);

    // Limpiar filtros
    const handleClearFilters = useCallback(() => {
        setSearchFilter('');
        setNombreServicio('');
        setNombreEmpresa('');
        setFechaDesde('');
        setFechaHasta('');
        setEstadoFilter('all');
        setNombreContacto('');
    }, []);

    // Funciones para cambio de estado de reservas
    const actualizarEstadoReserva = useCallback(async (reservaId: number, nuevoEstado: string, observacion?: string) => {
        try {
            if (!user) return;

            setAccionLoading(reservaId);
            setError(null);

            // Usar endpoint específico para cancelación
            const endpoint = nuevoEstado === 'cancelada' ? `/reservas/${reservaId}/cancelar` : `/reservas/${reservaId}/estado`;
            const body = nuevoEstado === 'cancelada' 
                ? { motivo: observacion || '' }
                : { nuevo_estado: nuevoEstado, observacion: observacion || '' };

            const response = await fetch(buildApiUrl(endpoint), {
                method: 'PUT',
                headers: getJsonHeaders(),
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al actualizar estado');
            }

            const result = await response.json();
            console.log('Estado actualizado:', result);

            // Mensaje específico para cancelación
            if (nuevoEstado === 'cancelada') {
                setMensajeExito('✅ Reserva cancelada - Los cambios se sincronizarán automáticamente');
            } else {
                setMensajeExito(`Reserva ${nuevoEstado} exitosamente`);
            }
            setTimeout(() => setMensajeExito(null), 5000);

            // Refetch inmediato para sincronización
            setSincronizando(true);
            await loadReservas(1);
            setSincronizando(false);
            setShowModal(false);
            setModalData(null);
        } catch (err) {
            setError('Error al actualizar el estado de la reserva');
            console.error('Error:', err);
        } finally {
            setAccionLoading(null);
        }
    }, [user, loadReservas]);

    const handleAccionReserva = useCallback((reservaId: number, accion: string) => {
        if (accionLoading === reservaId) {
            return;
        }
        
        setModalData({
            reservaId,
            accion,
            observacion: ''
        });
        setShowModal(true);
    }, [accionLoading]);

    const handleConfirmarReserva = useCallback(async (reservaId: number) => {
        if (accionLoading === reservaId) {
            return;
        }
        
        try {
            setAccionLoading(reservaId);
            setError(null);

            const response = await fetch(buildApiUrl(`/reservas/${reservaId}/confirmar`), {
                method: 'PUT',
                headers: getJsonHeaders()
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al confirmar la reserva');
            }

            const result = await response.json();
            console.log('Reserva confirmada:', result);

            setMensajeExito('✅ Reserva confirmada');
            setTimeout(() => setMensajeExito(null), 3000);

            await loadReservas(1);
        } catch (err) {
            setError('Error al confirmar la reserva');
            console.error('Error:', err);
        } finally {
            setAccionLoading(null);
        }
    }, [accionLoading, loadReservas]);

    // Funciones para calificación
    const handleCalificar = useCallback((reservaId: number) => {
        setCalificacionReservaId(reservaId);
        setShowCalificacionModal(true);
    }, []);

    const handleEnviarCalificacion = useCallback(async (data: {puntaje: number, comentario: string, satisfaccion_nps?: number}) => {
        if (!calificacionReservaId) return;

        try {
            setCalificacionLoading(true);
            setError(null);

            // Determinar el endpoint según la pestaña activa
            const endpoint = activeTab === 'reservas-proveedor' 
                ? `/calificacion/proveedor/${calificacionReservaId}`
                : `/calificacion/cliente/${calificacionReservaId}`;

            const response = await fetch(buildApiUrl(endpoint), {
                method: 'POST',
                headers: getJsonHeaders(),
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al enviar calificación');
            }

            setMensajeExito('✅ Calificación registrada con éxito');
            setTimeout(() => setMensajeExito(null), 3000);

            // Recargar datos para actualizar UI
            await loadReservas(1);
            setShowCalificacionModal(false);
            setCalificacionReservaId(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Error al enviar calificación');
            console.error('Error:', err);
        } finally {
            setCalificacionLoading(false);
        }
    }, [calificacionReservaId, activeTab, loadReservas]);

    const confirmarAccion = useCallback(() => {
        if (!modalData) return;
        
        if (modalData.accion === 'cancelada' && !modalData.observacion.trim()) {
            setError('Debés ingresar un motivo para cancelar la reserva');
            return;
        }
        
        if (modalData.accion === 'completada' && !modalData.observacion.trim()) {
            setError('Es recomendable agregar una observación al marcar como completada');
            return;
        }
        
        actualizarEstadoReserva(modalData.reservaId, modalData.accion, modalData.observacion);
    }, [modalData, actualizarEstadoReserva]);

    // Contar filtros activos
    const activeFiltersCount = useMemo(() => {
        let count = 0;
        if (searchFilter.trim()) count++;
        if (nombreServicio.trim()) count++;
        if (nombreEmpresa.trim()) count++;
        if (fechaDesde) count++;
        if (fechaHasta) count++;
        if (estadoFilter !== 'all') count++;
        if (nombreContacto.trim()) count++;
        return count;
    }, [searchFilter, nombreServicio, nombreEmpresa, fechaDesde, fechaHasta, estadoFilter, nombreContacto]);

    return {
        // Estados
        reservas,
        loading,
        error,
        pagination,
        searchFilter,
        setSearchFilter,
        nombreServicio,
        setNombreServicio,
        nombreEmpresa,
        setNombreEmpresa,
        fechaDesde,
        setFechaDesde,
        fechaHasta,
        setFechaHasta,
        estadoFilter,
        setEstadoFilter,
        nombreContacto,
        setNombreContacto,
        showFilters,
        setShowFilters,
        activeTab,
        setActiveTab,
        showModal,
        setShowModal,
        modalData,
        setModalData,
        accionLoading,
        mensajeExito,
        sincronizando,
        showCalificacionModal,
        setShowCalificacionModal,
        calificacionReservaId,
        setCalificacionReservaId,
        calificacionLoading,
        activeFiltersCount,
        // Funciones
        loadReservas,
        handleClearFilters,
        actualizarEstadoReserva,
        handleAccionReserva,
        handleConfirmarReserva,
        handleCalificar,
        handleEnviarCalificacion,
        confirmarAccion,
        setError
    };
};

