from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum, func
from database.connection import Base
from app.utils.enums import StatusSolicitacaoEnum  # Ajuste conforme sua estrutura

# ============================================
# MODELO: Solicitacao
# Tabela: problemas urbanos reportados pelos cidadãos
# Tabela CENTRAL do sistema - relaciona usuário, categoria, status
# ============================================

class Solicitacao(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "solicitacoes"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária (identificador único da solicitação)
    id = Column(Integer, primary_key=True, index=True)
    
    # USUARIO_ID: qual cidadão reportou este problema? (chave estrangeira)
    # ForeignKey conecta à tabela "usuarios"
    # index=True melhora buscas
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # CATEGORIA_ID: tipo do problema (Lixo, Iluminação, Acessibilidade)
    # ondelete="RESTRICT" impede deletar categoria se houver solicitação
    categoria_id = Column(
        Integer,
        ForeignKey("categorias.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    
    # STATUS_ID: estado atual do problema
    # status_id = Column(
    #     Integer,
    #     ForeignKey("status.id", ondelete="RESTRICT"),
    #     index=True,
    #     nullable=False
    # )
    status = Column(
        String(50),
        default="PENDENTE",
        nullable=False
    )

    # PROTOCOLO: código único para rastreamento (formato: YYYY-00000)
    # Ex: "2025-00001" = primeiro problema de 2025
    # unique=True garante que cada protocolo é único
    protocolo = Column(String(10), unique=True, index=True, nullable=False)
    
    # DESCRICAO: texto descrevendo o problema em detalhes
    # Campo TEXT permite textos longos (até 1GB no PostgreSQL)
    descricao = Column(Text, nullable=False)
    
    # LATITUDE: coordenada Y do GPS (WGS84)
    # Float armazena números decimais (ex: -23.5505)
    latitude = Column(Float, nullable=False)
    
    # LONGITUDE: coordenada X do GPS (WGS84)
    longitude = Column(Float, nullable=False)
    
    # ENDERECO: endereço legível para humanos ("Rua tal, nº 123")
    endereco = Column(String(500))
    
    # CONTADOR_APOIOS: quantas pessoas apoiaram este problema?
    # Incrementa quando alguém clica "apoiar"
    contador_apoios = Column(Integer, default=0, nullable=False)
    
    # PRAZO_RESOLUCAO: quantos dias até resolver? (ex: 7, 14, 30)
    prazo_resolucao = Column(Integer)  # Pode ser null se não definido
    
    # CRIADO_EM: data/hora de criação automática
    # index=True permite filtrar por data rapidamente
    criado_em = Column(DateTime, default=func.now(), index=True, nullable=False)
    
    # ATUALIZADO_EM: data/hora da última modificação
    atualizado_em = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

        # ========== RELACIONAMENTOS ==========
    # categoria = relationship("Categoria")
    # usuario = relationship("Usuario", back_populates="solicitacoes")
    # # comentarios = relationship("Comentario", back_populates="solicitacao", cascade="all, delete-orphan")
    # atualizacoes = relationship("AtualizacaoSolicitacao", back_populates="solicitacao", cascade="all, delete-orphan")
