import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// GitHub Pages serves this project site under /credit-risk-lab/.
export default defineConfig({
  base: '/credit-risk-lab/',
  plugins: [react()],
})
