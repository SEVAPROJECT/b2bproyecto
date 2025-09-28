# Admin Stats Router

Este archivo contiene endpoints optimizados para obtener estadísticas y contadores del dashboard administrativo.

## Endpoints disponibles:

### 1. Contadores individuales:
- `GET /users/count` - Total de usuarios
- `GET /categories/count` - Total de categorías  
- `GET /services/count` - Total de servicios
- `GET /providers/count` - Total de proveedores

### 2. Endpoint consolidado:
- `GET /dashboard/stats` - Todas las estadísticas en una sola llamada

## Uso en el frontend:

### Opción 1: Llamadas individuales (más flexible)
```typescript
// Llamar cada endpoint por separado
const usersCount = await fetch('/admin/users/count');
const categoriesCount = await fetch('/admin/categories/count');
const servicesCount = await fetch('/admin/services/count');
```

### Opción 2: Llamada consolidada (más eficiente)
```typescript
// Una sola llamada para todas las estadísticas
const dashboardStats = await fetch('/admin/dashboard/stats');
const data = await dashboardStats.json();

// Respuesta:
{
  "total_users": 25,
  "total_categories": 8,
  "total_services": 45,
  "total_providers": 12,
  "total_verification_requests": 20,
  "approved_requests": 15,
  "verification_rate": 75,
  "message": "Estadísticas del dashboard obtenidas exitosamente"
}
```

## Ventajas del endpoint consolidado:

1. **Rendimiento**: Una sola llamada HTTP en lugar de 4
2. **Eficiencia**: Consultas paralelas en la base de datos
3. **Simplicidad**: El frontend recibe todos los datos de una vez
4. **Escalabilidad**: Fácil agregar nuevas métricas

## Implementación en AdminDashboardPage:

```typescript
// Reemplazar las 4 llamadas individuales por una sola:
const apiCalls = [
    categoriesAPI.getCategories(user.accessToken, true).catch(() => []),
    servicesAPI.getServicesWithProviders(user.accessToken).catch(() =>
        servicesAPI.getServices(user.accessToken).catch(() => [])
    ),
    adminAPI.getAllSolicitudesVerificacion(user.accessToken).catch(() => []),
    // ✅ Nueva llamada consolidada
    fetch(buildApiUrl('/admin/dashboard/stats'), {
        headers: { 'Authorization': `Bearer ${user.accessToken}` }
    }).then(r => r.ok ? r.json() : {}).catch(() => ({}))
];

// Procesar la respuesta:
const dashboardStats = results[3].status === 'fulfilled' ? results[3].value : {};
const totalUsers = dashboardStats.total_users || 0;
const totalCategories = dashboardStats.total_categories || 0;
const totalServices = dashboardStats.total_services || 0;
const verificationRate = dashboardStats.verification_rate || 0;
```
