/* ============================================
   ARQUIVO: src/pages/ProblemReportPage.jsx
   STATUS: Temporário (será substituído depois)
   ============================================ */

import { useNavigate } from 'react-router-dom';

function ProblemReportPage() {
  // Hook para navegar entre páginas
  const navigate = useNavigate();

  return (
    <div className="problem-report-container">
      {/* Header */}
      <header className="problem-header">
        <h1>📍 Registrar Problema</h1>
        <p>Descreva o problema urbano</p>
      </header>

      {/* Conteúdo temporário */}
      <main className="problem-main">
        <div className="placeholder">
          <p>🔨 Página em desenvolvimento...</p>
          <p>Formulário completo virá em breve!</p>
        </div>
      </main>

      {/* Footer com botão voltar */}
      <footer className="problem-footer">
        <button
          className="btn-back"
          onClick={() => navigate('/')}
        >
          ← Voltar ao Mapa
        </button>
      </footer>
    </div>
  );
}

export default ProblemReportPage;
