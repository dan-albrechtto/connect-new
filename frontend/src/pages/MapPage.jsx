/* ============================================
   ARQUIVO: src/pages/MapPage.jsx
   DESCRIÇÃO: Página do mapa com geolocalização
   FUNCIONALIDADES:
   - Mostrar mapa com localização do usuário
   - Exibir problemas registrados como marcadores
   - Botões para registrar novo problema
   - Integração com backend para buscar problemas
   ============================================ */

// Importar hooks do React para gerenciar estado e efeitos
import { useEffect, useRef, useState } from 'react';

// Importar Leaflet para trabalhar com mapas
import L from 'leaflet';

// Importar CSS do Leaflet - CRÍTICO para que o mapa funcione
import 'leaflet/dist/leaflet.css';

// Importar serviço de API para comunicação com backend
import { getProblems } from '../services/api';

// Importar navegação entre páginas
import { useNavigate } from 'react-router-dom';

// Importar CSS customizado desta página
import '../styles/MapPage.css';

/* ============================================
   CORRIGIR ÍCONES DO LEAFLET
   Leaflet precisa de URLs corretas para exibir marcadores no mapa
   Sem isso, os marcadores não aparecem
   ============================================ */

// Deletar configuração padrão de ícone
delete L.Icon.Default.prototype._getIconUrl;

// Adicionar URLs corretas dos ícones (de um CDN)
L.Icon.Default.mergeOptions({
  // Ícone de marcador em alta resolução (2x)
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  
  // Ícone de marcador normal
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  
  // Sombra do marcador
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

/* ============================================
   COMPONENTE PRINCIPAL: MapPage
   ============================================ */

function MapPage() {
  // ========== ESTADOS ==========
  
  // Estado: armazena a localização do usuário [latitude, longitude]
  const [userLocation, setUserLocation] = useState(null);
  
  // Estado: armazena todos os problemas buscados do backend
  const [problems, setProblems] = useState([]);
  
  // Estado: indica se está carregando dados
  const [loading, setLoading] = useState(true);
  
  // Estado: armazena mensagens de erro
  const [error, setError] = useState(null);
  
  // ========== REFS ==========
  
  // Ref para acessar o elemento HTML do mapa (div#map)
  const mapRef = useRef(null);
  
  // Ref para armazenar a instância do mapa (para limpeza posterior)
  const mapInstanceRef = useRef(null);
  
  // Ref para armazenar os marcadores de problemas (array)
  const markersRef = useRef([]);
  
  // Hook para navegar entre páginas
  const navigate = useNavigate();

  /* ============================================
     useEffect: ETAPA 1 - Obter geolocalização do usuário
     Executa uma única vez quando o componente é montado
     ============================================ */

  useEffect(() => {
    // Verificar se o navegador suporta geolocalização (GPS)
    if (navigator.geolocation) {
      // Solicitar permissão ao usuário para acessar localização
      navigator.geolocation.getCurrentPosition(
        // SUCESSO: usuário permitiu acessar localização
        (position) => {
          // Extrair latitude e longitude da resposta
          const { latitude, longitude } = position.coords;
          
          // Salvar localização no estado [lat, lng]
          setUserLocation([latitude, longitude]);
          
          // Terminar carregamento
          setLoading(false);
        },
        
        // ERRO: usuário negou permissão ou erro técnico
        (err) => {
          // Log do erro no console para debug
          console.error('Erro ao obter localização:', err);
          
          // Mostrar mensagem de erro ao usuário
          setError('Não foi possível acessar sua localização. Usando localização padrão.');
          
          // Usar localização padrão: Caxias do Sul, RS
          // Formato: [latitude, longitude]
          setUserLocation([-29.1683, -51.1894]);
          
          // Terminar carregamento
          setLoading(false);
        }
      );
    } else {
      // Navegador não suporta geolocalização
      setError('Geolocalização não é suportada pelo seu navegador');
      
      // Usar localização padrão mesmo assim
      setUserLocation([-29.1683, -51.1894]);
      setLoading(false);
    }
  }, []); /* Array vazio = executar apenas uma vez ao montar componente */

  /* ============================================
     useEffect: ETAPA 2 - Buscar problemas do backend
     Executa quando o componente monta (loading muda)
     ============================================ */

  useEffect(() => {
    // Função assíncrona para buscar dados
    const fetchProblems = async () => {
      try {
        // Chamar API para buscar todos os problemas registrados
        const data = await getProblems();
        
        // Salvar problemas no estado
        setProblems(data);
      } catch (err) {
        // Se erro, registrar no console e mostrar mensagem
        console.error('Erro ao buscar problemas:', err.message);
        setError(err.message);
      }
    };

    // Chamar a função de busca
    fetchProblems();
  }, []); /* Executar apenas na montagem */

  /* ============================================
     useEffect: ETAPA 3 - Criar mapa e adicionar marcadores
     Executa quando temos localização do usuário
     ============================================ */

  useEffect(() => {
    // Verificar se temos localização E o container do mapa está pronto
    if (userLocation && mapRef.current && !mapInstanceRef.current) {
      // ========== CRIAR MAPA ==========
      
      // Criar instância do mapa usando Leaflet
      // mapRef.current = elemento HTML <div ref={mapRef} id="map">
      // setView([lat, lng], zoom) = centrar no ponto com zoom 15
      const map = L.map(mapRef.current).setView(userLocation, 15);

      // ========== ADICIONAR TILES (camada de mapa) ==========
      
      // Adicionar mapa base do OpenStreetMap
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        // maxZoom = quanto mais você pode aproximar
        maxZoom: 19,
        
        // attribution = crédito obrigatório do mapa
        attribution: '© OpenStreetMap',
      }).addTo(map); // .addTo(map) = adicionar ao mapa

      // ========== MARCADOR DO USUÁRIO ==========
      
      // Criar marcador na localização atual do usuário (cor padrão = vermelho)
      L.marker(userLocation)
        .addTo(map)
        .bindPopup(
          // Popup = janela que abre ao clicar no marcador
          `<strong>📍 Sua Localização</strong><br/>Lat: ${userLocation[0].toFixed(4)}<br/>Lng: ${userLocation[1].toFixed(4)}`
        )
        .openPopup(); // Abrir popup automaticamente

      // ========== MARCADORES DOS PROBLEMAS ==========
      
      // Limpar marcadores antigos (caso haja)
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current = [];

      // Loop: para cada problema registrado no backend
      problems.forEach((problem) => {
        // Extrair informações do problema
        const { latitude, longitude, descricao, categoria, id } = problem;

        // Verificar se problema tem coordenadas válidas
        if (latitude && longitude) {
          // Criar marcador customizado (cor verde)
          const problemMarker = L.marker(
            [latitude, longitude],
            {
              // Customizar ícone do marcador
              icon: L.icon({
                iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
                className: 'problem-marker', // CSS customizado
              }),
            }
          )
            .addTo(map)
            .bindPopup(
              // Popup com informações do problema
              `<div class="problem-popup">
                <strong>🔴 ${categoria || 'Sem categoria'}</strong><br/>
                <p>${descricao}</p>
                <small>ID: ${id}</small>
              </div>`
            );

          // Adicionar marcador à lista para limpeza posterior
          markersRef.current.push(problemMarker);
        }
      });

      // Armazenar referência ao mapa
      mapInstanceRef.current = map;

      // ========== CLEANUP: Destruir mapa ao desmontar componente ==========
      
      // Retornar função de limpeza (executada quando componente é removido)
      return () => {
        // Se mapa existe, remover
        if (mapInstanceRef.current) {
          // remove() = destruir instância do mapa
          mapInstanceRef.current.remove();
          
          // Resetar ref
          mapInstanceRef.current = null;
        }
      };
    }
  }, [userLocation, problems]); /* Executar quando localização ou problemas mudam */

  /* ============================================
     TELA DE CARREGAMENTO
     Mostrada enquanto obtém geolocalização
     ============================================ */

  if (loading) {
    return (
      <div className="map-page-container">
        <div className="loading-screen">
          <div className="loading-spinner">🔄</div>
          <p>📍 Obtendo sua localização...</p>
        </div>
      </div>
    );
  }

  /* ============================================
     RENDERIZAÇÃO PRINCIPAL
     Estrutura HTML da página do mapa
     ============================================ */

  return (
    <div className="map-page-container">
      {/* ========== HEADER ========== */}
      <header className="map-header">
        {/* Título da página */}
        <h1>🌍 Connect Cidade</h1>
        
        {/* Subtítulo */}
        <p>Mapeamento de Problemas Urbanos</p>
      </header>

      {/* ========== MAPA ========== */}
      <div className="map-wrapper">
        {/* Mostrar erro se houver */}
        {error && (
          <div className="error-message">
            {/* Ícone de aviso + mensagem de erro */}
            ⚠️ {error}
          </div>
        )}

        {/* Container do mapa */}
        {/* ref={mapRef} = permite que Leaflet acesse este elemento */}
        {/* className="map-container" = CSS para dimensionar o mapa */}
        <div ref={mapRef} className="map-container"></div>
      </div>

      {/* ========== FOOTER COM BOTÕES ========== */}
      <footer className="map-footer">
        {/* Botão 1: Registrar novo problema */}
        <button
          className="btn-primary"
          // onClick = executar função quando clicar
          onClick={() => navigate('/register-problem')}
        >
          {/* Ícone + texto */}
          ➕ Registrar Problema
        </button>

        {/* Botão 2: Centralizar no usuário (BÔNUS) */}
        <button
          className="btn-secondary"
          onClick={() => {
            // Se mapa existe, setView = voltar para localização do usuário
            if (mapInstanceRef.current && userLocation) {
              mapInstanceRef.current.setView(userLocation, 15);
            }
          }}
        >
          📍 Minha Localização
        </button>
      </footer>
    </div>
  );
}

// Exportar componente para ser usado em outros arquivos
export default MapPage;