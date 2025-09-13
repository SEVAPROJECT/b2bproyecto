export interface ChartDataPoint {
    name: string;
    value: number;
    [key: string]: any;
}

export interface Faq {
    question: string;
    answer: string;
}

export interface Location {
    department: string;
    city: string;
    neighborhood?: string;
    street?: string;
    number?: string;
    reference?: string;
    coords?: {
        lat: number;
        lng: number;
    };
}

export interface ApiResponse<T> {
    data: T;
    message?: string;
    success: boolean;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
}

export interface FilterOptions {
    search?: string;
    category?: string;
    dateRange?: {
        start: string;
        end: string;
    };
    priceRange?: {
        min: number;
        max: number;
    };
    location?: {
        department?: string;
        city?: string;
    };
    rating?: number;
    currency?: string;
}
