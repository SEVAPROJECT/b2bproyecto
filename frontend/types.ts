
import type React from 'react';

export interface Service {
  id: string;
  title: string;
  description: string;
  longDescription: string;
  category: string;
  price: number;
  priceType: 'por hora' | 'por proyecto';
  providerId: string;
  providerName: string;
  providerLogoUrl: string;
  rating: number;
  reviewCount: number;
  imageUrl: string;
  createdAt: string;
  status: 'active' | 'inactive';
}

export interface Category {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

// Tipos para backend (categorías)
export interface BackendCategory {
  id_categoria: number;
  nombre: string;
  estado: boolean;
  created_at: string;
}

export interface BackendCategoryIn {
  nombre: string;
  estado: boolean;
}

export interface BackendCategoryOut {
  id_categoria: number;
  nombre: string;
  estado: boolean;
  created_at: string;
}

// Tipos para backend (servicios)
export interface BackendService {
  id_servicio: number;
  id_categoria: number | null;
  id_perfil: number;
  id_moneda: number | null;
  nombre: string;
  descripcion: string;
  precio: number;
  estado: boolean;
  created_at: string;
  // Propiedades adicionales del marketplace
  razon_social: string | null;
  nombre_contacto: string | null;
  departamento: string | null;
  ciudad: string | null;
  barrio: string | null;
  codigo_iso_moneda: string | null;
  nombre_moneda: string | null;
  simbolo_moneda: string | null;
  imagen: string | null;
  tarifas: any[];
}

export interface BackendServiceIn {
  nombre: string;
  descripcion: string;
  precio: number;
  id_categoria: number;
  id_moneda: number;
}

export interface BackendServiceOut {
  id_servicio: number;
  id_categoria: number | null;
  id_perfil: number;
  id_moneda: number | null;
  nombre: string;
  descripcion: string;
  precio: number;
  estado: boolean;
  created_at: string;
}

// Tipos para solicitudes de servicios
export interface ServiceRequest {
  id_solicitud: number;
  id_perfil: number;
  id_categoria: number | null;
  nombre_servicio: string;
  descripcion: string;
  estado_aprobacion: 'pendiente' | 'aprobada' | 'rechazada';
  comentario_admin: string | null;
  created_at: string;

  // Información adicional (opcional para compatibilidad)
  nombre_categoria?: string | null;
  nombre_empresa?: string | null;
  nombre_contacto?: string | null;
  email_contacto?: string | null;
}

export interface ServiceRequestIn {
  nombre_servicio: string;
  descripcion: string;
  id_categoria: number;
  comentario_admin?: string | null;
}

export interface ServiceRequestOut {
  id_solicitud: number;
  id_perfil: number;
  nombre_servicio: string;
  descripcion: string;
  estado_aprobacion: string;
  comentario_admin: string | null;
  created_at: string;

  // Información adicional
  nombre_categoria?: string | null;
  nombre_empresa?: string | null;
  nombre_contacto?: string | null;
  email_contacto?: string | null;
}

// Tipos para monedas
export interface Currency {
  id_moneda: number;
  codigo_iso_moneda: string;
  nombre: string;
  simbolo: string;
  estado: boolean;
  created_at: string;
}

// Tipos para tipos de tarifa
export interface RateType {
  id_tarifa: number;
  nombre: string;
  descripcion: string;
  estado: boolean;
  created_at: string;
}

export interface Faq {
  question: string;
  answer: string;
}

export type UserRole = 'client' | 'provider' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  companyName: string;
  accessToken?: string;
}

export interface Reservation {
    id: string;
    serviceId: string;
    serviceTitle: string;
    date: string;
    status: 'pending' | 'confirmed' | 'completed' | 'cancelled';
}

export interface ChartDataPoint {
    name: string; // e.g., 'Jan', 'Feb'
    value: number;
}

// Interfaces para autenticación
export interface SignUpData {
    email: string;
    password: string;
    nombre_persona: string;
    nombre_empresa: string;
    ruc?: string;
}

export interface SignUpResponse {
    message: string;
    user_id?: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
}

export interface LoginData {
    email: string;
    password: string;
}

export interface AuthError {
    detail: string;
    status_code: number;
}

// Nuevas interfaces para onboarding de proveedor
export interface DocumentUpload {
  id: string;
  name: string;
  status: 'pending' | 'uploaded' | 'observado' | 'aprobado' | 'rechazado';
  file?: File;
  isOptional: boolean;
  description: string;
  observations?: string; // Observaciones del administrador
}

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
  documents: Record<string, DocumentUpload>;
}

// Nueva interfaz para el estado de la solicitud de proveedor
export interface ProviderApplicationStatus {
  status: 'none' | 'pending' | 'approved' | 'rejected';
  submittedAt?: string;
  reviewedAt?: string;
  observations?: string; // Observaciones generales del administrador
  documentObservations?: Record<string, string>; // Observaciones por documento
  canResubmit?: boolean;
  resubmissionDeadline?: string;
}