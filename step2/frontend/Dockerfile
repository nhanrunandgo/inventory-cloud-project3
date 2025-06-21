# Use the official lightweight Nginx image
FROM nginx:alpine

# Copy custom Nginx config
COPY default.conf /etc/nginx/conf.d/default.conf

# Copy static HTML content
COPY static/ /usr/share/nginx/html
