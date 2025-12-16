/* ============================================
   ARQUIVO: src/services/config.js
   DESCRIÇÃO: Configurações centralizadas da aplicação
   FUNCIONALIDADES:
   - URL da API backend
   - Timeout padrão
   ============================================ */

/* ============================================
   CONFIGURAÇÃO: URL DO BACKEND
   ============================================ */

// URL base da API do backend
// Pode ser 'http://localhost:8000' (desenvolvimento)
// Ou 'https://api.example.com' (produção)
// process.env.VITE_API_URL = variável de ambiente (se existir)
// Fallback = 'http://localhost:8000' (padrão)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/* ============================================
   CONFIGURAÇÃO: TIMEOUT
   ============================================ */

// Tempo máximo de espera por uma requisição (em milissegundos)
// 30000 ms = 30 segundos
// Se a requisição demorar mais que isso, será cancelada
const REQUEST_TIMEOUT = 30000;

/* ============================================
   EXPORTAR CONFIGURAÇÕES
   ============================================ */

// Exportar para usar em outros arquivos
// Exemplo: import { API_BASE_URL, REQUEST_TIMEOUT } from './config';
export {
  API_BASE_URL,
  REQUEST_TIMEOUT
};
