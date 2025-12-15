/* ============================================
   CONFIGURAÇÃO DO VITE
   Define como o Vite funciona durante dev e build
   ============================================ */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()], // Ativa suporte a React/JSX
  server: {
    host: '0.0.0.0', // Aceitar conexões de qualquer IP (permite acessar de celular)
    port: 5173 // Porta padrão do Vite
  }
})
