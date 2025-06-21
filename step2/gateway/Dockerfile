FROM nginx:alpine

COPY default.conf.template /etc/nginx/templates/default.conf.template

COPY ./certbot/www /var/www/certbot/www
COPY ./certbot/conf /etc/letsencrypt
