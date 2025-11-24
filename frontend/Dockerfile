# Build stage
FROM node:22.14 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
# NOTA: El archivo .dockerignore excluye archivos sensibles (.env, credenciales, etc.)
# para prevenir que se copien accidentalmente al contenedor
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine

# Crear usuario no root para ejecutar nginx (mejores prácticas de seguridad)
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx || true

# Copiar archivos estáticos
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Crear directorios necesarios y cambiar propiedad al usuario nginx
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run && \
    chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /var/run /etc/nginx/nginx.conf && \
    chmod -R 755 /usr/share/nginx/html

# Cambiar al usuario no root
USER nginx

# Exponer puerto (nginx escuchará en el puerto especificado por PORT o 8080 por defecto)
EXPOSE 8080

# Ejecutar nginx como usuario no root
# NOTA: Si PORT no está definido, nginx escuchará en 8080 (puerto no privilegiado)
CMD ["/bin/sh", "-c", "envsubst '${PORT:-8080}' < /etc/nginx/nginx.conf > /etc/nginx/nginx.conf.tmp && mv /etc/nginx/nginx.conf.tmp /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]
