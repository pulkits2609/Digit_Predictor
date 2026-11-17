import { defineConfig } from 'vitest/config';
import { loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig(({ mode }) => { const env = loadEnv(mode, '.', ''); return { define: { 'import.meta.env.API': JSON.stringify(env.API || env.VITE_API_BASE_URL || '') }, plugins: [react(), tailwindcss()], test: { environment: 'jsdom', setupFiles: './src/test/setup.ts', css: false } }; });
