import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// En desarrollo, Vite reenvía /api a Django: el navegador ve un solo origen y no hace falta CORS.
// DJANGO_URL es la dirección de Django vista desde donde corre Vite (en Docker, http://web:8000).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      // En Docker sobre Windows los cambios de archivos no llegan como eventos: se revisan cada tanto
      watch: env.VITE_POLLING ? { usePolling: true, interval: 300 } : undefined,
      proxy: {
        '/api': { target: env.DJANGO_URL || 'http://localhost:8002', changeOrigin: true },
      },
    },
  };
});
