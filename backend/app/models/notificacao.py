"""
Modelo: Notificacao
Tabela: notificacoes
Armazena notificações de atualização de solicitações para os cidadãos
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from database.connection import Base
from sqlalchemy.orm import relationship


class Notificacao(Base):
    """
    Modelo de Notificação
    
    Registra notificações de atualização de status de solicitações.
    Toda vez que um admin muda o status de uma solicitação,
    uma notificação é criada aqui (in-app) E um email é enviado.
    
    Simples e direto: sem tipos, sem canais, sem complexidade.
    """
    
    __tablename__ = "notificacoes"
    
    # ========== CHAVES ==========
    id = Column(Integer, primary_key=True, index=True)
    
    # FK para usuário que RECEBE a notificação
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # FK para solicitação relacionada
    solicitacao_id = Column(
        Integer,
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # ========== CONTEÚDO ==========
    titulo = Column(String(255), nullable=False)
    conteudo = Column(Text, nullable=False)
    
    # ========== CONTROLE ==========
    lida = Column(Boolean, default=False, nullable=False, index=True)
    
    # ========== DATAS ==========
    criado_em = Column(DateTime, default=func.now(), nullable=False, index=True)
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # # ========== RELACIONAMENTOS ==========
    # usuario = relationship("Usuario", back_populates="notificacoes")
    # solicitacao = relationship("Solicitacao", back_populates="notificacoes")
    
    def __repr__(self) -> str:
        return f"<Notificacao(id={self.id}, usuario_id={self.usuario_id}, lida={self.lida})>"
