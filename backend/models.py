# ============================================
# ARQUIVO: models.py
# DESCRIÇÃO: Modelos do banco de dados (tabelas)
# Define a estrutura de cada tabela usando SQLAlchemy
# ============================================

# Importar SQLAlchemy para definir modelos
from sqlalchemy import (
    Column,           # Define coluna da tabela
    Integer,          # Tipo: número inteiro
    String,           # Tipo: texto
    Float,            # Tipo: número com casas decimais
    DateTime,         # Tipo: data e hora
    Boolean,          # Tipo: verdadeiro/falso
    ForeignKey,       # Chave estrangeira (relacionamento)
    func,             # Funções SQL
)

# Importar Base para criar modelos
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# ========== BASE DECLARATIVA ==========

# Base = classe base para todos os modelos
# Todos os modelos herdam de Base
Base = declarative_base()

# ============================================
# MODELO: Usuario
# Tabela para armazenar usuários da aplicação
# ============================================

class Usuario(Base):
    # Nome da tabela no banco
    __tablename__ = "usuarios"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária (identificador único)
    id = Column(Integer, primary_key=True, index=True)
    
    # CPF: documento único
    cpf = Column(String(11), unique=True, index=True)
    
    # Senha: hash seguro (nunca armazenar em texto plano!)
    senha_hash = Column(String(255))
    
    # Nome completo
    nome = Column(String(255))
    
    # Email
    email = Column(String(255), unique=True, index=True)
    
    # Telefone
    telefone = Column(String(11))
    
    # Ativo: usuário pode fazer login?
    ativo = Column(Boolean, default=True)
    
    # Data de criação (automática)
    criado_em = Column(DateTime, default=datetime.utcnow)

# ============================================
# MODELO: Categoria
# Tabela para armazenar tipos de problemas
# ============================================

class Categoria(Base):
    # Nome da tabela
    __tablename__ = "categorias"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Nome: "Coleta de Lixo", "Iluminação", "Acessibilidade"
    nome = Column(String(255), unique=True, index=True)
    
    # Descrição: texto explicativo
    descricao = Column(String(500))
    
    # Ícone: emoji ou nome do ícone
    icone = Column(String(50))
    
    # Ativo: está disponível para seleção?
    ativo = Column(Boolean, default=True)
    
    # Data de criação
    criado_em = Column(DateTime, default=datetime.utcnow)

# ============================================
# MODELO: Status
# Tabela para armazenar estados do problema
# ============================================

class Status(Base):
    # Nome da tabela
    __tablename__ = "status"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Nome: "Aberto", "Em análise", "Resolvido", "Fechado"
    nome = Column(String(50), unique=True, index=True)
    
    # Descrição
    descricao = Column(String(255))

# ============================================
# MODELO: Solicitacao
# Tabela principal: armazena cada problema reportado
# ============================================

class Solicitacao(Base):
    # Nome da tabela
    __tablename__ = "solicitacoes"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária (identificador único)
    id = Column(Integer, primary_key=True, index=True)
    
    # Usuario_ID: quem reportou? (chave estrangeira)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    
    # Categoria_ID: tipo do problema (chave estrangeira)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), index=True)
    
    # Status_ID: estado do problema (chave estrangeira)
    status_id = Column(Integer, ForeignKey("status.id"), index=True)
    
    # Descrição: o que é o problema?
    descricao = Column(String(1000))
    
    # Latitude: coordenada Y do GPS
    latitude = Column(Float)
    
    # Longitude: coordenada X do GPS
    longitude = Column(Float)
    
    # Endereco: "Rua tal, nº 123"
    endereco = Column(String(500))
    
    # Data de criação (automática)
    criado_em = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Data de atualização
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================
# MODELO: Foto
# Tabela: armazena fotos anexadas aos problemas
# ============================================

class Foto(Base):
    # Nome da tabela
    __tablename__ = "fotos"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Solicitacao_ID: qual problema? (chave estrangeira)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), index=True)
    
    # Caminho_arquivo: "/uploads/20250116_120000_abc123.jpg"
    caminho_arquivo = Column(String(500), unique=True)
    
    # URL da foto (para acessar via browser)
    url = Column(String(500))
    
    # Tamanho em bytes
    tamanho = Column(Integer)
    
    # Tipo MIME: "image/jpeg", "image/png"
    tipo_mime = Column(String(50))
    
    # Data de upload (automática)
    criado_em = Column(DateTime, default=datetime.utcnow)

# ============================================
# MODELO: Apoio
# Tabela: armazena quem apoiou qual problema
# ============================================

class Apoio(Base):
    # Nome da tabela
    __tablename__ = "apoios"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Solicitacao_ID: qual problema? (chave estrangeira)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), index=True)
    
    # Usuario_ID: quem apoiou? (chave estrangeira)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    
    # Data do apoio (automática)
    criado_em = Column(DateTime, default=datetime.utcnow)

# ============================================
# MODELO: Comentario
# Tabela: comentários dos usuários/admin
# ============================================

class Comentario(Base):
    # Nome da tabela
    __tablename__ = "comentarios"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Solicitacao_ID: em qual problema? (chave estrangeira)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), index=True)
    
    # Usuario_ID: quem comentou? (chave estrangeira)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    
    # Texto: o comentário
    texto = Column(String(1000))
    
    # É interno? (só admin vê)
    interno = Column(Boolean, default=False)
    
    # Data do comentário (automática)
    criado_em = Column(DateTime, default=datetime.utcnow)
