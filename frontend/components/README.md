# Componentes de Ubicación

Este directorio contiene componentes para manejar la selección de ubicaciones (departamentos, ciudades y barrios) con búsqueda en tiempo real.

## Componentes Disponibles

### 1. LocationSelector
Un selector genérico para cualquier tipo de ubicación con búsqueda en tiempo real.

**Props:**
- `label`: Etiqueta del campo
- `placeholder`: Texto de placeholder
- `options`: Array de opciones disponibles
- `value`: Valor seleccionado
- `onChange`: Función callback cuando cambia la selección
- `isLoading`: Estado de carga
- `disabled`: Si el campo está deshabilitado
- `error`: Mensaje de error
- `className`: Clases CSS adicionales

**Uso:**
```tsx
<LocationSelector
    label="Departamento"
    placeholder="Selecciona un departamento..."
    options={departamentos}
    value={selectedDepartamento}
    onChange={setSelectedDepartamento}
    isLoading={isLoading}
/>
```

### 2. AddressSelector
Selector completo de dirección que maneja las dependencias entre departamento, ciudad y barrio.

**Props:**
- `onAddressChange`: Callback con la dirección completa seleccionada
- `initialValues`: Valores iniciales (opcional)
- `className`: Clases CSS adicionales
- `disabled`: Si está deshabilitado

**Uso:**
```tsx
<AddressSelector
    onAddressChange={(address) => {
        console.log('Departamento:', address.departamento?.nombre);
        console.log('Ciudad:', address.ciudad?.nombre);
        console.log('Barrio:', address.barrio?.nombre);
    }}
/>
```

### 3. LocationDemo
Componente de demostración que muestra cómo usar el AddressSelector.

## Servicios

### locations.ts
API para consumir los endpoints de ubicaciones del backend:

- `getDepartamentos()`: Obtiene todos los departamentos
- `getCiudadesPorDepartamento(idDepartamento)`: Obtiene ciudades por departamento
- `getBarriosPorCiudad(idCiudad)`: Obtiene barrios por ciudad

## Características

✅ **Búsqueda en tiempo real**: Los usuarios pueden escribir para filtrar opciones
✅ **Dependencias automáticas**: Los campos se habilitan secuencialmente
✅ **Validación**: Campos obligatorios marcados claramente
✅ **Responsive**: Diseño adaptativo para móviles y desktop
✅ **Accesibilidad**: Labels, placeholders y mensajes de error claros
✅ **Estados de carga**: Indicadores visuales durante las peticiones API

## Integración en el Onboarding

El `AddressSelector` ya está integrado en el paso 2 del onboarding de proveedores (`Step2_Address`), reemplazando los campos de texto simples por selectores inteligentes.

## Estilos

Los componentes utilizan Tailwind CSS para los estilos. Asegúrate de que Tailwind esté configurado en tu proyecto.

## Dependencias

- React 19+
- TypeScript
- Tailwind CSS
- API de ubicaciones del backend
