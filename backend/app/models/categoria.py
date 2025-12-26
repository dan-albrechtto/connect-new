from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from database.connection import Base

# ============================================
# MODELO: Categoria
# Tabela: tipos de problemas urbanos
# Armazena as 3 categorias: Coleta, Iluminação, Acessibilidade
# ============================================

class Categoria(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "categorias"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária (identificador único da categoria)
    id = Column(Integer, primary_key=True, index=True)
    
    # NOME: nome da categoria ("Coleta de Lixo", "Iluminação", "Acessibilidade")
    # unique=True garante que não há categorias duplicadas
    nome = Column(String(255), unique=True, index=True, nullable=False)
    
    # DESCRICAO: explicação detalhada do tipo de problema
    descricao = Column(String(500))
    
    # ICONE: emoji ou nome do ícone para exibição visual
    # Ex: "🗑️" para lixo, "💡" para iluminação
    icone = Column(String(50))
    
    # COR_HEX: cor para representar no mapa
    # Ex: "#FF0000" para vermelho
    cor_hex = Column(String(7))  # Formato #RRGGBB
    
    # ATIVO: categoria está disponível para seleção?
    # False = categoria desativada (não aparece mais)
    ativo = Column(Boolean, default=True, nullable=False)
    
    # CRIADO_EM: data/hora de criação automática
    criado_em = Column(DateTime, default=func.now(), nullable=False)