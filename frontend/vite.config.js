/* ============================================
   CONFIGURAÇÃO DO VITE
   Define como o Vite funciona durante dev e build
   ============================================ */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'

export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: fs.readFileSync('./cert-key.pem'),
      cert: fs.readFileSync('./cert.pem'),
    },
    host: '0.0.0.0',
    port: 5173
  }
})



