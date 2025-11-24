import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { 
    BriefcaseIcon, 
    MagnifyingGlassIcon, 
    PencilIcon, 
    TrashIcon,
    PlusIcon,
    XMarkIcon,
    CameraIcon,
    UploadCloudIcon,
    CalendarDaysIcon
} from '../../components/icons';
import { API_CONFIG } from '../../config/api';
import { AuthContext } from '../../contexts/AuthContext';
import { categoriesAPI, providerServicesAPI, servicesAPI, categoryRequestsAPI, serviceRequestsAPI } from '../../services/api';

// Funciones auxiliares
const formatNumber = (num: number): string => {
    if (Number.isNaN(num) || num === null || num === undefined) return '0';
    return num.toLocaleString('es-PY', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
};

// Función para generar IDs temporales únicos de forma segura
// Usa crypto.randomUUID() si está disponible, o una combinación de timestamp y performance.now()
const generateTempId = (prefix: string = 'temp'): string => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        // Usar crypto.randomUUID() si está disponible (navegadores modernos)
        return `${prefix}-${crypto.randomUUID()}`;
    }
    // Fallback: usar timestamp y performance.now() para mayor precisión
    // performance.now() es más preciso que Math.random() y no tiene problemas de seguridad
    const timestamp = Date.now();
    const performanceTime = typeof performance !== 'undefined' ? performance.now() : 0;
    return `${prefix}-${timestamp}-${performanceTime.toString().replace('.', '')}`;
};

// Función para formatear precio con puntos de mil mientras se escribe
const formatPriceInput = (value: string): string => {
    // Remover todos los caracteres no numéricos excepto punto y coma
    const cleanValue = value.replaceAll(/[^\d.,]/g, '');
    
    // Si está vacío, retornar vacío
    if (!cleanValue) return '';
    
    // Si el valor ya tiene puntos, removerlos todos y reformatear
    const numericOnly = cleanValue.replaceAll('.', '');
    
    // Separar parte entera y decimal
    const parts = numericOnly.split(',');
    const integerPart = parts[0];
    const decimalPart = parts[1];
    
    // Formatear la parte entera con puntos de mil usando un algoritmo seguro (evita ReDoS)
    const formatWithDots = (num: string): string => {
        // Algoritmo seguro: dividir en grupos de 3 dígitos desde la derecha
        if (!num) return '';
        
        let result = '';
        let count = 0;
        
        // Procesar desde la derecha hacia la izquierda
        for (let i = num.length - 1; i >= 0; i--) {
            if (count > 0 && count % 3 === 0) {
                result = '.' + result;
            }
            result = num[i] + result;
            count++;
        }
        
        return result;
    };
    
    const formattedInteger = formatWithDots(integerPart);
    
    // Reconstruir el valor - usar punto para decimales también
    if (decimalPart !== undefined) {
        return `${formattedInteger}.${decimalPart}`;
    }
    
    return formattedInteger;
};

// Función para parsear el precio formateado a número
const parsePriceInput = (formattedValue: string): number => {
    if (!formattedValue) return 0;
    
    // Remover todos los puntos de mil (separadores de miles)
    const withoutThousandsSeparators = formattedValue.replaceAll(/\.(?=\d{3})/g, '');
    
    // Parsear el número resultante
    const parsed = Number.parseFloat(withoutThousandsSeparators);
    return Number.isNaN(parsed) ? 0 : parsed;
};

const getTariffsSummary = (tarifas: any[], rateTypes: any[] = []): string => {
    if (!tarifas || tarifas.length === 0) return 'Sin tarifas';
    
    const tariffTexts = tarifas.map(tarifa => {
        const monto = formatNumber(Number.parseFloat(tarifa.monto?.toString().replace(',', '.') || '0') || 0);
        const descripcion = tarifa.descripcion || 'Sin descripción';
        const tipoTarifa = rateTypes.find(rt => rt.id_tarifa === tarifa.id_tarifa)?.nombre || 'Sin tipo';
        return `${monto} ₲ (${tipoTarifa}) - ${descripcion}`;
    });

    return tariffTexts.join(', ');
};

// Funciones helper para reducir complejidad cognitiva
const matchesCategoryFilter = (serviceCategory: number | undefined, categoryFilter: string): boolean => {
    if (categoryFilter === 'all') {
        return true;
    }
    return serviceCategory?.toString() === categoryFilter;
};

const matchesNameFilter = (serviceName: string | undefined, nameFilter: string | undefined): boolean => {
    const nameFilterStr = nameFilter?.toString().trim() || '';
    if (nameFilterStr === '') {
        return true;
    }

    const searchTerm = nameFilterStr.toLowerCase();
    const serviceNameLower = serviceName?.toLowerCase() || '';

    // Búsqueda por palabras completas o inicio de palabras
    const searchWords = searchTerm.split(' ').filter(word => word.length > 0);
    const nameWords = serviceNameLower.split(' ').filter(word => word.length > 0);

    // Verificar si todas las palabras de búsqueda están presentes
    return searchWords.every(searchWord =>
        nameWords.some(nameWord => nameWord.startsWith(searchWord))
    );
};

const matchesPriceFilter = (servicePrice: number | undefined, minPrice: string | undefined, maxPrice: string | undefined): boolean => {
    const minPriceStr = minPrice?.toString().trim() || '';
    const maxPriceStr = maxPrice?.toString().trim() || '';

    const minPriceValue = minPriceStr === '' ? null : parsePriceInput(minPriceStr);
    const maxPriceValue = maxPriceStr === '' ? null : parsePriceInput(maxPriceStr);

    const hasMinPriceFilter = minPriceValue !== null && minPriceValue > 0;
    const hasMaxPriceFilter = maxPriceValue !== null && maxPriceValue > 0;

    if (hasMinPriceFilter || hasMaxPriceFilter) {
        const price = servicePrice || 0;

        if (hasMinPriceFilter && price < minPriceValue) {
            return false;
        }
        if (hasMaxPriceFilter && price > maxPriceValue) {
            return false;
        }
    }

    return true;
};

const matchesStatusFilter = (serviceEstado: boolean | undefined, statusFilter: string): boolean => {
    if (statusFilter === 'all') {
        return true;
    }
    
    const isActive = serviceEstado === true;
    
    if (statusFilter === 'active' && !isActive) {
        return false;
    }
    if (statusFilter === 'inactive' && isActive) {
        return false;
    }
    
    return true;
};

// Función de filtrado de servicios (refactorizada para reducir complejidad cognitiva)
const filterServices = (services: any[], filters: any) => {
    return services.filter(service => {
        const matchesCategory = matchesCategoryFilter(service.id_categoria, filters.categoryFilter);
        const matchesName = matchesNameFilter(service.nombre, filters.nameFilter);
        const matchesPrice = matchesPriceFilter(service.precio, filters.minPrice, filters.maxPrice);
        const matchesStatus = matchesStatusFilter(service.estado, filters.statusFilter);
        
        return matchesCategory && matchesName && matchesPrice && matchesStatus;
    });
};

const ProviderMyServicesPage: React.FC = () => {
    const { user } = useContext(AuthContext);
    const [services, setServices] = useState<any[]>([]);
    const [filteredServices, setFilteredServices] = useState<any[]>([]);
    const [currencies, setCurrencies] = useState<any[]>([]);
    const [rateTypes, setRateTypes] = useState<any[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [editingService, setEditingService] = useState<any>(null);
    const [showEditModal, setShowEditModal] = useState(false);

    // Estados de filtros
    const [filters, setFilters] = useState({
        categoryFilter: 'all',
        nameFilter: '',
        minPrice: '',
        maxPrice: '',
        statusFilter: 'all'
    });

    // Estados del formulario de edición
    const [editForm, setEditForm] = useState({
        nombre: '',
        descripcion: '',
        precio: '',
        id_moneda: 1, // Guaraní paraguayo por defecto
        imagen: '',
        tarifas: [] as any[]
    });

    // Estados para manejo de imagen
    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [isUploadingImage, setIsUploadingImage] = useState(false);

    // Estados para plantillas
    const [showTemplateModal, setShowTemplateModal] = useState(false);
    const [templates, setTemplates] = useState<any[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
    const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
    const [templateForm, setTemplateForm] = useState({
        nombre: '',
        descripcion: '',
        precio: '',
        id_moneda: 1
    });
    const [isCreatingFromTemplate, setIsCreatingFromTemplate] = useState(false);

    // Estados para solicitudes de categorías
    const [showNewCategoryModal, setShowNewCategoryModal] = useState(false);
    const [newCategoryForm, setNewCategoryForm] = useState({
        nombre_categoria: '',
        descripcion: ''
    });
    const [isSubmittingCategory, setIsSubmittingCategory] = useState(false);
    const [showNewServiceRequest, setShowNewServiceRequest] = useState(false);
    const [newServiceRequest, setNewServiceRequest] = useState({
        nombre: '',
        descripcion: '',
        id_categoria: 0
    });

    useEffect(() => {
        loadData();
    }, []);

    // Aplicar filtros cuando cambien
    useEffect(() => {
        const filtered = filterServices(services, filters);
        setFilteredServices(filtered);
    }, [services, filters]);

    const loadData = async () => {
        try {
            setLoading(true);
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            // Cargar servicios, monedas, tipos de tarifa y categorías en paralelo
            const [servicesData, currenciesData, rateTypesData, categoriesData] = await Promise.all([
                providerServicesAPI.getProviderServices(accessToken),
                providerServicesAPI.getCurrencies(accessToken),
                providerServicesAPI.getRateTypes(accessToken),
                categoriesAPI.getCategories(accessToken)
            ]);

            setServices(servicesData);
            setCurrencies(currenciesData);
            setRateTypes(rateTypesData);
            setCategories(categoriesData);

        } catch (err: any) {
            setError(err.detail || 'Error al cargar los datos');
        } finally {
            setLoading(false);
        }
    };

    const resetFilters = () => {
        setFilters({
            categoryFilter: 'all',
            nameFilter: '',
            minPrice: '',
            maxPrice: '',
            statusFilter: 'all'
        });
    };

    const handleEditService = (service: any) => {
        setEditingService(service);
        
        // Buscar la moneda Guaraní en la lista de monedas
        const guaraniCurrency = currencies.find(c => c.nombre?.toLowerCase().includes('guaraní') || c.nombre?.toLowerCase().includes('guarani'));
        const defaultCurrencyId = guaraniCurrency?.id_moneda || 1;
        
        setEditForm({
            nombre: service.nombre || '',
            descripcion: service.descripcion || '',
            precio: service.precio ? formatPriceInput(service.precio.toString()) : '',
            id_moneda: defaultCurrencyId, // Siempre usar Guaraní por defecto al editar
            imagen: service.imagen || '',
            tarifas: (service.tarifas || []).map(tarifa => ({
                ...tarifa,
                monto: tarifa.monto ? formatPriceInput(tarifa.monto.toString()) : '',
                tempId: tarifa.tempId || generateTempId('tarifa')
            }))
        });

        // Inicializar vista previa si hay imagen existente
        if (service.imagen) {
            setImagePreview(service.imagen);
        } else {
            setImagePreview(null);
        }

        setSelectedImage(null);
        setShowEditModal(true);
    };

    const handleToggleServiceStatus = async (serviceId: number, currentStatus: boolean) => {
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            const newStatus = !currentStatus;
            
            // Actualizar el estado optimísticamente
            setServices(prevServices =>
                prevServices.map(service =>
                    service.id_servicio === serviceId
                        ? { ...service, estado: newStatus }
                        : service
                )
            );

            // Llamar a la API para actualizar el estado
            await providerServicesAPI.updateServiceStatus(serviceId, newStatus, accessToken);
            
            setSuccess(`Servicio ${newStatus ? 'activado' : 'desactivado'} exitosamente`);
            setTimeout(() => setSuccess(null), 3000);

        } catch (err: any) {
            // Revertir el cambio si la API falla
            setServices(prevServices =>
                prevServices.map(service =>
                    service.id_servicio === serviceId
                        ? { ...service, estado: currentStatus }
                        : service
                )
            );

            setError(err.detail || 'Error al actualizar el estado del servicio');
            setTimeout(() => setError(null), 3000);
        }
    };

    // Funciones para manejo de imagen
    const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validar tipo de archivo
            if (!file.type.startsWith('image/')) {
                setError('Solo se permiten archivos de imagen.');
                setTimeout(() => setError(null), 3000);
                return;
            }

            // Validar formato
            if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
                setError('Solo se permiten formatos PNG y JPG.');
                setTimeout(() => setError(null), 3000);
                return;
            }

            // Validar tamaño (5MB máximo)
            if (file.size > 5 * 1024 * 1024) {
                setError('La imagen no puede superar los 5MB.');
                setTimeout(() => setError(null), 3000);
                return;
            }

            setSelectedImage(file);

            // Crear vista previa
            const reader = new FileReader();
            reader.onload = (e) => {
                setImagePreview(e.target?.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleImageUpload = async () => {
        if (!selectedImage) return;

        setIsUploadingImage(true);
        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                setError('No tienes permisos para subir imágenes.');
                setTimeout(() => setError(null), 3000);
                setIsUploadingImage(false);
                return;
            }

            const formData = new FormData();
            formData.append('file', selectedImage);

            const apiBaseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
            const response = await fetch(`${apiBaseUrl}/api/v1/provider/services/upload-image`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al subir la imagen');
            }

            const result = await response.json();
            const imagePath = result.image_path;

            setEditForm(prev => ({ ...prev, imagen: imagePath }));
            setSelectedImage(null);
            setIsUploadingImage(false);
            setSuccess('Imagen subida exitosamente.');
            setTimeout(() => setSuccess(null), 3000);

        } catch (error) {
            console.error('Error al subir imagen:', error);
            setError(error instanceof Error ? error.message : 'Error al subir la imagen.');
            setTimeout(() => setError(null), 3000);
            setIsUploadingImage(false);
        }
    };

    const handleRemoveImage = async () => {
        try {
            // Si hay una imagen actual en el servicio, eliminarla del bucket
            if (editForm.imagen?.startsWith('https://') && editForm.imagen?.includes('supabase.co')) {
                const accessToken = localStorage.getItem('access_token');
                if (accessToken) {
                    try {
                        const apiBaseUrl = API_CONFIG.BASE_URL.replace('/api/v1', '');
                        const response = await fetch(`${apiBaseUrl}/api/v1/provider/services/delete-image?image_url=${encodeURIComponent(editForm.imagen)}`, {
                            method: 'DELETE',
                            headers: {
                                'Authorization': `Bearer ${accessToken}`
                            }
                        });

                        if (response.ok) {
                            console.log('✅ Imagen eliminada del bucket de Supabase Storage');
                        } else {
                            console.warn('⚠️ No se pudo eliminar la imagen del bucket, pero se continuará con la eliminación local');
                        }
                    } catch (error) {
                        console.warn('⚠️ Error eliminando imagen del bucket:', error);
                        // Continuar con la eliminación local aunque falle la eliminación del bucket
                    }
                }
            }
        } catch (error) {
            console.warn('⚠️ Error en eliminación de imagen:', error);
            // Continuar con la eliminación local aunque falle
        }

        // Eliminar imagen del estado local
        setSelectedImage(null);
        setImagePreview(null);
        setEditForm(prev => ({ ...prev, imagen: '' }));
    };

    const handleSaveService = async () => {
        if (!editingService) return;

        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            // Preparar datos para envío, convirtiendo precio y montos a números
            const serviceData = {
                ...editForm,
                precio: parsePriceInput(editForm.precio),
                tarifas: editForm.tarifas.map(tarifa => ({
                    ...tarifa,
                    monto: parsePriceInput(tarifa.monto.toString())
                }))
            };

            await providerServicesAPI.updateProviderService(editingService.id_servicio, serviceData, accessToken);

            // Actualizar solo el servicio específico en la lista sin recargar totalmente
            const updatedService = {
                ...editingService,
                ...serviceData
            };

            setServices(prevServices => 
                prevServices.map(service => 
                    service.id_servicio === editingService.id_servicio ? updatedService : service
                )
            );

            setSuccess('Servicio actualizado exitosamente');
            setShowEditModal(false);
            setEditingService(null);

            setTimeout(() => setSuccess(null), 3000);

        } catch (err: any) {
            setError(err.detail || 'Error al actualizar el servicio');
            setTimeout(() => setError(null), 3000);
        }
    };

    const addTarifa = () => {
        const newTarifa = {
            monto: '',
            descripcion: '',
            fecha_inicio: new Date().toISOString().split('T')[0],
            fecha_fin: null,
            id_tarifa: rateTypes[0]?.id_tarifa || 0,
            tempId: generateTempId('temp')
        };

        setEditForm(prev => ({
            ...prev,
            tarifas: [...prev.tarifas, newTarifa]
        }));
    };

    const updateTarifa = (index: number, field: string, value: any) => {
        setEditForm(prev => ({
            ...prev,
            tarifas: prev.tarifas.map((tarifa, i) =>
                i === index ? { ...tarifa, [field]: value } : tarifa
            )
        }));
    };

    const removeTarifa = (index: number) => {
        setEditForm(prev => ({
            ...prev,
            tarifas: prev.tarifas.filter((_, i) => i !== index)
        }));
    };

    // Funciones para manejo de plantillas
    const loadTemplatesByCategory = async (categoryId: number) => {
        try {
            console.log('🔍 Cargando servicios para categoría:', categoryId);
            const templatesData = await servicesAPI.getAllServicesByCategory(categoryId);
            console.log('📊 Servicios obtenidos:', templatesData);
            setTemplates(templatesData || []);
        } catch (err: any) {
            console.error('❌ Error al cargar servicios:', err);
            setTemplates([]); // Asegurar que siempre sea un array
            setError(err.detail || 'Error al cargar servicios de la categoría');
            setTimeout(() => setError(null), 3000);
        }
    };

    const handleSelectCategory = (categoryId: number) => {
        setSelectedCategory(categoryId);
        setSelectedTemplate(null);
        setTemplates([]);
        loadTemplatesByCategory(categoryId);
    };

    const handleSelectTemplate = (template: any) => {
        setSelectedTemplate(template);
        setTemplateForm({
            nombre: template.nombre || '', // Se mantiene para el backend, pero no se muestra en el formulario
            descripcion: template.descripcion || '',
            precio: '',
            id_moneda: 1
        });
    };

    const handleRequestNewService = () => {
        console.log('🔍 handleRequestNewService llamado');
        console.log('📂 Categoría seleccionada:', selectedCategory);
        
        if (!selectedCategory) {
            console.log('❌ No hay categoría seleccionada');
            setError('Por favor selecciona una categoría primero');
            setTimeout(() => setError(null), 3000);
            return;
        }
        
        console.log('✅ Mostrando formulario de solicitud');
        setShowNewServiceRequest(true);
        setNewServiceRequest({
            nombre: '',
            descripcion: '',
            id_categoria: selectedCategory
        });
    };

    const handleCreateFromTemplate = async () => {
        if (!selectedTemplate || !templateForm.precio.trim()) {
            setError('Por favor completa todos los campos requeridos');
            setTimeout(() => setError(null), 3000);
            return;
        }

        try {
            setIsCreatingFromTemplate(true);
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) return;

            const templateData = {
                template_id: selectedTemplate.id_servicio,
                nombre: templateForm.nombre.trim(),
                descripcion: templateForm.descripcion.trim(),
                precio: parsePriceInput(templateForm.precio),
                id_moneda: templateForm.id_moneda
            };

            await providerServicesAPI.createServiceFromTemplate(templateData, accessToken);
            
            setSuccess('Servicio creado exitosamente desde plantilla');
            setShowTemplateModal(false);
            setSelectedTemplate(null);
            setTemplateForm({ nombre: '', descripcion: '', precio: '', id_moneda: 1 });
            loadData(); // Recargar servicios
            setTimeout(() => setSuccess(null), 3000);

        } catch (err: any) {
            setError(err.detail || 'Error al crear servicio desde plantilla');
            setTimeout(() => setError(null), 3000);
        } finally {
            setIsCreatingFromTemplate(false);
        }
    };

    const handleCancelTemplate = () => {
        setShowTemplateModal(false);
        setSelectedTemplate(null);
        setSelectedCategory(null);
        setTemplates([]);
        setTemplateForm({ nombre: '', descripcion: '', precio: '', id_moneda: 1 });
        setShowNewServiceRequest(false);
        setNewServiceRequest({ nombre: '', descripcion: '', id_categoria: 0 });
    };

    const handleSubmitNewServiceRequest = async () => {
        console.log('🔍 handleSubmitNewServiceRequest llamado');
        console.log('📝 Datos del formulario:', newServiceRequest);
        
        if (!newServiceRequest.nombre.trim() || !newServiceRequest.descripcion.trim()) {
            console.log('❌ Campos requeridos faltantes');
            setError('Por favor completa todos los campos requeridos');
            setTimeout(() => setError(null), 3000);
            return;
        }

        try {
            const accessToken = localStorage.getItem('access_token');
            if (!accessToken) {
                console.log('❌ No hay access token');
                return;
            }

            console.log('🚀 Enviando solicitud...');
            const payload = {
                nombre_servicio: newServiceRequest.nombre.trim(),
                descripcion: newServiceRequest.descripcion.trim(),
                id_categoria: newServiceRequest.id_categoria,
                comentario_admin: null
            };
            console.log('📦 Payload:', payload);

            await serviceRequestsAPI.proposeService(payload, accessToken);

            console.log('✅ Solicitud enviada exitosamente');
            setSuccess('Solicitud de nuevo servicio enviada exitosamente');
            setShowNewServiceRequest(false);
            setNewServiceRequest({ nombre: '', descripcion: '', id_categoria: 0 });
            setTimeout(() => setSuccess(null), 3000);

        } catch (err: any) {
            console.log('❌ Error al enviar solicitud:', err);
            setError(err.detail || 'Error al enviar solicitud de nuevo servicio');
            setTimeout(() => setError(null), 3000);
        }
    };

    // Funciones para manejar solicitudes de categorías
    const handleRequestNewCategory = () => {
        setShowNewCategoryModal(true);
        setNewCategoryForm({ nombre_categoria: '', descripcion: '' });
    };

    const handleCancelNewCategory = () => {
        setShowNewCategoryModal(false);
        setNewCategoryForm({ nombre_categoria: '', descripcion: '' });
    };

    const handleSubmitNewCategory = async () => {
        if (!user?.accessToken) return;

        if (!newCategoryForm.nombre_categoria.trim() || !newCategoryForm.descripcion.trim()) {
            setError('Por favor completa todos los campos');
            setTimeout(() => setError(null), 3000);
            return;
        }

        try {
            setIsSubmittingCategory(true);
            await categoryRequestsAPI.createCategoryRequest(newCategoryForm, user.accessToken);
            
            setShowNewCategoryModal(false);
            setNewCategoryForm({ nombre_categoria: '', descripcion: '' });
            setSuccess('Solicitud de nueva categoría enviada exitosamente');
            setTimeout(() => setSuccess(null), 3000);

        } catch (err: any) {
            setError(err.detail || 'Error al enviar solicitud de nueva categoría');
            setTimeout(() => setError(null), 3000);
        } finally {
            setIsSubmittingCategory(false);
        }
    };

    const renderServicesContent = () => {
        if (filteredServices.length > 0) {
            return (
                <div className="divide-y divide-gray-200">
                    {filteredServices.map((service) => (
                        <div key={service.id_servicio} className="p-4 hover:bg-gray-50 transition-colors duration-200">
                            <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
                                {/* Imagen del servicio */}
                                <div className="flex-shrink-0 mx-auto sm:mx-0">
                                    {service.imagen ? (
                                        <img
                                            src={service.imagen.startsWith('http') ? service.imagen : `${API_CONFIG.BASE_URL.replace('/api/v1', '')}${service.imagen}`}
                                            alt={service.nombre}
                                            className="h-16 w-16 object-cover rounded-lg border border-gray-200"
                                            onError={(e) => {
                                                console.log('❌ Error cargando imagen en vista de servicios:', (e.target as HTMLImageElement).src);
                                                const target = e.target as HTMLImageElement;
                                                target.style.display = 'none';
                                                const parent = target.parentElement;
                                                if (parent) {
                                                    parent.innerHTML = `
                                                        <div class="h-16 w-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg border border-gray-200 flex items-center justify-center">
                                                            <svg class="h-6 w-6 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                                            </svg>
                                                        </div>
                                                    `;
                                                }
                                            }}
                                        />
                                    ) : (
                                        <div className="h-16 w-16 bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center">
                                            <BriefcaseIcon className="h-6 w-6 text-gray-400" />
                                        </div>
                                    )}
                                </div>

                                {/* Información principal */}
                                <div className="flex-1 min-w-0 text-center sm:text-left">
                                    <h3 className="text-lg font-semibold text-gray-900 break-words">{service.nombre}</h3>
                                    <p className="text-sm text-gray-600 mt-1 break-words">{service.descripcion}</p>
                                </div>

                                {/* Información compacta - responsive */}
                                <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-6 text-sm">
                                    {/* Precio */}
                                    <div className="text-center">
                                        <p className="text-xs font-medium text-gray-500 mb-1">💰 Precio</p>
                                        <p className="font-semibold text-green-600">
                                            {formatNumber(service.precio || 0)} ₲
                                        </p>
                                    </div>

                                    {/* Categoría */}
                                    <div className="text-center">
                                        <p className="text-xs font-medium text-gray-500 mb-1">📂 Categoría</p>
                                        <p className="font-semibold text-blue-600 break-words">
                                            {categories.find(c => c.id_categoria === service.id_categoria)?.nombre || 'No especificado'}
                                        </p>
                                    </div>

                                    {/* Estado */}
                                    <div className="text-center">
                                        <p className="text-xs font-medium text-gray-500 mb-1">📊 Estado</p>
                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                            service.estado 
                                                ? 'bg-green-100 text-green-800' 
                                                : 'bg-red-100 text-red-800'
                                        }`}>
                                            {service.estado ? 'Activo' : 'Inactivo'}
                                        </span>
                                    </div>

                                    {/* Tarifas */}
                                    <div className="text-center">
                                        <p className="text-xs font-medium text-gray-500 mb-1">📋 Tarifas</p>
                                        <p className="font-semibold text-orange-600">
                                            {service.tarifas?.length || 0}
                                        </p>
                                    </div>
                                </div>

                                {/* Botones de acción - responsive */}
                                <div className="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-2 mt-4 sm:mt-0">
                                    <button
                                        onClick={() => handleToggleServiceStatus(service.id_servicio, service.estado)}
                                        className={`w-full sm:w-auto inline-flex items-center justify-center px-4 py-2 border shadow-sm text-sm font-medium rounded-md transition-colors ${
                                            service.estado
                                                ? 'border-red-300 text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500'
                                                : 'border-green-300 text-green-700 bg-green-50 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500'
                                        }`}
                                    >
                                        {service.estado ? (
                                            <>
                                                <XMarkIcon className="h-4 w-4 mr-1" />
                                                <span className="hidden sm:inline">Desactivar</span>
                                                <span className="sm:hidden">Desactivar</span>
                                            </>
                                        ) : (
                                            <>
                                                <PlusIcon className="h-4 w-4 mr-1" />
                                                <span className="hidden sm:inline">Activar</span>
                                                <span className="sm:hidden">Activar</span>
                                            </>
                                        )}
                                    </button>
                                    <button
                                        onClick={() => handleEditService(service)}
                                        className="w-full sm:w-auto inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                                    >
                                        <PencilIcon className="h-4 w-4 mr-1" />
                                        <span className="hidden sm:inline">Editar</span>
                                        <span className="sm:hidden">Editar</span>
                                    </button>
                                </div>
                            </div>

                            {/* Resumen de tarifas (expandible) */}
                            {service.tarifas && service.tarifas.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                    <div className="space-y-2">
                                        <p className="text-xs font-medium text-gray-500">📋 Detalle de tarifas:</p>
                                        <div className="bg-gray-50 rounded-md p-2">
                                            <p className="text-xs text-gray-700 leading-relaxed">
                                                {getTariffsSummary(service.tarifas, rateTypes)}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            );
        }
        
        if (services.length === 0) {
            return (
                <div className="text-center py-12">
                    <BriefcaseIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No tienes servicios</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        Solicita nuevos servicios para comenzar a ofrecerlos.
                    </p>
                </div>
            );
        }
        
        return (
            <div className="text-center py-12">
                <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No hay servicios que coincidan con los filtros</h3>
                <p className="mt-1 text-sm text-gray-500">
                    Prueba ajustando los filtros para ver más resultados.
                </p>
                <button
                    onClick={resetFilters}
                    className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                >
                    🔄 Limpiar Filtros
                </button>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Cargando tus servicios...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Mensajes de error y éxito */}
            {error && (
                <div className="fixed top-4 right-4 z-50 bg-red-50 border border-red-200 rounded-md p-4 shadow-lg max-w-md animate-fade-in">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="ml-3 flex-1">
                            <p className="text-sm text-red-800">{error}</p>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                            <button
                                onClick={() => setError(null)}
                                className="text-red-400 hover:text-red-600"
                            >
                                <XMarkIcon className="h-5 w-5" />
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {success && (
                <div className="fixed top-4 right-4 z-50 bg-green-50 border border-green-200 rounded-md p-4 shadow-lg max-w-md animate-fade-in">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="ml-3 flex-1">
                            <p className="text-sm text-green-800">{success}</p>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                            <button
                                onClick={() => setSuccess(null)}
                                className="text-green-400 hover:text-green-600"
                            >
                                <XMarkIcon className="h-5 w-5" />
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-4 sm:py-6">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                            <div>
                                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Mis Servicios</h1>
                                <p className="mt-1 text-xs sm:text-sm text-gray-500">
                                    Gestiona y administra todos tus servicios. Crea nuevos servicios desde plantillas existentes.
                                </p>
                            </div>
                            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                                <button
                                    onClick={handleRequestNewCategory}
                                    className="w-full sm:w-auto inline-flex items-center justify-center px-3 sm:px-4 py-2 border border-gray-300 rounded-md shadow-sm text-xs sm:text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                                >
                                    <PlusIcon className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                                    Solicitar Categoría
                                </button>
                                <button
                                    onClick={() => setShowTemplateModal(true)}
                                    className="w-full sm:w-auto inline-flex items-center justify-center px-3 sm:px-4 py-2 border border-transparent rounded-md shadow-sm text-xs sm:text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
                                >
                                    <PlusIcon className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                                    Agregar Servicio
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
                {/* Filtros */}
                <div className="bg-white p-4 sm:p-6 rounded-lg shadow border border-gray-200 mb-6 sm:mb-8">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                        <h2 className="text-base sm:text-lg font-medium text-gray-900">Filtros</h2>
                        <button
                            onClick={resetFilters}
                            className="text-xs sm:text-sm text-blue-600 hover:text-blue-800 transition-colors"
                        >
                            Limpiar Filtros
                        </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 sm:gap-4">
                        {/* Filtro por categoría */}
                        <div>
                            <label htmlFor="filter-category-provider-services" className="block text-sm font-medium text-gray-700 mb-2">Categoría</label>
                            <select
                                id="filter-category-provider-services"
                                value={filters.categoryFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, categoryFilter: e.target.value }))}
                                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todas las categorías</option>
                                {categories.map(category => (
                                    <option key={category.id_categoria} value={category.id_categoria}>
                                        {category.nombre}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Filtro por nombre */}
                        <div>
                            <label htmlFor="filter-name-provider-services" className="block text-sm font-medium text-gray-700 mb-2">Nombre del Servicio</label>
                            <input
                                id="filter-name-provider-services"
                                type="text"
                                value={filters.nameFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, nameFilter: e.target.value }))}
                                placeholder="Escribe para buscar..."
                                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Filtro por estado */}
                        <div>
                            <label htmlFor="filter-status-provider-services" className="block text-sm font-medium text-gray-700 mb-2">Estado</label>
                            <select
                                id="filter-status-provider-services"
                                value={filters.statusFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, statusFilter: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todos los estados</option>
                                <option value="active">Activos</option>
                                <option value="inactive">Inactivos</option>
                            </select>
                        </div>

                        {/* Filtro por precio mínimo */}
                        <div>
                            <label htmlFor="filter-min-price-provider-services" className="block text-sm font-medium text-gray-700 mb-2">Precio Mínimo</label>
                            <input
                                id="filter-min-price-provider-services"
                                type="text"
                                value={filters.minPrice}
                                onChange={(e) => {
                                    const formattedValue = formatPriceInput(e.target.value);
                                    setFilters(prev => ({ ...prev, minPrice: formattedValue }));
                                }}
                                placeholder="0"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Filtro por precio máximo */}
                        <div>
                            <label htmlFor="filter-max-price-provider-services" className="block text-sm font-medium text-gray-700 mb-2">Precio Máximo</label>
                            <input
                                id="filter-max-price-provider-services"
                                type="text"
                                value={filters.maxPrice}
                                onChange={(e) => {
                                    const formattedValue = formatPriceInput(e.target.value);
                                    setFilters(prev => ({ ...prev, maxPrice: formattedValue }));
                                }}
                                placeholder="Sin límite"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                </div>

                {/* Contador de resultados */}
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <div className="text-center sm:text-left">
                            <h3 className="text-lg font-medium text-gray-900">
                                Total: {filteredServices.length} servicios
                            </h3>
                        </div>
                        <div className="text-center sm:text-right">
                            <div className="text-sm text-gray-500">
                                {filteredServices.length > 0 && (
                                    <span className="text-gray-600">
                                        Mostrando {filteredServices.length} de {services.length} resultados
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Services List */}
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                    {renderServicesContent()}
                </div>
            </div>

            {/* Mensaje para dirigir a Mi Agenda */}
            {filteredServices.length > 0 && (
                <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <CalendarDaysIcon className="h-6 w-6 text-blue-600" />
                        <h2 className="text-xl font-semibold text-blue-900">📅 Configurar Disponibilidades</h2>
                    </div>
                    <p className="text-blue-800 mb-4">
                        Para configurar los horarios disponibles de tus servicios, utiliza la nueva sección "Mi Agenda" 
                        donde podrás gestionar todas las disponibilidades en un solo lugar.
                    </p>
                    <Link 
                        to="/dashboard/agenda" 
                        className="btn-blue inline-flex items-center gap-2"
                    >
                        <CalendarDaysIcon className="h-5 w-5" />
                        Ir a Mi Agenda
                    </Link>
                </div>
            )}

            {/* Edit Service Modal */}
            {showEditModal && editingService && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
                        <div className="mt-3">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    Editar Servicio: {editingService.nombre}
                                </h3>
                                <button
                                    onClick={() => setShowEditModal(false)}
                                    className="text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                    <XMarkIcon className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="space-y-4">
                                {/* Nombre */}
                                <div>
                                    <label htmlFor="edit-service-name" className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre del servicio *
                                    </label>
                                    <input
                                        id="edit-service-name"
                                        type="text"
                                        value={editForm.nombre}
                                        readOnly
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-600 cursor-not-allowed"
                                        title="El nombre del servicio no se puede editar"
                                    />
                                    <p className="mt-1 text-xs text-gray-500">
                                        El nombre del servicio no se puede modificar una vez creado
                                    </p>
                                </div>

                                {/* Descripción */}
                                <div>
                                    <label htmlFor="edit-service-description" className="block text-sm font-medium text-gray-700 mb-2">
                                        Descripción *
                                    </label>
                                    <textarea
                                        id="edit-service-description"
                                        value={editForm.descripcion}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, descripcion: e.target.value }))}
                                        rows={3}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors resize-none"
                                    />
                                </div>

                                {/* Precio y Moneda */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label htmlFor="edit-service-price" className="block text-sm font-medium text-gray-700 mb-2">
                                            Precio *
                                        </label>
                                        <input
                                            id="edit-service-price"
                                            type="text"
                                            value={editForm.precio}
                                            onChange={(e) => {
                                                const inputValue = e.target.value;
                                                // Formatear el precio con puntos de mil mientras se escribe
                                                const formattedValue = formatPriceInput(inputValue);
                                                setEditForm(prev => ({ ...prev, precio: formattedValue }));
                                            }}
                                            placeholder="0"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="edit-service-currency" className="block text-sm font-medium text-gray-700 mb-2">
                                            Moneda
                                        </label>
                                        <select
                                            id="edit-service-currency"
                                            value={editForm.id_moneda}
                                            onChange={(e) => setEditForm(prev => ({ ...prev, id_moneda: Number.parseInt(e.target.value) }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                                        >
                                            {currencies.map((currency) => (
                                                <option key={currency.id_moneda} value={currency.id_moneda}>
                                                    {currency.nombre} ({currency.simbolo})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {/* Imagen */}
                                <div>
                                    <h4 className="block text-sm font-medium text-gray-700 mb-2">
                                        Imagen del servicio
                                    </h4>
                                    
                                    {/* Vista previa de imagen */}
                                    {imagePreview && (
                                        <div className="mb-3">
                                            <img
                                                src={imagePreview}
                                                alt="Vista previa"
                                                className="h-32 w-32 object-cover rounded-lg border border-gray-200"
                                            />
                                        </div>
                                    )}

                                    {/* Controles de imagen */}
                                    <div className="flex items-center space-x-3">
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={handleImageSelect}
                                            className="hidden"
                                            id="image-upload"
                                        />
                                        <label
                                            htmlFor="image-upload"
                                            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cursor-pointer transition-colors"
                                        >
                                            <CameraIcon className="h-4 w-4 mr-2" />
                                            Seleccionar Imagen
                                        </label>

                                        {selectedImage && (
                                            <button
                                                onClick={handleImageUpload}
                                                disabled={isUploadingImage}
                                                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 transition-colors"
                                            >
                                                {isUploadingImage ? (
                                                    <>
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                        Subiendo...
                                                    </>
                                                ) : (
                                                    <>
                                                        <UploadCloudIcon className="h-4 w-4 mr-2" />
                                                        Subir
                                                    </>
                                                )}
                                            </button>
                                        )}

                                        {imagePreview && (
                                            <button
                                                onClick={handleRemoveImage}
                                                className="inline-flex items-center px-3 py-2 border border-red-300 text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                                            >
                                                <TrashIcon className="h-4 w-4 mr-2" />
                                                Eliminar
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {/* Tarifas */}
                                <div>
                                    <div className="flex items-center justify-between mb-3">
                                        <h4 className="block text-sm font-medium text-gray-700">
                                            Tarifas del servicio
                                        </h4>
                                        <button
                                            onClick={addTarifa}
                                            className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                                        >
                                            <PlusIcon className="h-3 w-3 mr-1" />
                                            Agregar Tarifa
                                        </button>
                                    </div>

                                    {editForm.tarifas.map((tarifa, index) => (
                                        <div key={tarifa.tempId || `tarifa-${index}`} className="border border-gray-200 rounded-lg p-3 mb-3">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-gray-700">Tarifa {index + 1}</span>
                                                <button
                                                    onClick={() => removeTarifa(index)}
                                                    className="text-red-600 hover:text-red-800 transition-colors"
                                                >
                                                    <TrashIcon className="h-4 w-4" />
                                                </button>
                                            </div>
                                            
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                                <div>
                                                    <label htmlFor={`tarifa-monto-${index}`} className="block text-xs font-medium text-gray-600 mb-1">
                                                        Monto
                                                    </label>
                                                    <input
                                                        id={`tarifa-monto-${index}`}
                                                        type="text"
                                                        value={tarifa.monto || ''}
                                                        onChange={(e) => {
                                                            const inputValue = e.target.value;
                                                            // Formatear el monto con puntos de mil mientras se escribe
                                                            const formattedValue = formatPriceInput(inputValue);
                                                            updateTarifa(index, 'monto', formattedValue);
                                                        }}
                                                        placeholder="0"
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                                    />
                                                </div>
                                                <div>
                                                    <label htmlFor={`tarifa-descripcion-${index}`} className="block text-xs font-medium text-gray-600 mb-1">
                                                        Descripción
                                                    </label>
                                                    <input
                                                        id={`tarifa-descripcion-${index}`}
                                                        type="text"
                                                        value={tarifa.descripcion}
                                                        onChange={(e) => updateTarifa(index, 'descripcion', e.target.value)}
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label htmlFor={`tarifa-tipo-${index}`} className="block text-xs font-medium text-gray-600 mb-1">
                                                        Tipo de Tarifa
                                                    </label>
                                                    <select
                                                        id={`tarifa-tipo-${index}`}
                                                        value={tarifa.id_tarifa}
                                                        onChange={(e) => updateTarifa(index, 'id_tarifa', Number.parseInt(e.target.value))}
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    >
                                                        {rateTypes.map((rateType) => (
                                                            <option key={rateType.id_tarifa} value={rateType.id_tarifa}>
                                                                {rateType.nombre}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Botones de acción */}
                            <div className="flex justify-end space-x-3 mt-6">
                                <button
                                    onClick={() => setShowEditModal(false)}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleSaveService}
                                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
                                >
                                    Guardar Cambios
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Agregar Servicio */}
            {showTemplateModal && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
                        <div className="mt-3">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-medium text-gray-900">Agregar Nuevo Servicio</h3>
                                <button
                                    onClick={handleCancelTemplate}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <XMarkIcon className="h-6 w-6" />
                                </button>
                            </div>

                            {showNewServiceRequest ? (
                                /* Formulario de Solicitud de Nuevo Servicio */
                                <div className="space-y-4">
                                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                        <h4 className="text-md font-medium text-blue-900 mb-2">Solicitar Nuevo Servicio</h4>
                                        <p className="text-sm text-blue-700">
                                            Categoría: <strong>{categories.find(c => c.id_categoria === selectedCategory)?.nombre}</strong>
                                        </p>
                                    </div>

                                    <div>
                                        <label htmlFor="new-service-request-name" className="block text-sm font-medium text-gray-700 mb-2">
                                            Nombre del Servicio *
                                        </label>
                                        <input
                                            id="new-service-request-name"
                                            type="text"
                                            value={newServiceRequest.nombre}
                                            onChange={(e) => setNewServiceRequest(prev => ({ ...prev, nombre: e.target.value }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder="Ingresa el nombre del servicio que deseas"
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="new-service-request-description" className="block text-sm font-medium text-gray-700 mb-2">
                                            Descripción del Servicio *
                                        </label>
                                        <textarea
                                            id="new-service-request-description"
                                            value={newServiceRequest.descripcion}
                                            onChange={(e) => setNewServiceRequest(prev => ({ ...prev, descripcion: e.target.value }))}
                                            rows={4}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder="Describe detalladamente el servicio que necesitas"
                                        />
                                    </div>

                                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                                        <p className="text-sm text-yellow-800">
                                            <strong>Nota:</strong> Tu solicitud será revisada por el administrador. Una vez aprobada, podrás crear servicios basados en esta solicitud.
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    {/* Paso 1: Selección de Categoría */}
                                    <div>
                                        <h4 className="text-md font-medium text-gray-700 mb-3">1. Selecciona una Categoría</h4>
                                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                                            {categories.map((category) => (
                                                <button
                                                    key={category.id_categoria}
                                                    onClick={() => handleSelectCategory(category.id_categoria)}
                                                    className={`p-3 border rounded-lg text-left transition-colors ${
                                                        selectedCategory === category.id_categoria
                                                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                                                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                                    }`}
                                                >
                                                    <div className="text-sm font-medium">{category.nombre}</div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Paso 2: Todos los Servicios o Solicitar Nuevo */}
                                    {selectedCategory && (
                                        <div>
                                            <div className="flex items-center justify-between mb-3">
                                                <h4 className="text-md font-medium text-gray-700">
                                                    2. Todos los Servicios en "{categories.find(c => c.id_categoria === selectedCategory)?.nombre}"
                                                </h4>
                                                <span className="text-sm text-gray-500">
                                                    {templates.length} servicio{templates.length === 1 ? '' : 's'} encontrado{templates.length === 1 ? '' : 's'}
                                                </span>
                                            </div>
                                            
                                            {templates.length > 0 ? (
                                                <div className="space-y-4">
                                                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                                        <p className="text-sm text-blue-800">
                                                            <strong>💡 Tip:</strong> Puedes reutilizar cualquier servicio como plantilla. 
                                                            Solo personaliza el precio, descripción e imagen según tus necesidades.
                                                        </p>
                                                    </div>
                                                    
                                                    <div className="max-h-80 overflow-y-auto space-y-2">
                                                        {templates.map((template) => (
                                                            <button
                                                                key={template.id_servicio}
                                                                type="button"
                                                                aria-label={`Seleccionar plantilla ${template.nombre}`}
                                                                onClick={() => handleSelectTemplate(template)}
                                                                className={`w-full text-left p-3 border rounded-lg cursor-pointer transition-colors ${
                                                                    selectedTemplate?.id_servicio === template.id_servicio
                                                                        ? 'border-green-500 bg-green-50'
                                                                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                                                }`}
                                                            >
                                                                <div className="flex items-start space-x-3">
                                                                    <div className="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                                                                        <BriefcaseIcon className="h-5 w-5 text-gray-400" />
                                                                    </div>
                                                                    <div className="flex-1 min-w-0">
                                                                        <h5 className="text-sm font-medium text-gray-900 truncate">
                                                                            {template.nombre}
                                                                        </h5>
                                                                        <p className="text-xs text-gray-600 line-clamp-2 mt-1">
                                                                            {template.descripcion}
                                                                        </p>
                                                                        <div className="flex items-center space-x-2 mt-2">
                                                                            <span className="text-xs text-green-600 font-medium">
                                                                                {formatNumber(template.precio || 0)} ₲
                                                                            </span>
                                                                            <span className="text-xs text-gray-500">
                                                                                • Creado: {new Date(template.created_at).toLocaleDateString()}
                                                                            </span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </button>
                                                        ))}
                                                    </div>

                                                    {/* Formulario de personalización */}
                                                    {selectedTemplate && (
                                                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                                            <h5 className="text-sm font-medium text-gray-700 mb-3">Personalizar tu Servicio</h5>
                                                            
                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                <div>
                                                                    <label htmlFor="template-service-name" className="block text-xs font-medium text-gray-600 mb-1">
                                                                        Nombre del Servicio
                                                                    </label>
                                                                    <input
                                                                        id="template-service-name"
                                                                        type="text"
                                                                        value={selectedTemplate.nombre}
                                                                        readOnly
                                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-gray-100 text-gray-600 cursor-not-allowed"
                                                                    />
                                                                </div>
                                                                <div>
                                                                    <label htmlFor="template-service-price" className="block text-xs font-medium text-gray-600 mb-1">
                                                                        Precio *
                                                                    </label>
                                                                    <input
                                                                        id="template-service-price"
                                                                        type="text"
                                                                        value={templateForm.precio}
                                                                        onChange={(e) => {
                                                                            const inputValue = e.target.value;
                                                                            // Formatear el precio con puntos de mil mientras se escribe
                                                                            const formattedValue = formatPriceInput(inputValue);
                                                                            setTemplateForm(prev => ({ ...prev, precio: formattedValue }));
                                                                        }}
                                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                                                        placeholder="0"
                                                                    />
                                                                </div>
                                                            </div>
                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                                                                <div>
                                                                    <label htmlFor="template-service-currency" className="block text-xs font-medium text-gray-600 mb-1">
                                                                        Moneda *
                                                                    </label>
                                                                    <select
                                                                        id="template-service-currency"
                                                                        value={templateForm.id_moneda}
                                                                        onChange={(e) => setTemplateForm(prev => ({ ...prev, id_moneda: Number.parseInt(e.target.value) }))}
                                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                                    >
                                                                        <option value="">Selecciona una moneda</option>
                                                                        {currencies.map((currency) => (
                                                                            <option key={currency.id_moneda} value={currency.id_moneda}>
                                                                                {currency.nombre} ({currency.simbolo})
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                </div>
                                                            </div>
                                                            <div className="mt-3">
                                                                <label htmlFor="template-service-description" className="block text-xs font-medium text-gray-600 mb-1">
                                                                    Descripción
                                                                </label>
                                                                <textarea
                                                                    id="template-service-description"
                                                                    value={templateForm.descripcion}
                                                                    onChange={(e) => setTemplateForm(prev => ({ ...prev, descripcion: e.target.value }))}
                                                                    rows={2}
                                                                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                                    placeholder="Describe tu servicio"
                                                                />
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="flex justify-between items-center pt-4 border-t border-gray-200">
                                                        <button
                                                            onClick={handleRequestNewService}
                                                            className="text-sm text-blue-600 hover:text-blue-800"
                                                        >
                                                            ¿No encuentras el servicio que necesitas? Solicitar nuevo servicio
                                                        </button>
                                                        <button
                                                            onClick={handleCreateFromTemplate}
                                                            disabled={!selectedTemplate || !templateForm.precio.trim() || isCreatingFromTemplate}
                                                            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                                        >
                                                            {isCreatingFromTemplate ? 'Creando...' : 'Crear Servicio'}
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="text-center py-8 bg-gray-50 border border-gray-200 rounded-lg">
                                                    <BriefcaseIcon className="mx-auto h-12 w-12 text-gray-400" />
                                                    <h3 className="mt-2 text-sm font-medium text-gray-900">No hay servicios en esta categoría</h3>
                                                    <p className="mt-1 text-sm text-gray-500 mb-4">
                                                        No se encontraron servicios en esta categoría. 
                                                        Puedes solicitar un nuevo servicio para que sea agregado a la plataforma.
                                                    </p>
                                                    <button
                                                        onClick={handleRequestNewService}
                                                        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                                    >
                                                        <PlusIcon className="h-4 w-4 mr-2" />
                                                        Solicitar Nuevo Servicio
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            <div className="flex justify-end space-x-3 mt-6">
                                <button
                                    onClick={handleCancelTemplate}
                                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                >
                                    Cancelar
                                </button>
                                {showNewServiceRequest && (
                                    <button
                                        onClick={() => {
                                            console.log('🔘 Botón Enviar Solicitud clickeado');
                                            console.log('📝 Estado showNewServiceRequest:', showNewServiceRequest);
                                            console.log('📝 Datos newServiceRequest:', newServiceRequest);
                                            handleSubmitNewServiceRequest();
                                        }}
                                        disabled={!newServiceRequest.nombre.trim() || !newServiceRequest.descripcion.trim()}
                                        className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Enviar Solicitud
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal para Solicitar Nueva Categoría */}
            {showNewCategoryModal && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                        <div className="mt-3">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-medium text-gray-900">Solicitar Nueva Categoría</h3>
                                <button
                                    onClick={handleCancelNewCategory}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <XMarkIcon className="h-6 w-6" />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                    <h4 className="text-md font-medium text-blue-900 mb-2">Nueva Categoría</h4>
                                    <p className="text-sm text-blue-700">
                                        Solicita una nueva categoría de servicios para la plataforma.
                                    </p>
                                </div>

                                <div>
                                    <label htmlFor="new-category-name" className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre de la Categoría *
                                    </label>
                                    <input
                                        id="new-category-name"
                                        type="text"
                                        value={newCategoryForm.nombre_categoria}
                                        onChange={(e) => setNewCategoryForm(prev => ({ ...prev, nombre_categoria: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Ej: Marketing Digital, Consultoría Legal, etc."
                                    />
                                </div>

                                <div>
                                    <label htmlFor="new-category-description" className="block text-sm font-medium text-gray-700 mb-2">
                                        Descripción de la Categoría *
                                    </label>
                                    <textarea
                                        id="new-category-description"
                                        value={newCategoryForm.descripcion}
                                        onChange={(e) => setNewCategoryForm(prev => ({ ...prev, descripcion: e.target.value }))}
                                        rows={4}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Describe qué tipo de servicios incluiría esta categoría"
                                    />
                                </div>

                                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                                    <p className="text-sm text-yellow-800">
                                        <strong>Nota:</strong> Tu solicitud será revisada por el administrador. Una vez aprobada, la categoría estará disponible para todos los proveedores.
                                    </p>
                                </div>
                            </div>

                            <div className="flex justify-end space-x-3 mt-6">
                                <button
                                    onClick={handleCancelNewCategory}
                                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleSubmitNewCategory}
                                    disabled={!newCategoryForm.nombre_categoria.trim() || !newCategoryForm.descripcion.trim() || isSubmittingCategory}
                                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isSubmittingCategory ? 'Enviando...' : 'Enviar Solicitud'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProviderMyServicesPage;
