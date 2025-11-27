// services/locations.ts

import { API_CONFIG, buildApiUrl } from '../config/api';

// Interfaces para los datos de ubicación
export interface Departamento {
    id: number;
    nombre: string;
    id_departamento: number;
    created_at: string;
}

export interface Ciudad {
    id: number;
    nombre: string;
    id_ciudad: number;
    id_departamento: number;
    created_at: string;
}

export interface Barrio {
    id: number;
    nombre: string;
    id_barrio: number;
    id_ciudad: number;
}

// Función helper para manejar errores de la API
const handleApiError = async (response: Response): Promise<Error> => {
    try {
        const errorData = await response.json();
        return new Error(errorData.detail || 'Error desconocido');
    } catch {
        return new Error(`Error ${response.status}: ${response.statusText}`);
    }
};

// API de ubicaciones
export const locationsAPI = {
    // Obtener todos los departamentos
    async getDepartamentos(): Promise<Departamento[]> {
        try {
            const response = await fetch(buildApiUrl(API_CONFIG.LOCATIONS.DEPARTMENTS));
            
            if (!response.ok) {
                throw await handleApiError(response);
            }
            
            const data = await response.json();
            // Mapear los datos para incluir la propiedad id
            return data.map((dept: any) => ({
                ...dept,
                id: dept.id_departamento
            }));
        } catch (error) {
            console.error('❌ Error al obtener departamentos:', error);
            throw error;
        }
    },

    // Obtener ciudades por departamento
    async getCiudadesPorDepartamento(idDepartamento: number): Promise<Ciudad[]> {
        try {
            const url = buildApiUrl(`${API_CONFIG.LOCATIONS.CITIES}/${idDepartamento}`);
            console.log(`🔍 [locationsAPI] Obteniendo ciudades para departamento ID: ${idDepartamento}`);
            console.log(`🔗 [locationsAPI] URL: ${url}`);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw await handleApiError(response);
            }
            
            const data = await response.json();
            console.log(`✅ [locationsAPI] Respuesta recibida:`, data);
            console.log(`📊 [locationsAPI] Total de ciudades recibidas: ${Array.isArray(data) ? data.length : 'No es un array'}`);
            
            // Verificar que sea un array
            if (!Array.isArray(data)) {
                console.error('❌ [locationsAPI] La respuesta no es un array:', data);
                return [];
            }
            
            // Mapear los datos para incluir la propiedad id
            const ciudadesMapeadas = data.map((ciudad: any) => ({
                ...ciudad,
                id: ciudad.id_ciudad
            }));
            
            console.log(`✅ [locationsAPI] Ciudades mapeadas: ${ciudadesMapeadas.length}`);
            if (ciudadesMapeadas.length > 0) {
                console.log(`📋 [locationsAPI] Nombres de ciudades:`, ciudadesMapeadas.map(c => c.nombre));
            }
            
            return ciudadesMapeadas;
        } catch (error) {
            console.error('❌ Error al obtener ciudades:', error);
            throw error;
        }
    },

    // Obtener barrios por ciudad
    async getBarriosPorCiudad(idCiudad: number): Promise<Barrio[]> {
        try {
            const response = await fetch(buildApiUrl(`${API_CONFIG.LOCATIONS.NEIGHBORHOODS}/${idCiudad}`));
            
            if (!response.ok) {
                throw await handleApiError(response);
            }
            
            const data = await response.json();
            // Mapear los datos para incluir la propiedad id
            return data.map((barrio: any) => ({
                ...barrio,
                id: barrio.id_barrio
            }));
        } catch (error) {
            console.error('❌ Error al obtener barrios:', error);
            throw error;
        }
    }
};
