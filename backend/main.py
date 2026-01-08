# ============================================================================
# main.py - APLICAÇÃO FASTAPI PRINCIPAL (ATUALIZADO COM JWT SECURITY)
# ============================================================================
# Alterações:
# 1. Adicionado custom_openapi() para configurar segurança JWT no Swagger
# 2. Botão "Authorize" agora aparece no Swagger (/docs)
# 3. Suporte a Bearer token configurado
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from database.connection import criar_todas_as_tabelas, testar_conexao
from config import APP_NAME, APP_VERSION, DEBUG
import logging
from app.models import Base, Usuario, Solicitacao, Avaliacao, Categoria

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
# CUSTOM OpenAPI Schema - Habilita botão "Authorize" no Swagger
# ============================================================================
# Sem essa função, o Swagger não sabe que a API usa JWT e não mostra o botão!
# ============================================================================

def custom_openapi():
    """
    Personaliza o esquema OpenAPI para incluir configuração de segurança JWT.
    Isso faz aparecer o botão "Authorize" (cadeado) no Swagger.
    
    Como usar:
    1. Acesse http://localhost:8000/docs
    2. Clique no cadeado "Authorize" (canto superior direito)
    3. Cole seu token JWT (SEM "Bearer " no início)
    4. Clique "Authorize"
    5. Pronto! Todos os endpoints protegidos usarão o token automaticamente
    """
    
    if app.openapi_schema:
        # Se já foi gerado, retorna em cache
        return app.openapi_schema
    
    # Gera schema padrão do FastAPI
    openapi_schema = get_openapi(
        title=APP_NAME,
        version=APP_VERSION,
        description="API para mapeamento de problemas urbanos",
        routes=app.routes,
    )
    
    # ✅ Adiciona configuração de segurança JWT (Bearer token)
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Cole seu token JWT aqui (sem 'Bearer ' na frente)"
        }
    }
    
    # ✅ Define que todos os endpoints exigem autenticação por padrão
    # (rotas públicas podem override isso)
    openapi_schema["security"] = [{"Bearer": []}]
    
    # Armazena em cache
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# ✅ Registra a função customizada
app.openapi = custom_openapi

# ============================================================================
# STARTUP - Executar ao iniciar
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Executado quando FastAPI inicia"""
    logger.info("🚀 Iniciando Connect Cidade API")
    
    # Testar conexão com banco
    if testar_conexao():
        logger.info("✅ Conexão com banco OK")
    else:
        logger.error("❌ Falha ao conectar ao banco")
        raise Exception("Não conseguiu conectar ao banco de dados")
    
    # Criar tabelas se não existirem
    criar_todas_as_tabelas()
    logger.info("✅ Tabelas criadas/verificadas")

# ============================================================================
# HEALTH CHECK - Endpoints públicos para verificar se API está rodando
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
# INCLUIR ROTAS
# ============================================================================
# As rotas são importadas dos módulos em app/routes/

from app.routes import auth
app.include_router(auth.router)

from app.routes import solicitacoes
app.include_router(solicitacoes.router)

from app.routes import fotos
app.include_router(fotos.router)

from app.routes import avaliacoes
app.include_router(avaliacoes.router)

from app.routes import apoios
app.include_router(apoios.router)

from app.routes import admin
app.include_router(admin.router)


# Exemplo de como adicionar mais rotas no futuro:
# from app.routes import fotos
# app.include_router(fotos.router, prefix="/api", tags=["Fotos"])
#
# from app.routes import admin
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# ============================================================================
# INICIAR SERVIDOR (se executado diretamente)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )

# ============================================================================
# COMO USAR
# ============================================================================
# 1. Terminal: cd backend && source venv/Scripts/activate
# 2. Terminal: uvicorn main:app --reload
# 3. Browser: http://localhost:8000/docs
# 4. Clique no cadeado "Authorize" para adicionar token JWT
# 5. Teste os endpoints protegidos
# ============================================================================