FROM nginx:1.21-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/

# Create necessary directories
RUN mkdir -p /var/www/static
RUN mkdir -p /var/www/media

# Copy static files (this will be done in docker-compose)
# The actual static files will be mounted as a volume in docker-compose

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
