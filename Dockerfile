# Static site (the who-knows-whom graph viewer) served by nginx on Cloud Run.
FROM nginx:1.27-alpine

# Cloud Run sends traffic to $PORT (default 8080); our nginx.conf listens on 8080.
COPY nginx.conf /etc/nginx/nginx.conf

# Only the assets the viewer needs at runtime.
COPY index.html graph-data.js graph.json graph.png /usr/share/nginx/html/

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
