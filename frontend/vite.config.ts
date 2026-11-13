import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The verifier starts isolated backend ports and points the preview proxy at
// the one it owns. Falls back to the standard local development port.
declare const process: { env: Record<string, string | undefined> }
const apiTarget = process.env.SETTLEIQ_API_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/v1': apiTarget,
      '/health': apiTarget,
    },
  },
  preview: {
    port: 4173,
    proxy: {
      '/v1': apiTarget,
      '/health': apiTarget,
    },
  },
})
