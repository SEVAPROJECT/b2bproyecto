import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserCircleIcon, PencilIcon, CameraIcon, XMarkIcon, ExclamationTriangleIcon } from '../components/icons';
import { profileAPI, adminAPI } from '../services/api';
import { API_CONFIG } from '../config/api';

const ManageProfilePage: React.FC = () => {
    const { user, reloadUserProfile, logout } = useAuth();
    const navigate = useNavigate();
    const [isEditing, setIsEditing] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [formData, setFormData] = useState({
        name: user?.name || '',
        email: user?.email || '',
        companyName: user?.companyName || ''
    });
    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [isUploadingImage, setIsUploadingImage] = useState(false);
    const [showDeactivateModal, setShowDeactivateModal] = useState(false);
    const [isDeactivating, setIsDeactivating] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Sincronizar formData cuando el usuario se carga
    useEffect(() => {
        if (user) {
            console.log('🔍 ManageProfilePage: Usuario cargado, RUC:', user.ruc);
            setFormData({
                name: user.name || '',
                email: user.email || '',
                companyName: user.companyName || ''
            });
        }
    }, [user]);

    // Función para obtener el rol en español
    const getRoleInSpanish = (role: string) => {
        switch (role?.toLowerCase()) {
            case 'admin':
                return 'Administrador';
            case 'provider':
                return 'Proveedor';
            case 'client':
                return 'Cliente';
            default:
                return 'Cliente';
        }
    };

    // Función para obtener la URL de la foto de perfil
    const getProfileImageUrl = () => {
        if (user?.foto_perfil) {
            // Si es una URL relativa, construir la URL completa
            if (user.foto_perfil.startsWith('/')) {
                // Usar la URL del backend directamente
                const apiBaseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
                const fullUrl = `${apiBaseUrl}${user.foto_perfil}`;
                return fullUrl;
            }
            return user.foto_perfil;
        }
        return null;
    };

    const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validar tipo de archivo
            if (!file.type.startsWith('image/')) {
                setError('Por favor selecciona un archivo de imagen válido');
                return;
            }

            // Validar tamaño (5MB máximo)
            if (file.size > 5 * 1024 * 1024) {
                setError('El archivo no puede ser mayor a 5MB');
                return;
            }

            setSelectedImage(file);
            
            // Crear preview
            const reader = new FileReader();
            reader.onload = (e) => {
                setImagePreview(e.target?.result as string);
            };
            reader.readAsDataURL(file);
            setError(null);
        }
    };

    const handleRemoveImage = () => {
        setSelectedImage(null);
        setImagePreview(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // Función helper para validar el token de acceso
    const validateAccessToken = (): boolean => {
        if (!user?.accessToken) {
            setError('No se encontró el token de acceso');
            return false;
        }
        return true;
    };

    // Función helper para eliminar la foto anterior de Supabase Storage
    const deletePreviousPhoto = async (photoUrl: string, accessToken: string): Promise<void> => {
        if (!photoUrl.startsWith('https://') || !photoUrl.includes('supabase.co')) {
            return;
        }

        try {
            const apiBaseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
            const deleteResponse = await fetch(`${apiBaseUrl}/api/v1/auth/delete-profile-photo?image_url=${encodeURIComponent(photoUrl)}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            if (deleteResponse.ok) {
                console.log('✅ Foto de perfil anterior eliminada del bucket de Supabase Storage');
            } else {
                console.warn('⚠️ No se pudo eliminar la foto anterior del bucket, pero se continuará con la subida');
            }
        } catch (deleteError) {
            console.warn('⚠️ Error eliminando foto anterior:', deleteError);
            // Continuar con la subida aunque falle la eliminación
        }
    };

    // Función helper para subir la nueva imagen de perfil
    const uploadProfileImage = async (image: File, accessToken: string): Promise<string> => {
        setIsUploadingImage(true);
        try {
            // Eliminar foto anterior si existe
            if (user?.foto_perfil) {
                await deletePreviousPhoto(user.foto_perfil, accessToken);
            }

            const uploadResult = await profileAPI.uploadProfilePhoto(image, accessToken);
            return uploadResult.image_path;
        } catch (uploadError: any) {
            throw new Error(uploadError.detail || 'Error al subir la imagen');
        } finally {
            setIsUploadingImage(false);
        }
    };

    // Función helper para manejar el éxito de la actualización
    const handleUpdateSuccess = async () => {
        setSuccess('Perfil actualizado exitosamente');
        setIsEditing(false);
        setSelectedImage(null);
        setImagePreview(null);
        
        // Recargar el perfil del usuario
        await reloadUserProfile();
        
        setTimeout(() => setSuccess(null), 3000);
    };

    // Función helper para manejar errores
    const handleUpdateError = (err: any) => {
        setError(err.detail || err.message || 'Error al actualizar el perfil');
        setTimeout(() => setError(null), 5000);
    };

    const handleSave = async () => {
        if (!validateAccessToken()) {
            return;
        }

        setIsLoading(true);
        setError(null);
        setSuccess(null);

        try {
            let profileData: any = {
                nombre_persona: formData.name.trim()
            };

            // Si hay una imagen seleccionada, subirla primero
            if (selectedImage && user?.accessToken) {
                profileData.foto_perfil = await uploadProfileImage(selectedImage, user.accessToken);
            }

            // Actualizar el perfil
            const result = await profileAPI.updateProfile(profileData, user.accessToken);
            
            if (result.success) {
                await handleUpdateSuccess();
            } else {
                throw new Error(result.mensaje || 'Error al actualizar el perfil');
            }
        } catch (err: any) {
            handleUpdateError(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelfDeactivate = async () => {
        if (!user) return;

        setIsDeactivating(true);
        setError(null);

        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                throw new Error('No se encontró el token de acceso');
            }

            console.log('🔍 Iniciando auto-desactivación...');
            const result = await adminAPI.selfDeactivateUser(accessToken);
            console.log('✅ Auto-desactivación exitosa:', result);

            // Cerrar el modal
            setShowDeactivateModal(false);

            // Mostrar mensaje de éxito
            setSuccess('Tu cuenta ha sido desactivada exitosamente. Serás redirigido al login.');

            // Logout automático después de un breve delay
            setTimeout(async () => {
                await logout();
                navigate('/login');
            }, 2000);

        } catch (err: any) {
            console.error('❌ Error en auto-desactivación:', err);
            setError(err.detail || 'Error desactivando la cuenta');
        } finally {
            setIsDeactivating(false);
        }
    };

    return (
        <div className="p-4 sm:p-6">
            <div className="max-w-4xl mx-auto">
                <div className="mb-6 sm:mb-8">
                    <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Mi Perfil</h1>
                    <p className="mt-2 text-sm sm:text-base text-gray-600">Gestiona tu información personal</p>
                </div>

                {/* Mensajes de éxito y error */}
                {success && (
                    <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
                        <p className="text-green-800">{success}</p>
                    </div>
                )}

                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
                        <p className="text-red-800">{error}</p>
                    </div>
                )}

                <div className="bg-white shadow rounded-lg">
                    <div className="px-4 sm:px-6 py-4 border-b border-gray-200">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                            <h2 className="text-lg font-medium text-gray-900">Información Personal</h2>
                            <button
                                onClick={() => setIsEditing(!isEditing)}
                                disabled={isLoading}
                                className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors"
                            >
                                <PencilIcon className="w-4 h-4 mr-1" />
                                {isEditing ? 'Cancelar' : 'Editar'}
                            </button>
                        </div>
                    </div>

                    <div className="p-4 sm:p-6">
                        {/* Foto de perfil */}
                        <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6 mb-6 sm:mb-8">
                            <div className="relative">
                                {getProfileImageUrl() || imagePreview ? (
                                    <img
                                        src={imagePreview || getProfileImageUrl() || ''}
                                        alt="Foto de perfil"
                                        className="w-20 h-20 sm:w-24 sm:h-24 rounded-full object-cover border-4 border-gray-200"
                                        onError={(e) => {
                                            // Si hay error, mostrar el ícono por defecto
                                            const target = e.target as HTMLImageElement;
                                            target.style.display = 'none';
                                            const parent = target.parentElement;
                                            if (parent) {
                                                const fallback = document.createElement('div');
                                                fallback.className = 'w-24 h-24 bg-red-100 rounded-full flex items-center justify-center border-4 border-red-200';
                                                fallback.innerHTML = '<svg class="w-12 h-12 text-red-600" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" /></svg>';
                                                parent.appendChild(fallback);
                                            }
                                        }}
                                    />
                                ) : (
                                    <div className="w-20 h-20 sm:w-24 sm:h-24 bg-blue-100 rounded-full flex items-center justify-center border-4 border-gray-200">
                                        <UserCircleIcon className="w-10 h-10 sm:w-12 sm:h-12 text-blue-600" />
                                    </div>
                                )}
                                
                                {isEditing && (
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="absolute -bottom-1 -right-1 sm:-bottom-2 sm:-right-2 bg-blue-600 text-white rounded-full p-1.5 sm:p-2 hover:bg-blue-700 transition-colors"
                                        disabled={isUploadingImage}
                                        title="Cambiar foto de perfil"
                                    >
                                        <CameraIcon className="w-3 h-3 sm:w-4 sm:h-4" />
                                    </button>
                                )}
                            </div>
                            
                            <div className="flex-1 text-center sm:text-left">
                                <h3 className="text-lg sm:text-xl font-medium text-gray-900">{user?.name}</h3>
                                <p className="text-sm sm:text-base text-gray-600">{user?.email}</p>
                                <p className="text-xs sm:text-sm text-gray-500">Rol: {getRoleInSpanish(user?.role || '')}</p>
                                {user?.companyName && (
                                    <p className="text-xs sm:text-sm text-gray-500">Razón social de la empresa: {user.companyName}</p>
                                )}
                            </div>
                        </div>

                        {/* Input de archivo oculto */}
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/png,image/jpeg,image/jpg"
                            onChange={handleImageSelect}
                            className="hidden"
                        />

                        {/* Preview de imagen seleccionada */}
                        {imagePreview && isEditing && (
                            <div className="mb-6 p-3 sm:p-4 bg-gray-50 rounded-lg">
                                <div className="flex items-center justify-between gap-3">
                                    <div className="flex items-center space-x-2 sm:space-x-3">
                                        <img
                                            src={imagePreview}
                                            alt="Vista previa"
                                            className="w-12 h-12 sm:w-16 sm:h-16 rounded-full object-cover flex-shrink-0"
                                        />
                                        <div className="min-w-0">
                                            <p className="text-xs sm:text-sm font-medium text-gray-900">Nueva foto de perfil</p>
                                            <p className="text-xs text-gray-500">Se guardará al actualizar el perfil</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleRemoveImage}
                                        className="text-red-600 hover:text-red-800 flex-shrink-0 p-1"
                                    >
                                        <XMarkIcon className="w-4 h-4 sm:w-5 sm:h-5" />
                                    </button>
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                            {/* Nombre - Editable */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Nombre</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                                    disabled={!isEditing}
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm sm:text-base focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                                />
                            </div>

                            {/* Email - No editable */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Email</label>
                                <input
                                    type="email"
                                    value={formData.email}
                                    disabled
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm sm:text-base bg-gray-50 text-gray-500"
                                />
                                <p className="mt-1 text-xs text-gray-500">El email no se puede modificar</p>
                            </div>

                            {/* Empresa - No editable */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Razón social de la empresa</label>
                                <input
                                    type="text"
                                    value={formData.companyName || 'No especificada'}
                                    disabled
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm sm:text-base bg-gray-50 text-gray-500"
                                />
                                <p className="mt-1 text-xs text-gray-500">Información de la empresa asociada</p>
                            </div>

                            {/* RUC - No editable */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700">RUC</label>
                                <input
                                    type="text"
                                    value={(() => {
                                        const rucValue = user?.ruc || 'No especificado';
                                        console.log('🔍 Renderizando RUC:', rucValue, 'Usuario:', user?.name);
                                        return rucValue;
                                    })()}
                                    disabled
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm sm:text-base bg-gray-50 text-gray-500"
                                />
                                <p className="mt-1 text-xs text-gray-500">Registro Único de Contribuyente de la empresa asociada</p>
                            </div>

                            {/* Rol - No editable */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Rol Principal</label>
                                <input
                                    type="text"
                                    value={getRoleInSpanish(user?.role || '')}
                                    disabled
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-sm sm:text-base bg-gray-50 text-gray-500"
                                />
                                <p className="mt-1 text-xs text-gray-500">Rol asignado en la plataforma</p>
                            </div>
                        </div>

                        {/* Información sobre la foto */}
                        {isEditing && (
                            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                                <p className="text-xs sm:text-sm text-blue-800">
                                    <strong>📸 Foto de perfil:</strong> Puedes subir una imagen en formato PNG o JPG (máximo 5MB)
                                </p>
                            </div>
                        )}

                        {/* Sección de darse de baja */}
                        {!isEditing && (
                            <div className="mt-6 sm:mt-8 pt-4 sm:pt-6 border-t border-gray-200">
                                <div className="flex justify-center">
                                    <button
                                        onClick={() => setShowDeactivateModal(true)}
                                        className="inline-flex items-center px-3 sm:px-4 py-2 border border-transparent text-xs sm:text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                                    >
                                        <ExclamationTriangleIcon className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                                        Darse de baja del sistema
                                    </button>
                                </div>
                            </div>
                        )}


                        {isEditing && (
                            <div className="mt-6 flex flex-col sm:flex-row justify-end gap-3">
                                <button
                                    onClick={() => {
                                        setIsEditing(false);
                                        setSelectedImage(null);
                                        setImagePreview(null);
                                        setError(null);
                                    }}
                                    disabled={isLoading}
                                    className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={isLoading || isUploadingImage}
                                    className="w-full sm:w-auto px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                >
                                    {isLoading ? (
                                        <span className="flex items-center justify-center">
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                            <span className="text-xs sm:text-sm">
                                                {isUploadingImage ? 'Subiendo imagen...' : 'Guardando...'}
                                            </span>
                                        </span>
                                    ) : (
                                        'Guardar Cambios'
                                    )}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Modal de confirmación para darse de baja */}
            {showDeactivateModal && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div className="relative top-10 sm:top-20 mx-auto p-4 sm:p-5 border w-11/12 sm:w-96 shadow-lg rounded-md bg-white">
                        <div className="mt-3 text-center">
                            <div className="mx-auto flex items-center justify-center h-10 w-10 sm:h-12 sm:w-12 rounded-full bg-red-100">
                                <ExclamationTriangleIcon className="h-5 w-5 sm:h-6 sm:w-6 text-red-600" />
                            </div>
                            <h3 className="text-base sm:text-lg font-medium text-gray-900 mt-3 sm:mt-4">
                                Confirmar desactivación de cuenta
                            </h3>
                            <div className="mt-2 px-4 sm:px-7 py-3">
                                <p className="text-xs sm:text-sm text-gray-500">
                                    ¿Estás seguro de que quieres darte de baja del sistema? Esta acción:
                                </p>
                                <ul className="text-xs sm:text-sm text-gray-500 mt-2 text-left list-disc list-inside">
                                    <li>Desactivará tu cuenta permanentemente</li>
                                    <li>Te impedirá acceder a la plataforma</li>
                                    <li>No se puede deshacer</li>
                                </ul>
                                <p className="text-xs sm:text-sm text-gray-500 mt-3 font-medium">
                                    Si estás seguro, escribe "CONFIRMAR" en el campo de abajo:
                                </p>
                                <input
                                    type="text"
                                    placeholder="Escribe CONFIRMAR"
                                    className="mt-2 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                                    id="confirmInput"
                                />
                            </div>
                            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 px-4 py-3">
                                <button
                                    onClick={() => setShowDeactivateModal(false)}
                                    disabled={isDeactivating}
                                    className="w-full sm:w-auto px-4 py-2 bg-gray-500 text-white text-sm font-medium rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50 transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleSelfDeactivate}
                                    disabled={isDeactivating}
                                    className="w-full sm:w-auto px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
                                >
                                    {isDeactivating ? (
                                        <div className="flex items-center justify-center">
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1"></div>
                                            <span className="text-xs">...</span>
                                        </div>
                                    ) : (
                                        'Confirmar'
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ManageProfilePage;

