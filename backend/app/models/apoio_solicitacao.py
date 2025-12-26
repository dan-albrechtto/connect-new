from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, UniqueConstraint
from database.connection import Base

# ============================================
# MODELO: Apoio
# Tabela: cidadãos que apoiam problemas reportados
# Relaciona Usuário + Solicitação (muitos para muitos)
# ============================================

class Apoio(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "apoios"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # SOLICITACAO_ID: qual problema? (chave estrangeira)
    # ondelete="CASCADE" remove apoio se problema for deletado
    solicitacao_id = Column(
        Integer,
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # USUARIO_ID: qual usuário? (chave estrangeira)
    # ondelete="CASCADE" remove apoio se usuário for deletado
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Restrição: um usuário só pode apoiar uma vez por problema
    # __table_args__ define restrições adicionais
    __table_args__ = (
        UniqueConstraint('solicitacao_id', 'usuario_id', name='unique_apoio_por_usuario'),
    )
    
    # CRIADO_EM: data/hora do apoio automática
    criado_em = Column(DateTime, default=func.now(), nullable=False)