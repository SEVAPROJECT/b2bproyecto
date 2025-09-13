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
        'patente': { id: 'patente', name: 'Patente Comercial', status: 'pending', isOptional: false, description: 'Patente Comercial Vigente' },
        'contrato': { id: 'cedula', name: 'Cédula de Identidad del Representante', status: 'pending', isOptional: false, description: 'Cédula de Identidad Vigente del Representante Legal de la Empresa' },
        'balance': { id: 'constitucion', name: 'Constitución de la Empresa', status: 'pending', isOptional: false, description: 'Documento de Constitución de la Empresa' },
        'certificado': { id: 'tributario', name: 'Certificado de Cumplimiento Tributario', status: 'pending', isOptional: false, description: 'Certificado de Cumplimiento Tributario Emitido por la SET' },
        'certificaciones': { id: 'certificaciones', name: 'Certificado de Calidad', status: 'pending', isOptional: true, description: 'Certificaciones de Calidad o Internacionales' },
        'certificados_rubro': { id: 'certificados_rubro', name: 'Certificaciones del Rubro', status: 'pending', isOptional: true, description: 'Certificados Varios del Rubro' },
    },
};
