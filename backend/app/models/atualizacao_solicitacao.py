from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from database.connection import Base

# ============================================
# MODELO: AtualizacaoSolicitacao
# Tabela: histórico de mudanças no status/dados
# Admin usa para registrar o que foi feito em cada problema
# ============================================

class AtualizacaoSolicitacao(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "atualizacoes_solicitacao"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # SOLICITACAO_ID: qual problema foi atualizado? (chave estrangeira)
    solicitacao_id = Column(
        Integer,
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # ADMINISTRADOR_ID: qual admin fez a mudança? (chave estrangeira)
    administrador_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        index=True
    )
    
    # STATUS_NOVO_ID: novo status após atualização (chave estrangeira)
    # status_novo_id = Column(
    #     Integer,
    #     ForeignKey("status.id", ondelete="RESTRICT"),
    #     index=True,
    #     nullable=False
    # )
    # Status ANTES (texto simples):
    status_anterior = Column(
        String(50),
        nullable=False
    )
    
    # Status DEPOIS (texto simples):
    status_novo = Column(
        String(50),
        nullable=False
    )
    
    # DESCRICAO: por que foi mudado? Qual ação foi tomada?
    # Ex: "Encaminhado para setor de limpeza"
    descricao = Column(Text)
    
    # CRIADO_EM: data/hora da atualização automática
    criado_em = Column(DateTime, default=func.now(), nullable=False)

    # ========== RELACIONAMENTOS ==========
    # solicitacao = relationship("Solicitacao", back_populates="atualizacoes")