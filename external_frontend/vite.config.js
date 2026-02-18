import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    build: {
        chunkSizeWarningLimit: 1000,
        rollupOptions: {
            output: {
                manualChunks: {
                    'react-vendor': ['react', 'react-dom', 'react-router-dom'],
                    'chart-vendor': ['recharts'],
                    'map-vendor': ['react-simple-maps', 'cobe'],
                    'animation-vendor': ['framer-motion', 'gsap']
                }
            }
        }
    }
})
