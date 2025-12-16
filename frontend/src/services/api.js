/* ============================================
   ARQUIVO: src/services/api.js
   DESCRIÇÃO: Serviço de comunicação com backend
   FUNCIONALIDADES:
   - Fazer login
   - Registrar novo problema
   - Buscar problemas
   - Buscar categorias
   ============================================ */

// Importar axios para fazer requisições HTTP
import axios from 'axios';

// Importar configurações (URL base da API)
import { API_BASE_URL, REQUEST_TIMEOUT } from './config';

/* ============================================
   CRIAR INSTÂNCIA DO AXIOS
   Uma instância customizada com configurações padrão
   ============================================ */

// Criar instância com configurações
const api = axios.create({
  // baseURL = URL padrão para todas as requisições
  // Exemplo: se baseURL = 'http://localhost:8000'
  // E você faz api.get('/api/problems')
  // A URL completa fica: 'http://localhost:8000/api/problems'
  baseURL: API_BASE_URL,
  
  // timeout = tempo máximo de espera (em ms)
  // Se demorar mais de 30 segundos, cancela a requisição
  timeout: REQUEST_TIMEOUT,
  
  // headers = cabeçalhos padrão de todas as requisições
  headers: {
    // Content-Type = formato dos dados sendo enviados
    'Content-Type': 'application/json',
  },
});

/* ============================================
   FUNÇÃO: Fazer login
   POST /auth/login
   ============================================ */

// Função assíncrona: pode usar await
export const loginUser = async (cpf, senha) => {
  try {
    // Fazer requisição POST para /auth/login
    // Enviar: { cpf, senha }
    // Receber: { token, usuario_id, ... }
    const response = await api.post('/auth/login', { cpf, senha });
    
    // Se respondeu com token
    if (response.data.token) {
      // Salvar token no localStorage (persiste mesmo fechando navegador)
      localStorage.setItem('token', response.data.token);
      
      // Adicionar token ao header padrão para próximas requisições
      // Todas as requisições a partir de agora terão:
      // Authorization: Bearer <token>
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
    }
    
    // Retornar resposta (data com token, user_id, etc)
    return response.data;
  } catch (error) {
    // Se erro, extrair mensagem do backend ou usar genérica
    // error.response.data.detail = mensagem do FastAPI
    throw new Error(error.response?.data?.detail || 'Erro ao fazer login');
  }
};

/* ============================================
   FUNÇÃO: Registrar novo problema
   POST /api/problems/create
   ============================================ */

// Função assíncrona para enviar problema com foto
export const createProblem = async (formData) => {
  try {
    // Configuração especial para upload de arquivo
    const config = {
      headers: {
        // multipart/form-data = formato para enviar arquivos
        // Permite enviar: texto, números E arquivos
        'Content-Type': 'multipart/form-data',
      },
    };
    
    // Fazer requisição POST para /api/problems/create
    // formData = objeto FormData com:
    //   - latitude, longitude (GPS)
    //   - descricao (texto)
    //   - categoria_id (número)
    //   - arquivo de foto
    //   - usuario_id (do token)
    const response = await api.post('/api/problems/create', formData, config);
    
    // Retornar resposta do backend
    return response.data;
  } catch (error) {
    // Se erro, extrair mensagem
    throw new Error(error.response?.data?.detail || 'Erro ao registrar problema');
  }
};

/* ============================================
   FUNÇÃO: Obter todos os problemas
   GET /api/problems/list
   ============================================ */

// Função assíncrona para buscar lista de problemas
export const getProblems = async () => {
  try {
    // Fazer requisição GET para /api/problems/list
    // Retorna array de todos os problemas registrados
    const response = await api.get('/api/problems/list');
    
    // Retornar array de problemas
    return response.data;
  } catch (error) {
    // Se erro, extrair mensagem
    throw new Error(error.response?.data?.detail || 'Erro ao buscar problemas');
  }
};

/* ============================================
   FUNÇÃO: Obter categorias
   GET /api/categories/list
   ============================================ */

// Função assíncrona para buscar categorias disponíveis
export const getCategories = async () => {
  try {
    // Fazer requisição GET para /api/categories/list
    // Retorna array com: Coleta de Lixo, Iluminação, Acessibilidade
    const response = await api.get('/api/categories/list');
    
    // Retornar array de categorias
    return response.data;
  } catch (error) {
    // Se erro, extrair mensagem
    throw new Error(error.response?.data?.detail || 'Erro ao buscar categorias');
  }
};

/* ============================================
   EXPORTAR INSTÂNCIA DO AXIOS
   Para usar em outros componentes se necessário
   ============================================ */

// Exportar como default para usar em qualquer lugar
// Exemplo: import api from '../services/api';
export default api;
