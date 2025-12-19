# ============================================================================
# seed.py - POPULAÇÃO INICIAL DO BANCO
# ============================================================================

from database.connection import SessionLocal, engine, create_all_tables
from app.models import Base, Usuario, Categoria, Status
from app.utils.security import hash_senha
from config import (
    TIPO_USUARIO, STATUS_SOLICITACAO, CATEGORIAS,
    ADMIN_PADRAO_CPF, ADMIN_PADRAO_SENHA, ADMIN_PADRAO_NOME, ADMIN_PADRAO_EMAIL
)
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CRIAR TABELAS
# ============================================================================

def criar_tabelas():
    """Cria todas as tabelas do banco"""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tabelas criadas/verificadas")


# ============================================================================
# SEED DE STATUS
# ============================================================================

def seed_status(db):
    """Cria os 5 status possíveis"""
    status_list = [
        {"id": 1, "nome": "PENDENTE", "descricao": "Recém criado, aguardando análise"},
        {"id": 2, "nome": "EM_ANALISE", "descricao": "Admin recebeu e está analisando"},
        {"id": 3, "nome": "EM_ANDAMENTO", "descricao": "Setor responsável está trabalhando"},
        {"id": 4, "nome": "RESOLVIDO", "descricao": "Problema foi solucionado"},
        {"id": 5, "nome": "CANCELADO", "descricao": "Cancelado (spam, duplicado, etc)"}
    ]
    
    for status_data in status_list:
        # Verifica se já existe
        existe = db.query(Status).filter_by(id=status_data["id"]).first()
        if existe:
            logger.info(f"  ⚠️  Status '{status_data['nome']}' já existe")
            continue
        
        status = Status(**status_data)
        db.add(status)
        logger.info(f"  ✅ Status '{status_data['nome']}' criado")
    
    db.commit()


# ============================================================================
# SEED DE CATEGORIAS
# ============================================================================

def seed_categorias(db):
    """Cria as 3 categorias de problemas"""
    categorias_list = [
        {"id": 1, "nome": "Coleta de Lixo", "descricao": "Lixo não coletado", "icone": "🗑️", "cor_hex": "#FF6B6B"},
        {"id": 2, "nome": "Iluminação Pública", "descricao": "Poste sem luz", "icone": "💡", "cor_hex": "#FFD93D"},
        {"id": 3, "nome": "Acessibilidade", "descricao": "Calçada quebrada, rampa faltante", "icone": "♿", "cor_hex": "#6BCB77"}
    ]
    
    for cat_data in categorias_list:
        existe = db.query(Categoria).filter_by(id=cat_data["id"]).first()
        if existe:
            logger.info(f"  ⚠️  Categoria '{cat_data['nome']}' já existe")
            continue
        
        categoria = Categoria(**cat_data)
        db.add(categoria)
        logger.info(f"  ✅ Categoria '{cat_data['nome']}' criada")
    
    db.commit()


# ============================================================================
# SEED DE ADMIN
# ============================================================================

def seed_admin(db):
    """Cria o admin padrão"""
    from app.models import TipoUsuarioEnum
    
    # Verifica se já existe
    existe = db.query(Usuario).filter_by(cpf=ADMIN_PADRAO_CPF).first()
    if existe:
        logger.info(f"  ⚠️  Admin já existe")
        return
    
    admin = Usuario(
        cpf=ADMIN_PADRAO_CPF,
        email=ADMIN_PADRAO_EMAIL,
        nome=ADMIN_PADRAO_NOME,
        senha_hash=hash_senha(ADMIN_PADRAO_SENHA),
        tipo_usuario=TipoUsuarioEnum.ADMINISTRADOR,
        ativo=True
    )



# ============================================================================
# EXECUTAR SEED
# ============================================================================

def main():
    """Executa todo o seed"""
    logger.info("=" * 60)
    logger.info("INICIANDO SEED")
    logger.info("=" * 60)
    
    try:
        # 1. Criar tabelas
        logger.info("\n[1/4] Criando tabelas...")
        criar_tabelas()
        
        # 2. Abrir sessão
        db = SessionLocal()
        
        # 3. Seed de status
        logger.info("\n[2/4] Criando status...")
        seed_status(db)
        
        # 4. Seed de categorias
        logger.info("\n[3/4] Criando categorias...")
        seed_categorias(db)
        
        # 5. Seed de admin
        logger.info("\n[4/4] Criando admin padrão...")
        seed_admin(db)
        
        db.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ SEED CONCLUÍDO COM SUCESSO!")
        logger.info("=" * 60)
        logger.info(f"\nAdmin criado:")
        logger.info(f"  Email: {ADMIN_PADRAO_EMAIL}")
        logger.info(f"  Senha: {ADMIN_PADRAO_SENHA}")
        logger.info(f"  ⚠️  MUDE A SENHA APÓS PRIMEIRO LOGIN!")
        
    except Exception as e:
        logger.error(f"❌ ERRO: {e}")
        raise


if __name__ == "__main__":
    main()
