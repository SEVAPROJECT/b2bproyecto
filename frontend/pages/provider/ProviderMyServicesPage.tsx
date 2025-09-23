import React, { useState, useEffect, useContext } from 'react';
import { 
    BriefcaseIcon, 
    MagnifyingGlassIcon, 
    PencilIcon, 
    TrashIcon,
    PlusIcon,
    XMarkIcon,
    CameraIcon,
    UploadCloudIcon
} from '../../components/icons';
import { API_CONFIG, buildApiUrl } from '../../config/api';
import { AuthContext } from '../../contexts/AuthContext';
import { categoriesAPI, providerServicesAPI, servicesAPI, categoryRequestsAPI, serviceRequestsAPI } from '../../services/api';

// Funciones auxiliares
const formatNumber = (num: number): string => {
    if (isNaN(num) || num === null || num === undefined) return '0';
    return num.toLocaleString('es-PY', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
};

// Función para formatear precio con puntos de mil mientras se escribe
const formatPriceInput = (value: string): string => {
    // Remover todos los caracteres no numéricos excepto punto y coma
    const cleanValue = value.replace(/[^\d.,]/g, '');
    
    // Si está vacío, retornar vacío
    if (!cleanValue) return '';
    
    // Si el valor ya tiene puntos, removerlos todos y reformatear
    const numericOnly = cleanValue.replace(/\./g, '');
    
    // Separar parte entera y decimal
    const parts = numericOnly.split(',');
    const integerPart = parts[0];
    const decimalPart = parts[1];
    
    // Formatear la parte entera con puntos de mil usando una función más simple
    const formatWithDots = (num: string): string => {
        return num.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
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
    const withoutThousandsSeparators = formattedValue.replace(/\.(?=\d{3})/g, '');
    
    // Parsear el número resultante
    const parsed = parseFloat(withoutThousandsSeparators);
    return isNaN(parsed) ? 0 : parsed;
};

const getTariffsSummary = (tarifas: any[], rateTypes: any[] = []): string => {
    if (!tarifas || tarifas.length === 0) return 'Sin tarifas';
    
    const tariffTexts = tarifas.map(tarifa => {
        const monto = formatNumber(parseFloat(tarifa.monto?.toString().replace(',', '.') || '0') || 0);
        const descripcion = tarifa.descripcion || 'Sin descripción';
        const tipoTarifa = rateTypes.find(rt => rt.id_tarifa === tarifa.id_tarifa)?.nombre || 'Sin tipo';
        return `${monto} ₲ (${tipoTarifa}) - ${descripcion}`;
    });

    return tariffTexts.join(', ');
};

// Función de filtrado de servicios
const filterServices = (services: any[], filters: any) => {
    return services.filter(service => {
        // Filtro por categoría
        if (filters.categoryFilter !== 'all' && service.id_categoria?.toString() !== filters.categoryFilter) {
            return false;
        }

        // Filtro por nombre con autocompletado inteligente
        const nameFilterStr = filters.nameFilter?.toString().trim() || '';
        if (nameFilterStr !== '') {
            const searchTerm = nameFilterStr.toLowerCase();
            const serviceName = service.nombre?.toLowerCase() || '';

            // Búsqueda por palabras completas o inicio de palabras
            const searchWords = searchTerm.split(' ').filter(word => word.length > 0);
            const nameWords = serviceName.split(' ').filter(word => word.length > 0);

            // Verificar si todas las palabras de búsqueda están presentes
            const matches = searchWords.every(searchWord =>
                nameWords.some(nameWord => nameWord.startsWith(searchWord))
            );

            if (!matches) {
                return false;
            }
        }

        // Filtro por precio
        const minPriceStr = filters.minPrice?.toString().trim() || '';
        const maxPriceStr = filters.maxPrice?.toString().trim() || '';

        const minPriceValue = minPriceStr !== '' && !isNaN(parseFloat(minPriceStr)) ? parseFloat(minPriceStr) : null;
        const maxPriceValue = maxPriceStr !== '' && !isNaN(parseFloat(maxPriceStr)) ? parseFloat(maxPriceStr) : null;

        const hasMinPriceFilter = minPriceValue !== null && minPriceValue > 0;
        const hasMaxPriceFilter = maxPriceValue !== null && maxPriceValue > 0;

        if (hasMinPriceFilter || hasMaxPriceFilter) {
            const price = service.precio || 0;

            if (hasMinPriceFilter && price < minPriceValue) {
                return false;
            }
            if (hasMaxPriceFilter && price > maxPriceValue) {
                return false;
            }
        }

        // Filtro por estado
        if (filters.statusFilter !== 'all') {
            const isActive = service.estado === true;
            if (filters.statusFilter === 'active' && !isActive) {
                return false;
            }
            if (filters.statusFilter === 'inactive' && isActive) {
                return false;
            }
        }

        return true;
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
    const [editingService, setEditingService] = useState<any | null>(null);
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
    const [selectedTemplate, setSelectedTemplate] = useState<any | null>(null);
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
                monto: tarifa.monto ? formatPriceInput(tarifa.monto.toString()) : ''
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

    const handleRemoveImage = () => {
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

            // Actualizar solo el servicio específico en la lista sin recargar todo
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
            id_tarifa: rateTypes[0]?.id_tarifa || 0
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

            // Debug: Verificar datos del formulario
            console.log('🔍 Datos del formulario:', {
                nombre: templateData.nombre,
                descripcion: templateData.descripcion,
                precio: templateData.precio,
                id_moneda: templateData.id_moneda
            });

            // Debug: Verificar plantilla seleccionada
            console.log('🔍 Plantilla seleccionada:', {
                id_categoria: selectedTemplate.id_categoria,
                categoria: selectedTemplate.categoria,
                nombre: selectedTemplate.nombre
            });

            // Crear servicio optimista para evitar refresco de pantalla
            const tempId = Date.now(); // ID temporal
            const selectedCurrency = currencies.find(c => c.id_moneda === templateData.id_moneda) || currencies[0];
            
            // Crear servicio optimista con estructura completa
            const optimisticService = {
                id_servicio: tempId,
                nombre: templateData.nombre,
                descripcion: templateData.descripcion,
                precio: templateData.precio,
                id_categoria: selectedTemplate.id_categoria, // ✅ Usar el ID de categoría de la plantilla
                id_perfil: selectedTemplate.id_perfil,
                id_moneda: templateData.id_moneda,
                estado: true, // ✅ Activo por defecto
                imagen: selectedTemplate.imagen || null,
                tarifas: selectedTemplate.tarifas || [],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                // Datos de categoría completos (para renderizado directo)
                categoria: {
                    id_categoria: selectedTemplate.id_categoria,
                    nombre: selectedTemplate.categoria?.nombre || 'Categoría',
                    descripcion: selectedTemplate.categoria?.descripcion || '',
                    estado: true
                },
                // Datos de moneda completos
                moneda: {
                    id_moneda: selectedCurrency.id_moneda,
                    nombre: selectedCurrency.nombre,
                    codigo_iso_moneda: selectedCurrency.codigo_iso_moneda,
                    simbolo: selectedCurrency.simbolo
                },
                isOptimistic: true // Marcar como optimista
            };

            // Debug: Verificar si la categoría existe en el array categories
            const foundCategory = categories.find(c => c.id_categoria === selectedTemplate.id_categoria);
            console.log('🔍 Categoría encontrada en array:', foundCategory);
            console.log('🔍 Array de categorías:', categories.map(c => ({ id: c.id_categoria, nombre: c.nombre })));

            // Debug: Verificar datos del servicio optimista
            console.log('🔍 Servicio optimista creado:', {
                nombre: optimisticService.nombre,
                descripcion: optimisticService.descripcion,
                precio: optimisticService.precio,
                id_categoria: optimisticService.id_categoria,
                estado: optimisticService.estado,
                categoria: optimisticService.categoria
            });

            // Debug: Verificar qué categoría se encontrará en el renderizado
            const categoryForRender = categories.find(c => c.id_categoria === optimisticService.id_categoria);
            console.log('🔍 Categoría para renderizado:', categoryForRender);
            console.log('🔍 Nombre de categoría que se mostrará:', categoryForRender?.nombre || 'No especificado');

            // Actualización optimista: agregar el servicio inmediatamente
            setServices(prev => {
                const newServices = [optimisticService, ...prev];
                console.log('🔍 Servicios después de agregar optimista:', newServices.length);
                console.log('🔍 Primer servicio (optimista):', newServices[0]);
                return newServices;
            });

            // Limpiar formulario y cerrar modal inmediatamente
            setShowTemplateModal(false);
            setSelectedTemplate(null);
            setTemplateForm({ nombre: '', descripcion: '', precio: '', id_moneda: 1 });
            
            // Mostrar mensaje de éxito inmediatamente
            setSuccess('Servicio creado exitosamente desde plantilla');
            setTimeout(() => setSuccess(null), 3000);

            // Llamar a la API en segundo plano
            try {
                const newService = await providerServicesAPI.createServiceFromTemplate(templateData, accessToken);
                
                // Reemplazar el servicio optimista con el real
                setServices(prev => prev.map(service => 
                    service.id_servicio === tempId 
                        ? { ...newService, isOptimistic: false }
                        : service
                ));
            } catch (apiError) {
                // Si falla, remover el servicio optimista
                setServices(prev => prev.filter(service => service.id_servicio !== tempId));
                throw apiError;
            }

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
                            <label className="block text-sm font-medium text-gray-700 mb-2">Categoría</label>
                            <select
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
                            <label className="block text-sm font-medium text-gray-700 mb-2">Nombre del Servicio</label>
                            <input
                                type="text"
                                value={filters.nameFilter}
                                onChange={(e) => setFilters(prev => ({ ...prev, nameFilter: e.target.value }))}
                                placeholder="Escribe para buscar..."
                                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Filtro por estado */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Estado</label>
                            <select
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
                            <label className="block text-sm font-medium text-gray-700 mb-2">Precio Mínimo</label>
                            <input
                                type="number"
                                value={filters.minPrice}
                                onChange={(e) => setFilters(prev => ({ ...prev, minPrice: e.target.value }))}
                                placeholder="0"
                                min="0"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Filtro por precio máximo */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Precio Máximo</label>
                            <input
                                type="number"
                                value={filters.maxPrice}
                                onChange={(e) => setFilters(prev => ({ ...prev, maxPrice: e.target.value }))}
                                placeholder="Sin límite"
                                min="0"
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

                {/* Success Messages */}
                {/* {success && (
                    <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4">
                        <div className="text-sm text-green-700">{success}</div>
                    </div>
                )} */}

                {/* Services List */}
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                    {filteredServices.length > 0 ? (
                        <div className="divide-y divide-gray-200">
                            {filteredServices.map((service) => (
                                <div key={service.id_servicio} className={`p-4 transition-colors duration-200 ${service.isOptimistic ? 'bg-blue-50 border-l-4 border-blue-400' : 'hover:bg-gray-50'}`}>
                                    <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
                                        {/* Imagen del servicio */}
                                        <div className="flex-shrink-0 mx-auto sm:mx-0">
                                            {service.imagen ? (
                                                <img
                                                    src={`${API_CONFIG.BASE_URL.replace('/api/v1', '')}${service.imagen}`}
                                                    alt={service.nombre}
                                                    className="h-16 w-16 object-cover rounded-lg border border-gray-200"
                                                    onError={(e) => {
                                                        const target = e.target as HTMLImageElement;
                                                        target.style.display = 'none';
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
                                            <div className="flex items-center gap-2 justify-center sm:justify-start">
                                                <h3 className="text-lg font-semibold text-gray-900 break-words">{service.nombre}</h3>
                                                {service.isOptimistic && (
                                                    <div className="flex items-center gap-1">
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                                        <span className="text-xs text-blue-600 font-medium">Creando...</span>
                                                    </div>
                                                )}
                                            </div>
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
                    ) : services.length === 0 ? (
                        <div className="text-center py-12">
                            <BriefcaseIcon className="mx-auto h-12 w-12 text-gray-400" />
                            <h3 className="mt-2 text-sm font-medium text-gray-900">No tienes servicios</h3>
                            <p className="mt-1 text-sm text-gray-500">
                                Solicita nuevos servicios para comenzar a ofrecerlos.
                            </p>
                        </div>
                    ) : (
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
                    )}
                </div>
            </div>

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
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre del servicio *
                                    </label>
                                    <input
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
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Descripción *
                                    </label>
                                    <textarea
                                        value={editForm.descripcion}
                                        onChange={(e) => setEditForm(prev => ({ ...prev, descripcion: e.target.value }))}
                                        rows={3}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors resize-none"
                                    />
                                </div>

                                {/* Precio y Moneda */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Precio *
                                        </label>
                                        <input
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
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Moneda
                                        </label>
                                        <select
                                            value={editForm.id_moneda}
                                            onChange={(e) => setEditForm(prev => ({ ...prev, id_moneda: parseInt(e.target.value) }))}
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
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Imagen del servicio
                                    </label>
                                    
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
                                        <label className="block text-sm font-medium text-gray-700">
                                            Tarifas del servicio
                                        </label>
                                        <button
                                            onClick={addTarifa}
                                            className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                                        >
                                            <PlusIcon className="h-3 w-3 mr-1" />
                                            Agregar Tarifa
                                        </button>
                                    </div>

                                    {editForm.tarifas.map((tarifa, index) => (
                                        <div key={index} className="border border-gray-200 rounded-lg p-3 mb-3">
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
                                                    <label className="block text-xs font-medium text-gray-600 mb-1">
                                                        Monto
                                                    </label>
                                                    <input
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
                                                    <label className="block text-xs font-medium text-gray-600 mb-1">
                                                        Descripción
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={tarifa.descripcion}
                                                        onChange={(e) => updateTarifa(index, 'descripcion', e.target.value)}
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-600 mb-1">
                                                        Tipo de Tarifa
                                                    </label>
                                                    <select
                                                        value={tarifa.id_tarifa}
                                                        onChange={(e) => updateTarifa(index, 'id_tarifa', parseInt(e.target.value))}
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

                            {!showNewServiceRequest ? (
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
                                                    {templates.length} servicio{templates.length !== 1 ? 's' : ''} encontrado{templates.length !== 1 ? 's' : ''}
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
                                                            <div
                                                                key={template.id_servicio}
                                                                onClick={() => handleSelectTemplate(template)}
                                                                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
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
                                                            </div>
                                                        ))}
                                                    </div>

                                                    {/* Formulario de personalización */}
                                                    {selectedTemplate && (
                                                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                                            <h5 className="text-sm font-medium text-gray-700 mb-3">Personalizar tu Servicio</h5>
                                                            
                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                <div>
                                                                    <label className="block text-xs font-medium text-gray-600 mb-1">
                                                                        Nombre del Servicio
                                                                    </label>
                                                                    <input
                                                                        type="text"
                                                                        value={selectedTemplate.nombre}
                                                                        readOnly
                                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-gray-100 text-gray-600 cursor-not-allowed"
                                                                    />
                                                                </div>
                                                                <div>
                                                                    <label className="block text-xs font-medium text-gray-600 mb-1">
                                                                        Precio *
                                                                    </label>
                                                                    <input
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
                                                                    <label className="block text-xs font-medium text-gray-600 mb-1">
                                                                        Moneda *
                                                                    </label>
                                                                    <select
                                                                        value={templateForm.id_moneda}
                                                                        onChange={(e) => setTemplateForm(prev => ({ ...prev, id_moneda: parseInt(e.target.value) }))}
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
                                                                <label className="block text-xs font-medium text-gray-600 mb-1">
                                                                    Descripción
                                                                </label>
                                                                <textarea
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
                            ) : (
                                /* Formulario de Solicitud de Nuevo Servicio */
                                <div className="space-y-4">
                                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                        <h4 className="text-md font-medium text-blue-900 mb-2">Solicitar Nuevo Servicio</h4>
                                        <p className="text-sm text-blue-700">
                                            Categoría: <strong>{categories.find(c => c.id_categoria === selectedCategory)?.nombre}</strong>
                                        </p>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Nombre del Servicio *
                                        </label>
                                        <input
                                            type="text"
                                            value={newServiceRequest.nombre}
                                            onChange={(e) => setNewServiceRequest(prev => ({ ...prev, nombre: e.target.value }))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder="Ingresa el nombre del servicio que deseas"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Descripción del Servicio *
                                        </label>
                                        <textarea
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
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Nombre de la Categoría *
                                    </label>
                                    <input
                                        type="text"
                                        value={newCategoryForm.nombre_categoria}
                                        onChange={(e) => setNewCategoryForm(prev => ({ ...prev, nombre_categoria: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Ej: Marketing Digital, Consultoría Legal, etc."
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Descripción de la Categoría *
                                    </label>
                                    <textarea
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
