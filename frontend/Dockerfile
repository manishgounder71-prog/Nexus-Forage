FROM nginx:alpine

COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/css/ /usr/share/nginx/html/css/
COPY frontend/js/ /usr/share/nginx/html/js/

EXPOSE 5500

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:5500/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
