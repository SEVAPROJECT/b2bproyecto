import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui';
import { EyeIcon, EyeSlashIcon } from '../../components/icons';
import Alert from '../../components/ui/Alert';
import MainLayout from '../../components/layouts/MainLayout';
import { authAPI } from '../../services/api';

const RegisterPage: React.FC = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { register, isLoading, error } = useAuth();
    const [formData, setFormData] = useState({
        companyName: '',
        name: '',
        email: '',
        password: '',
        ruc: ''
    });
    const [rucDocument, setRucDocument] = useState<File | null>(null);
    const [passwordVisible, setPasswordVisible] = useState(false);
    const [showSuccessModal, setShowSuccessModal] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [processingMessage, setProcessingMessage] = useState('');
    const [isCorrigiendoRUC, setIsCorrigiendoRUC] = useState(false);
    const [tokenCorreccion, setTokenCorreccion] = useState<string | null>(null);
    const [comentarioRechazo, setComentarioRechazo] = useState<string | null>(null);
    const [cargandoDatos, setCargandoDatos] = useState(false);
    const [errorToken, setErrorToken] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        // Validar que se haya subido el documento RUC
        if (!rucDocument) {
            alert('Por favor, sube la constancia de RUC de tu empresa');
            return;
        }
        
        // Validar tamaño del archivo antes de enviar (validación adicional)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (rucDocument.size > maxSize) {
            const fileSizeMB = (rucDocument.size / 1024 / 1024).toFixed(2);
            alert(`El archivo no debe superar los 10MB. El archivo seleccionado tiene ${fileSizeMB}MB`);
            return;
        }
        
        setIsProcessing(true);
        setProcessingMessage(isCorrigiendoRUC ? 'Reenviando verificación de RUC...' : 'Creando tu cuenta...');
        
        try {
            // Si hay token, usar endpoint de reenvío
            if (isCorrigiendoRUC && tokenCorreccion) {
                setTimeout(() => setProcessingMessage('Validando tus datos...'), 1000);
                setTimeout(() => setProcessingMessage('Subiendo nuevo documento de RUC...'), 2000);
                setTimeout(() => setProcessingMessage('Finalizando corrección...'), 4000);
                
                await authAPI.reenviarVerificacionRUC(
                    tokenCorreccion,
                    formData.email,
                    formData.name,
                    formData.companyName,
                    formData.ruc || null,
                    rucDocument
                );
                
                setIsProcessing(false);
                setProcessingMessage('');
                
                // Mostrar modal de éxito
                setShowSuccessModal(true);
                // Redirigir a login después de 3 segundos automáticamente
                setTimeout(() => {
                    setShowSuccessModal(false);
                    navigate('/login');
                }, 3000);
            } else {
                // Registro normal
                setTimeout(() => setProcessingMessage('Validando tus datos...'), 1000);
                setTimeout(() => setProcessingMessage('Subiendo documento de RUC...'), 2000);
                setTimeout(() => setProcessingMessage('Finalizando registro...'), 4000);
                
                await register({ 
                    companyName: formData.companyName, 
                    name: formData.name, 
                    email: formData.email, 
                    password: formData.password,
                    ruc: formData.ruc,
                    rucDocument: rucDocument
                });
                
                setIsProcessing(false);
                setProcessingMessage('');
                
                // Mostrar modal de éxito
                setShowSuccessModal(true);
                // Redirigir a login después de 3 segundos automáticamente
                setTimeout(() => {
                    setShowSuccessModal(false);
                    navigate('/login');
                }, 3000);
            }
        } catch (err) {
            setIsProcessing(false);
            setProcessingMessage('');
            // El error ya se maneja en el contexto
            console.error('Error:', err);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    // Cargar datos si hay token en la URL
    useEffect(() => {
        const token = searchParams.get('token');
        if (token) {
            setTokenCorreccion(token);
            setIsCorrigiendoRUC(true);
            setCargandoDatos(true);
            
            // Obtener datos del usuario con el token
            authAPI.getVerificacionRUCDatos(token)
                .then((data) => {
                    if (data && data.token_valido) {
                        // Pre-cargar formulario con datos existentes
                        setFormData({
                            companyName: data.nombre_empresa || '',
                            name: data.nombre_persona || '',
                            email: data.email || '',
                            password: '', // No pre-cargar contraseña
                            ruc: data.ruc || ''
                        });
                        setComentarioRechazo(data.comentario_rechazo || null);
                        setCargandoDatos(false);
                    } else {
                        setErrorToken('Token inválido o expirado');
                        setCargandoDatos(false);
                    }
                })
                .catch((err: any) => {
                    console.error('Error cargando datos de corrección:', err);
                    setErrorToken(err.detail || 'Error al cargar los datos. El token puede haber expirado.');
                    setCargandoDatos(false);
                });
        }
    }, [searchParams]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            // Validar tipo de archivo (PDF o imagen)
            const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                alert('Por favor, sube un archivo PDF o imagen (JPG, PNG)');
                e.target.value = '';
                return;
            }
            // Validar tamaño (10MB máximo)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
                alert(`El archivo no debe superar los 10MB. El archivo seleccionado tiene ${fileSizeMB}MB`);
                e.target.value = '';
                setRucDocument(null);
                return;
            }
            setRucDocument(file);
        }
    };

    // Mostrar loading mientras se cargan los datos
    if (cargandoDatos) {
        return (
            <MainLayout>
                <div className="min-h-[70vh] flex items-center justify-center bg-slate-50 px-4 py-8 sm:px-6 sm:py-12">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                        <p className="mt-4 text-slate-600">Cargando tus datos...</p>
                    </div>
                </div>
            </MainLayout>
        );
    }

    return (
        <MainLayout>
            <div className="min-h-[70vh] flex items-center justify-center bg-slate-50 px-4 py-8 sm:px-6 sm:py-12">
                <div className="w-full max-w-lg p-6 sm:p-8 space-y-6 sm:space-y-8 bg-white rounded-xl sm:rounded-2xl shadow-xl border border-slate-200/80">
                    <div className="text-center">
                        <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                            {isCorrigiendoRUC ? 'Corregir verificación de RUC' : 'Crear cuenta de empresa'}
                        </h2>
                        <p className="mt-2 text-sm sm:text-base text-slate-500">
                            {isCorrigiendoRUC ? (
                                'Por favor, revisa y corrige los datos según el comentario del administrador'
                            ) : (
                                <>
                                    ¿Ya tenés una cuenta?{' '}
                                    <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500 transition-colors duration-200">
                                        Iniciá sesión
                                    </Link>
                                </>
                            )}
                        </p>
                    </div>
                        
                    {error && <Alert variant="error">{error}</Alert>}
                    {errorToken && <Alert variant="error">{errorToken}</Alert>}
                    
                    {isCorrigiendoRUC && comentarioRechazo && (
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                            <h3 className="text-sm font-semibold text-amber-800 mb-2">📝 Comentario del administrador:</h3>
                            <p className="text-sm text-amber-700">{comentarioRechazo}</p>
                        </div>
                    )}

                    <form className="w-full space-y-4 sm:space-y-6" onSubmit={handleSubmit}>
                        <div className="space-y-2">
                            <label htmlFor="companyName" className="block text-sm sm:text-base font-medium text-slate-700">
                                Razón social de la empresa
                            </label>
                            <input
                                type="text"
                                name="companyName"
                                id="companyName"
                                value={formData.companyName}
                                onChange={handleChange}
                                className="w-full px-3 py-2 sm:px-4 sm:py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                                placeholder="Mi Empresa S.A."
                                required
                                autoComplete="organization"
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="ruc" className="block text-sm sm:text-base font-medium text-slate-700">
                                RUC de la empresa
                            </label>
                            <input
                                type="text"
                                name="ruc"
                                id="ruc"
                                value={formData.ruc}
                                onChange={handleChange}
                                className="w-full px-3 py-2 sm:px-4 sm:py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                                placeholder="80022614-0, 3864187-8 o 123456-9"
                                pattern="[0-9]{6,8}-[0-9]"
                                title="Formato: 6 a 8 dígitos seguidos de un guión y un dígito verificador (ej: 80022614-0, 3864187-8 o 123456-9)"
                            />
                            <p className="text-sm text-slate-500">
                                Formato: 6 a 8 dígitos seguidos de un guión y un dígito verificador (ej: 80022614-0, 3864187-8 o 123456-9)
                            </p>
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="rucDocument" className="block text-sm sm:text-base font-medium text-slate-700">
                                Constancia de RUC <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="file"
                                name="rucDocument"
                                id="rucDocument"
                                accept=".pdf,.jpg,.jpeg,.png"
                                onChange={handleFileChange}
                                className="w-full px-3 py-2 sm:px-4 sm:py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                                required
                            />
                            {rucDocument && (
                                <p className="text-sm text-green-600">
                                    ✓ Archivo seleccionado: {rucDocument.name} ({(rucDocument.size / 1024 / 1024).toFixed(2)} MB)
                                </p>
                            )}
                            <p className="text-sm text-slate-500 bg-blue-50 p-3 rounded-lg border border-blue-200">
                                <strong>Importante:</strong> Debes subir la constancia de RUC de tu empresa (PDF o imagen). 
                                El archivo no debe superar los <strong>10MB</strong>. 
                                Tu cuenta será activada en un plazo máximo de 72 horas hábiles después de que nuestro equipo verifique tu documento.
                            </p>
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="name" className="block text-sm sm:text-base font-medium text-slate-700">
                                Nombre del Contacto
                            </label>
                            <input
                                type="text"
                                name="name"
                                id="name"
                                value={formData.name}
                                onChange={handleChange}
                                className="w-full px-3 py-2 sm:px-4 sm:py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                                placeholder="Juan Perez"
                                required
                                autoComplete="name"
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="email" className="block text-sm sm:text-base font-medium text-slate-700">
                                Correo electrónico
                            </label>
                            <input
                                type="email"
                                name="email"
                                id="email"
                                value={formData.email}
                                onChange={handleChange}
                                className="w-full px-3 py-2 sm:px-4 sm:py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                                placeholder="micorreo@gmail.com"
                                required
                                autoComplete="email"
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="password" className="block text-sm sm:text-base font-medium text-slate-700">
                                Contraseña
                            </label>
                            <div className="relative">
                                <input 
                                    type={passwordVisible ? "text" : "password"} 
                                    name="password" 
                                    id="password" 
                                    value={formData.password} 
                                    onChange={handleChange} 
                                    className="w-full px-3 py-2 sm:px-4 sm:py-3 pr-12 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                                    placeholder="Mín. 8 caracteres, mayúscula, minúscula, número y símbolo"
                                    minLength={8}
                                    required 
                                    autoComplete="new-password"
                                />
                                <button 
                                    type="button" 
                                    onClick={() => setPasswordVisible(!passwordVisible)}
                                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-700 transition-colors duration-200 touch-manipulation min-h-[44px] min-w-[44px]"
                                    aria-label={passwordVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
                                >
                                    {passwordVisible ? (
                                        <EyeSlashIcon className="h-5 w-5" /> 
                                    ) : (
                                        <EyeIcon className="h-5 w-5" />
                                    )}
                                </button>
                            </div>
                            <p className="mt-2 text-sm text-slate-500 bg-blue-50 p-3 rounded-lg border border-blue-200">
                                La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula, un número y un símbolo especial.
                            </p>
                        </div>

                        <Button
                            type="submit"
                            variant="primary"
                            className="w-full px-4 py-2 sm:px-6 sm:py-3 text-base sm:text-lg"
                            disabled={isLoading || isProcessing || cargandoDatos}
                        >
                            {isLoading || isProcessing ? 'Procesando...' : isCorrigiendoRUC ? 'Reenviar verificación de RUC' : 'Crear mi cuenta'}
                        </Button>
                    </form>
                </div>
            </div>

            {/* Modal de procesamiento */}
            {isProcessing && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 text-center">
                        <div className="mb-4">
                            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-primary-100">
                                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
                            </div>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            Procesando tu registro
                        </h3>
                        <p className="text-gray-600 mb-4">
                            {processingMessage || 'Por favor espera, esto puede tardar unos segundos...'}
                        </p>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                        </div>
                        <p className="text-sm text-gray-500 mt-4">
                            No cierres esta ventana
                        </p>
                    </div>
                </div>
            )}

            {/* Modal de éxito */}
            {showSuccessModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 text-center">
                        <div className="mb-4">
                            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {isCorrigiendoRUC ? 'Corrección enviada exitosamente' : 'Registro exitoso'}
                        </h3>
                        <p className="text-gray-600 mb-6">
                            {isCorrigiendoRUC 
                                ? 'Hemos recibido tu corrección. Tu solicitud será revisada nuevamente por nuestro equipo en un plazo máximo de 72 horas hábiles. Te notificaremos por email una vez que tu cuenta sea activada.'
                                : 'Tu cuenta está en proceso de verificación. Hemos recibido tu constancia de RUC y será revisada por nuestro equipo en un plazo máximo de 72 horas hábiles. Te notificaremos por email una vez que tu cuenta sea activada.'
                            }
                        </p>
                        <p className="text-sm text-gray-500 mb-4">
                            <strong>Importante:</strong> No podrás iniciar sesión hasta que tu RUC sea verificado y tu cuenta sea activada.
                        </p>
                    </div>
                </div>
            )}
        </MainLayout>
    );
};

export default RegisterPage;
