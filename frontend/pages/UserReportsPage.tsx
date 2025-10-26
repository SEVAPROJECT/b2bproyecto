import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { DocumentArrowDownIcon, EyeIcon } from '../components/icons';
import { API_CONFIG, buildApiUrl } from '../config/api';

interface ReporteData {
    total_calificaciones?: number;
    calificaciones?: any[];
    fecha_generacion: string;
}

const UserReportsPage: React.FC = () => {
    const { user } = useAuth();
    const [reportes, setReportes] = useState<{[key: string]: ReporteData}>({});
    const [loading, setLoading] = useState<{[key: string]: boolean}>({});
    const [loadedReports, setLoadedReports] = useState<Set<string>>(new Set());
    const [isProvider, setIsProvider] = useState(false);

    // Detectar si el usuario es proveedor o cliente
    useEffect(() => {
        if (user && user.role) {
            const userRole = user.role.toLowerCase();
            const provider = userRole === 'proveedor' || userRole === 'provider' || userRole === 'proveedores';
            setIsProvider(provider);
            console.log('🔍 Usuario es proveedor:', provider, 'Rol:', user.role);
        }
    }, [user]);

    // Función helper para formatear valores
    const formatValue = (value: any, fieldName?: string): string => {
        if (value === null || value === undefined || value === '') {
            if (fieldName === 'comentario') return '';
            return 'N/A';
        }

        // Detectar y formatear fechas
        const looksLikeDate = typeof value === 'string' && (
            value.includes('T') || value.includes('-') || value.includes('/') ||
            /^\d{4}-\d{2}-\d{2}/.test(value) || /^\d{2}\/\d{2}\/\d{4}/.test(value)
        );
        
        if (looksLikeDate) {
            try {
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

        return String(value);
    };

    const formatArgentinaDateTime = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            return date.toLocaleString('es-AR', {
                timeZone: 'America/Argentina/Buenos_Aires',
                hour12: false,
            });
        } catch (error) {
            return dateString;
        }
    };

    const formatArgentinaDate = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('es-AR', {
                timeZone: 'America/Argentina/Buenos_Aires',
            });
        } catch (error) {
            return dateString;
        }
    };

    // Función para generar fecha actual en ISO (la conversión a zona horaria se hace en formatArgentinaDateTime)
    const getCurrentDateISO = (): string => {
        return new Date().toISOString();
    };

    const reportTypes = isProvider ? [
        {
            id: 'mis-calificaciones-recibidas-proveedor',
            title: 'Mis Calificaciones Recibidas',
            description: 'Calificaciones que he recibido de mis clientes',
            icon: '⭐',
            color: 'blue'
        }
    ] : [
        {
            id: 'mis-calificaciones-recibidas-cliente',
            title: 'Mis Calificaciones Recibidas',
            description: 'Calificaciones que he recibido de proveedores',
            icon: '⭐',
            color: 'green'
        }
    ];

    const loadReporte = async (reportType: string) => {
        if (!user?.accessToken || loading[reportType]) {
            return;
        }

        console.log(`🚀 Cargando reporte: ${reportType}`);
        setLoading(prev => ({ ...prev, [reportType]: true }));

        try {
            const timeoutDuration = 15000; // 15 segundos
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout de carga')), timeoutDuration)
            );

            let dataPromise: Promise<ReporteData>;
            
            if (reportType === 'mis-calificaciones-recibidas-cliente') {
                // Cliente: calificaciones recibidas de proveedores
                dataPromise = (async () => {
                    console.log('⭐ Cargando calificaciones recibidas (cliente)...');
                    try {
                        const response = await fetch(buildApiUrl('/calificacion/mis-calificaciones-recibidas-cliente'), {
                            headers: { 'Authorization': `Bearer ${user.accessToken}` }
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        
                        const data = await response.json();
                        console.log('✅ Calificaciones recibidas (cliente) cargadas:', data);
                        // Asegurar fecha_generacion actualizada con hora correcta
                        return {
                            ...data,
                            fecha_generacion: getCurrentDateISO()
                        };
                    } catch (error) {
                        console.error('❌ Error cargando calificaciones recibidas (cliente):', error);
                        throw error;
                    }
                })();
            } else if (reportType === 'mis-calificaciones-recibidas-proveedor') {
                // Proveedor: calificaciones recibidas de clientes
                dataPromise = (async () => {
                    console.log('⭐ Cargando calificaciones recibidas (proveedor)...');
                    try {
                        const response = await fetch(buildApiUrl('/calificacion/mis-calificaciones-recibidas-proveedor'), {
                            headers: { 'Authorization': `Bearer ${user.accessToken}` }
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        
                        const data = await response.json();
                        console.log('✅ Calificaciones recibidas (proveedor) cargadas:', data);
                        // Asegurar fecha_generacion actualizada con hora correcta
                        return {
                            ...data,
                            fecha_generacion: getCurrentDateISO()
                        };
                    } catch (error) {
                        console.error('❌ Error cargando calificaciones recibidas (proveedor):', error);
                        throw error;
                    }
                })();
            } else {
                throw new Error('Tipo de reporte no válido');
            }

            const data = await Promise.race([dataPromise, timeoutPromise]);
            console.log(`Reporte ${reportType} cargado exitosamente:`, data);

            setReportes(prev => ({ ...prev, [reportType]: data as ReporteData }));
            setLoadedReports(prev => new Set(prev).add(reportType));
        } catch (err: any) {
            console.error(`❌ Error cargando reporte ${reportType}:`, err);
        } finally {
            setLoading(prev => ({ ...prev, [reportType]: false }));
        }
    };

    const viewAllData = async (reportType: string) => {
        if (!loadedReports.has(reportType)) {
            await loadReporte(reportType);
        }
        
        const reporte = reportes[reportType];
        if (!reporte || !reporte.calificaciones || reporte.calificaciones.length === 0) return;

        const reportInfo = reportTypes.find(r => r.id === reportType);
        if (!reportInfo) return;

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
                    table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        margin-top: 20px;
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
                    }
                    tr:nth-child(even) {
                        background-color: #f9fafb;
                    }
                    .btn {
                        background-color: #3b82f6;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        margin: 10px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 ${reportInfo.title}</h1>
                    <div class="info">
                        <p><strong>📅 Fecha de generación:</strong> ${formatArgentinaDateTime(reporte.fecha_generacion)}</p>
                        <p><strong>📈 Total de registros:</strong> ${reporte.calificaciones.length}</p>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                ${Object.keys(reporte.calificaciones[0]).map(key => {
                                    let headerName = key.replace(/_/g, ' ').toUpperCase();
                                    if (key === 'fecha') headerName = 'FECHA';
                                    if (key === 'servicio') headerName = 'SERVICIO';
                                    if (key === 'proveedor_empresa') headerName = 'PROVEEDOR (EMPRESA)';
                                    if (key === 'proveedor_persona') headerName = 'PROVEEDOR (PERSONA)';
                                    if (key === 'cliente_persona') headerName = 'CLIENTE (PERSONA)';
                                    if (key === 'cliente_empresa') headerName = 'CLIENTE (EMPRESA)';
                                    if (key === 'puntaje') headerName = 'PUNTAJE (1-5)';
                                    if (key === 'nps') headerName = 'NPS (1-10)';
                                    if (key === 'comentario') headerName = 'COMENTARIO';
                                    return `<th>${headerName}</th>`;
                                }).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${reporte.calificaciones.map(item => 
                                `<tr>${Object.entries(item).map(([key, value]) => 
                                    `<td>${formatValue(value, key)}</td>`
                                ).join('')}</tr>`
                            ).join('')}
                        </tbody>
                    </table>
                    <div style="text-align: center; margin-top: 20px;">
                        <button class="btn" onclick="window.print()">🖨️ Imprimir</button>
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
        if (!reporte || !reporte.calificaciones) return;

        const reportInfo = reportTypes.find(r => r.id === reportType);
        if (!reportInfo) return;

        let htmlContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>${reportInfo.title}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #1f2937; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { border: 1px solid #d1d5db; padding: 8px; text-align: left; }
                    th { background: #f9fafb; font-weight: bold; }
                </style>
            </head>
            <body>
                <h1>SEVA Empresas - ${reportInfo.title}</h1>
                <p>Generado el: ${formatArgentinaDateTime(reporte.fecha_generacion)}</p>
                <p><strong>Total: ${reporte.total_calificaciones || reporte.calificaciones.length}</strong></p>
                <table>
                    <thead>
                        <tr>
                            ${Object.keys(reporte.calificaciones[0] || {}).map(key => {
                                let headerName = key.replace(/_/g, ' ').toUpperCase();
                                if (key === 'fecha') headerName = 'FECHA';
                                if (key === 'servicio') headerName = 'SERVICIO';
                                if (key === 'proveedor_empresa') headerName = 'PROVEEDOR (EMPRESA)';
                                if (key === 'proveedor_persona') headerName = 'PROVEEDOR (PERSONA)';
                                if (key === 'cliente_persona') headerName = 'CLIENTE (PERSONA)';
                                if (key === 'cliente_empresa') headerName = 'CLIENTE (EMPRESA)';
                                if (key === 'puntaje') headerName = 'PUNTAJE (1-5)';
                                if (key === 'nps') headerName = 'NPS (1-10)';
                                if (key === 'comentario') headerName = 'COMENTARIO';
                                return `<th>${headerName}</th>`;
                            }).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${reporte.calificaciones.map(item => 
                            `<tr>${Object.entries(item).map(([key, value]) => 
                                `<td>${formatValue(value, key)}</td>`
                            ).join('')}</tr>`
                        ).join('')}
                    </tbody>
                </table>
            </body>
            </html>
        `;

        const printWindow = window.open('', '_blank');
        if (printWindow) {
            printWindow.document.write(htmlContent);
            printWindow.document.close();
            printWindow.print();
        }
    };

    const renderReportData = (reportType: string) => {
        const reporte = reportes[reportType];
        if (!reporte || !reporte.calificaciones || reporte.calificaciones.length === 0) {
            return <p className="text-gray-500">No hay calificaciones disponibles</p>;
        }

        const data = reporte.calificaciones.slice(0, 10);

        return (
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            {Object.keys(data[0]).map((key) => {
                                let headerName = key.replace(/_/g, ' ');
                                if (key === 'fecha') headerName = 'FECHA';
                                if (key === 'servicio') headerName = 'SERVICIO';
                                if (key === 'proveedor_empresa') headerName = 'PROVEEDOR (EMPRESA)';
                                if (key === 'proveedor_persona') headerName = 'PROVEEDOR (PERSONA)';
                                if (key === 'cliente_persona') headerName = 'CLIENTE (PERSONA)';
                                if (key === 'cliente_empresa') headerName = 'CLIENTE (EMPRESA)';
                                if (key === 'puntaje') headerName = 'PUNTAJE (1-5)';
                                if (key === 'nps') headerName = 'NPS (1-10)';
                                if (key === 'comentario') headerName = 'COMENTARIO';
                                
                                return (
                                    <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        {headerName}
                                    </th>
                                );
                            })}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {data.map((item, index) => (
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
                {reporte.calificaciones.length > 10 && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-800">
                            <strong>Vista previa:</strong> Mostrando 10 de {reporte.calificaciones.length} registros.
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
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">Mis Reportes</h1>
                    <p className="mt-2 text-gray-600">
                        {isProvider ? 'Consulta las calificaciones que has recibido de tus clientes' : 'Consulta las calificaciones que has recibido de proveedores'}
                    </p>
                </div>

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
                                        {reportes[report.id]?.total_calificaciones ?? 0}
                                    </p>
                                    {loading[report.id] && (
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                    )}
                                </div>
                                <p className="text-sm text-gray-500">Total de calificaciones</p>
                            </div>

                            <div className="flex space-x-2">
                                <button
                                    onClick={async () => {
                                        if (!reportes[report.id]) {
                                            await loadReporte(report.id);
                                        }
                                        // Siempre abrir reporte completo después de cargar
                                        setTimeout(() => viewAllData(report.id), 100);
                                    }}
                                    disabled={loading[report.id]}
                                    className="flex-1 flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                                >
                                    <EyeIcon className="w-4 h-4 mr-2" />
                                    {loading[report.id] ? 'Cargando...' : 'Ver Reporte'}
                                </button>
                                
                                <button
                                    onClick={async () => {
                                        if (!reportes[report.id]) {
                                            await loadReporte(report.id);
                                        }
                                        setTimeout(() => generatePDF(report.id), 100);
                                    }}
                                    disabled={loading[report.id]}
                                    className="flex-1 flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                                    PDF
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default UserReportsPage;

