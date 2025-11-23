/**
 * Valida si un email tiene formato válido
 */
export const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

/**
 * Valida si una contraseña cumple con los requisitos mínimos
 */
export const isValidPassword = (password: string): boolean => {
    // Mínimo 8 caracteres, al menos una letra y un número
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/;
    return passwordRegex.test(password);
};

/**
 * Valida si un teléfono tiene formato válido
 */
export const isValidPhone = (phone: string): boolean => {
    // Formato paraguayo: +595XXXXXXXXX o 09XXXXXXXX
    const phoneRegex = /^(\+595|0)\d{8,9}$/;
    return phoneRegex.test(phone.replaceAll(/\s/g, ''));
};

/**
 * Valida si un RUC tiene formato válido
 */
export const isValidRUC = (ruc: string): boolean => {
    // RUC paraguayo: 7 u 8 dígitos seguidos de un guión y un dígito verificador
    const rucRegex = /^\d{7,8}-\d$/;
    return rucRegex.test(ruc);
};

/**
 * Valida si un campo requerido no está vacío
 */
export const isRequired = (value: string | number | null | undefined): boolean => {
    if (typeof value === 'string') {
        return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
};

/**
 * Valida si un número está en un rango específico
 */
export const isInRange = (value: number, min: number, max: number): boolean => {
    return value >= min && value <= max;
};

/**
 * Valida si una fecha es válida y no es futura
 */
export const isValidDate = (dateString: string, allowFuture: boolean = false): boolean => {
    const date = new Date(dateString);
    const today = new Date();
    
    if (Number.isNaN(date.getTime())) {
        return false;
    }
    
    if (!allowFuture && date > today) {
        return false;
    }
    
    return true;
};
