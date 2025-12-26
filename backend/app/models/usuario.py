from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Enum, func
from database.connection import Base
from app.utils.enums import TipoUsuarioEnum  # Ajuste conforme sua estrutura

# ============================================
# MODELO: Usuario
# Tabela: usuários cadastrados no sistema
# Armazena dados de login e perfil de cada usuário
# ============================================

class Usuario(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "usuarios"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária (identificador único do usuário)
    # index=True melhora performance em buscas
    id = Column(Integer, primary_key=True, index=True)
    
    # TIPO_USUARIO: 1=Cidadão, 2=Administrador
    # Enum mapeia para números no banco
    tipo_usuario = Column(
        Enum(TipoUsuarioEnum),
        default=TipoUsuarioEnum.CIDADAO,
        nullable=False
    )
    
    # CPF: documento único do usuário (formato: 00000000000)
    # unique=True garante que não há CPFs duplicados
    # index=True acelera buscas por CPF
    cpf = Column(String(11), unique=True, index=True, nullable=False)
    
    # SENHA_HASH: hash seguro da senha (NUNCA armazenar em texto plano!)
    # Usar bcrypt ou similar para fazer hash
    senha_hash = Column(String(255), nullable=False)
    
    # NOME: nome completo do usuário
    nome = Column(String(255), nullable=False)
    
    # EMAIL: endereço de email para contato/recuperação de senha
    # unique=True garante que emails não se repetem
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # TELEFONE: celular para notificações e recuperação de acesso
    telefone = Column(String(20))  # Aceita formatos diferentes
    
    # DATA_NASCIMENTO: data de nascimento do usuário
    # Requisitado por RF2 da documentação
    data_nascimento = Column(Date)
    
    # ATIVO: usuário pode fazer login? (controle de acesso)
    # True = pode usar, False = conta desativada/deletada
    ativo = Column(Boolean, default=True, nullable=False)
    
    # CRIADO_EM: data/hora de criação automática
    # func.now() executa a função NOW() do PostgreSQL
    criado_em = Column(DateTime, default=func.now(), nullable=False)
    
    # ATUALIZADO_EM: data/hora da última atualização
    # onupdate=func.now() atualiza automaticamente ao modificar registro
    atualizado_em = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

        # ========== RELACIONAMENTOS ==========
    # solicitacoes = relationship("Solicitacao", back_populates="usuario")
    # comentarios = relationship("Comentario", back_populates="usuario")