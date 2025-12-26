# ============================================
# ARQUIVO: connection.py
# DESCRIÇÃO: Conexão com PostgreSQL
# Configuração do SQLAlchemy e dependência FastAPI
# ============================================

# Importações necessárias
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator  # ← ADICIONE ESTA LINHA (foi adicionada)
import os
from dotenv import load_dotenv
import logging
from sqlalchemy.orm import declarative_base


# ═══════════════════════════════════════════════════════════════════════════
# 2. CONFIGURAÇÃO DE LOGGING
# ═══════════════════════════════════════════════════════════════════════════

Base = declarative_base()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# ═══════════════════════════════════════════════════════════════════════════
# 3. CARREGAR VARIÁVEIS DE AMBIENTE
# ═══════════════════════════════════════════════════════════════════════════


load_dotenv()


# ═══════════════════════════════════════════════════════════════════════════
# 4. EXTRAIR CREDENCIAIS DO BANCO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════


DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "connect_cidade")


# ═══════════════════════════════════════════════════════════════════════════
# 5. CONSTRUIR STRING DE CONEXÃO
# ═══════════════════════════════════════════════════════════════════════════


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


logger.info(f"📝 Conectando em: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")


# ═══════════════════════════════════════════════════════════════════════════
# 6. CRIAR ENGINE DO SQLALCHEMY
# ═══════════════════════════════════════════════════════════════════════════


try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    logger.info("✅ Engine SQLAlchemy criado com sucesso!")
except Exception as e:
    logger.error(f"❌ Erro ao criar engine: {e}")
    raise


# ═══════════════════════════════════════════════════════════════════════════
# 7. CRIAR SESSIONMAKER
# ═══════════════════════════════════════════════════════════════════════════


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


logger.info("✅ SessionLocal criada com sucesso!")


# ═══════════════════════════════════════════════════════════════════════════
# 8. FUNÇÃO DE DEPENDENCY INJECTION PARA FASTAPI
# ═══════════════════════════════════════════════════════════════════════════


def obter_conexao() -> Generator[Session, None, None]:  # ← ESTA LINHA FOI ALTERADA
    """
    Fornece uma sessão do banco para cada requisição FastAPI.
    
    Uso em FastAPI:
        @app.get("/usuarios")
        def listar_usuarios(db: Session = Depends(obter_conexao)):
            return db.query(Usuario).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"❌ Erro durante requisição: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
# 9. FUNÇÃO PARA CRIAR TODAS AS TABELAS
# ═══════════════════════════════════════════════════════════════════════════


def criar_todas_as_tabelas():
    """Cria todas as tabelas do banco baseado nos modelos."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelas criadas/verificadas com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# 10. FUNÇÃO PARA TESTAR A CONEXÃO
# ═══════════════════════════════════════════════════════════════════════════


def testar_conexao():
    """Testa se a conexão com o banco está funcionando."""
    try:
        connection = engine.connect()
        result = connection.execute(text("SELECT 1"))
        result.scalar()
        connection.close()
        logger.info("✅ Conexão com banco testada com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Falha ao conectar ao banco: {e}")
        return False
    
# ═══════════════════════════════════════════════════════════════════════════
# ATALHOS PARA COMPATIBILIDADE (se houver código antigo)
# ═══════════════════════════════════════════════════════════════════════════

# Se ainda houver imports de get_db() em outro lugar, pode usar:
get_db = obter_conexao  # Alias para compatibilidade com código antigo
create_all_tables = criar_todas_as_tabelas
test_connection = testar_conexao