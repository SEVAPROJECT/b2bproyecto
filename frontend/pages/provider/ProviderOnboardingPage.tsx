import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui';
import { ClockIcon, CheckCircleIcon } from '../../components/icons';
import { AddressSelector } from '../../components/AddressSelector';
import { providersAPI, adminAPI } from '../../services/api';
import { ProviderOnboardingData } from '../../types/provider';
import { locationsAPI, Departamento, Ciudad, Barrio } from '../../services/locations';
import { buildApiUrl } from '../../config/api';

// Debug: verificar que providersAPI se importa correctamente
console.log('🔍 providersAPI importado:', providersAPI);
console.log('🔍 Métodos disponibles en providersAPI:', Object.keys(providersAPI));

// Funciones temporales para debuggear
const testDatos = async (accessToken: string) => {
    try {
        console.log(`🧪 Probando endpoint de datos...`);
        const response = await fetch(buildApiUrl('/providers/test-datos'), {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ Datos de prueba obtenidos:', result);
        return result;
    } catch (error) {
        console.error('❌ Error en testDatos:', error);
        throw error;
    }
};

const getMisDatosSolicitud = async (accessToken: string) => {
    try {
        console.log(`📋 Obteniendo datos de solicitud del proveedor...`);
        const response = await fetch(buildApiUrl('/providers/mis-datos-solicitud'), {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ Datos de solicitud del proveedor obtenidos:', result);
        return result;
    } catch (error) {
        console.error('❌ Error en getMisDatosSolicitud:', error);
        throw error;
    }
};

// Función para probar la autenticación
const debugAuth = async (accessToken: string) => {
    try {
        console.log(`🔐 Probando autenticación...`);
        const response = await fetch(buildApiUrl(`/providers/debug-auth?token=${encodeURIComponent(accessToken)}`));

        const result = await response.json();
        console.log('🔐 Resultado de debug auth:', result);
        return result;
    } catch (error) {
        console.error('❌ Error en debug auth:', error);
        throw error;
    }
};

// Función para probar documento específico
const testDocumento = async (documentoId: number) => {
    try {
        console.log(`📄 Probando documento ${documentoId}...`);
        const response = await fetch(buildApiUrl(`/providers/test-documento/${documentoId}`));

        const result = await response.json();
        console.log('📄 Resultado de test documento:', result);
        return result;
    } catch (error) {
        console.error('❌ Error en test documento:', error);
        throw error;
    }
};

// Función para probar endpoint de diagnóstico
const testDiagnostic = async () => {
    try {
        console.log(`🔧 Probando endpoint de diagnóstico...`);
        const response = await fetch(buildApiUrl('/providers/diagnostic'));

        const result = await response.json();
        console.log('🔧 Resultado de diagnóstico:', result);
        return result;
    } catch (error) {
        console.error('❌ Error en diagnóstico:', error);
        throw error;
    }
};


// Datos iniciales para el onboarding de proveedor
const initialOnboardingData: ProviderOnboardingData = {
    company: {
        tradeName: '',
    },
    address: {
        department: '',
        city: '',
        neighborhood: '',
        street: '',
        number: '',
        reference: '',
        coords: null,
    },
    branch: {
        name: '',
        phone: '',
        email: '',
        useFiscalAddress: true,
    },
    documents: {
        'ruc': { id: 'ruc', name: 'Constancia de RUC', status: 'pending', isOptional: false, description: 'Constancia de Registro Único de Contribuyentes (RUC)' },
        'cedula': { id: 'cedula', name: 'Cédula MiPymes', status: 'pending', isOptional: false, description: 'Cédula MiPymes' },
        'certificado': { id: 'tributario', name: 'Certificado de Cumplimiento Tributario', status: 'pending', isOptional: false, description: 'Certificado de Cumplimiento Tributario Emitido por la SET' },
        'certificados_rubro': { id: 'certificados_rubro', name: 'Certificados del Rubro', status: 'pending', isOptional: false, description: 'Título que certifica la profesión' },
    },
};

// Componente de barra de progreso
const OnboardingProgressBar: React.FC<{ currentStep: number }> = ({ currentStep }) => {
    const steps = [
        { number: 1, title: 'Empresa' },
        { number: 2, title: 'Dirección' },
        { number: 3, title: 'Contacto' },
        { number: 4, title: 'Documentos' },
        { number: 5, title: 'Revisión' }
    ];

    return (
        <div className="flex items-center justify-between">
            {steps.map((step, index) => (
                <div key={step.number} className="flex items-center">
                    <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                        currentStep >= step.number 
                            ? 'bg-primary-600 text-white' 
                            : 'bg-slate-200 text-slate-600'
                    }`}>
                        {step.number}
                    </div>
                    <span className={`ml-2 text-sm font-medium ${
                        currentStep >= step.number ? 'text-primary-600' : 'text-slate-600'
                    }`}>
                        {step.title}
                    </span>
                    {index < steps.length - 1 && (
                        <div className={`w-16 h-0.5 mx-4 ${
                            currentStep > step.number ? 'bg-primary-600' : 'bg-slate-200'
                        }`} />
                    )}
                </div>
            ))}
        </div>
    );
};

// Componentes de pasos del onboarding
const Step1CompanyData: React.FC<{data: ProviderOnboardingData, setData: React.Dispatch<React.SetStateAction<ProviderOnboardingData>>}> = ({data, setData}) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setData(prev => ({ ...prev, company: { ...prev.company, [e.target.name]: e.target.value }}));
    };
    return (
        <form className="space-y-6">
            <h2 className="text-xl font-semibold">1. Datos de la Empresa</h2>
            <div>
                <label htmlFor="tradeName" className="block text-sm font-medium text-slate-700">Nombre de Fantasía</label>
                <input 
                    type="text" 
                    name="tradeName" 
                    id="tradeName" 
                    value={data.company.tradeName} 
                    onChange={handleChange} 
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" 
                />
            </div>
            <div>
                <label htmlFor="provider-status" className="block text-sm font-medium text-slate-700">Estado</label>
                <p id="provider-status" className="mt-1 text-sm text-slate-500 bg-slate-100 px-3 py-2 rounded-md">Pendiente de Verificación</p>
            </div>
        </form>
    );
};

const Step2Address: React.FC<{data: ProviderOnboardingData, setData: React.Dispatch<React.SetStateAction<ProviderOnboardingData>>}> = ({data, setData}) => {
    const [departamentos, setDepartamentos] = useState<Departamento[]>([]);
    const [ciudades, setCiudades] = useState<Ciudad[]>([]);
    const [barrios, setBarrios] = useState<Barrio[]>([]);

    // Cargar departamentos al montar el componente
    useEffect(() => {
        const loadDepartamentos = async () => {
            try {
                const data = await locationsAPI.getDepartamentos();
                setDepartamentos(data);
            } catch (error) {
                console.error('Error al cargar departamentos:', error);
            }
        };
        loadDepartamentos();
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setData(prev => ({ ...prev, address: { ...prev.address, [e.target.name]: e.target.value }}));
    };

    const handleAddressChange = async (address: {
        departamento: any;
        ciudad: any;
        barrio: any;
    }) => {
        setData(prev => ({
            ...prev,
            address: {
                ...prev.address,
                department: address.departamento?.nombre || '',
                city: address.ciudad?.nombre || '',
                neighborhood: address.barrio?.nombre || ''
            }
        }));

        // Cargar ciudades cuando se selecciona un departamento
        if (address.departamento?.id_departamento) {
            try {
                const ciudadesData = await locationsAPI.getCiudadesPorDepartamento(address.departamento.id_departamento);
                setCiudades(ciudadesData);
            } catch (error) {
                console.error('Error al cargar ciudades:', error);
            }
        }

        // Cargar barrios cuando se selecciona una ciudad
        if (address.ciudad?.id_ciudad) {
            try {
                const barriosData = await locationsAPI.getBarriosPorCiudad(address.ciudad.id_ciudad);
                setBarrios(barriosData);
            } catch (error) {
                console.error('Error al cargar barrios:', error);
            }
        }
    };

    // Convertir strings a objetos para el AddressSelector
    const getInitialValues = () => {
        const initialValues: any = {};
        
        // Debug específico para verificar datos de ubicación
        console.log('🚨 DEBUG AddressSelector - Datos de ubicación en el formulario:');
        console.log('   Department:', data.address.department);
        console.log('   City:', data.address.city);
        console.log('   Neighborhood:', data.address.neighborhood);
        console.log('   Departamentos disponibles:', departamentos.length);
        
        if (data.address.department) {
            // Buscar el departamento por nombre para obtener el ID
            const departamento = departamentos.find(d => d.nombre === data.address.department);
            if (departamento) {
                initialValues.departamento = departamento;
                console.log('✅ Departamento encontrado con ID:', departamento.id_departamento);
            } else {
                // Si no se encuentra, crear un objeto temporal con solo el nombre
                initialValues.departamento = { nombre: data.address.department };
                console.log('⚠️ Departamento no encontrado, usando solo nombre:', data.address.department);
            }
        }
        if (data.address.city) {
            // Buscar la ciudad por nombre para obtener el ID
            const ciudad = ciudades.find(c => c.nombre === data.address.city);
            if (ciudad) {
                initialValues.ciudad = ciudad;
            } else {
                // Si no se encuentra, crear un objeto temporal con solo el nombre
                initialValues.ciudad = { nombre: data.address.city };
            }
        }
        if (data.address.neighborhood) {
            // Buscar el barrio por nombre para obtener el ID
            const barrio = barrios.find(b => b.nombre === data.address.neighborhood);
            if (barrio) {
                initialValues.barrio = barrio;
            } else {
                // Si no se encuentra, crear un objeto temporal con solo el nombre
                initialValues.barrio = { nombre: data.address.neighborhood };
            }
        }
        
        return initialValues;
    };
    
    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold">2. Dirección Fiscal</h2>
            
            {/* Selector de ubicaciones con búsqueda en tiempo real */}
            <div className="bg-gray-50 p-4 rounded-lg border">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Ubicación</h3>
                <AddressSelector
                    onAddressChange={handleAddressChange}
                    initialValues={getInitialValues()}
                    className="mb-4"
                />
            </div>

            {/* Campos adicionales de dirección */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label htmlFor="street" className="block text-sm font-medium text-slate-700">Calle</label>
                    <input 
                        type="text" 
                        name="street" 
                        id="street" 
                        value={data.address.street} 
                        onChange={handleChange} 
                        className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" 
                        placeholder="Av. Principal" 
                    />
                </div>
                <div>
                    <label htmlFor="number" className="block text-sm font-medium text-slate-700">Número</label>
                    <input 
                        type="text" 
                        name="number" 
                        id="number" 
                        value={data.address.number} 
                        onChange={handleChange} 
                        className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" 
                        placeholder="123" 
                    />
                </div>
            </div>
            <div>
                <label htmlFor="reference" className="block text-sm font-medium text-slate-700">Referencia</label>
                <input 
                    type="text" 
                    name="reference" 
                    id="reference" 
                    value={data.address.reference} 
                    onChange={handleChange} 
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" 
                    placeholder="Entre calles X e Y" 
                />
            </div>
        </div>
    );
};

const Step3Branch: React.FC<{data: ProviderOnboardingData, setData: React.Dispatch<React.SetStateAction<ProviderOnboardingData>>}> = ({data, setData}) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setData(prev => ({ ...prev, branch: { ...prev.branch, [e.target.name]: e.target.value }}));
    };
    
    const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setData(prev => ({ ...prev, branch: { ...prev.branch, useFiscalAddress: e.target.checked }}));
    };
    
    return (
        <form className="space-y-6">
            <h2 className="text-xl font-semibold">3. Información de Contacto</h2>
            <div>
                <label htmlFor="name" className="block text-sm font-medium text-slate-700">Nombre de la Sucursal</label>
                <input 
                    type="text" 
                    name="name" 
                    id="name" 
                    value={data.branch.name} 
                    onChange={handleChange} 
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" 
                />
            </div>
            <div>
                <label htmlFor="phone" className="block text-sm font-medium text-slate-700">Teléfono</label>
                <input 
                    type="tel" 
                    name="phone" 
                    id="phone" 
                    value={data.branch.phone} 
                    onChange={handleChange} 
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" 
                />
            </div>
            <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700">Email</label>
                <input 
                    type="email" 
                    name="email" 
                    id="email" 
                    value={data.branch.email} 
                    onChange={handleChange} 
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" 
                />
            </div>
            <div className="flex items-center">
                <input 
                    type="checkbox" 
                    name="useFiscalAddress" 
                    id="useFiscalAddress" 
                    checked={data.branch.useFiscalAddress} 
                    onChange={handleCheckboxChange} 
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded" 
                />
                <label htmlFor="useFiscalAddress" className="ml-2 block text-sm text-slate-700">
                    Usar la misma dirección física
                </label>
            </div>
        </form>
    );
};

const Step4Documents: React.FC<{data: ProviderOnboardingData, setData: React.Dispatch<React.SetStateAction<ProviderOnboardingData>>}> = ({data, setData}) => {
    const [misDocumentos, setMisDocumentos] = useState<any[]>([]);
    const { user } = useAuth();

    // Cargar documentos del proveedor
    useEffect(() => {
        const loadMisDocumentos = async () => {
            if (user?.accessToken) {
                try {
                    // Usar endpoint con información completa de sucursal
                    const documentosData = await adminAPI.getVerificacionDatos(user.accessToken);
                    console.log('📋 Datos completos para documentos:', documentosData);

                    // Transformar documentos para asegurar que tipo_documento sea string
                    const documentosTransformados = (documentosData.documentos || []).map((doc: any) => ({
                        ...doc,
                        tipo_documento: String(doc.tipo_documento) // Asegurar que sea string
                    }));

                    console.log('📄 Documentos transformados:', documentosTransformados);
                    setMisDocumentos(documentosTransformados);
                } catch (error) {
                    console.log('No se pudieron cargar los documentos:', error);
                }
            }
        };

        loadMisDocumentos();
    }, [user?.accessToken]);

    const handleFileUpload = (docId: string, file: File) => {
        // Validar tamaño del archivo (máximo 10MB)
        const maxSizeInBytes = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSizeInBytes) {
            alert(`El archivo "${file.name}" es demasiado grande. El tamaño máximo permitido es de 10MB.`);
            return;
        }

        setData(prev => ({
            ...prev,
            documents: {
                ...prev.documents,
                [docId]: {
                    ...prev.documents[docId],
                    status: 'uploaded',
                    file: file,
                    url: undefined // Limpiar URL anterior al subir nuevo archivo
                }
            }
        }));
    };

    const uploadedCount = Object.values(data.documents).filter((d) => d.status === 'uploaded' && !d.isOptional).length;
    const requiredCount = Object.values(data.documents).filter((d) => !d.isOptional).length;
    const progress = (uploadedCount / requiredCount) * 100;

    // Debug: mostrar estado completo de documentos
    console.log('📋 Estado completo de documentos en Step4:', data.documents);
    console.log('📋 Mis documentos cargados:', misDocumentos);

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold">4. Documentos Requeridos</h2>
            <p className="text-slate-600">Subí los documentos necesarios para verificar tu empresa.</p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                    <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="ml-3">
                        <h3 className="text-sm font-medium text-blue-800">Información importante sobre los archivos</h3>
                        <div className="mt-2 text-sm text-blue-700">
                            <ul className="list-disc list-inside space-y-1">
                                <li>Tamaño máximo por archivo: <strong>10 MB</strong></li>
                                <li>Formatos aceptados: PDF, JPG, JPEG, PNG, DOC, DOCX</li>
                                <li>Asegúrate de que los documentos sean legibles y estén completos</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Barra de progreso */}
            <div className="bg-slate-50 p-4 rounded-lg border">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-slate-700">Progreso de documentos</span>
                    <span className="text-sm text-slate-500">{Math.round(progress)}%</span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div className="bg-primary-600 h-2.5 rounded-full" style={{width: `${progress}%`}}></div>
                </div>
                <p className="text-sm text-slate-600 mt-2">{`Completaste ${uploadedCount} de ${requiredCount} documentos obligatorios.`}</p>
            </div>
            
            <div className="space-y-4">
                {Object.entries(data.documents).map(([key, doc]) => (
                    <div key={key} className="border border-slate-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                                <div>
                                    <h3 className="font-medium text-slate-900">
                                        {doc.name} {!doc.isOptional && <span className="text-red-500">*</span>}
                                    </h3>
                                    <p className="text-sm text-slate-500">{doc.description}</p>
                                    {doc.isOptional && (
                                        <span className="inline-block mt-1 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                                            Opcional
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                                    doc.status === 'uploaded' 
                                        ? 'bg-green-100 text-green-800' 
                                        : 'bg-slate-100 text-slate-800'
                                }`}>
                                    {doc.status === 'uploaded' ? '✅ Subido' : '⏳ Pendiente'}
                                </span>
                                <div>
                                    <input
                                        type="file"
                                        accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                                        onChange={(e) => {
                                            const file = e.target.files?.[0];
                                            if (file) handleFileUpload(key, file);
                                        }}
                                        className="text-sm"
                                    />
                                    <p className="text-xs text-slate-500 mt-1">(PNG/JPG/PDF, máximo 10MB)</p>
                                </div>
                            </div>
                        </div>
                        
                        {/* Mostrar documento previamente subido */}
                        {doc.status === 'uploaded' && doc.url && (
                            <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm text-green-700">📄 Documento previamente subido</span>
                                        <button
                                            onClick={() => {
                                                console.log('🔍 Intentando ver documento:', {
                                                    docName: doc.name,
                                                    docStatus: doc.status,
                                                    docUrl: doc.url,
                                                    misDocumentosCount: misDocumentos.length
                                                });

                                                // Buscar el documento correspondiente en misDocumentos
                                                const documentoCorrespondiente = misDocumentos.find(d => {
                                                    const tipoDoc = String(d.tipo_documento || '').toLowerCase();
                                                    const docName = String(doc.name || '').toLowerCase();
                                                    return tipoDoc === docName || tipoDoc.includes(docName);
                                                });

                                                console.log('🔍 Documento correspondiente encontrado:', documentoCorrespondiente);

                                                if (documentoCorrespondiente) {
                                                    // Usar endpoint con mejor manejo de autenticación
                                                    const url = buildApiUrl(`/providers/mis-documentos/${documentoCorrespondiente.id_documento}/servir`);
                                                    const authUrl = `${url}?token=${encodeURIComponent(user.accessToken)}`;
                                                    console.log('🔗 URL de documento:', authUrl);
                                                    window.open(authUrl, '_blank');
                                                } else {
                                                    // Fallback: intentar acceder directamente a la URL del documento
                                                    console.log('⚠️ Usando fallback para abrir documento:', doc.url);
                                                    if (doc.url?.startsWith('http')) {
                                                        window.open(doc.url, '_blank');
                                                    } else {
                                                        alert('Documento no disponible para visualización');
                                                    }
                                                }
                                            }}
                                            className="text-sm text-green-600 hover:text-green-800 underline"
                                        >
                                            Ver documento
                                        </button>
                                    </div>
                                    <span className="text-xs text-green-600">Puedes reemplazarlo subiendo un nuevo archivo</span>
                                </div>

                                {/* Mostrar observaciones si existen */}
                                {doc.rejectionReason && (
                                    <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm">
                                        <span className="font-medium text-yellow-800">Observación del administrador:</span>
                                        <p className="text-yellow-700 mt-1">{doc.rejectionReason}</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Debug: mostrar información del documento */}
                        {(() => {
                            console.log(`🔍 Documento ${key}:`, {
                                name: doc.name,
                                status: doc.status,
                                hasUrl: !!doc.url,
                                url: doc.url,
                                rejectionReason: doc.rejectionReason
                            });
                            return null;
                        })()}
                    </div>
                ))}
            </div>
        </div>
    );
};

const Step5Review: React.FC<{data: ProviderOnboardingData}> = ({data}) => {
    const getDocumentStatusClasses = (status: string, isOptional: boolean): string => {
        if (status === 'uploaded') {
            return 'bg-green-100 text-green-800';
        }
        if (isOptional) {
            return 'bg-blue-100 text-blue-800';
        }
        return 'bg-red-100 text-red-800';
    };

    const getDocumentStatusText = (status: string, isOptional: boolean): string => {
        if (status === 'uploaded') {
            return '✅ Subido';
        }
        if (isOptional) {
            return '⚪ Opcional';
        }
        return '❌ Requerido';
    };

    return (
        <div className="space-y-4">
            <div className="text-center mb-6">
                <h2 className="text-xl font-semibold text-slate-900">5. Revisión Final</h2>
                <p className="text-sm text-slate-600 mt-1">Revisá toda la información antes de enviar tu solicitud</p>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Datos de la Empresa */}
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <h3 className="font-medium text-slate-900 mb-2 text-sm">🏢 Datos de la Empresa</h3>
                    <p className="text-sm text-slate-700"><strong>Nombre:</strong> {data.company.tradeName}</p>
                </div>
                
                {/* Contacto */}
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <h3 className="font-medium text-slate-900 mb-2 text-sm">📞 Contacto</h3>
                    <p className="text-sm text-slate-700"><strong>Sucursal:</strong> {data.branch.name}</p>
                    <p className="text-sm text-slate-700"><strong>Teléfono:</strong> {data.branch.phone}</p>
                    <p className="text-sm text-slate-700"><strong>Email:</strong> {data.branch.email}</p>
                </div>
            </div>
            
            {/* Dirección - Ocupa completamente el ancho */}
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <h3 className="font-medium text-slate-900 mb-2 text-sm">📍 Dirección</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-slate-700">
                    <div>
                        <p><strong>Calle:</strong> {data.address.street} {data.address.number}</p>
                        <p><strong>Barrio:</strong> {data.address.neighborhood}</p>
                    </div>
                    <div>
                        <p><strong>Ciudad:</strong> {data.address.city}</p>
                        <p><strong>Departamento:</strong> {data.address.department}</p>
                    </div>
                </div>
                {data.address.reference && (
                    <p className="text-sm text-slate-700 mt-2"><strong>Referencia:</strong> {data.address.reference}</p>
                )}
            </div>
            
            {/* Documentos - Ocupa completamente el ancho */}
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <h3 className="font-medium text-slate-900 mb-3 text-sm">📄 Documentos</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {Object.entries(data.documents).map(([key, doc]) => (
                        <div key={key} className="flex items-center justify-between py-1 px-2 bg-white rounded border">
                            <span className="text-sm text-slate-700">{doc.name}</span>
                            <span className={`px-2 py-1 text-xs rounded-full font-medium ${getDocumentStatusClasses(doc.status, doc.isOptional)}`}>
                                {getDocumentStatusText(doc.status, doc.isOptional)}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// Página principal del onboarding
const ProviderOnboardingPage: React.FC = () => {
    const [step, setStep] = useState(1);
    const [data, setData] = useState<ProviderOnboardingData>(initialOnboardingData);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { user, providerStatus, submitProviderApplication, resubmitProviderApplication } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    // Función helper para mapear documentos del backend
    const mapDocumentsFromBackend = (documentos: any[], documentosMapeados: any): any => {
        if (!documentos || !Array.isArray(documentos)) {
            console.log('⚠️ No hay documentos para mapear o no es un array');
            return documentosMapeados;
        }

        console.log('📄 Procesando documentos del backend (manual):', documentos.length);
        console.log('📄 Documentos recibidos:', documentos.map(d => ({
            id: d.id_documento,
            tipo: d.tipo_documento,
            url: d.url_archivo
        })));
        
        // Mapeo exacto según los nombres en la base de datos
        const tipoDocumentoMap: Record<string, string> = {
            // Nombres exactos de la base de datos (case-insensitive)
            'constancia de ruc': 'ruc',
            'constancia ruc': 'ruc',
            'ruc': 'ruc',
            'cédula mipymes': 'cedula',
            'cedula mipymes': 'cedula',
            'cédula mipyme': 'cedula',
            'cedula mipyme': 'cedula',
            'cedula': 'cedula',
            'cédula': 'cedula',
            'certificado de cumplimiento tributario': 'certificado',
            'certificado cumplimiento tributario': 'certificado',
            'certificado tributario': 'certificado',
            'certificado de cumplimiento': 'certificado',
            'certificados del rubro': 'certificados_rubro',
            'certificados rubro': 'certificados_rubro',
            'certificaciones del rubro': 'certificados_rubro'
        };
        
        for (const doc of documentos) {
            console.log('📄 Procesando documento individual (manual):', {
                id: doc.id_documento,
                tipo: doc.tipo_documento,
                tipo_original: doc.tipo_documento, // Mantener original para debug
                url: doc.url_archivo,
                observacion: doc.observacion
            });

            if (!doc.tipo_documento) {
                console.log('⚠️ Documento sin tipo_documento, saltando:', doc);
                continue;
            }

            const tipoDoc = doc.tipo_documento.toLowerCase().trim();
            let docKey = '';

            // Estrategia 1: Búsqueda exacta en el mapa (prioridad)
            if (tipoDocumentoMap[tipoDoc]) {
                docKey = tipoDocumentoMap[tipoDoc];
                console.log(`✅ Mapeo exacto encontrado: "${doc.tipo_documento}" -> "${docKey}"`);
            } else {
                // Estrategia 2: Búsqueda por palabras clave (fallback)
                // Constancia de RUC
                if (tipoDoc.includes('constancia') && tipoDoc.includes('ruc')) {
                    docKey = 'ruc';
                }
                // Cédula MiPymes
                else if ((tipoDoc.includes('cédula') || tipoDoc.includes('cedula')) && 
                         (tipoDoc.includes('mipymes') || tipoDoc.includes('mipyme'))) {
                    docKey = 'cedula';
                }
                // Certificado de Cumplimiento Tributario
                else if (tipoDoc.includes('certificado') && 
                        (tipoDoc.includes('cumplimiento') || tipoDoc.includes('tributario'))) {
                    docKey = 'certificado';
                }
                // Certificados del Rubro
                else if ((tipoDoc.includes('certificados') || tipoDoc.includes('certificaciones')) && 
                         tipoDoc.includes('rubro')) {
                    docKey = 'certificados_rubro';
                }
                
                if (docKey) {
                    console.log(`✅ Mapeo por palabras clave: "${doc.tipo_documento}" -> "${docKey}"`);
                } else {
                    console.log(`⚠️ No se pudo mapear el documento: "${doc.tipo_documento}" (normalizado: "${tipoDoc}")`);
                }
            }

            if (docKey && documentosMapeados[docKey]) {
                console.log(`🔍 Antes de mapear documento ${docKey}:`, {
                    url_archivo_original: doc.url_archivo,
                    url_archivo_tipo: typeof doc.url_archivo,
                    url_archivo_existe: !!doc.url_archivo
                });
                
                documentosMapeados[docKey] = {
                    ...documentosMapeados[docKey],
                    status: 'uploaded',
                    url: doc.url_archivo,
                    rejectionReason: doc.observacion || undefined
                };
                
                console.log(`✅ Documento ${docKey} mapeado como subido:`, {
                    url_asignada: documentosMapeados[docKey].url,
                    status_final: documentosMapeados[docKey].status,
                    tiene_url: !!documentosMapeados[docKey].url
                });
            } else if (docKey) {
                console.log(`⚠️ Documento mapeado a "${docKey}" pero no existe en documentosMapeados`);
            }
        }

        console.log('📄 Documentos mapeados finales:', Object.entries(documentosMapeados).map(([key, doc]: [string, any]) => ({
            key,
            name: doc.name,
            status: doc.status,
            hasUrl: !!doc.url
        })));

        return documentosMapeados;
    };

    // Estado para controlar si los datos ya se cargaron
    const [dataLoaded, setDataLoaded] = useState(false);
    const [loadingPreviousData, setLoadingPreviousData] = useState(false);
    
    // Usar useRef para rastrear si ya se procesó la navegación desde "Corregir y reenviar"
    const hasProcessedNavigationRef = React.useRef(false);
    
    // Capturar el valor inicial de location.state (solo una vez al montar)
    const shouldLoadPreviousDataRef = React.useRef(location.state?.loadPreviousData === true);

    // Cargar datos previos si es una solicitud rechazada - Mejorado para recargar automáticamente
    useEffect(() => {
        const loadRejectedData = async () => {
            // Si se navegó desde "Corregir y reenviar" y aún no se ha procesado, resetear dataLoaded
            if (shouldLoadPreviousDataRef.current && !hasProcessedNavigationRef.current) {
                console.log('🔄 Navegación desde "Corregir y reenviar" detectada, reseteando dataLoaded');
                setDataLoaded(false);
                hasProcessedNavigationRef.current = true; // Marcar como procesado
                // Salir aquí para que el efecto se vuelva a ejecutar con dataLoaded = false
                return;
            }
            
            // Cargar datos si:
            // 1. El estado es 'rejected' o 'pending'
            // 2. Hay un token de acceso disponible
            // 3. Aún no se han cargado los datos
            const shouldLoad = (providerStatus === 'rejected' || providerStatus === 'pending') && 
                              user?.accessToken && 
                              !dataLoaded;
            
            if (shouldLoad) {
                try {
                    setLoadingPreviousData(true);
                    console.log('🔄 Cargando datos de solicitud previa...');
                
                // Debug: Verificar sucursales
                try {
                    const debugResponse = await fetch(buildApiUrl('/auth/debug-sucursal'), {
                        headers: { 'Authorization': `Bearer ${user.accessToken}` }
                    });
                    const debugData = await debugResponse.json();
                    console.log('🔍 DEBUG Sucursales:', debugData);
                } catch (debugError) {
                    console.log('⚠️ Error en debug sucursales:', debugError);
                }
                
                const datosRechazados = await adminAPI.getVerificacionDatos(user.accessToken);

                    console.log('📋 Estructura completa de datosRechazados:', JSON.stringify(datosRechazados, null, 2));
                    console.log('🔍 Verificando success:', datosRechazados.success);
                    console.log('🔍 Verificando empresa:', datosRechazados.empresa);
                    console.log('📄 Documentos recibidos del endpoint:', datosRechazados.documentos);
                    console.log('📄 Nombres exactos de tipos de documento:', 
                        datosRechazados.documentos?.map((d: any) => d.tipo_documento) || []);
                    console.log('🏢 Datos de sucursal en empresa:', {
                        nombre_sucursal: datosRechazados.empresa?.nombre_sucursal,
                        nombre_fantasia: datosRechazados.empresa?.nombre_fantasia,
                        razon_social: datosRechazados.empresa?.razon_social,
                        telefono_contacto: datosRechazados.empresa?.telefono_contacto,
                        email_contacto: datosRechazados.empresa?.email_contacto
                    });

                    // Verificar si tenemos datos válidos
                    const empresaData = datosRechazados.empresa || datosRechazados;
                    console.log('🔍 Datos de empresa encontrados:', empresaData);
                    console.log('🔍 Campos disponibles en empresaData:', Object.keys(empresaData));
                    console.log('🔍 Valores específicos:', {
                        nombre_fantasia: empresaData.nombre_fantasia,
                        razon_social: empresaData.razon_social,
                        direccion: empresaData.direccion,
                        referencia: empresaData.referencia,
                        departamento: empresaData.departamento,
                        ciudad: empresaData.ciudad,
                        barrio: empresaData.barrio,
                        telefono: empresaData.telefono,
                        email: empresaData.email
                    });
                    
                    // Debug específico para verificar datos de ubicación
                    console.log('🚨 DEBUG UBICACIÓN - Datos recibidos del backend:');
                    console.log('   Departamento:', empresaData.departamento);
                    console.log('   Ciudad:', empresaData.ciudad);
                    console.log('   Barrio:', empresaData.barrio);
                    console.log('   Tipo de datos:', {
                        departamento_type: typeof empresaData.departamento,
                        ciudad_type: typeof empresaData.ciudad,
                        barrio_type: typeof empresaData.barrio
                    });

                    if (empresaData && (empresaData.nombre_fantasia || empresaData.razon_social || empresaData.direccion)) {
                        console.log('✅ Datos de solicitud rechazada cargados:', datosRechazados);

                        // Mapear datos de la empresa al formato del formulario - EXACTAMENTE COMO EN AppOriginal.tsx
                        const datosFormulario: ProviderOnboardingData = {
                            ...initialOnboardingData,
                            company: {
                                ...initialOnboardingData.company,
                                tradeName: empresaData.nombre_fantasia || empresaData.razon_social || '',
                            },
                            address: {
                                ...initialOnboardingData.address,
                                street: empresaData.direccion || '',
                                number: empresaData.direccion ?
                                    empresaData.direccion.match(/\d+/)?.[0] || '' : '',
                                reference: empresaData.referencia || '',
                                department: empresaData.departamento || '',
                                city: empresaData.ciudad || '',
                                neighborhood: empresaData.barrio || '',
                            },
                            branch: {
                                ...initialOnboardingData.branch,
                                name: empresaData.nombre_sucursal || empresaData.nombre_fantasia || empresaData.razon_social || 'Casa Matriz',
                                phone: empresaData.telefono_contacto || empresaData.telefono || '',
                                email: empresaData.email_contacto || empresaData.email || '',
                                useFiscalAddress: true,
                            },
                            documents: mapDocumentsFromBackend(
                                datosRechazados.documentos,
                                { ...initialOnboardingData.documents }
                            )
                        };

                        console.log('📄 Documentos mapeados correctamente');
                        console.log('📄 Estado final de documentos:', Object.entries(datosFormulario.documents).map(([key, doc]: [string, any]) => ({
                            key,
                            name: doc.name,
                            status: doc.status,
                            hasUrl: !!doc.url,
                            url: doc.url
                        })));
                        setData(datosFormulario);
                        setDataLoaded(true); // Marcar que los datos se cargaron
                        console.log('✅ Formulario cargado con datos de solicitud rechazada');
                    } else {
                        console.log('⚠️ No se pudieron cargar los datos de la solicitud rechazada');
                        console.log('❌ datosRechazados:', datosRechazados);
                        console.log('❌ datosRechazados.empresa:', datosRechazados?.empresa);
                        console.log('❌ empresaData:', empresaData);
                        // Marcar como cargado incluso si no hay datos para evitar reintentos infinitos
                        setDataLoaded(true);
                    }
                } catch (error) {
                    console.error('❌ Error cargando datos de solicitud rechazada:', error);
                    // Marcar como cargado para evitar reintentos infinitos en caso de error
                    setDataLoaded(true);
                } finally {
                    setLoadingPreviousData(false);
                }
            }
        };

        loadRejectedData();
    }, [providerStatus, user?.accessToken, dataLoaded]);

    // Resetear el flag de carga cuando cambia el estado del proveedor (nueva solicitud rechazada)
    // Pero solo si no se está procesando una navegación desde "Corregir y reenviar"
    useEffect(() => {
        if (providerStatus === 'rejected' && !shouldLoadPreviousDataRef.current && !hasProcessedNavigationRef.current) {
            setDataLoaded(false);
        }
    }, [providerStatus]);

    const nextStep = () => setStep(s => Math.min(s + 1, 5));
    const prevStep = () => setStep(s => Math.max(s - 1, 1));
    

    const handleSubmit = async () => {
        console.log('🔘 handleSubmit llamado');
        console.log('📊 Estado actual:', { isSubmitting, providerStatus });
        
        if (isSubmitting) {
            console.log('⚠️ Ya se está enviando, ignorando clic');
            return; // Prevenir múltiples envíos
        }
        
        try {
            console.log('✅ Iniciando envío de solicitud...');
            setIsSubmitting(true);
            
            if (providerStatus === 'rejected') {
                console.log('🔄 Reenviando solicitud rechazada...');
                await resubmitProviderApplication(data);
                alert("¡Gracias! Tu solicitud corregida ha sido enviada para revisión. Te notificaremos en un plazo máximo de 3 días hábiles.");
            } else {
                console.log('📤 Enviando nueva solicitud...');
                await submitProviderApplication(data);
                alert("¡Gracias! Tu perfil de proveedor está en revisión. Te notificaremos en un plazo máximo de 3 días hábiles.");
            }
            navigate('/dashboard');
        } catch (error) {
            console.error('❌ Error al enviar la solicitud:', error);
            const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
            alert(`Error al enviar la solicitud: ${errorMessage}. Por favor, inténtalo nuevamente.`);
        } finally {
            setIsSubmitting(false);
        }
    };

    const getSubmitButtonText = (): string => {
        if (providerStatus === 'rejected') {
            return 'Reenviar solicitud corregida';
        }
        return 'Enviar a verificación';
    };

    const renderStep = () => {
        switch (step) {
            case 1: return <Step1CompanyData data={data} setData={setData} />;
            case 2: return <Step2Address data={data} setData={setData} />;
            case 3: return <Step3Branch data={data} setData={setData} />;
            case 4: return <Step4Documents data={data} setData={setData} />;
            case 5: return <Step5Review data={data} />;
            default: return null;
        }
    };
    
    const allRequiredDocsUploaded = Object.values(data.documents).every((doc) => doc.isOptional || doc.status === 'uploaded');
    
    // Para solicitudes rechazadas que se están reenviando, permitir reenviar incluso si faltan algunos documentos
    // ya que los documentos que ya estaban subidos se mantienen
    const canSubmit = providerStatus === 'rejected' ? true : allRequiredDocsUploaded;

    // Pantalla de carga al enviar solicitud
    if (isSubmitting) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="bg-white p-8 rounded-xl shadow-md border border-slate-200 text-center max-w-md mx-auto">
                    <div className="flex justify-center mb-4">
                        <svg className="animate-spin h-12 w-12 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    </div>
                    <h2 className="text-xl font-semibold text-slate-800 mb-2">Procesando su solicitud</h2>
                    <p className="text-slate-600 mb-4">Estamos procesando su solicitud, espere un momento por favor.</p>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <p className="text-sm text-blue-700">
                            <strong>No cierres esta ventana</strong> hasta que se complete el proceso.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    // Verificar si ya hay una solicitud pendiente
    if (providerStatus === 'pending') {
        return (
            <div className="bg-white p-8 rounded-xl shadow-md border border-blue-200 text-center max-w-4xl mx-auto">
                <ClockIcon className="w-16 h-16 mx-auto text-blue-500" />
                <h2 className="mt-4 text-2xl font-bold text-slate-800">Ya tienes una solicitud en revisión</h2>
                <p className="mt-2 text-slate-600 max-w-xl mx-auto">
                    Ya has enviado una solicitud para convertirte en proveedor y está siendo revisada por nuestro equipo. 
                    No puedes enviar otra solicitud hasta que se complete la revisión.
                </p>
                <div className="mt-6">
                    <Button variant="primary" onClick={() => navigate('/dashboard')}>
                        Volver al dashboard
                    </Button>
                </div>
            </div>
        );
    }

    // Verificar si la solicitud fue aprobada
    if (providerStatus === 'approved') {
        return (
            <div className="bg-white p-8 rounded-xl shadow-md border border-green-200 text-center max-w-4xl mx-auto">
                <CheckCircleIcon className="w-16 h-16 mx-auto text-green-500" />
                <h2 className="mt-4 text-2xl font-bold text-slate-800">¡Ya eres proveedor!</h2>
                <p className="mt-2 text-slate-600 max-w-xl mx-auto">
                    Tu solicitud ya fue aprobada. Ya puedes comenzar a ofrecer tus servicios en la plataforma.
                </p>
                <div className="mt-6">
                    <Button variant="primary" onClick={() => navigate('/dashboard')}>
                        Ir al dashboard
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-md border border-slate-200/80 max-w-5xl mx-auto">
            {/* Header fijo */}
            <div className="p-6 sm:p-8 border-b border-slate-200">
                <h1 className="text-2xl font-bold text-slate-900">
                    {providerStatus === 'rejected' ? 'Corregir solicitud de proveedor' : 'Registro de Proveedor'}
                </h1>
                <p className="text-slate-500 mt-1">
                    {providerStatus === 'rejected' 
                        ? 'Corregí los puntos señalados y reenviá tu solicitud.'
                        : 'Completá los 5 pasos para empezar a ofrecer tus servicios.'
                    }
                </p>
                
                <div className="my-6">
                    <OnboardingProgressBar currentStep={step} />
                </div>
            </div>
            
            {/* Contenido con scroll */}
            <div className="p-6 sm:p-8 max-h-[70vh] overflow-y-auto">
                {/* Indicador de carga de datos previos */}
                {loadingPreviousData && (
                    <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center">
                            <svg className="animate-spin h-5 w-5 text-blue-600 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <div>
                                <p className="text-sm font-medium text-blue-800">Cargando datos de tu solicitud anterior...</p>
                                <p className="text-xs text-blue-600 mt-1">Los campos se completarán automáticamente con la información que ya enviaste.</p>
                            </div>
                        </div>
                    </div>
                )}
                
                {/* Mensaje informativo cuando los datos se cargaron */}
                {dataLoaded && providerStatus === 'rejected' && !loadingPreviousData && (
                    <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-start">
                            <CheckCircleIcon className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-green-800">Datos de tu solicitud anterior cargados</p>
                                <p className="text-xs text-green-700 mt-1">Revisá y corregí los campos según las observaciones del administrador. Los documentos que ya subiste se mantendrán si no los cambias.</p>
                            </div>
                        </div>
                    </div>
                )}
                
                {renderStep()}
            </div>
            

            {/* Botones de navegación */}
            <div className="p-6 sm:p-8 pt-0 border-t border-slate-200 bg-slate-50 rounded-b-xl">
                <div className="flex justify-between items-center">
                    <div>
                        {step > 1 && <Button variant="secondary" onClick={prevStep}>Anterior</Button>}
                    </div>
                    <div className="space-x-4">
                        <Button variant="ghost" onClick={() => alert('¡Borrador guardado!')}>Guardar borrador</Button>
                        {step < 5 && <Button variant="primary" onClick={nextStep}>Siguiente</Button>}
                        {step === 5 && <Button variant="primary" onClick={handleSubmit} disabled={!canSubmit || isSubmitting}>
                            {isSubmitting ? (
                                <div className="flex items-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Enviando solicitud...
                                </div>
                            ) : (
                                getSubmitButtonText()
                            )}
                        </Button>}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProviderOnboardingPage;