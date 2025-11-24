/**
 * Valida si un email tiene formato válido
 * Usa validación segura para evitar ReDoS (Regular Expression Denial of Service)
 */
export const isValidEmail = (email: string): boolean => {
    if (!email || typeof email !== 'string') {
        return false;
    }
    
    // Validación segura sin regex compleja: dividir en partes y validar cada una
    const parts = email.split('@');
    
    // Debe tener exactamente una @
    if (parts.length !== 2) {
        return false;
    }
    
    const [localPart, domain] = parts;
    
    // La parte local no puede estar vacía y no puede tener espacios
    if (!localPart || localPart.length === 0 || localPart.includes(' ')) {
        return false;
    }
    
    // El dominio debe tener al menos un punto y no puede tener espacios
    if (!domain || domain.length === 0 || domain.includes(' ')) {
        return false;
    }
    
    const domainParts = domain.split('.');
    
    // Debe tener al menos un punto (TLD separado)
    if (domainParts.length < 2) {
        return false;
    }
    
    // El TLD (última parte) debe tener al menos 2 caracteres
    const tld = domainParts[domainParts.length - 1];
    if (!tld || tld.length < 2) {
        return false;
    }
    
    // Validar que no haya partes vacías en el dominio
    if (domainParts.some(part => part.length === 0)) {
        return false;
    }
    
    return true;
};

/**
 * Valida si una contraseña cumple con los requisitos mínimos
 * Usa validación segura sin regex compleja para evitar ReDoS
 */
export const isValidPassword = (password: string): boolean => {
    if (!password || typeof password !== 'string') {
        return false;
    }
    
    // Mínimo 8 caracteres
    if (password.length < 8) {
        return false;
    }
    
    // Debe contener al menos una letra
    const hasLetter = /[A-Za-z]/.test(password);
    if (!hasLetter) {
        return false;
    }
    
    // Debe contener al menos un número
    const hasNumber = /\d/.test(password);
    if (!hasNumber) {
        return false;
    }
    
    // Solo caracteres permitidos: letras, números y caracteres especiales específicos
    const allowedChars = /^[A-Za-z\d@$!%*#?&]+$/;
    if (!allowedChars.test(password)) {
        return false;
    }
    
    return true;
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
