const apiHost =
  typeof window !== 'undefined' && window.location.hostname
    ? window.location.hostname
    : '127.0.0.1';

export const environment = {
  production: false,
  apiBaseUrl: `http://${apiHost}:8000`,
} as const;
