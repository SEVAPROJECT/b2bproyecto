export interface Service {
    id: number;
    name: string;
    description: string;
    price: number;
    category: string;
    provider: string;
    rating: number;
    reviews: number;
    image?: string;
    location: string;
    availability: string;
    tags: string[];
}

export interface TarifaServicio {
    id_tarifa_servicio: number;
    monto: number;
    descripcion: string;
    fecha_inicio: string;
    fecha_fin: string | null;
    id_tarifa: number | null;
    nombre_tipo_tarifa: string | null;
}

export interface BackendService {
    id_servicio: number;
    nombre: string;
    descripcion: string;
    precio: number | null;
    moneda: string;
    id_categoria: number;
    razon_social: string | null;
    nombre_contacto: string | null;
    telefono_contacto: string | null;
    email_contacto: string | null;
    departamento: string | null;
    ciudad: string | null;
    imagen: string | null;
    estado: boolean;
    created_at: string;
    updated_at: string;
    tarifas: TarifaServicio[];
}

export interface Category {
    id: number;
    name: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    servicesCount: number;
}

export interface BackendCategory {
    id_categoria: number;
    nombre: string;
    descripcion: string | null;
    created_at: string;
    updated_at: string;
}

export interface ServiceRequest {
    id: number;
    serviceId: number;
    clientId: number;
    status: 'pending' | 'accepted' | 'rejected' | 'completed';
    message: string;
    createdAt: string;
    updatedAt: string;
}
