/* ============================================
   COMPONENTE PRINCIPAL - APP.JSX
   Página do mapa com geolocalização
   VERSÃO CORRIGIDA: Leaflet funciona como teste
   ============================================ */

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css'; /* Importar CSS do Leaflet - CRÍTICO */
import './App.css';

/* ============================================
   CORRIGIR ÍCONE DO LEAFLET
   Leaflet precisa de URLs corretas para exibir marcadores
   ============================================ */
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

/* ============================================
   FUNÇÃO PRINCIPAL DO APP
   ============================================ */
function App() {
  /* Estados da aplicação */
  const [userLocation, setUserLocation] = useState(null); /* Localização do usuário */
  const [loading, setLoading] = useState(true); /* Indicador de carregamento */
  const [error, setError] = useState(null); /* Mensagens de erro */
  
  /* Ref para o container do mapa - CRÍTICO */
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null); /* Armazena instância do mapa */

  /* ============================================
     useEffect: Obter geolocalização do usuário
     Executa uma única vez quando o componente é montado
     ============================================ */
  useEffect(() => {
    // Verificar se o navegador suporta geolocalização
    if (navigator.geolocation) {
      // Solicitar permissão ao usuário para acessar localização
      navigator.geolocation.getCurrentPosition(
        (position) => {
          // Sucesso: extrair latitude e longitude
          const { latitude, longitude } = position.coords;
          setUserLocation([latitude, longitude]);
          setLoading(false);
        },
        (err) => {
          // Erro: mostrar mensagem mas usar localização padrão (Caxias do Sul)
          console.error('Erro ao obter localização:', err);
          setError('Não foi possível acessar sua localização. Usando localização padrão.');
          // Fallback: coordenadas de Caxias do Sul (latitude, longitude)
          setUserLocation([-29.1683, -51.1894]);
          setLoading(false);
        }
      );
    } else {
      // Navegador não suporta geolocalização
      setError('Geolocalização não é suportada pelo seu navegador');
      setUserLocation([-29.1683, -51.1894]);
      setLoading(false);
    }
  }, []); /* Array vazio = executa apenas na montagem do componente */

  /* ============================================
     useEffect: Criar mapa quando temos localização
     Executa quando userLocation muda
     ============================================ */
  useEffect(() => {
    /* Só criar mapa se temos localização E container está pronto */
    if (userLocation && mapRef.current && !mapInstanceRef.current) {
      // Criar instância do mapa (exatamente como no teste que funcionou)
      const map = L.map(mapRef.current).setView(userLocation, 15);

      // Adicionar tiles do OpenStreetMap
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap',
      }).addTo(map);

      // Adicionar marcador na localização do usuário
      L.marker(userLocation)
        .addTo(map)
        .bindPopup(
          `<strong>Sua Localização</strong><br/>Lat: ${userLocation[0].toFixed(4)}<br/>Lng: ${userLocation[1].toFixed(4)}`
        )
        .openPopup();

      // Armazenar referência ao mapa para limpeza posterior
      mapInstanceRef.current = map;

      // Cleanup: destruir mapa ao desmontar componente
      return () => {
        if (mapInstanceRef.current) {
          mapInstanceRef.current.remove();
          mapInstanceRef.current = null;
        }
      };
    }
  }, [userLocation]); /* Executar quando userLocation muda */

  /* ============================================
     Tela de carregamento
     Mostrada enquanto aguarda a geolocalização
     ============================================ */
  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <p>📍 Obtendo sua localização...</p>
        </div>
      </div>
    );
  }

  /* ============================================
     RETORNO PRINCIPAL
     Estrutura HTML da página
     ============================================ */
  return (
    <div className="container">
      {/* ========== HEADER ========== */}
      <header className="header">
        <h1>🌍 Connect Cidade</h1>
        <p>Mapeamento de Problemas Urbanos</p>
      </header>

      {/* ========== MAPA ========== */}
      <div className="map-wrapper">
        {/* Mostrar mensagem de erro se houver */}
        {error && <div className="error-message">{error}</div>}
        
        {/* Container do mapa - ref permite que Leaflet acesse este elemento */}
        <div ref={mapRef} className="map-container"></div>
      </div>

      {/* ========== FOOTER COM BOTÕES ========== */}
      <footer className="footer">
        {/* Botão para reportar novo problema */}
        <button className="btn-primary">➕ Reportar Problema</button>
        
        {/* Botão para visualizar seus reportes */}
        <button className="btn-secondary">📋 Meus Reportes</button>
      </footer>
    </div>
  );
}

export default App;
