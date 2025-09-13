export interface ProviderOnboardingData {
    company: {
        tradeName: string;
    };
    address: {
        department: string;
        city: string;
        neighborhood: string;
        street: string;
        number: string;
        reference: string;
        coords: { lat: number; lng: number } | null;
    };
    branch: {
        name: string;
        phone: string;
        email: string;
        useFiscalAddress: boolean;
    };
    documents: {
        [key: string]: DocumentUpload;
    };
}

export interface DocumentUpload {
    id: string;
    name: string;
    status: 'pending' | 'uploaded' | 'approved' | 'rejected';
    isOptional: boolean;
    description: string;
    file?: File;
    url?: string;
    rejectionReason?: string;
}

export interface ProviderApplicationStatus {
    status: 'none' | 'pending' | 'approved' | 'rejected';
    submittedAt?: string;
    reviewedAt?: string;
    rejectionReason?: string;
    documents: {
        [key: string]: {
            status: 'pending' | 'uploaded' | 'approved' | 'rejected';
            rejectionReason?: string;
        };
    };
}
