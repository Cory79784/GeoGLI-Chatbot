# Frontend Dockerfile for UNCCD GeoGLI Chatbot
FROM nginx:alpine

# Copy the HTML file to nginx web root
COPY index.html /usr/share/nginx/html/

# Copy custom nginx configuration if needed
# COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

