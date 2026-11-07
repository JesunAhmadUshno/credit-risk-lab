import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// The site reads ../results/*.json and two markdown files at build time, so every number on the page is generated, never typed.
// It is published under /lab/ beside the existing React dashboard (web/) at the Pages root.
export default defineConfig({
  base: '/credit-risk-lab/lab/',
  plugins: [react()],
  server: { fs: { allow: ['..'] } },
});
