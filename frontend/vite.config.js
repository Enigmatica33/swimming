import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// В dev-режиме Vite-сервер (5173) проксирует /api на Django (8000),
// поэтому API-запросы из фронтенда не упираются в CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
