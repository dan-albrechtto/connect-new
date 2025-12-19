# ============================================================================
# main.py - APLICAÇÃO FASTAPI PRINCIPAL
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.connection import create_all_tables, test_connection
from config import APP_NAME, APP_VERSION, DEBUG
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CRIAR APLICAÇÃO
# ============================================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API para mapeamento de problemas urbanos",
    debug=DEBUG
)

# ============================================================================
# CORS - Permitir requisições do frontend
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# STARTUP - Executar ao iniciar
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Executado quando FastAPI inicia"""
    logger.info("🚀 Iniciando Connect Cidade API")
    
    # Testar conexão
    if test_connection():
        logger.info("✅ Conexão com banco OK")
    else:
        logger.error("❌ Falha ao conectar ao banco")
        raise Exception("Não conseguiu conectar ao banco de dados")
    
    # Criar tabelas
    create_all_tables()
    logger.info("✅ Tabelas criadas/verificadas")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/", tags=["Health"])
def health_check():
    """Verifica se API está rodando"""
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION
    }


@app.get("/api/health", tags=["Health"])
def api_health():
    """Verifica saúde da API"""
    return {
        "status": "healthy",
        "message": "API rodando corretamente"
    }


# ============================================================================
# INCLUIR ROTAS (quando criadas)
# ============================================================================

# from app.routes import auth, problems, admin
# app.include_router(auth.router, prefix="/api/auth", tags=["Autenticação"])
# app.include_router(problems.router, prefix="/api", tags=["Problemas"])
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )
