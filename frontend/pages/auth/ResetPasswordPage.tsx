import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MainLayout } from '../../components/layouts';
import Button from '../../components/ui/Button';
import { EyeIcon, EyeSlashIcon } from '../../components/icons';
import { buildApiUrl } from '../../config/api';

// Tipos para el flujo de restablecimiento
type ResetStep = 'email' | 'code' | 'new-password' | 'success';

interface ResetState {
    step: ResetStep;
    email: string;
    code: string;
    newPassword: string;
    confirmPassword: string;
    loading: boolean;
    error: string;
    success: string;
    codeExpiresIn: number;
    remainingAttempts: number;
    codeVerified: boolean; // Nuevo campo para mantener el estado de verificación
}

const ResetPasswordPage: React.FC = () => {
    const navigate = useNavigate();
    const [state, setState] = useState<ResetState>({
        step: 'email',
        email: '',
        code: '',
        newPassword: '',
        confirmPassword: '',
        loading: false,
        error: '',
        success: '',
        codeExpiresIn: 0,
        remainingAttempts: 3,
        codeVerified: false
    });
    const [newPasswordVisible, setNewPasswordVisible] = useState(false);
    const [confirmPasswordVisible, setConfirmPasswordVisible] = useState(false);

    // Timer para el código de expiración - solo corre si no está verificado
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (state.step === 'code' && state.codeExpiresIn > 0 && !state.codeVerified) {
            interval = setInterval(() => {
                setState(prev => ({
                    ...prev,
                    codeExpiresIn: Math.max(0, prev.codeExpiresIn - 1)
                }));
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [state.step, state.codeExpiresIn, state.codeVerified]);

    // Función para validar contraseña
    const validatePassword = (password: string) => {
        const hasMinLength = password.length >= 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>\/?]/.test(password);
        
        return {
            isValid: hasMinLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar,
            hasMinLength,
            hasUpperCase,
            hasLowerCase,
            hasNumber,
            hasSpecialChar
        };
    };

    const updateState = (updates: Partial<ResetState>) => {
        setState(prev => ({ ...prev, ...updates }));
    };

    const clearError = () => {
        updateState({ error: '' });
    };

    // Paso 1: Solicitar código
    const handleRequestCode = async (e: React.FormEvent) => {
        e.preventDefault();
        clearError();
        updateState({ loading: true });

        try {
            const response = await fetch(buildApiUrl('/password-reset-direct/request'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: state.email }),
            });

            const data = await response.json();

            if (data.success) {
                updateState({
                    step: 'code',
                    loading: false,
                    success: 'Código enviado exitosamente',
                    codeExpiresIn: data.expires_in_seconds || 60
                });
            } else {
                updateState({
                    loading: false,
                    error: data.message || 'Error enviando el código'
                });
            }
        } catch (_error_) {
            updateState({
                loading: false,
                error: 'Error de conexión. Inténtalo nuevamente.'
            });
        }
    };

    // Paso 2: Verificar código
    const handleVerifyCode = async (e: React.FormEvent) => {
        e.preventDefault();
        clearError();

        if (state.code.length !== 4) {
            updateState({ error: 'El código debe tener 4 dígitos' });
            return;
        }

        // Verificar si el código ha expirado
        if (state.codeExpiresIn === 0 && !state.codeVerified) {
            updateState({ error: 'El código ha expirado. Solicita un nuevo código.' });
            return;
        }

        updateState({ loading: true });

        try {
            const response = await fetch(buildApiUrl('/password-reset-direct/verify-code'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: state.email,
                    code: state.code
                }),
            });

            const data = await response.json();

            if (data.success) {
                updateState({
                    step: 'new-password',
                    loading: false,
                    success: 'Código verificado correctamente',
                    codeExpiresIn: 0, // Detener el timer cuando el código es correcto
                    codeVerified: true // Marcar el código como verificado
                });
            } else {
                updateState({
                    loading: false,
                    error: data.message || 'Código incorrecto',
                    remainingAttempts: data.remaining_attempts || 0
                });
            }
        } catch (_error_) {
            updateState({
                loading: false,
                error: 'Error de conexión. Inténtalo nuevamente.'
            });
        }
    };

    // Paso 3: Establecer nueva contraseña
    const handleSetNewPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        clearError();

        if (state.newPassword !== state.confirmPassword) {
            updateState({ error: 'Las contraseñas no coinciden' });
            return;
        }

        const passwordValidation = validatePassword(state.newPassword);
        if (!passwordValidation.isValid) {
            updateState({ error: 'La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula, un número y un símbolo especial' });
            return;
        }

        updateState({ loading: true });

        try {
            // Si el código ya fue verificado, no lo enviamos al backend
            const requestBody = state.codeVerified 
                ? {
                    email: state.email,
                    new_password: state.newPassword,
                    confirm_password: state.confirmPassword
                }
                : {
                    email: state.email,
                    code: state.code,
                    new_password: state.newPassword,
                    confirm_password: state.confirmPassword
                };

            const response = await fetch(buildApiUrl('/password-reset-direct/set-new-password'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();

            if (data.success) {
                updateState({
                    step: 'success',
                    loading: false,
                    success: data.message
                });
            } else {
                updateState({
                    loading: false,
                    error: data.message || 'Error actualizando la contraseña'
                });
            }
        } catch (_error_) {
            updateState({
                loading: false,
                error: 'Error de conexión. Inténtalo nuevamente.'
            });
        }
    };

    // Solicitar nuevo código
    const handleResendCode = async () => {
        clearError();
        updateState({ loading: true });

        try {
            const response = await fetch(buildApiUrl('/password-reset-direct/request'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: state.email }),
            });

            const data = await response.json();

            if (data.success) {
                updateState({
                    loading: false,
                    success: 'Nuevo código enviado',
                    codeExpiresIn: data.expires_in_seconds || 60,
                    remainingAttempts: 3,
                    codeVerified: false // Resetear el estado de verificación
                });
            } else {
                updateState({
                    loading: false,
                    error: data.message || 'Error enviando el código'
                });
            }
        } catch (_error_) {
            updateState({
                loading: false,
                error: 'Error de conexión. Inténtalo nuevamente.'
            });
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
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
                            {state.step === 'email' && 'Restablecer contraseña'}
                            {state.step === 'code' && 'Verificar código'}
                            {state.step === 'new-password' && 'Nueva contraseña'}
                            {state.step === 'success' && '¡Listo!'}
                        </h2>
                        <p className="mt-2 text-center text-sm text-slate-600">
                            {state.step === 'email' && 'Ingresa tu email y te enviaremos un código de verificación.'}
                            {state.step === 'code' && `Ingresa el código de 4 dígitos enviado a ${state.email}`}
                            {state.step === 'new-password' && 'Establece tu nueva contraseña'}
                            {state.step === 'success' && 'Tu contraseña ha sido actualizada exitosamente'}
                        </p>
                    </div>

                    {/* Mensajes de error y éxito */}
                    {state.error && (
                        <div className="bg-red-50 border border-red-200 rounded-md p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm text-red-800">{state.error}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {state.success && (
                        <div className="bg-green-50 border border-green-200 rounded-md p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm text-green-800">{state.success}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Paso 1: Solicitar email */}
                    {state.step === 'email' && (
                        <form className="mt-8 space-y-6" onSubmit={handleRequestCode}>
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
                                    value={state.email}
                                    onChange={(e) => updateState({ email: e.target.value })}
                                />
                            </div>

                            <Button
                                type="submit"
                                variant="primary"
                                className="w-full"
                                disabled={state.loading}
                            >
                                {state.loading ? 'Enviando...' : 'Solicitar código'}
                            </Button>
                        </form>
                    )}

                    {/* Paso 2: Verificar código */}
                    {state.step === 'code' && (
                        <form className="mt-8 space-y-6" onSubmit={handleVerifyCode}>
                            <div>
                                <label htmlFor="code" className="block text-sm font-medium text-slate-700">
                                    Código de verificación
                                </label>
                                <input
                                    id="code"
                                    name="code"
                                    type="text"
                                    maxLength={4}
                                    required
                                    className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-slate-300 placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm text-center text-2xl tracking-widest"
                                    placeholder="1234"
                                    value={state.code}
                                    onChange={(e) => updateState({ code: e.target.value.replaceAll(/\D/g, '') })}
                                />
                                <p className="mt-2 text-sm text-slate-500">
                                    Código de 4 dígitos enviado a {state.email}
                                </p>
                            </div>

                            {/* Timer de expiración - solo mostrar si no está verificado */}
                            {state.codeExpiresIn > 0 && !state.codeVerified && (
                                <div className="text-center">
                                    <p className="text-sm text-slate-600">
                                        El código expira en: <span className="font-mono font-bold text-primary-600">{formatTime(state.codeExpiresIn)}</span>
                                    </p>
                                </div>
                            )}

                            {/* Mensaje cuando el código fue verificado */}
                            {state.codeVerified && (
                                <div className="text-center">
                                    <p className="text-sm text-green-600 font-medium">
                                        ✅ Código verificado correctamente
                                    </p>
                                </div>
                            )}

                            {/* Código expirado - solo mostrar si no está verificado */}
                            {state.codeExpiresIn === 0 && !state.codeVerified && (
                                <div className="text-center">
                                    <p className="text-sm text-red-600 mb-2">El código ha expirado</p>
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        onClick={handleResendCode}
                                        disabled={state.loading}
                                    >
                                        {state.loading ? 'Enviando...' : 'Solicitar nuevo código'}
                                    </Button>
                                </div>
                            )}

                            {(state.codeExpiresIn > 0 || state.codeVerified) && (
                                <Button
                                    type="submit"
                                    variant="primary"
                                    className="w-full"
                                    disabled={state.loading || state.code.length !== 4 || (state.codeExpiresIn === 0 && !state.codeVerified)}
                                >
                                    {state.loading ? 'Verificando...' : 'Verificar código'}
                                </Button>
                            )}

                            <div className="text-center">
                                <Button
                                    type="button"
                                    variant="ghost"
                                    onClick={handleResendCode}
                                    disabled={state.loading}
                                >
                                    ¿No recibiste el código? Reenviar
                                </Button>
                            </div>
                        </form>
                    )}

                    {/* Paso 3: Nueva contraseña */}
                    {state.step === 'new-password' && (
                        <form className="mt-8 space-y-6" onSubmit={handleSetNewPassword}>
                            <div>
                                <label htmlFor="newPassword" className="block text-sm font-medium text-slate-700">
                                    Nueva contraseña
                                </label>
                                <div className="relative">
                                    <input
                                        id="newPassword"
                                        name="newPassword"
                                        type={newPasswordVisible ? "text" : "password"}
                                        required
                                        className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 pr-12 border border-slate-300 placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                                        placeholder="Mín. 8 caracteres, mayúscula, minúscula, número y símbolo"
                                        value={state.newPassword}
                                        onChange={(e) => updateState({ newPassword: e.target.value })}
                                    />
                                    <button 
                                        type="button" 
                                        onClick={() => setNewPasswordVisible(!newPasswordVisible)}
                                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-700 transition-colors duration-200 touch-manipulation min-h-[44px] min-w-[44px]"
                                        aria-label={newPasswordVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
                                    >
                                        {newPasswordVisible ? (
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

                            <div>
                                <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700">
                                    Confirmar nueva contraseña
                                </label>
                                <div className="relative">
                                    <input
                                        id="confirmPassword"
                                        name="confirmPassword"
                                        type={confirmPasswordVisible ? "text" : "password"}
                                        required
                                        className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 pr-12 border border-slate-300 placeholder-slate-400 text-slate-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                                        placeholder="Repite tu nueva contraseña"
                                        value={state.confirmPassword}
                                        onChange={(e) => updateState({ confirmPassword: e.target.value })}
                                    />
                                    <button 
                                        type="button" 
                                        onClick={() => setConfirmPasswordVisible(!confirmPasswordVisible)}
                                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-700 transition-colors duration-200 touch-manipulation min-h-[44px] min-w-[44px]"
                                        aria-label={confirmPasswordVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
                                    >
                                        {confirmPasswordVisible ? (
                                            <EyeSlashIcon className="h-5 w-5" /> 
                                        ) : (
                                            <EyeIcon className="h-5 w-5" />
                                        )}
                                    </button>
                                </div>
                            </div>

                            <Button
                                type="submit"
                                variant="primary"
                                className="w-full"
                                disabled={state.loading || !state.newPassword || !state.confirmPassword}
                            >
                                {state.loading ? 'Actualizando...' : 'Actualizar contraseña'}
                            </Button>
                        </form>
                    )}

                    {/* Paso 4: Éxito */}
                    {state.step === 'success' && (
                        <div className="mt-8 text-center space-y-6">
                            <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-green-100">
                                <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            
                            <div>
                                <p className="text-lg font-medium text-slate-900 mb-2">
                                    ¡Contraseña actualizada exitosamente!
                                </p>
                                <p className="text-sm text-slate-600">
                                    Ahora podés iniciar sesión con tu nueva contraseña.
                                </p>
                            </div>

                            <Button
                                variant="primary"
                                className="w-full"
                                onClick={() => navigate('/login')}
                            >
                                Ir al inicio de sesión
                            </Button>
                        </div>
                    )}

                    {/* Navegación */}
                    {state.step !== 'success' && (
                        <div className="text-center">
                            <Link
                                to="/login"
                                className="text-primary-600 hover:text-primary-500 text-sm"
                            >
                                ← Volver al inicio de sesión
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </MainLayout>
    );
};

export default ResetPasswordPage;
