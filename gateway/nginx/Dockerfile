FROM nginx:1.25-alpine

# Remove default configuration
RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy custom gateway configurations
COPY nginx.conf /etc/nginx/nginx.conf

# Expose gateway port
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
