# syntax=docker/dockerfile:1
# ---- Frontend: build Angular 19, serve static files + reverse-proxy /api via nginx ----
#
# This app is served under a SUB-PATH, not at "/", because port 80 on the target
# server already belongs to another application. The prefix is fixed in three
# places that must agree:
#   1. APP_BASE_PATH below (compiled into index.html's <base href>)
#   2. the directory the built bundle is copied into (last COPY of stage 2)
#   3. every `location` block in nginx.conf
# Changing the prefix means changing all three.

# Stage 1: build the production bundle
FROM node:20-alpine AS build
WORKDIR /app

# The public path the SPA is served from. Angular rewrites <base href> to this,
# and the router derives every in-app URL from it, so routerLink="/rwa-agent"
# resolves to /rwa-enhance/rwa-agent in the browser.
ARG APP_BASE_PATH=/rwa-enhance/

COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# `ng build` defaults to the production configuration (see angular.json),
# which swaps in environment.prod.ts (apiBaseUrl = '' -> same-origin, resolved
# against <base href> at runtime by rwa-agent-api.service.ts).
RUN npm run build -- --base-href "$APP_BASE_PATH"

# Stage 2: serve with nginx
FROM nginx:1.27-alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/app.conf
# Must match APP_BASE_PATH above: nginx serves this from the document root, so
# a request for /rwa-enhance/main-<hash>.js maps to this directory on disk.
COPY --from=build /app/dist/rwa/browser /usr/share/nginx/html/rwa-enhance
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/rwa-enhance/ >/dev/null 2>&1 || exit 1
