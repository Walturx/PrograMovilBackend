import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import reactRefresh from '@vitejs/plugin-react-refresh';

export default defineConfig(({ mode }) => ({
  build: {
    outDir: 'build',
    rollupOptions: {
      input: {
        web: fileURLToPath(new URL('./src/entries/web.jsx', import.meta.url)),
        app: fileURLToPath(new URL('./src/entries/app.jsx', import.meta.url))
      },
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            return 'vendor'; // Todos los módulos de node_modules van a vendor.js
          }
        },
        entryFileNames: chunkInfo => {
          return `[name].js`;
        },
        chunkFileNames: '[name].js',
        assetFileNames: assetInfo => {
          return `[name][extname]`;
        },
      }
    }
  },
  plugins: [
    react(),
    reactRefresh(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
}));
