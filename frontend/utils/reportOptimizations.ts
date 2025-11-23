// Utilidades para optimizar el rendimiento de reportes

// Función para debounce (evitar múltiples llamadas)
export const debounce = <T extends (...args: any[]) => any>(
    func: T,
    wait: number
): ((...args: Parameters<T>) => void) => {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
};

// Función para throttle (limitar frecuencia de llamadas)
export const throttle = <T extends (...args: any[]) => any>(
    func: T,
    limit: number
): ((...args: Parameters<T>) => void) => {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
};

// Función para memoizar resultados de API
export class ReportCache {
    private readonly cache = new Map<string, { data: unknown; timestamp: number }>();
    private readonly TTL = 5 * 60 * 1000; // 5 minutos

    get(key: string): unknown | null {
        const item = this.cache.get(key);
        if (!item) return null;
        
        if (Date.now() - item.timestamp > this.TTL) {
            this.cache.delete(key);
            return null;
        }
        
        return item.data;
    }

    set(key: string, data: unknown): void {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    clear(): void {
        this.cache.clear();
    }
}

// Función para optimizar procesamiento de datos grandes
export const processLargeDataset = <T>(
    data: T[],
    processor: (batch: T[]) => void,
    batchSize: number = 100
): Promise<void> => {
    return new Promise((resolve) => {
        let index = 0;
        
        const processBatch = () => {
            const batch = data.slice(index, index + batchSize);
            if (batch.length > 0) {
                processor(batch);
                index += batchSize;
                // Usar setTimeout para no bloquear el hilo principal
                setTimeout(processBatch, 0);
            } else {
                resolve();
            }
        };
        
        processBatch();
    });
};

// Función para optimizar filtros
export const optimizeFilters = (filters: any): any => {
    const optimized: any = {};
    
    for (const key of Object.keys(filters)) {
        const value = filters[key];
        if (value !== null && value !== undefined && value !== '') {
            optimized[key] = value;
        }
    }
    
    return optimized;
};

// Función para paginación virtual
export const getVirtualPage = <T>(
    data: T[],
    page: number,
    pageSize: number
): { items: T[]; totalPages: number; hasMore: boolean } => {
    const startIndex = page * pageSize;
    const endIndex = startIndex + pageSize;
    const items = data.slice(startIndex, endIndex);
    const totalPages = Math.ceil(data.length / pageSize);
    const hasMore = endIndex < data.length;
    
    return { items, totalPages, hasMore };
};








