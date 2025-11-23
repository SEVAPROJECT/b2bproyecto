import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MainLayout } from '../../components/layouts';
import Button from '../../components/ui/Button';
import { buildApiUrl } from '../../config/api';

const SimpleResetPasswordPage: React.FC = () => {
    
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [isSubmitted, setIsSubmitted] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const response = await fetch(buildApiUrl('/password-reset-native/request'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: email.trim() }),
            });

            const data = await response.json();

            if (data.success) {
                setSuccess(data.message);
                setIsSubmitted(true);
            } else {
                setError(data.message || 'Error enviando el email de restablecimiento');
            }
        } catch (_error_) {
            setError('Error de conexión. Inténtalo nuevamente.');
        } finally {
            setLoading(false);
        }
    };

    const handleResend = async () => {
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const response = await fetch(buildApiUrl('/password-reset-native/request'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: email.trim() }),
            });

            const data = await response.json();

            if (data.success) {
                setSuccess('Email reenviado exitosamente');
            } else {
                setError(data.message || 'Error reenviando el email');
            }
        } catch (_error_) {
            setError('Error de conexión. Inténtalo nuevamente.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <MainLayout>
            <div className="min-h-screen flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
                <div className="max-w-md w-full space-y-8">
                    {/* Header */}
                    <div className="text-center">
                        <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-100">
                            <svg className="h-6 w-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                            </svg>
                        </div>
                        <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900">
                            {isSubmitted ? 'Email enviado' : 'Restablecer contraseña'}
                        </h2>
                        <p className="mt-2 text-center text-sm text-slate-600">
                            {isSubmitted
                                ? 'Te hemos enviado un email con un enlace para restablecer tu contraseña.'
                                : 'Ingresa tu email y te enviaremos un enlace para restablecer tu contraseña.'
                            }
                        </p>
                    </div>

                    {/* Mensajes de error y éxito */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-md p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm text-red-800">{error}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {success && (
                        <div className="bg-green-50 border border-green-200 rounded-md p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm text-green-800">{success}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Formulario */}
                    {isSubmitted ? (
                        <div className="mt-8 text-center space-y-4">
                            <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-green-100">
                                <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            
                            <div>
                                <p className="text-lg font-medium text-slate-900 mb-2">
                                    ¡Email enviado exitosamente!
                                </p>
                                <p className="text-sm text-slate-600">
                                    Revisa tu bandeja de entrada y sigue las instrucciones para restablecer tu contraseña.
                                </p>
                            </div>

                            <div className="space-y-2">
                                <Button
                                    variant="secondary"
                                    onClick={handleResend}
                                    disabled={loading}
                                    className="w-full"
                                >
                                    {loading ? 'Reenviando...' : '¿No recibiste el email? Reenviar'}
                                </Button>
                                
                                <Button
                                    variant="ghost"
                                    onClick={() => {
                                        setIsSubmitted(false);
                                        setEmail('');
                                        setError('');
                                        setSuccess('');
                                    }}
                                    className="w-full"
                                >
                                    Intentar con otro email
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-slate-700">
                                    Correo electrónico
                                </label>
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    autoComplete="email"
                                    required
                                    className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-slate-300 placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                                    placeholder="tu@email.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>

                            <Button
                                type="submit"
                                variant="primary"
                                className="w-full"
                                disabled={loading}
                            >
                                {loading ? 'Enviando...' : 'Enviar enlace de restablecimiento'}
                            </Button>
                        </form>
                    )}

                    {/* Navegación */}
                    <div className="text-center">
                        <Link
                            to="/login"
                            className="text-primary-600 hover:text-primary-500 text-sm"
                        >
                            ← Volver al inicio de sesión
                        </Link>
                    </div>
                </div>
            </div>
        </MainLayout>
    );
};

export default SimpleResetPasswordPage;
