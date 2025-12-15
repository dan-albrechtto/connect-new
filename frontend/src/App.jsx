/* ============================================
   COMPONENTE PRINCIPAL - APP.JSX
   Responsável pela página do mapa e geolocalização
   ============================================ */

import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import './App.css';

/* ============================================
   CORRIGIR ÍCONE DO LEAFLET
   O Leaflet precisa de URLs corretas para exibir marcadores
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
  const [userLocation, setUserLocation] = useState(null); // Localização do usuário
  const [loading, setLoading] = useState(true); // Indicador de carregamento
  const [error, setError] = useState(null); // Mensagens de erro

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
          setError('Não foi possível acessar sua localização');
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
  }, []); // Array vazio = executa apenas na montagem do componente

  /* ============================================
     Tela de carregamento
     Mostrada enquanto aguarda a geolocalização
     ============================================ */
  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <p>Obtendo sua localização...</p>
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
        <h1>Connect Cidade</h1>
        <p>Mapeamento de Problemas Urbanos</p>
      </header>

      {/* ========== MAPA ========== */}
      <div className="map-wrapper">
        {/* Mostrar mensagem de erro se houver */}
        {error && <div className="error-message">{error}</div>}
        
        {/* Renderizar mapa apenas se temos a localização do usuário */}
        {userLocation && (
          <MapContainer
            center={userLocation} // Centro do mapa na localização do usuário
            zoom={15} // Nível de zoom (quanto maior, mais próximo)
            scrollWheelZoom={true} // Permitir zoom com rodinha do mouse/trackpad
            className="map-container"
          >
            {/* Adicionar tiles (imagens) do mapa */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              crossOrigin="anonymous"
              tms={false} /* TMS não é usado para OpenStreetMap */
              noWrap={false} /* Permite repetir o mapa horizontalmente */
              maxZoom={19}
              minZoom={1}
              detectRetina={true} /* Melhora em telas de alta densidade */
            />
            
            {/* Adicionar marcador na localização do usuário */}
            <Marker position={userLocation}>
              <Popup>
                <strong>Sua Localização</strong>
                <br />
                Lat: {userLocation[0].toFixed(4)}
                <br />
                Lng: {userLocation[1].toFixed(4)}
              </Popup>
            </Marker>
          </MapContainer>
        )}
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
