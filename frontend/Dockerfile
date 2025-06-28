# 1. Wir starten von nginx:alpine
FROM nginx:alpine

# 2. Alten Content entfernen
RUN rm -rf /usr/share/nginx/html/*

# 3. Eigenen Code kopieren
COPY . /usr/share/nginx/html

# 4. Port 80 freigeben
EXPOSE 80
