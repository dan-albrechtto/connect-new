from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from database.connection import Base

# ============================================
# MODELO: Avaliacao
# Tabela: cidadão avalia se problema foi resolvido bem (nota 1-5)
# Permite sistema de qualidade e feedback
# ============================================

class Avaliacao(Base):
    """
    Modelo de Avaliação de Solicitação
    
    Cidadão avalia uma solicitação resolvida/cancelada.
    Contém nota (1-5), confirmação se foi realmente resolvido, e comentário.
    """
    __tablename__ = "avaliacoes"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # SOLICITACAO_ID: qual problema foi avaliado? (chave estrangeira)
    solicitacao_id = Column(
        Integer,
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # USUARIO_ID: quem avaliou? (chave estrangeira)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # NOTA: avaliação de 1 a 5 estrelas
    # 1 = muito ruim, 5 = excelente
    nota = Column(Integer, nullable=False)  # Validar 1-5 na aplicação
    
    # PROBLEMA_RESOLVIDO: cidadão confirma se problema foi realmente resolvido
    # NOT NULL DEFAULT FALSE força resposta obrigatória
    problema_resolvido = Column(Boolean, nullable=False, default=False)
    
    # COMENTARIO: feedback do cidadão sobre a solução (opcional, máx 500 caracteres)
    comentario = Column(String(500))
    
    # CRIADO_EM: data/hora da avaliação automática
    criado_em = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # ========== RELACIONAMENTOS ==========
    # solicitacao = relationship("Solicitacao", back_populates="avaliacao")
    # usuario = relationship("Usuario")
    
    def __repr__(self):
        return f"<Avaliacao(id={self.id}, solicitacao_id={self.solicitacao_id}, nota={self.nota})>"