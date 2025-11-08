import { ProviderOnboardingData } from '../types/provider';

export const initialOnboardingData: ProviderOnboardingData = {
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
        'certificados_rubro': { id: 'certificados_rubro', name: 'Certificacion del Rubro', status: 'pending', isOptional: false, description: 'Título que certifica la profesión.' },
    },
};
