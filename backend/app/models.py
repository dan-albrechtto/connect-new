# ============================================
# ARQUIVO: models.py
# DESCRIÇÃO: Modelos do banco de dados (tabelas)
# Define a estrutura de cada tabela usando SQLAlchemy + PostgreSQL
# ============================================

# Importações SQLAlchemy para definir modelos
from sqlalchemy import (
    Column,           # Define coluna da tabela
    Integer,          # Tipo: número inteiro
    String,           # Tipo: texto
    Float,            # Tipo: número com casas decimais
    DateTime,         # Tipo: data e hora
    Date,             # Tipo: apenas data (sem hora)
    Boolean,          # Tipo: verdadeiro/falso
    ForeignKey,       # Chave estrangeira (relacionamento)
    func,             # Funções SQL (NOW, etc)
    Enum,             # Tipo: Enum (valores pré-definidos)
    Text,             # Tipo: texto longo
    UniqueConstraint, # Restrição: valor único em múltiplas colunas
)

from sqlalchemy.orm import relationship

# Importar Base para criar modelos
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum
from datetime import datetime

from database.connection import Base


# ========== ENUMS PYTHON ==========
# Define valores pré-fixos para tipos de usuário e status

class TipoUsuarioEnum(PyEnum):
    """Enum para tipo de usuário: cidadão ou administrador."""
    CIDADAO = 1
    ADMINISTRADOR = 2


class StatusSolicitacaoEnum(PyEnum):
    """Enum para status da solicitação: estados possíveis."""
    PENDENTE = 1           # Acabou de ser criado
    EM_ANALISE = 2         # Admin recebeu e está analisando
    EM_ANDAMENTO = 3       # Setor responsável está trabalhando
    RESOLVIDO = 4          # Problema foi solucionado
    CANCELADO = 5          # Foi cancelado (spam, duplicado, etc)


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
        Enum(StatusSolicitacaoEnum, native_enum=False),
        default=StatusSolicitacaoEnum.PENDENTE,
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



# ============================================
# MODELO: Foto
# Tabela: fotos anexadas aos problemas
# Armazena referências aos arquivos de imagem
# ============================================

class Foto(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "fotos"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # SOLICITACAO_ID: a qual problema esta foto pertence? (chave estrangeira)
    # ondelete="CASCADE" deleta foto se problema for deletado
    solicitacao_id = Column(
        Integer,
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # CAMINHO_ARQUIVO: caminho relativo do arquivo no servidor
    # Ex: "/uploads/2025/01/16/abc123def456.jpg"
    # unique=True garante que o arquivo não está duplicado
    caminho_arquivo = Column(String(500), unique=True, nullable=False)
    
    # TAMANHO: tamanho do arquivo em bytes
    # Util para validar limite de upload
    tamanho = Column(Integer, nullable=False)
    
    # TIPO_MIME: tipo do arquivo (image/jpeg, image/png, etc)
    # Usado para servir arquivo com content-type correto
    tipo_mime = Column(String(50), nullable=False)
    
    # ORDEM: posição da foto (1ª, 2ª, 3ª, etc)
    # Permite ordenar fotos como o usuário fez upload
    ordem = Column(Integer, default=1, nullable=False)
    
    # CRIADO_EM: data/hora do upload automática
    criado_em = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Foto id={self.id} solicitacao={self.solicitacao_id}>"


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


# ============================================
# MODELO: Comentario
# Tabela: comentários de cidadãos e admin em solicitações
# Permite diálogo entre usuário e administrador
# ============================================

class Comentario(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "comentarios"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # SOLICITACAO_ID: em qual problema? (chave estrangeira)
    solicitacao_id = Column(
        Integer,
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # USUARIO_ID: quem comentou? (chave estrangeira)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # TEXTO: conteúdo do comentário
    texto = Column(Text, nullable=False)
    
    # INTERNO: só admin vê? (comentários privados)
    # True = comentário confidencial (cidadão não vê)
    # False = comentário público (todos veem)
    interno = Column(Boolean, default=False, nullable=False)
    
    # CRIADO_EM: data/hora do comentário automática
    criado_em = Column(DateTime, default=func.now(), nullable=False)

     # ========== RELACIONAMENTOS ==========
    # solicitacao = relationship("Solicitacao", back_populates="comentarios")
    # usuario = relationship("Usuario", back_populates="comentarios")


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


# ============================================
# MODELO: Relatorio
# Tabela: relatórios gerados pelo admin
# Armazena dados de relatórios (PDF, CSV, Excel, etc)
# ============================================

class Relatorio(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "relatorios"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # ADMINISTRADOR_ID: qual admin gerou? (chave estrangeira)
    administrador_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # NOME_RELATORIO: título descritivo
    # Ex: "Relatório de Iluminação - Janeiro 2025"
    nome_relatorio = Column(String(255), nullable=False)
    
    # DESCRICAO: resumo do que o relatório contém
    descricao = Column(Text)
    
    # PERIODO_INICIAL: primeira data incluída no relatório
    periodo_inicial = Column(Date, nullable=False)
    
    # PERIODO_FINAL: última data incluída no relatório
    periodo_final = Column(Date, nullable=False)
    
    # FORMATO_SAIDA: tipo de arquivo gerado
    # Ex: "PDF", "CSV", "EXCEL"
    formato_saida = Column(String(50), nullable=False)
    
    # CAMINHO_ARQUIVO: onde o arquivo está armazenado
    # Ex: "/relatorios/2025/01/relatorio_janeiro_20250116.pdf"
    # Null enquanto está sendo gerado
    caminho_arquivo = Column(String(500))
    
    # FILTROS_APLICADOS: quais filtros foram usados? (JSON string)
    # Ex: '{"categoria": 1, "status": 4, "cidade": "São Paulo"}'
    filtros_aplicados = Column(Text)
    
    # CRIADO_EM: data/hora de criação automática
    criado_em = Column(DateTime, default=func.now(), nullable=False)



# ========== RESUMO DAS TABELAS ==========
# 1. usuarios          - dados de login/perfil dos usuários
# 2. categorias        - tipos de problemas (Lixo, Iluminação, Acessibilidade)
# 3. status            - estados de solicitação (Pendente, Em análise, etc)
# 4. solicitacoes      - problemas reportados (central)
# 5. fotos             - imagens anexadas aos problemas
# 6. apoios            - cidadãos apoiando problemas
# 7. comentarios       - diálogo entre usuários e admin
# 8. atualizacoes_solicitacao - histórico de mudanças
# 9. avaliacoes        - notas 1-5 sobre soluções
# 10. relatorios       - relatórios gerados pelo admin
#
# Total: 10 tabelas, estrutura completa conforme documentação!