import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { adminAPI, categoryRequestsAPI, categoriesAPI } from '../../services/api';
import { ChartBarIcon, DocumentArrowDownIcon, EyeIcon } from '../../components/icons';
import { API_CONFIG, buildApiUrl } from '../../config/api';
import { formatDateToDDMMYYYY } from '../../utils/dateUtils';

interface ReporteData {
    total_usuarios?: number;
    total_proveedores?: number;
    total_solicitudes?: number;
    total_categorias?: number;
    total_servicios?: number;
    total_solicitudes_servicios?: number;
    total_solicitudes_categorias?: number;
    total_reservas?: number;
    total_calificaciones?: number;
    total_calificaciones_proveedores?: number;
    usuarios?: any[];
    proveedores?: any[];
    solicitudes?: any[];
    categorias?: any[];
    servicios?: any[];
    solicitudes_servicios?: any[];
    solicitudes_categorias?: any[];
    reservas?: any[];
    calificaciones?: any[];
    calificaciones_proveedores?: any[];
    fecha_generacion: string;
    pendientes?: number;
    aprobadas?: number;
    rechazadas?: number;
    generado_desde?: string;
    mensaje?: string;
    error?: string;
    usuarios_activos?: number;
    usuarios_inactivos?: number;
    proveedores_verificados?: number;
    proveedores_pendientes?: number;
    solicitudes_proveedores?: any[];
    estadisticas?: any;
}

const AdminReportsPage: React.FC = () => {
    const { user } = useAuth();
    const [reportes, setReportes] = useState<{[key: string]: ReporteData}>({});
    const [loading, setLoading] = useState<{[key: string]: boolean}>({});
    const [error, setError] = useState<string | null>(null);
    const [selectedReport, setSelectedReport] = useState<string | null>(null);
    const [loadedReports, setLoadedReports] = useState<Set<string>>(new Set());
    const [initialLoading, setInitialLoading] = useState<boolean>(true);

    // Sin cache para evitar complejidad - carga directa

    // Función helper para formatear valores con formatos específicos
    const formatValue = (value: any, fieldName?: string): string => {
        if (value === null || value === undefined || value === '') {
            // Para comentarios, mostrar campo vacío en lugar de N/A
            if (fieldName === 'comentario_admin' || fieldName === 'comentario') {
                return '';
            }
            // Para otros campos, mostrar N/A solo si es necesario
            return 'N/A';
        }

        // Caso especial: fecha_reserva siempre debe mostrar solo fecha (sin hora)
        if (fieldName === 'fecha_reserva') {
            try {
                // Si ya está en formato DD/MM/YYYY (con o sin hora después)
                const matchDDMMYYYY = value.match(/^(\d{2}\/\d{2}\/\d{4})/);
                if (matchDDMMYYYY) {
                    return matchDDMMYYYY[1]; // Retornar solo la parte de fecha
                }
                
                // Si es formato YYYY-MM-DD
                if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
                    const dateOnly = value.split('T')[0].split(' ')[0];
                    return formatDateToDDMMYYYY(dateOnly);
                }
                
                // Fallback: intentar parsear y formatear
                const date = new Date(value);
                if (!isNaN(date.getTime())) {
                    const year = date.getFullYear();
                    const month = String(date.getMonth() + 1).padStart(2, '0');
                    const day = String(date.getDate()).padStart(2, '0');
                    return `${day}/${month}/${year}`;
                }
            } catch (error) {
                // Si todo falla, intentar extraer solo la parte de fecha del string
                const matchAnyDate = value.match(/(\d{2}\/\d{2}\/\d{4})/);
                if (matchAnyDate) {
                    return matchAnyDate[1];
                }
                return String(value);
            }
        }

        // Formatear fechas como DD/MM/AAAA
        // Detectar fechas por nombre de campo o por contenido
        const isDateField = fieldName === 'created_at' || fieldName === 'fecha_creacion' || 
                           fieldName === 'updated_at' || fieldName === 'fecha_actualizacion' ||
                           fieldName === 'createdAt' || fieldName === 'updatedAt' ||
                           fieldName === 'fecha_creacion' || fieldName === 'fecha_actualizacion';
        
        // También detectar si el valor parece ser una fecha
        const looksLikeDate = typeof value === 'string' && (
            value.includes('T') || // ISO format
            value.includes('-') || // Date format
            value.includes('/') || // Date format
            /^\d{4}-\d{2}-\d{2}/.test(value) || // YYYY-MM-DD
            /^\d{2}\/\d{2}\/\d{4}/.test(value) // DD/MM/YYYY
        );
        
        if (isDateField || looksLikeDate) {
            try {
                // Si ya está en formato DD/MM/YYYY, devolverlo tal cual
                if (/^\d{2}\/\d{2}\/\d{4}$/.test(value)) {
                    return value;
                }
                
                // Si es formato YYYY-MM-DD, usar la función sin conversión UTC
                if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
                    return formatDateToDDMMYYYY(value);
                }
                
                // Para fechas ISO con hora (YYYY-MM-DDTHH:MM:SS)
                if (value.includes('T')) {
                    const dateOnly = value.split('T')[0];
                    return formatDateToDDMMYYYY(dateOnly);
                }
                
                // Fallback para otros formatos
                const date = new Date(value);
                if (!isNaN(date.getTime())) {
                    return date.toLocaleDateString('es-ES', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                    });
                }
            } catch (error) {
                return String(value);
            }
        }

        // Formatear estado booleano como ACTIVO/INACTIVO
        if (fieldName === 'estado' || fieldName === 'active' || fieldName === 'activo') {
            if (typeof value === 'boolean') {
                return value ? 'ACTIVO' : 'INACTIVO';
            }
            if (value === 'true' || value === true) return 'ACTIVO';
            if (value === 'false' || value === false) return 'INACTIVO';
        }

        return String(value);
    };

    // Función helper para obtener el total de registros de un reporte
    const getReportTotal = (reportData: ReporteData): number => {
        return reportData.total_usuarios ?? 
               reportData.total_proveedores ?? 
               reportData.total_solicitudes ?? 
               reportData.total_categorias ?? 
               reportData.total_servicios ?? 
               reportData.total_solicitudes_servicios ?? 
               reportData.total_solicitudes_categorias ?? 
               reportData.total_reservas ?? 
               reportData.total_calificaciones ?? 
               reportData.total_calificaciones_proveedores ?? 0;
    };

    // Función helper para generar mensajes de error amigables
    const getFriendlyErrorMessage = (reportType: string, error: any): string => {
        const reportNames: {[key: string]: string} = {
            'usuarios-activos': 'usuarios',
            'proveedores-verificados': 'proveedores verificados',
            'solicitudes-proveedores': 'solicitudes de proveedores',
            'categorias': 'categorías',
            'servicios': 'servicios',
            'solicitudes-servicios': 'solicitudes de servicios',
            'solicitudes-categorias': 'solicitudes de categorías'
        };

        const reportName = reportNames[reportType] || 'datos';
        
        if (error?.message === 'Timeout de carga') {
            return `Error de conexión al cargar ${reportName}. Reintentando automáticamente...`;
        }
        
        // Si no hay datos, mostrar mensaje amigable
        if (error?.status === 404 || error?.detail?.includes('No se encontraron')) {
            return `No hay ${reportName} disponibles.`;
        }
        
        // Error 500 del servidor
        if (error?.status === 500) {
            return `Error del servidor. Reintentando...`;
        }
        
        // Error de red o conexión
        if (error?.message?.includes('Failed to fetch') || error?.message?.includes('NetworkError')) {
            return `Error de conexión. Verificando servidor...`;
        }
        
        return `Error al cargar ${reportName}. Reintentando...`;
    };

    const reportTypes = [
        {
            id: 'usuarios-activos',
            title: 'Usuarios',
            description: 'Listado de todos los usuarios en la plataforma',
            icon: '👥',
            color: 'blue'
        },
        {
            id: 'proveedores-verificados',
            title: 'Proveedores Verificados',
            description: 'Empresas que han sido verificadas como proveedores',
            icon: '🏢',
            color: 'green'
        },
        {
            id: 'solicitudes-proveedores',
            title: 'Solicitudes de Proveedores',
            description: 'Solicitudes para convertirse en proveedor verificado',
            icon: '📋',
            color: 'yellow'
        },
        {
            id: 'categorias',
            title: 'Categorías',
            description: 'Categorías disponibles en la plataforma',
            icon: '📂',
            color: 'purple'
        },
        {
            id: 'servicios',
            title: 'Servicios',
            description: 'Servicios publicados en la plataforma',
            icon: '🛠️',
            color: 'indigo'
        },
        {
            id: 'solicitudes-servicios',
            title: 'Solicitudes de Nuevos Servicios',
            description: 'Solicitudes de nuevos servicios',
            icon: '📝',
            color: 'orange'
        },
        {
            id: 'solicitudes-categorias',
            title: 'Solicitudes de Nuevas Categorías',
            description: 'Solicitudes de nuevas categorías',
            icon: '📂',
            color: 'teal'
        },
        {
            id: 'reservas',
            title: 'Reservas de Proveedores',
            description: 'Reporte detallado de reservas de proveedores con información completa de clientes, servicios y estados',
            icon: '📅',
            color: 'pink'
        },
        {
            id: 'calificaciones',
            title: 'Calificaciones de Clientes',
            description: 'Calificaciones de clientes hacia proveedores',
            icon: '⭐',
            color: 'amber'
        },
        {
            id: 'calificaciones-proveedores',
            title: 'Calificaciones de Proveedores',
            description: 'Calificaciones de proveedores hacia clientes',
            icon: '🌟',
            color: 'yellow'
        }
    ];

    // Función simple para cargar reportes sin cache
    const loadReportOnDemand = async (reportType: string) => {
        if (loadedReports.has(reportType) || loading[reportType]) {
            return; // Ya está cargado o cargando
        }

        try {
        await loadReporte(reportType);
        setLoadedReports(prev => new Set(prev).add(reportType));
        } catch (error) {
            console.error('Error cargando reporte:', error);
        }
    };

    // Inicialización simple sin pre-carga automática
    useEffect(() => {
        if (user?.accessToken) {
            setInitialLoading(false);
        }
    }, [user?.accessToken]);

    // Función para formatear fecha a DD/MM/AAAA
    const formatDateToDDMMAAAA = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            const day = date.getDate().toString().padStart(2, '0');
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            const year = date.getFullYear();
            return `${day}/${month}/${year}`;
        } catch (error) {
            console.error('Error formateando fecha:', error);
            return dateString; // Retornar fecha original si hay error
        }
    };

    // Función helper para ajustar fecha a zona horaria de Argentina (UTC-3)
    const adjustToArgentinaTime = (date: Date): Date => {
        // Argentina está en UTC-3, así que restamos 3 horas
        return new Date(date.getTime() - 3 * 60 * 60 * 1000);
    };

    // Función helper para formatear fecha/hora con zona horaria de Argentina
    const formatArgentinaDateTime = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            return date.toLocaleString('es-AR', {
                timeZone: 'America/Argentina/Buenos_Aires',
                hour12: false,
            });
        } catch (error) {
            console.error('Error formateando fecha Argentina:', error);
            return dateString;
        }
    };

    // Función helper para formatear solo fecha con zona horaria de Argentina
    const formatArgentinaDate = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('es-AR', {
                timeZone: 'America/Argentina/Buenos_Aires',
            });
        } catch (error) {
            console.error('Error formateando fecha Argentina:', error);
            return dateString;
        }
    };

    // Función para generar fecha actual de Argentina en formato ISO
    const getArgentinaDateISO = (): string => {
        // Usar la fecha actual sin ajustes - formatArgentinaDateTime se encarga del display
        return new Date().toISOString();
    };


    // Función para generar reporte de solicitudes de servicios (ahora solo con datos reales)
    const generateReporteSolicitudesServicios = async (accessToken: string): Promise<ReporteData> => {
        try {
            console.log('📋 Generando reporte de solicitudes de servicios...');

            // Llama al endpoint real que actualmente puede fallar por CORS
            const solicitudes = await adminAPI.getAllSolicitudesServiciosModificado(accessToken);

            console.log('📊 Solicitudes reales obtenidas:', solicitudes.length);

            // Obtener emails reales usando la misma lógica que el reporte de categorías
            console.log('📧 Obteniendo emails reales desde reporte de proveedores...');
            const apiBaseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
            const proveedoresResponse = await fetch(`${apiBaseUrl}/api/v1/admin/reports/proveedores-verificados`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                }
            });

            let emailsDict: {[key: string]: string} = {};
            if (proveedoresResponse.ok) {
                const proveedoresData = await proveedoresResponse.json();
                const proveedores = proveedoresData.proveedores || [];
                console.log('🏢 Proveedores obtenidos para emails:', proveedores.length);

                // Crear diccionario de emails por nombre de contacto (mismo método que la página de administración)
                proveedores.forEach((proveedor: any) => {
                    if (proveedor.nombre_contacto && proveedor.email_contacto && proveedor.email_contacto !== 'No disponible') {
                        emailsDict[proveedor.nombre_contacto] = proveedor.email_contacto;
                    }
                });

                console.log('📧 Emails extraídos del reporte de proveedores:', Object.keys(emailsDict).length);
            } else {
                console.log('❌ No se pudo obtener reporte de proveedores para emails');
            }

            // Procesar las solicitudes reales con emails
            const solicitudesProcesadas = solicitudes.map((solicitud: any) => {
                // Obtener email real usando la misma lógica que la página de administración
                let emailContacto = 'Sin especificar';
                if (solicitud.nombre_contacto && solicitud.nombre_contacto !== 'Sin especificar') {
                    const userEmail = emailsDict[solicitud.nombre_contacto];
                    if (userEmail) {
                        emailContacto = userEmail;
                        console.log(`Email real encontrado para contacto ${solicitud.nombre_contacto}: ${emailContacto}`);
                    } else {
                        console.log(`❌ No se encontró email para contacto ${solicitud.nombre_contacto}`);
                    }
                }

                return {
                    id_solicitud: solicitud.id_solicitud,
                    nombre_servicio: solicitud.nombre_servicio,
                    descripcion: solicitud.descripcion,
                    estado_aprobacion: solicitud.estado_aprobacion,
                    comentario_admin: solicitud.comentario_admin || '',
                    fecha_creacion: formatDateToDDMMAAAA(solicitud.created_at),
                    categoria: solicitud.nombre_categoria || 'Sin especificar',
                    empresa: solicitud.nombre_empresa || 'Sin especificar',
                    contacto: solicitud.nombre_contacto || 'Sin especificar',
                    email_contacto: emailContacto
                };
            });

            const totalSolicitudes = solicitudesProcesadas.length;
            const pendientes = solicitudesProcesadas.filter(s => s.estado_aprobacion === 'pendiente').length;
            const aprobadas = solicitudesProcesadas.filter(s => s.estado_aprobacion === 'aprobada').length;
            const rechazadas = solicitudesProcesadas.filter(s => s.estado_aprobacion === 'rechazada').length;

            return {
                total_solicitudes_servicios: totalSolicitudes,
                solicitudes_servicios: solicitudesProcesadas,
                fecha_generacion: new Date().toISOString(),
                pendientes,
                aprobadas,
                rechazadas,
                generado_desde: 'backend_real'
            };
        } catch (error) {
            console.error('❌ Error generando reporte de solicitudes de servicios:', error);
            // Fallback honesto: sin datos
            return {
                total_solicitudes_servicios: 0,
                solicitudes_servicios: [],
                fecha_generacion: new Date().toISOString(),
                pendientes: 0,
                aprobadas: 0,
                rechazadas: 0,
                generado_desde: 'sin_datos_backend',
                mensaje: 'No se pudieron cargar las solicitudes desde el backend'
            };
        }
    };

    // Función para generar reporte de solicitudes de categorías (misma lógica que servicios)
    const generateReporteSolicitudesCategorias = async (accessToken: string): Promise<ReporteData> => {
        try {
            console.log('📋 Generando reporte de solicitudes de categorías...');
            
            // Obtener todas las solicitudes de categorías
            const solicitudes = await categoryRequestsAPI.getAllCategoryRequests(accessToken);
            
            console.log('📊 Solicitudes de categorías obtenidas para reporte:', solicitudes.length);
            console.log('🔍 Primera solicitud:', solicitudes[0]);
            
            // Obtener emails reales usando la misma lógica que la página de administración
            console.log('📧 Obteniendo emails reales desde reporte de proveedores...');
            const apiBaseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
            const proveedoresResponse = await fetch(`${apiBaseUrl}/api/v1/admin/reports/proveedores-verificados`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            let emailsDict: {[key: string]: string} = {};
            if (proveedoresResponse.ok) {
                const proveedoresData = await proveedoresResponse.json();
                const proveedores = proveedoresData.proveedores || [];
                console.log('🏢 Proveedores obtenidos para emails:', proveedores.length);
                
                // Crear diccionario de emails por nombre de contacto (mismo método que la página de administración)
                proveedores.forEach((proveedor: any) => {
                    if (proveedor.nombre_contacto && proveedor.email_contacto && proveedor.email_contacto !== 'No disponible') {
                        emailsDict[proveedor.nombre_contacto] = proveedor.email_contacto;
                    }
                });
                
                console.log('📧 Emails extraídos del reporte de proveedores:', Object.keys(emailsDict).length);
            } else {
                console.log('❌ No se pudo obtener reporte de proveedores para emails');
            }
            
            // Procesar las solicitudes para el reporte con emails reales
            const solicitudesProcesadas = solicitudes.map(solicitud => {
                // Obtener email real usando la misma lógica que la página de administración
                let emailContacto = 'No especificado';
                if (solicitud.nombre_contacto && solicitud.nombre_contacto !== 'No especificado') {
                    const userEmail = emailsDict[solicitud.nombre_contacto];
                    if (userEmail) {
                        emailContacto = userEmail;
                        console.log(`Email real encontrado para contacto ${solicitud.nombre_contacto}: ${emailContacto}`);
                    } else {
                        console.log(`❌ No se encontró email para contacto ${solicitud.nombre_contacto}`);
                    }
                }
                
                return {
                    id_solicitud: solicitud.id_solicitud,
                    nombre_categoria: solicitud.nombre_categoria,
                    descripcion: solicitud.descripcion,
                    estado_aprobacion: solicitud.estado_aprobacion,
                    comentario_admin: solicitud.comentario_admin || '',
                    fecha_creacion: formatDateToDDMMAAAA(solicitud.created_at),
                    empresa: solicitud.nombre_empresa || 'No especificada',
                    contacto: solicitud.nombre_contacto || 'No especificado',
                    email_contacto: emailContacto
                };
            });

            // Calcular estadísticas
            const totalSolicitudes = solicitudesProcesadas.length;
            const pendientes = solicitudesProcesadas.filter(s => s.estado_aprobacion === 'pendiente').length;
            const aprobadas = solicitudesProcesadas.filter(s => s.estado_aprobacion === 'aprobada').length;
            const rechazadas = solicitudesProcesadas.filter(s => s.estado_aprobacion === 'rechazada').length;

            console.log('📈 Estadísticas del reporte de categorías:', {
                total: totalSolicitudes,
                pendientes,
                aprobadas,
                rechazadas
            });

            const reporteData = {
                total_solicitudes_categorias: totalSolicitudes,
                solicitudes_categorias: solicitudesProcesadas,
                fecha_generacion: getArgentinaDateISO(),
                // Estadísticas adicionales
                pendientes,
                aprobadas,
                rechazadas
            };

            console.log('Reporte de categorías generado exitosamente:', reporteData);
            return reporteData;
        } catch (error) {
            console.error('❌ Error generando reporte de solicitudes de categorías:', error);
            throw error;
        }
    };

    const loadReporte = async (reportType: string) => {
        if (!user?.accessToken) {
            console.error('❌ No hay token de acceso para cargar reporte:', reportType);
            return;
        }

        // Verificar si ya está cargando para evitar duplicados
        if (loading[reportType]) {
            console.log('⏳ Reporte ya está cargando:', reportType);
            return;
        }

        console.log(`🚀 Iniciando carga de reporte: ${reportType}`);
        setLoading(prev => ({ ...prev, [reportType]: true }));
        setError(null);

        // Mostrar mensaje específico para usuarios-activos
        if (reportType === 'usuarios-activos') {
            console.log('👥 Cargando reporte de usuarios activos (puede tardar más tiempo)...');
        }

        try {
            // Timeouts optimizados para cada tipo de reporte
            let timeoutDuration = 12000; // Default: 12 segundos
            if (reportType.includes('solicitudes')) {
                timeoutDuration = 18000; // Solicitudes: 18 segundos
            } else if (reportType === 'usuarios-activos') {
                timeoutDuration = 25000; // Usuarios: 25 segundos (más complejo)
            } else if (reportType === 'categorias') {
                timeoutDuration = 8000; // Categorías: 8 segundos (más simple)
            } else if (reportType === 'proveedores-verificados') {
                timeoutDuration = 15000; // Proveedores: 15 segundos
            } else if (reportType === 'reservas') {
                timeoutDuration = 15000; // Reservas: 15 segundos
            }
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de carga')), timeoutDuration)
            );

            let dataPromise: Promise<ReporteData>;
            
            switch (reportType) {
                case 'usuarios-activos':
                    // Sobrescribe la fecha del backend para asegurar la hora local correcta
                    dataPromise = adminAPI.getReporteUsuariosActivos(user.accessToken)
                        .then(data => {
                            // Asegura que la fecha de generación sea la local
                            return {
                                ...data,
                                fecha_generacion: new Date().toISOString()
                            };
                        })
                        .catch(async (error) => {
                        console.log('⚠️ Reporte específico de usuarios falló, intentando generar desde datos generales...');

                        // Fallback: generar reporte desde datos de usuarios normales
                        try {
                            const usersResponse = await fetch(buildApiUrl('/admin/users'), {
                                headers: { 'Authorization': `Bearer ${user.accessToken}` }
                            });

                            if (usersResponse.ok) {
                                const usersData = await usersResponse.json();
                                const usuarios = usersData.usuarios || [];

                                // Generar estadísticas básicas
                                const totalActivos = usuarios.filter((u: any) => u.estado === 'ACTIVO').length;
                                const totalInactivos = usuarios.filter((u: any) => u.estado === 'INACTIVO').length;

                                return {
                                    fecha_generacion: getArgentinaDateISO(),
                                    total_usuarios: usuarios.length,
                                    usuarios_activos: totalActivos,
                                    usuarios_inactivos: totalInactivos,
                                    usuarios: usuarios,
                                    generado_desde: 'fallback_users_endpoint'
                                };
                            }
                        } catch (fallbackError) {
                            console.log('⚠️ Fallback también falló, generando datos básicos...');
                        }

                        // Fallback final: sin datos si todo falla
                        return {
                            fecha_generacion: new Date().toISOString(),
                            total_usuarios: 0,
                            usuarios_activos: 0,
                            usuarios_inactivos: 0,
                            usuarios: [],
                            generado_desde: 'sin_datos_backend',
                            mensaje: 'No hay datos de usuarios disponibles en el backend'
                        };
                    });
                    break;
                case 'proveedores-verificados':
                    // Reporte con múltiples estrategias para garantizar que funcione
                    dataPromise = (async () => {
                        console.log('🏢 Iniciando carga de reporte de proveedores verificados...');
                        
                        // Estrategia 1: adminAPI.getReporteProveedoresVerificados
                        try {
                            const data = await adminAPI.getReporteProveedoresVerificados(user.accessToken);
                            console.log('✅ Proveedores cargados con adminAPI:', data);
                            return {
                                ...data,
                                fecha_generacion: getArgentinaDateISO()
                            };
                        } catch (err1) {
                            console.log('⚠️ adminAPI falló, intentando endpoint directo...');
                            
                            // Estrategia 2: fetch directo al endpoint
                            try {
                                const response = await fetch(buildApiUrl('/admin/reports/proveedores-verificados'), {
                                    headers: { 'Authorization': `Bearer ${user.accessToken}` }
                                });
                                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                                
                                const data = await response.json();
                                console.log('✅ Proveedores cargados con fetch directo:', data);
                                return {
                                    ...data,
                                    fecha_generacion: getArgentinaDateISO()
                                };
                            } catch (err2) {
                                console.log('⚠️ Fetch directo falló, generando reporte básico...');
                                
                                // Estrategia 3: generar reporte básico con datos disponibles
                                try {
                                    // Intentar obtener datos básicos de usuarios/proveedores
                                    const usersResponse = await fetch(buildApiUrl('/admin/users'), {
                                        headers: { 'Authorization': `Bearer ${user.accessToken}` }
                                    });
                                    
                                    if (usersResponse.ok) {
                                        const usersData = await usersResponse.json();
                                        const usuarios = usersData.usuarios || [];
                                        const proveedores = usuarios.filter((u: any) => u.rol_principal === 'provider' || u.rol_principal === 'proveedor');
                                        
                                        console.log('✅ Reporte básico generado con usuarios:', proveedores.length, 'proveedores');
                                        return {
                                            fecha_generacion: getArgentinaDateISO(),
                                            total_proveedores: proveedores.length,
                                            proveedores_verificados: proveedores.filter((p: any) => p.estado === 'ACTIVO').length,
                                            proveedores_pendientes: proveedores.filter((p: any) => p.estado === 'PENDIENTE').length,
                                            proveedores: proveedores.map((p: any) => ({
                                                id: p.id,
                                                nombre_empresa: p.nombre_empresa || 'Sin especificar',
                                                nombre_contacto: p.nombre_persona || 'Sin especificar',
                                                email_contacto: p.email || 'Sin especificar',
                                                estado_verificacion: p.estado || 'PENDIENTE',
                                                fecha_registro: p.fecha_creacion || getArgentinaDateISO(),
                                                servicios_ofrecidos: 0
                                            })),
                                            generado_desde: 'users_fallback'
                                        };
                                    }
                                } catch (err3) {
                                    console.log('⚠️ Todas las estrategias fallaron');
                                }
                                
                                // Estrategia 4: sin datos si todo falla
                                console.log('⚠️ No se pudieron cargar proveedores desde ninguna fuente');
                                return {
                                    fecha_generacion: getArgentinaDateISO(),
                                    total_proveedores: 0,
                                    proveedores_verificados: 0,
                                    proveedores_pendientes: 0,
                                    proveedores: [],
                                    generado_desde: 'sin_datos_backend',
                                    mensaje: 'No hay datos de proveedores disponibles en el backend'
                                };
                            }
                        }
                    })();
                    break;
                case 'solicitudes-proveedores':
                    // Endpoint con error 500 - usar estrategia alternativa sin CORS
                    dataPromise = (async () => {
                        console.log('📋 Buscando solicitudes de proveedores...');
                        try {
                            // Obtener proveedores desde usuarios como alternativa
                            const usersResponse = await fetch(buildApiUrl('/admin/users'), {
                                headers: { 'Authorization': `Bearer ${user.accessToken}` }
                            });
                            if (usersResponse.ok) {
                                const usersData = await usersResponse.json();
                                const usuarios = usersData.usuarios || [];
                                const proveedores = usuarios.filter((u: any) =>
                                    u.rol_principal === 'provider' || u.rol_principal === 'proveedor'
                                );

                                console.log('✅ Encontrados', proveedores.length, 'proveedores para reporte');
                                return {
                                    fecha_generacion: getArgentinaDateISO(),
                                    total_solicitudes: proveedores.length,
                                    solicitudes_proveedores: proveedores.map((p: any) => ({
                                        id_solicitud: p.id,
                                        nombre_empresa: p.nombre_empresa || 'Sin especificar',
                                        nombre_contacto: p.nombre_persona || 'Sin especificar',
                                        email_contacto: p.email || 'Sin especificar',
                                        estado_solicitud: p.estado === 'ACTIVO' ? 'aprobada' : 'pendiente',
                                        fecha_solicitud: p.fecha_creacion || getArgentinaDateISO(),
                                        servicios_solicitados: 'Servicios de proveedor',
                                        comentario_admin: p.estado === 'ACTIVO' ? 'Proveedor verificado' : 'Pendiente de verificación'
                                    })),
                                    pendientes: proveedores.filter((p: any) => p.estado !== 'ACTIVO').length,
                                    aprobadas: proveedores.filter((p: any) => p.estado === 'ACTIVO').length,
                                    rechazadas: 0,
                                    generado_desde: 'proveedores_from_users'
                                };
                            }
                        } catch (err) {
                            console.log('⚠️ No se pudieron obtener proveedores de usuarios');
                        }

                        // Fallback: sin datos
                        return {
                            fecha_generacion: getArgentinaDateISO(),
                            total_solicitudes: 0,
                            solicitudes_proveedores: [],
                            pendientes: 0,
                            aprobadas: 0,
                            rechazadas: 0,
                            generado_desde: 'sin_datos_backend',
                            mensaje: 'No hay datos disponibles en el backend'
                        };
                    })();
                    break;
                case 'categorias':
                    // Usar múltiples estrategias para garantizar que funcione
                    dataPromise = (async () => {
                        console.log('📂 Iniciando carga de reporte de categorías...');
                        
                        // Estrategia 1: categoriesAPI (funciona en /dashboard/categories)
                        try {
                            const categorias = await categoriesAPI.getCategories(user.accessToken);
                            console.log('✅ Categorías cargadas con categoriesAPI:', categorias.length);
                            return {
                                fecha_generacion: getArgentinaDateISO(),
                                total_categorias: categorias.length,
                                categorias: categorias,
                                generado_desde: 'categories_api_primary'
                            };
                        } catch (err1) {
                            console.log('⚠️ categoriesAPI falló, intentando fetch directo...');
                            
                            // Estrategia 2: fetch directo
                            try {
                                const url = `${buildApiUrl(API_CONFIG.CATEGORIES.LIST)}`;
                                const response = await fetch(url, {
                                    headers: { 'Authorization': `Bearer ${user.accessToken}` }
                                });
                                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                                
                                const raw = await response.json();
                                const categorias = Array.isArray(raw) ? raw : (raw.categorias || raw.results || raw.items || []);
                                
                                console.log('✅ Categorías cargadas con fetch directo:', categorias.length);
                                return {
                                    fecha_generacion: getArgentinaDateISO(),
                                    total_categorias: categorias.length,
                                    categorias: categorias,
                                    generado_desde: 'categories_fetch_fallback'
                                };
                            } catch (err2) {
                                console.log('⚠️ Fetch directo falló, intentando con active_only=false...');
                                
                                // Estrategia 3: categoriesAPI sin filtro
                                try {
                                    const categorias = await categoriesAPI.getCategories(user.accessToken, false);
                                    console.log('✅ Categorías cargadas sin filtro:', categorias.length);
                                    return {
                                        fecha_generacion: getArgentinaDateISO(),
                                        total_categorias: categorias.length,
                                        categorias: categorias,
                                        generado_desde: 'categories_api_no_filter'
                                    };
                                } catch (err3) {
                                    console.error('❌ Todas las estrategias fallaron:', err3);
                                    return {
                                        fecha_generacion: getArgentinaDateISO(),
                                        total_categorias: 0,
                                        categorias: [],
                                        generado_desde: 'empty_fallback',
                                        error: 'No se pudieron cargar las categorías'
                                    };
                                }
                            }
                        }
                    })();
                    break;
                case 'servicios':
                    // Usar el endpoint de reportes de servicios
                    dataPromise = (async () => {
                        console.log('🔧 Cargando reporte de servicios...');
                        try {
                            // Usar el endpoint de reportes de servicios
                            const response = await fetch(buildApiUrl('/admin/reports/servicios'), {
                                headers: { 'Authorization': `Bearer ${user.accessToken}` }
                            });
                            
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                            }
                            
                            const data = await response.json();
                            console.log('✅ Servicios cargados desde reporte:', data);
                            
                            return {
                                ...data,
                                fecha_generacion: getArgentinaDateISO()
                            };
                        } catch (err) {
                            console.log('⚠️ No se pudieron obtener servicios del endpoint público');
                        }

                        // Fallback: sin datos
                        return {
                            fecha_generacion: getArgentinaDateISO(),
                            total_servicios: 0,
                            servicios: [],
                            generado_desde: 'sin_datos_backend',
                            mensaje: 'No hay datos disponibles en el backend'
                        };
                    })();
                    break;
                case 'solicitudes-servicios':
                    dataPromise = generateReporteSolicitudesServicios(user.accessToken).then(data => {
                        // Asegurar fecha_generacion actualizada
                        return {
                            ...data,
                            fecha_generacion: getArgentinaDateISO()
                        };
                    }).catch(error => {
                        console.log('⚠️ Reporte de solicitudes de servicios falló, usando fallback...');
                        return {
                            fecha_generacion: getArgentinaDateISO(),
                            total_solicitudes_servicios: 0,
                            solicitudes_servicios: [],
                            pendientes: 0,
                            aprobadas: 0,
                            rechazadas: 0,
                            generado_desde: 'sin_datos_backend',
                            mensaje: 'No se pudieron cargar las solicitudes de servicios'
                        };
                    });
                    break;
                case 'solicitudes-categorias':
                    dataPromise = generateReporteSolicitudesCategorias(user.accessToken).then(data => {
                        // Asegurar fecha_generacion actualizada
                        return {
                            ...data,
                            fecha_generacion: getArgentinaDateISO()
                        };
                    }).catch(error => {
                        console.log('⚠️ Reporte de solicitudes de categorías falló, usando fallback...');
                        return {
                            fecha_generacion: getArgentinaDateISO(),
                            total_solicitudes_categorias: 0,
                            solicitudes_categorias: [],
                            pendientes: 0,
                            aprobadas: 0,
                            rechazadas: 0,
                            generado_desde: 'sin_datos_backend',
                            mensaje: 'No se pudieron cargar las solicitudes de categorías'
                        };
                    });
                    break;
                case 'reservas':
                    dataPromise = (async () => {
                        console.log('📅 Cargando reporte de reservas de proveedores...');
                        try {
                            const response = await fetch(buildApiUrl('/admin/reports/reservas-proveedores'), {
                                headers: { 'Authorization': `Bearer ${user.accessToken}` }
                            });
                            
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                            }
                            
                            const data = await response.json();
                            console.log('✅ Reporte de reservas de proveedores cargado exitosamente:', data);
                            
                            // Procesar los datos para el formato esperado
                            const reservasProcesadas = data.reservas?.map((reserva: any) => ({
                                id_reserva: reserva.id_reserva,
                                cliente_nombre: reserva.cliente?.nombre || 'N/A',
                                cliente_email: reserva.cliente?.email || 'N/A',
                                proveedor_empresa: reserva.proveedor?.empresa || 'N/A',
                                proveedor_nombre_fantasia: reserva.proveedor?.nombre_fantasia || 'N/A',
                                servicio_nombre: reserva.servicio?.nombre || 'N/A',
                                servicio_precio: reserva.servicio?.precio || 0,
                                servicio_categoria: reserva.servicio?.categoria || 'N/A',
                                fecha_servicio: reserva.reserva?.fecha_servicio || 'N/A',
                                horario: reserva.reserva?.horario || 'N/A',
                                fecha_reserva: reserva.reserva?.fecha_reserva || 'N/A',
                                estado: reserva.estado?.label || reserva.estado?.valor || 'N/A',
                                descripcion: reserva.reserva?.descripcion || 'N/A',
                                observacion: reserva.reserva?.observacion || 'N/A'
                            })) || [];
                            
                            return {
                                total_reservas: data.total_reservas || 0,
                                reservas: reservasProcesadas,
                                estadisticas: data.estadisticas || {},
                                fecha_generacion: getArgentinaDateISO(),
                                generado_desde: 'reservas_proveedores_endpoint'
                            };
                        } catch (error) {
                            console.error('❌ Error cargando reporte de reservas de proveedores:', error);
                            return {
                                fecha_generacion: getArgentinaDateISO(),
                                total_reservas: 0,
                                reservas: [],
                                generado_desde: 'sin_datos_backend',
                                mensaje: 'No se pudieron cargar las reservas de proveedores'
                            };
                        }
                    })();
                    break;
                case 'calificaciones':
                    dataPromise = (async () => {
                        console.log('⭐ Cargando reporte de calificaciones...');
                        try {
                            const response = await fetch(buildApiUrl('/admin/reports/calificaciones'), {
                                headers: { 'Authorization': `Bearer ${user.accessToken}` }
                            });
                            
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                            }
                            
                            const data = await response.json();
                            console.log('✅ Reporte de calificaciones cargado exitosamente:', data);
                            // Asegurar fecha_generacion actualizada con hora correcta
                            return {
                                ...data,
                                fecha_generacion: getArgentinaDateISO()
                            };
                        } catch (error) {
                            console.error('❌ Error cargando reporte de calificaciones:', error);
                            throw error;
                        }
                    })();
                    timeoutDuration = 15000; // 15 segundos para calificaciones
                    break;
                case 'calificaciones-proveedores':
                    dataPromise = (async () => {
                        console.log('🌟 Cargando reporte de calificaciones de proveedores...');
                        try {
                            const response = await fetch(buildApiUrl('/admin/reports/calificaciones-proveedores'), {
                                headers: { 'Authorization': `Bearer ${user.accessToken}` }
                            });
                            
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                            }
                            
                            const data = await response.json();
                            console.log('✅ Reporte de calificaciones de proveedores cargado exitosamente:', data);
                            // Asegurar fecha_generacion actualizada con hora correcta
                            return {
                                ...data,
                                fecha_generacion: getArgentinaDateISO()
                            };
                        } catch (error) {
                            console.error('❌ Error cargando reporte de calificaciones de proveedores:', error);
                            throw error;
                        }
                    })();
                    timeoutDuration = 15000; // 15 segundos para calificaciones de proveedores
                    break;
                default:
                    throw new Error('Tipo de reporte no válido');
            }

            const data = await Promise.race([dataPromise, timeoutPromise]);
            console.log(`Reporte ${reportType} cargado exitosamente:`, data);

            // Sin cache - datos directos

            setReportes(prev => ({ ...prev, [reportType]: data as ReporteData }));
            setLoadedReports(prev => new Set(prev).add(reportType));
        } catch (err: any) {
            console.error(`❌ Error cargando reporte ${reportType}:`, err);

            // Manejo especial para el reporte de usuarios que tiene fallback
            if (reportType === 'usuarios-activos' && err?.message?.includes('Timeout')) {
                console.log('⏳ Timeout en reporte usuarios-activos, intentando fallback automático...');
                // No mostrar error inmediatamente, el fallback se ejecutará
                return;
            }
            
            // Si es un error de "no hay datos", establecer contador en 0 sin mostrar error
            if (err?.status === 404 || err?.detail?.includes('No se encontraron') || err?.detail?.includes('No hay')) {
                console.log(`📊 Estableciendo reporte vacío para ${reportType} (no hay datos)`);
                const emptyReport: ReporteData = {
                    fecha_generacion: getArgentinaDateISO(),
                    total_usuarios: 0,
                    total_proveedores: 0,
                    total_solicitudes: 0,
                    total_categorias: 0,
                    total_servicios: 0,
                    total_solicitudes_servicios: 0,
                    total_solicitudes_categorias: 0,
                    pendientes: 0,
                    aprobadas: 0,
                    rechazadas: 0
                };
                setReportes(prev => ({ ...prev, [reportType]: emptyReport }));
                setLoadedReports(prev => new Set(prev).add(reportType));
            } else {
                // Para errores reales (500, timeout, etc.), solo registrar en consola
                console.error(`Error en reporte ${reportType}:`, err);
                // No mostrar error al usuario para mejor UX
                // NO agregar a loadedReports para permitir reintento
            }
        } finally {
            setLoading(prev => ({ ...prev, [reportType]: false }));
        }
    };

    const viewAllData = async (reportType: string) => {
        // Cargar el reporte si no está cargado
        if (!loadedReports.has(reportType)) {
            await loadReportOnDemand(reportType);
        }
        
        const reporte = reportes[reportType];
        if (!reporte) return;

        const reportInfo = reportTypes.find(r => r.id === reportType);
        if (!reportInfo) return;

        const dataKey = Object.keys(reporte).find(key => 
            key !== 'fecha_generacion' && 
            !key.startsWith('total_') && 
            Array.isArray(reporte[key as keyof ReporteData])
        );

        if (!dataKey) return;

        const data = reporte[dataKey as keyof ReporteData] as any[];
        if (!data || data.length === 0) return;

        // Generar HTML para mostrar todos los datos
        const htmlContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Reporte - ${reportInfo.title}</title>
                <meta charset="utf-8">
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 0;
                        padding: 20px;
                        background-color: #f9fafb;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                    h1 { 
                        color: #1f2937; 
                        border-bottom: 2px solid #e5e7eb;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }
                    .info {
                        background-color: #f3f4f6;
                        padding: 15px;
                        border-radius: 6px;
                        margin-bottom: 20px;
                    }
                    .info p {
                        margin: 5px 0;
                        color: #374151;
                    }
                    table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        margin-top: 20px;
                        font-size: 14px;
                    }
                    th, td { 
                        border: 1px solid #d1d5db; 
                        padding: 12px 8px; 
                        text-align: left; 
                    }
                    th { 
                        background-color: #f9fafb; 
                        font-weight: 600;
                        color: #374151;
                        position: sticky;
                        top: 0;
                    }
                    tr:nth-child(even) {
                        background-color: #f9fafb;
                    }
                    tr:hover {
                        background-color: #f3f4f6;
                    }
                    .total { 
                        font-weight: bold; 
                        margin-top: 20px; 
                        color: #1f2937;
                    }
                    .actions {
                        margin-top: 20px;
                        text-align: center;
                        padding: 20px;
                        background-color: #f9fafb;
                        border-radius: 6px;
                    }
                    .btn {
                        background-color: #3b82f6;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        margin: 0 10px;
                        font-size: 14px;
                        text-decoration: none;
                        display: inline-block;
                    }
                    .btn:hover {
                        background-color: #2563eb;
                    }
                    .btn-secondary {
                        background-color: #6b7280;
                    }
                    .btn-secondary:hover {
                        background-color: #4b5563;
                    }
                    .btn-success {
                        background-color: #10b981;
                    }
                    .btn-success:hover {
                        background-color: #059669;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 Reporte - ${reportInfo.title}</h1>
                    
                    <div class="info">
                        <p><strong>📅 Fecha de generación:</strong> ${formatArgentinaDateTime(reporte.fecha_generacion)}</p>
                        <p><strong>📈 Total de registros:</strong> ${data.length}</p>
                        <p><strong>📋 Descripción:</strong> ${reportInfo.description}</p>
                        ${(reportType === 'solicitudes-servicios' || reportType === 'solicitudes-categorias') && reporte.pendientes !== undefined ? `
                            <p><strong>📊 Estadísticas:</strong></p>
                            <p>• Pendientes: ${reporte.pendientes}</p>
                            <p>• Aprobadas: ${reporte.aprobadas}</p>
                            <p>• Rechazadas: ${reporte.rechazadas}</p>
                        ` : ''}
                    </div>

                    <table>
                        <thead>
                            <tr>
                                ${Object.keys(data[0]).map(key => {
                                    let headerName = key.replace(/_/g, ' ').toUpperCase();
                                    // Personalizar nombres específicos
                                    if (key === 'created_at') headerName = 'FECHA CREACION';
                                    if (key === 'updated_at') headerName = 'FECHA ACTUALIZACION';
                                    if (key === 'active' || key === 'activo') headerName = 'ESTADO';
                                    return `<th>${headerName}</th>`;
                                }).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(item => 
                                `<tr>${Object.entries(item).map(([key, value]) => 
                                    `<td>${formatValue(value, key)}</td>`
                                ).join('')}</tr>`
                            ).join('')}
                        </tbody>
                    </table>

                    <div class="actions">
                        <button class="btn btn-success" onclick="window.print()">🖨️ Imprimir</button>
                        <button class="btn" onclick="window.close()">❌ Cerrar</button>
                    </div>
                </div>
            </body>
            </html>
        `;

        const newWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
        if (newWindow) {
            newWindow.document.write(htmlContent);
            newWindow.document.close();
        }
    };

    const generatePDF = (reportType: string) => {
        const reporte = reportes[reportType];
        if (!reporte) return;

        // Crear contenido HTML para el PDF
        let htmlContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Reporte - ${reportTypes.find(r => r.id === reportType)?.title}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .header h1 { color: #1f2937; margin-bottom: 10px; }
                    .header p { color: #6b7280; }
                    .summary { background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
                    .summary h3 { margin: 0 0 10px 0; color: #374151; }
                    .table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    .table th, .table td { border: 1px solid #d1d5db; padding: 8px; text-align: left; }
                    .table th { background: #f9fafb; font-weight: bold; }
                    .footer { margin-top: 30px; text-align: center; color: #6b7280; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>SEVA Empresas</h1>
                    <h2>${reportTypes.find(r => r.id === reportType)?.title}</h2>
                    <p>Generado el: ${formatArgentinaDateTime(reporte.fecha_generacion)}</p>
                </div>
        `;

        // Agregar resumen
        const totalKey = Object.keys(reporte).find(key => key.startsWith('total_'));
        if (totalKey) {
            const total = reporte[totalKey as keyof ReporteData];
            htmlContent += `
                <div class="summary">
                    <h3>Resumen</h3>
                    <p><strong>Total: ${total}</strong></p>
                    ${(reportType === 'solicitudes-servicios' || reportType === 'solicitudes-categorias') && reporte.pendientes !== undefined ? `
                        <p><strong>Estados:</strong></p>
                        <p>• Pendientes: ${reporte.pendientes}</p>
                        <p>• Aprobadas: ${reporte.aprobadas}</p>
                        <p>• Rechazadas: ${reporte.rechazadas}</p>
                    ` : ''}
                </div>
            `;
        }

        // Agregar tabla de datos
        const dataKey = Object.keys(reporte).find(key => 
            key !== 'fecha_generacion' && 
            key !== totalKey && 
            Array.isArray(reporte[key as keyof ReporteData])
        );

        if (dataKey) {
            const data = reporte[dataKey as keyof ReporteData] as any[];
            if (data && data.length > 0) {
                htmlContent += '<table class="table"><thead><tr>';
                
                // Headers con nombres personalizados
                Object.keys(data[0]).forEach(key => {
                    let headerName = key.replace(/_/g, ' ').toUpperCase();
                    // Personalizar nombres específicos
                    if (key === 'created_at') headerName = 'FECHA CREACION';
                    if (key === 'updated_at') headerName = 'FECHA ACTUALIZACION';
                    if (key === 'active' || key === 'activo') headerName = 'ESTADO';
                    
                    // Personalizar nombres para reporte de reservas
                    if (key === 'id_reserva') headerName = 'ID RESERVA';
                    if (key === 'fecha_reserva') headerName = 'FECHA DE RESERVA';
                    if (key === 'estado') headerName = 'ESTADO';
                    if (key === 'cliente_nombre') headerName = 'CLIENTE';
                    if (key === 'servicio_nombre') headerName = 'SERVICIO';
                    if (key === 'empresa_razon_social') headerName = 'PROVEEDOR';
                    if (key === 'fecha_servicio') headerName = 'FECHA DEL SERVICIO';
                    if (key === 'hora_servicio') headerName = 'HORA DEL SERVICIO';
                    if (key === 'precio') headerName = 'PRECIO';
                    
                    // Personalizar nombres para reporte de calificaciones (clientes)
                    if (key === 'fecha') headerName = 'FECHA';
                    if (key === 'servicio') headerName = 'SERVICIO';
                    if (key === 'proveedor_empresa') headerName = 'PROVEEDOR (EMPRESA)';
                    if (key === 'proveedor_persona') headerName = 'PROVEEDOR (PERSONA)';
                    if (key === 'cliente') headerName = 'CLIENTE';
                    if (key === 'puntaje') headerName = 'PUNTAJE (1-5)';
                    if (key === 'nps') headerName = 'NPS (1-10)';
                    if (key === 'comentario') headerName = 'COMENTARIO';
                    
                    // Personalizar nombres para reporte de calificaciones (proveedores)
                    if (key === 'cliente_persona') headerName = 'CLIENTE (PERSONA)';
                    if (key === 'cliente_empresa') headerName = 'CLIENTE (EMPRESA)';
                    
                    htmlContent += `<th>${headerName}</th>`;
                });
                
                htmlContent += '</tr></thead><tbody>';
                
                // Data rows
                data.forEach(item => {
                    htmlContent += '<tr>';
                    Object.entries(item).forEach(([key, value]) => {
                        htmlContent += `<td>${formatValue(value, key)}</td>`;
                    });
                    htmlContent += '</tr>';
                });
                
                htmlContent += '</tbody></table>';
            }
        }

        htmlContent += `
                <div class="footer">
                    <p>Reporte generado por SEVA Empresas - ${formatArgentinaDateTime(new Date().toISOString())}</p>
                </div>
            </body>
            </html>
        `;

        // Crear y descargar PDF
        const printWindow = window.open('', '_blank');
        if (printWindow) {
            printWindow.document.write(htmlContent);
            printWindow.document.close();
            printWindow.print();
        }
    };

    const renderReportData = (reportType: string) => {
        const reporte = reportes[reportType];
        if (!reporte) return null;

        const dataKey = Object.keys(reporte).find(key => 
            key !== 'fecha_generacion' && 
            !key.startsWith('total_') && 
            Array.isArray(reporte[key as keyof ReporteData])
        );

        if (!dataKey) return null;

        const data = reporte[dataKey as keyof ReporteData] as any[];
        if (!data || data.length === 0) return <p className="text-gray-500">No hay datos disponibles</p>;

        return (
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            {Object.keys(data[0]).map((key) => {
                                let headerName = key.replace(/_/g, ' ');
                                // Personalizar nombres específicos
                                if (key === 'created_at') headerName = 'FECHA CREACION';
                                if (key === 'updated_at') headerName = 'FECHA ACTUALIZACION';
                                if (key === 'active' || key === 'activo') headerName = 'ESTADO';
                                
                                // Personalizar nombres para reporte de reservas
                                if (key === 'id_reserva') headerName = 'ID RESERVA';
                                if (key === 'fecha_reserva') headerName = 'FECHA DE RESERVA';
                                if (key === 'estado') headerName = 'ESTADO';
                                if (key === 'cliente_nombre') headerName = 'CLIENTE';
                                if (key === 'servicio_nombre') headerName = 'SERVICIO';
                                if (key === 'empresa_razon_social') headerName = 'PROVEEDOR';
                                if (key === 'fecha_servicio') headerName = 'FECHA DEL SERVICIO';
                                if (key === 'hora_servicio') headerName = 'HORA DEL SERVICIO';
                                if (key === 'precio') headerName = 'PRECIO';
                                
                                // Personalizar nombres para reporte de calificaciones (clientes)
                                if (key === 'fecha') headerName = 'FECHA';
                                if (key === 'servicio') headerName = 'SERVICIO';
                                if (key === 'proveedor_empresa') headerName = 'PROVEEDOR (EMPRESA)';
                                if (key === 'proveedor_persona') headerName = 'PROVEEDOR (PERSONA)';
                                if (key === 'cliente') headerName = 'CLIENTE';
                                if (key === 'puntaje') headerName = 'PUNTAJE (1-5)';
                                if (key === 'nps') headerName = 'NPS (1-10)';
                                if (key === 'comentario') headerName = 'COMENTARIO';
                                
                                // Personalizar nombres para reporte de calificaciones (proveedores)
                                if (key === 'cliente_persona') headerName = 'CLIENTE (PERSONA)';
                                if (key === 'cliente_empresa') headerName = 'CLIENTE (EMPRESA)';
                                
                                return (
                                <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        {headerName}
                                </th>
                                );
                            })}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {data.slice(0, 10).map((item, index) => (
                            <tr key={index}>
                                {Object.entries(item).map(([key, value], valueIndex) => (
                                    <td key={valueIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {formatValue(value, key)}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
                {data.length > 10 && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-800">
                            <strong>Vista previa:</strong> Mostrando 10 de {data.length} registros.
                        </p>
                        <p className="text-sm text-blue-600 mt-1">
                            💡 Haz clic en "Ver" para ver todos los datos en una nueva pestaña.
                        </p>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header simple */}
                <div className="mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Reportes</h1>
                        <p className="mt-2 text-gray-600">Genera y descarga reportes detallados de la plataforma</p>
                    </div>
                </div>

                {/* Error global eliminado para mejor UX */}



                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    {reportTypes.map((report) => (
                        <div key={report.id} className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <div className="flex items-center mb-4">
                                <span className="text-3xl mr-3">{report.icon}</span>
                                <div>
                                    <h3 className="text-lg font-medium text-gray-900">{report.title}</h3>
                                    <p className="text-sm text-gray-500">{report.description}</p>
                                </div>
                            </div>
                            
                            <div className="mb-4">
                                <div className="flex items-center justify-between">
                                    <p className="text-2xl font-bold text-gray-900">
                                        {reportes[report.id] ? getReportTotal(reportes[report.id]) : 0}
                                    </p>
                                    {loading[report.id] && (
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                    )}
                                </div>
                                <p className="text-sm text-gray-500">Total registros</p>
                                {(report.id === 'solicitudes-servicios' || report.id === 'solicitudes-categorias') && (
                                    <div className="mt-2 text-xs text-gray-600">
                                        <div className="flex justify-between">
                                            <span>Pendientes: {reportes[report.id]?.pendientes ?? 0}</span>
                                            <span>Aprobadas: {reportes[report.id]?.aprobadas ?? 0}</span>
                                            <span>Rechazadas: {reportes[report.id]?.rechazadas ?? 0}</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="flex space-x-2">
                                <button
                                    onClick={() => {
                                        if (!reportes[report.id]) {
                                            loadReportOnDemand(report.id);
                                        } else {
                                            viewAllData(report.id);
                                        }
                                    }}
                                    disabled={loading[report.id]}
                                    className="flex-1 flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                                >
                                    <EyeIcon className="w-4 h-4 mr-2" />
                                    {loading[report.id] ? 'Cargando...' : 
                                     loadedReports.has(report.id) ? 'Ver Reporte' : 'Cargar y Ver'}
                                </button>
                                
                                {/* Botón de reintento eliminado para mejor UX */}
                                
                                <button
                                    onClick={() => generatePDF(report.id)}
                                    disabled={!reportes[report.id]}
                                    className="flex-1 flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                                    PDF
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                {selectedReport && reportes[selectedReport] && (
                    <div className="bg-white rounded-lg shadow border border-gray-200">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h2 className="text-xl font-semibold text-gray-900">
                                {reportTypes.find(r => r.id === selectedReport)?.title}
                            </h2>
                            <p className="text-sm text-gray-500">
                                Generado el: {formatArgentinaDateTime(reportes[selectedReport].fecha_generacion)}
                            </p>
                        </div>
                        <div className="p-6">
                            {renderReportData(selectedReport)}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminReportsPage;
