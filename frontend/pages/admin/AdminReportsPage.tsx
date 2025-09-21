import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { adminAPI, categoryRequestsAPI } from '../../services/api';
import { ChartBarIcon, DocumentArrowDownIcon, EyeIcon } from '../../components/icons';
import { API_CONFIG, buildApiUrl } from '../../config/api';

interface ReporteData {
    total_usuarios?: number;
    total_proveedores?: number;
    total_solicitudes?: number;
    total_categorias?: number;
    total_servicios?: number;
    total_solicitudes_servicios?: number;
    total_solicitudes_categorias?: number;
    usuarios?: any[];
    proveedores?: any[];
    solicitudes?: any[];
    categorias?: any[];
    servicios?: any[];
    solicitudes_servicios?: any[];
    solicitudes_categorias?: any[];
    fecha_generacion: string;
    pendientes?: number;
    aprobadas?: number;
    rechazadas?: number;
}

const AdminReportsPage: React.FC = () => {
    const { user } = useAuth();
    const [reportes, setReportes] = useState<{[key: string]: ReporteData}>({});
    const [loading, setLoading] = useState<{[key: string]: boolean}>({});
    const [error, setError] = useState<string | null>(null);
    const [selectedReport, setSelectedReport] = useState<string | null>(null);
    const [loadedReports, setLoadedReports] = useState<Set<string>>(new Set());
    const [initialLoading, setInitialLoading] = useState<boolean>(true);

    // Cache inteligente con expiración (5 minutos)
    const [cache, setCache] = useState<{[key: string]: {data: ReporteData, timestamp: number}}>({});
    const CACHE_DURATION = 5 * 60 * 1000; // 5 minutos

    // Utilidades de cache
    const isCacheValid = useCallback((reportType: string): boolean => {
        const cached = cache[reportType];
        if (!cached) return false;
        return Date.now() - cached.timestamp < CACHE_DURATION;
    }, [cache]);

    const getCachedData = useCallback((reportType: string): ReporteData | null => {
        return isCacheValid(reportType) ? cache[reportType].data : null;
    }, [cache, isCacheValid]);

    const setCachedData = useCallback((reportType: string, data: ReporteData) => {
        setCache(prev => ({
            ...prev,
            [reportType]: { data, timestamp: Date.now() }
        }));
    }, []);

    // Función helper para formatear valores nulos de manera profesional
    const formatValue = (value: any, fieldName?: string): string => {
        if (value === null || value === undefined || value === '') {
            // Para comentarios, mostrar campo vacío en lugar de N/A
            if (fieldName === 'comentario_admin' || fieldName === 'comentario') {
                return '';
            }
            // Para otros campos, mostrar N/A solo si es necesario
            return 'N/A';
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
               reportData.total_solicitudes_categorias ?? 0;
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
            return `La carga de ${reportName} está tardando demasiado. Por favor, intenta nuevamente.`;
        }
        
        // Si no hay datos, mostrar mensaje amigable
        if (error?.status === 404 || error?.detail?.includes('No se encontraron')) {
            return `No hay ${reportName} disponibles en este momento.`;
        }
        
        // Error 500 del servidor
        if (error?.status === 500) {
            return `Error del servidor al cargar ${reportName}. Por favor, intenta nuevamente.`;
        }
        
        // Error de red o conexión
        if (error?.message?.includes('Failed to fetch') || error?.message?.includes('NetworkError')) {
            return `Error de conexión al cargar ${reportName}. Verifica tu conexión e intenta nuevamente.`;
        }
        
        return `No se pudieron cargar los ${reportName}. Por favor, intenta nuevamente.`;
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
            icon: '✅',
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
        }
    ];

    // Función optimizada para cargar reporte con cache inteligente
    const loadReport = useCallback(async (reportType: string, showLoading: boolean = true) => {
        // Verificar cache primero
        const cachedData = getCachedData(reportType);
        if (cachedData) {
            console.log(`💾 Usando datos cacheados para ${reportType}`);
            setReportes(prev => ({ ...prev, [reportType]: cachedData }));
            setLoadedReports(prev => new Set(prev).add(reportType));
            return;
        }

        if (loadedReports.has(reportType) || loading[reportType]) {
            return; // Ya está cargado o cargando
        }

        if (showLoading) {
            setLoading(prev => ({ ...prev, [reportType]: true }));
        }

        try {
            await loadReporte(reportType);
            setLoadedReports(prev => new Set(prev).add(reportType));
        } finally {
            if (showLoading) {
                setLoading(prev => ({ ...prev, [reportType]: false }));
            }
        }
    }, [getCachedData, loadedReports, loading, loadReporte]);

    // Función legacy para compatibilidad
    const loadReportOnDemand = useCallback((reportType: string) => loadReport(reportType, true), [loadReport]);

    // Carga paralela inteligente de reportes críticos al inicializar
    useEffect(() => {
        if (!user?.accessToken) return;

        const loadCriticalReportsInParallel = async () => {
            console.log('🚀 Iniciando carga paralela de reportes críticos...');

            // Reportes que se cargan automáticamente (los más usados)
            const criticalReports = ['solicitudes-proveedores', 'proveedores-verificados', 'categorias'];

            // Cargar en paralelo sin bloquear la UI
            const promises = criticalReports.map(reportType => loadReport(reportType, false));

            try {
                await Promise.allSettled(promises);
                console.log('✅ Reportes críticos cargados exitosamente en background');
            } catch (error) {
                console.log('⚠️ Algunos reportes críticos fallaron, pero la página funciona');
            }

            // Marcar inicialización completa
            setInitialLoading(false);
        };

        loadCriticalReportsInParallel();
    }, [user?.accessToken, loadReport]);

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

    // Función helper para formatear fecha con zona horaria de Argentina
    const formatArgentinaDateTime = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            const adjustedDate = adjustToArgentinaTime(date);
            return adjustedDate.toLocaleString('es-AR', { hour12: false });
        } catch (error) {
            console.error('Error formateando fecha Argentina:', error);
            return dateString;
        }
    };

    // Función helper para formatear solo fecha con zona horaria de Argentina
    const formatArgentinaDate = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            const adjustedDate = adjustToArgentinaTime(date);
            return adjustedDate.toLocaleDateString('es-AR', { hour12: false });
        } catch (error) {
            console.error('Error formateando fecha Argentina:', error);
            return dateString;
        }
    };


    // Función para generar reporte de solicitudes de servicios (versión ultra simplificada)
    const generateReporteSolicitudesServicios = async (accessToken: string): Promise<ReporteData> => {
        try {
            console.log('📋 Generando reporte de solicitudes de servicios...');
            
            // Obtener todas las solicitudes de servicios
            const solicitudes = await adminAPI.getAllSolicitudesServiciosModificado(accessToken);
            
            console.log('📊 Solicitudes obtenidas para reporte:', solicitudes.length);
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
                        console.log(`✅ Email real encontrado para contacto ${solicitud.nombre_contacto}: ${emailContacto}`);
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
                    categoria: solicitud.nombre_categoria || 'No especificada',
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

            console.log('📈 Estadísticas del reporte:', {
                total: totalSolicitudes,
                pendientes,
                aprobadas,
                rechazadas
            });

            const reporteData = {
                total_solicitudes_servicios: totalSolicitudes,
                solicitudes_servicios: solicitudesProcesadas,
                fecha_generacion: new Date().toISOString(),
                // Estadísticas adicionales
                pendientes,
                aprobadas,
                rechazadas
            };

            console.log('✅ Reporte generado exitosamente:', reporteData);
            return reporteData;
        } catch (error) {
            console.error('❌ Error generando reporte de solicitudes de servicios:', error);
            throw error;
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
                        console.log(`✅ Email real encontrado para contacto ${solicitud.nombre_contacto}: ${emailContacto}`);
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
                fecha_generacion: new Date().toISOString(),
                // Estadísticas adicionales
                pendientes,
                aprobadas,
                rechazadas
            };

            console.log('✅ Reporte de categorías generado exitosamente:', reporteData);
            return reporteData;
        } catch (error) {
            console.error('❌ Error generando reporte de solicitudes de categorías:', error);
            throw error;
        }
    };

    const loadReporte = useCallback(async (reportType: string) => {
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
            // Timeout más agresivo para reportes pesados
            // Especialmente para usuarios-activos que requiere más procesamiento
            let timeoutDuration = 10000;
            if (reportType.includes('solicitudes')) {
                timeoutDuration = 15000;
            } else if (reportType === 'usuarios-activos') {
                timeoutDuration = 25000; // Más tiempo para usuarios
            }
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de carga')), timeoutDuration)
            );

            let dataPromise: Promise<ReporteData>;
            
            switch (reportType) {
                case 'usuarios-activos':
                    // Intentar primero el reporte específico, si falla usar datos de usuarios normales
                    dataPromise = adminAPI.getReporteUsuariosActivos(user.accessToken).catch(async (error) => {
                        console.log('⚠️ Reporte específico falló, intentando generar desde datos generales...');

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
                                    fecha_generacion: new Date().toISOString(),
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

                        // Último fallback: datos mock básicos
                        return {
                            fecha_generacion: new Date().toISOString(),
                            total_usuarios: 0,
                            usuarios_activos: 0,
                            usuarios_inactivos: 0,
                            usuarios: [],
                            generado_desde: 'mock_data',
                            mensaje: 'Datos no disponibles temporalmente'
                        };
                    });
                    break;
                case 'proveedores-verificados':
                    dataPromise = adminAPI.getReporteProveedoresVerificados(user.accessToken);
                    break;
                case 'solicitudes-proveedores':
                    dataPromise = adminAPI.getReporteSolicitudesProveedores(user.accessToken);
                    break;
                case 'categorias':
                    dataPromise = adminAPI.getReporteCategorias(user.accessToken);
                    break;
                case 'servicios':
                    dataPromise = adminAPI.getReporteServicios(user.accessToken);
                    break;
                case 'solicitudes-servicios':
                    dataPromise = generateReporteSolicitudesServicios(user.accessToken);
                    break;
                case 'solicitudes-categorias':
                    dataPromise = generateReporteSolicitudesCategorias(user.accessToken);
                    break;
                default:
                    throw new Error('Tipo de reporte no válido');
            }

            const data = await Promise.race([dataPromise, timeoutPromise]);
            console.log(`✅ Reporte ${reportType} cargado exitosamente:`, data);

            // Guardar en cache
            setCachedData(reportType, data as ReporteData);

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
                    fecha_generacion: new Date().toISOString(),
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
                // Para errores reales (500, timeout, etc.), mostrar error y NO marcar como cargado
                console.error(`🚨 Error real en reporte ${reportType}:`, err);
                setError(getFriendlyErrorMessage(reportType, err));
                // NO agregar a loadedReports para permitir reintento
            }
        } finally {
            setLoading(prev => ({ ...prev, [reportType]: false }));
        }
    }, [user?.accessToken, loading, setCachedData]);

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
                                ${Object.keys(data[0]).map(key => `<th>${key.replace(/_/g, ' ').toUpperCase()}</th>`).join('')}
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
                    <p>Generado el: ${formatArgentinaDate(reporte.fecha_generacion)}</p>
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
                
                // Headers
                Object.keys(data[0]).forEach(key => {
                    htmlContent += `<th>${key.replace(/_/g, ' ').toUpperCase()}</th>`;
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
                            {Object.keys(data[0]).map((key) => (
                                <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    {key.replace(/_/g, ' ')}
                                </th>
                            ))}
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

    // Estadísticas de optimización
    const optimizationStats = {
        loadedReports: loadedReports.size,
        cachedReports: Object.keys(cache).filter(key => isCacheValid(key)).length,
        loadingReports: Object.values(loading).filter(Boolean).length,
        totalReports: reportTypes.length
    };

    return (
        <div className="p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header con estadísticas de optimización */}
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Reportes</h1>
                            <p className="mt-2 text-gray-600">Genera y descarga reportes detallados de la plataforma</p>
                        </div>

                        {/* Indicadores de optimización */}
                        <div className="hidden md:flex items-center space-x-6 text-sm">
                            <div className="flex items-center space-x-2">
                                <span className="text-green-600 text-lg">✅</span>
                                <div>
                                    <div className="font-medium text-gray-900">{optimizationStats.loadedReports}/{optimizationStats.totalReports}</div>
                                    <div className="text-gray-500 text-xs">Cargados</div>
                                </div>
                            </div>
                            <div className="flex items-center space-x-2">
                                <span className="text-purple-600 text-lg">💾</span>
                                <div>
                                    <div className="font-medium text-gray-900">{optimizationStats.cachedReports}</div>
                                    <div className="text-gray-500 text-xs">Cacheados</div>
                                </div>
                            </div>
                            {optimizationStats.loadingReports > 0 && (
                                <div className="flex items-center space-x-2">
                                    <span className="text-blue-600 text-lg">🔄</span>
                                    <div>
                                        <div className="font-medium text-gray-900">{optimizationStats.loadingReports}</div>
                                        <div className="text-gray-500 text-xs">Cargando</div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Barra de progreso de optimización */}
                    <div className="mt-4 bg-gray-200 rounded-full h-2">
                        <div
                            className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all duration-1000 ease-out"
                            style={{ width: `${Math.round((optimizationStats.loadedReports / optimizationStats.totalReports) * 100)}%` }}
                        ></div>
                    </div>
                    <p className="mt-2 text-sm text-gray-600 text-center">
                        Optimización activa: {Math.round((optimizationStats.loadedReports / optimizationStats.totalReports) * 100)}% de reportes disponibles
                    </p>
                </div>

                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
                        <div className="flex items-center justify-between">
                            <p className="text-red-800">{error}</p>
                                <button
                                    onClick={() => {
                                        setError(null);
                                        // Limpiar reportes cargados para permitir recarga
                                        setLoadedReports(new Set());
                                        setReportes({});
                                    }}
                                    className="ml-4 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                                >
                                    Limpiar
                                </button>
                        </div>
                    </div>
                )}



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
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-2xl font-bold text-gray-900">
                                        {reportes[report.id] ? getReportTotal(reportes[report.id]) : 0}
                                    </p>
                                    <div className="flex items-center space-x-2">
                                        {loading[report.id] && (
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                        )}
                                        {loadedReports.has(report.id) && !loading[report.id] && (
                                            <span className="text-green-500 text-xs" title="Datos cargados">✅</span>
                                        )}
                                        {isCacheValid(report.id) && !loading[report.id] && (
                                            <span className="text-purple-500 text-xs" title="Datos cacheados">💾</span>
                                        )}
                                        {error && error.includes(reportTypes.find(r => r.id === report.id)?.title || '') && !loading[report.id] && (
                                            <span className="text-red-500 text-xs" title="Error al cargar">⚠️</span>
                                        )}
                                    </div>
                                </div>

                                {/* Indicadores de estado detallados */}
                                <div className="flex flex-wrap gap-1">
                                    {loading[report.id] && (
                                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                                            🔄 Cargando...
                                        </span>
                                    )}
                                    {loadedReports.has(report.id) && !loading[report.id] && (
                                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                                            ✅ Listo
                                        </span>
                                    )}
                                    {isCacheValid(report.id) && !loading[report.id] && (
                                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
                                            💾 Cacheado
                                        </span>
                                    )}
                                    {report.id === 'usuarios-activos' && (
                                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-orange-100 text-orange-800 rounded-full">
                                            ⏱️ Timeout extendido
                                        </span>
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
                                
                                {/* Botón de reintento individual si hay error */}
                                {error && error.includes(reportTypes.find(r => r.id === report.id)?.title || '') && (
                                    <button
                                        onClick={() => {
                                            setError(null);
                                            loadReporte(report.id);
                                        }}
                                        className="ml-2 px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200"
                                        title="Reintentar este reporte"
                                    >
                                        🔄
                                    </button>
                                )}
                                
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
