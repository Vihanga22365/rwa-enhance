# syntax=docker/dockerfile:1
# ---- Frontend: build Angular 19, serve static files + reverse-proxy /api via nginx ----

# Stage 1: build the production bundle
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# `ng build` defaults to the production configuration (see angular.json),
# which swaps in environment.prod.ts (apiBaseUrl = '' -> same-origin /api).
RUN npm run build

# Stage 2: serve with nginx
FROM nginx:1.27-alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/app.conf
COPY --from=build /app/dist/rwa/browser /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1
