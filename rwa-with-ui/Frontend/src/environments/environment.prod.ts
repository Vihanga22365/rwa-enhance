// Production build config (swapped in for environment.ts via angular.json
// fileReplacements). apiBaseUrl is empty so the API service calls the relative
// path /api/rwa/... on the SAME origin, which nginx proxies to the backend.
// This works for both http://91.230.110.121 and a future https://domain.
export const environment = {
  production: true,
  apiBaseUrl: '',
} as const;
