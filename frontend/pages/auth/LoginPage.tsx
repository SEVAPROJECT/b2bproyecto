import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { MainLayout } from '../../components/layouts';
import { Button, Alert } from '../../components/ui';

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const { login, isLoading, error } = useAuth();
    const [formData, setFormData] = useState({ email: '', password: '' });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await login(formData.email, formData.password);
            navigate('/');
        } catch (err) {
            // El error ya se maneja en el contexto
            console.error('Error de login:', err);
        }
    };

    const handleResetPassword = () => {
        navigate('/reset-password');
    };

    return (
        <MainLayout>
            <div className="min-h-[60vh] flex items-center justify-center bg-slate-50 px-4 py-8 sm:px-6 sm:py-12">
                <div className="w-full max-w-md p-6 sm:p-8 space-y-6 sm:space-y-8 bg-white rounded-xl sm:rounded-2xl shadow-xl border border-slate-200/80">
                    <div className="text-center">
                        <h2 className="text-xl sm:text-2xl font-bold text-slate-900">Iniciar sesión</h2>
                        <p className="mt-2 text-sm sm:text-base text-slate-500">
                            ¿No tenés cuenta?{' '}
                            <Link to="/register" className="font-medium text-primary-600 hover:text-primary-500 transition-colors duration-200">
                                Creá una ahora
                            </Link>
                        </p>
                    </div>
                    
                    {error && <Alert variant="error">{error}</Alert>}
                    
                    <form onSubmit={handleSubmit} className="w-full space-y-4 sm:space-y-6">
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
                                placeholder="tu@email.com"
                                required
                                autoComplete="email"
                            />
                    </div>
                        <div className="space-y-2">
                            <label htmlFor="password" className="block text-sm sm:text-base font-medium text-slate-700">
                                Contraseña
                            </label>
                            <input
                                type="password"
                                name="password"
                                id="password"
                                value={formData.password}
                                onChange={handleChange}
                                className="w-full px-3 py-2 sm:px-4 sm:py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                                placeholder="Tu contraseña"
                                required
                                autoComplete="current-password"
                            />
                        </div>
                        <div className="space-y-3">
                        <Button 
                            type="submit" 
                            variant="primary" 
                                className="w-full px-4 py-2 sm:px-6 sm:py-3 text-base sm:text-lg"
                            disabled={isLoading}
                        >
                            {isLoading ? 'Iniciando sesión...' : 'Iniciar sesión'}
                        </Button>
                        
                        <Button 
                            type="button" 
                            variant="ghost" 
                                className="w-full text-sm sm:text-base"
                            onClick={handleResetPassword}
                        >
                            Restablecer contraseña
                        </Button>
                        </div>
                    </form>
                </div>
            </div>
        </MainLayout>
    );
};

export default LoginPage;
