import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui';
import { EyeIcon, EyeSlashIcon } from '../../components/icons';
import Alert from '../../components/ui/Alert';
import MainLayout from '../../components/layouts/MainLayout';

const RegisterPage: React.FC = () => {
    const navigate = useNavigate();
    const { register, isLoading, error } = useAuth();
    const [formData, setFormData] = useState({
        companyName: '',
        name: '',
        email: '',
        password: '',
        ruc: ''
    });
    const [passwordVisible, setPasswordVisible] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await register({ 
                companyName: formData.companyName, 
                name: formData.name, 
                email: formData.email, 
                password: formData.password,
                ruc: formData.ruc
            });
            // Mostrar mensaje de éxito y redirigir al dashboard
            alert('¡Registro exitoso! Tu cuenta es de tipo Cliente por defecto. Ahora podés convertirte en proveedor desde tu panel.');
            // Pequeña pausa para asegurar que el usuario se haya creado completamente
            setTimeout(() => {
                // Redirigir al dashboard del usuario
                navigate('/dashboard');
            }, 1000);
        } catch (err) {
            // El error ya se maneja en el contexto
            console.error('Error de registro:', err);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    return (
        <MainLayout>
            <div className="min-h-[70vh] flex items-center justify-center bg-slate-50 px-4 py-8 sm:px-6 sm:py-12">
                <div className="w-full max-w-lg p-6 sm:p-8 space-y-6 sm:space-y-8 bg-white rounded-xl sm:rounded-2xl shadow-xl border border-slate-200/80">
                    <div className="text-center">
                        <h2 className="text-xl sm:text-2xl font-bold text-slate-900">Crear cuenta de empresa</h2>
                        <p className="mt-2 text-sm sm:text-base text-slate-500">
                            ¿Ya tenés una cuenta?{' '}
                            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500 transition-colors duration-200">
                                Iniciá sesión
                            </Link>
                        </p>
                    </div>
                        
                    {error && <Alert variant="error">{error}</Alert>}

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
                                placeholder="80022614-0"
                                pattern="[0-9]{8}-[0-9]"
                                title="Formato: 8 dígitos seguidos de un guión y un dígito verificador (ej: 80022614-0)"
                            />
                            <p className="text-sm text-slate-500">
                                Formato: 8 dígitos seguidos de un guión y un dígito verificador (ej: 80022614-0)
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
                            disabled={isLoading}
                        >
                            {isLoading ? 'Creando cuenta...' : 'Crear mi cuenta'}
                        </Button>
                    </form>
                </div>
            </div>
        </MainLayout>
    );
};

export default RegisterPage;
