/* ============================================
   COMPONENTE PRINCIPAL - APP.JSX
   Página do mapa com geolocalização
   VERSÃO CORRIGIDA: Leaflet funciona como teste
   ============================================ */

/* ============================================
   IMPORTAÇÕES - Trazer bibliotecas do React
   ============================================ */

// Import do React Router para navegar entre páginas
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// ⭐ NOVO: Import apenas do MapPage (página principal)
import MapPage from './pages/MapPage';

// Import da página para registrar problema
import ProblemReportPage from './pages/ProblemReportPage';

// ⭐ NOVO: Importar CSS da página
import './styles/ProblemReportPage.css';

// Import do CSS customizado
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
   Agora com React Router para navegar entre páginas
   ============================================ */

/* ============================================
   FUNÇÃO PRINCIPAL DO APP
   Agora com o mapa como página inicial
   ============================================ */

function App() {
  // Router = permite navegar entre páginas sem recarregar
  return (
    <Router>
      {/* Routes = container que gerencia qual página mostrar */}
      <Routes>
        {/* ⭐ Rota 1: "/" = MAPA É A PÁGINA INICIAL */}
        {/* Quando usuário abre http://localhost:5173/ já vê o mapa */}
        <Route path="/" element={<MapPage />} />
        
        {/* Rota 2: "/register-problem" = Registrar novo problema */}
        {/* Quando usuário clica em "Registrar" vai para este formulário */}
        <Route path="/register-problem" element={<ProblemReportPage />} />
      </Routes>
    </Router>
  );
}




export default App;
