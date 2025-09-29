import { ProviderApplicationStatus } from './provider';

export type { ProviderApplicationStatus };

export interface User {
    id: number;
    name: string;
    email: string;
    role: UserRole;
    companyName?: string;
    ruc?: string;
    phone?: string;
    address?: string;
    createdAt: string;
    updatedAt: string;
    providerStatus?: 'none' | 'pending' | 'approved' | 'rejected';
    providerApplication?: ProviderApplicationStatus;
    accessToken?: string;
    foto_perfil?: string;
}

export type UserRole = 'client' | 'provider' | 'admin';

export interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    providerStatus: 'none' | 'pending' | 'approved' | 'rejected';
    providerApplication: ProviderApplicationStatus;
    login: (email: string, password: string) => Promise<void>;
    register: (data: { companyName: string; name: string; email: string; password: string; ruc?: string }) => Promise<void>;
    logout: () => Promise<void>;
    refreshToken: () => Promise<string>;
    reloadUserProfile: () => Promise<void>;
    submitProviderApplication: (data: any) => Promise<void>;
    resubmitProviderApplication: (data: any) => Promise<void>;
    updateProviderStatus: (status: 'none' | 'pending' | 'approved' | 'rejected') => void;
    updateProviderApplication: (application: ProviderApplicationStatus) => void;
    isLoading: boolean;
    error: string | null;
}

export interface LoginData {
    email: string;
    password: string;
}

export interface RegisterData {
    companyName: string;
    name: string;
    email: string;
    password: string;
    ruc?: string;
}

export interface SignUpData {
    nombre_empresa: string;
    nombre_persona: string;
    email: string;
    password: string;
    ruc?: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    expires_in: number;
}

export interface SignUpResponse {
    message: string;
    email: string;
    nombre_persona: string;
    nombre_empresa: string;
}

export interface AuthError {
    detail: string;
    status_code: number;
}
