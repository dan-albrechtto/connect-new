from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional


# ========== ENUMS - IMPORTAR DIRETO DO UTILS ==========

from app.utils.enums import StatusSolicitacaoEnum, TipoUsuarioEnum



# ============================================
# USUARIO
# ============================================

class UsuarioCreate(BaseModel):
    """Schema para CRIAR usuário (input do cliente)"""
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo")
    email: EmailStr = Field(..., description="Email único")
    cpf: str = Field(..., pattern=r"^\d{11}$", description="CPF sem formatação (11 dígitos)")
    senha: str = Field(..., min_length=6, description="Senha mínima 6 caracteres")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone opcional")
    data_nascimento: Optional[date] = Field(None, description="Data de nascimento")


class UsuarioResponse(BaseModel):
    """Schema para RETORNAR usuário (output da API)"""
    id: int
    nome: str
    email: str
    cpf: str
    tipo_usuario: int  # Armazena como int (1 ou 2)
    telefone: Optional[str] = None
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True
    
    @field_serializer('tipo_usuario')
    def serializar_tipo_usuario(self, value):
        """
        Converte valor int/Enum para o nome do enum (STRING).
        
        Exemplo:
            Se BD tem 1 → retorna "CIDADAO"
            Se BD tem 2 → retorna "ADMINISTRADOR"
        """
        if isinstance(value, TipoUsuarioEnum):
            return value.name  # "CIDADAO", "ADMINISTRADOR"
        
        # Se vier como int, converte para enum e pega o nome
        try:
            enum_obj = TipoUsuarioEnum.from_value(value)
            return enum_obj.name
        except:
            return str(value)
    
class UsuarioUpdate(BaseModel):
    """Schema para ATUALIZAR dados básicos do usuário"""
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone opcional")
    data_nascimento: Optional[date] = Field(None, description="Data de nascimento opcional")


class MudarSenhaRequest(BaseModel):
    """Schema para MUDAR SENHA"""
    senha_atual: str = Field(..., description="Senha atual para validação")
    nova_senha: str = Field(..., min_length=8, description="Nova senha")
    confirmar_senha: str = Field(..., description="Confirmação da nova senha")
    
    @field_validator('nova_senha', mode='after')
    @classmethod
    def validar_forca_senha(cls, v):
        if len(v) < 8:
            raise ValueError('Senha deve ter mínimo 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter pelo menos 1 MAIÚSCULA')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter pelo menos 1 minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos 1 número')
        caracteres_especiais = '!@#$%^&*'
        if not any(c in caracteres_especiais for c in v):
            raise ValueError('Senha deve conter pelo menos 1 caractere especial (!@#$%^&*)')
        return v
    
    @field_validator('confirmar_senha', mode='after')
    @classmethod
    def validar_senhas_iguais(cls, v, info):
        if 'nova_senha' in info.data and v != info.data['nova_senha']:
            raise ValueError('Senhas não correspondem')
        return v


class MudarSenhaResponse(BaseModel):
    """Schema para resposta ao mudar senha"""
    mensagem: str = "Senha alterada com sucesso"


# ============================================
# CATEGORIA
# ============================================

class CategoriaResponse(BaseModel):
    """Schema para RETORNAR categoria (apenas leitura - pré-definidas pelo sistema)
    
    Categorias são criadas apenas pelo desenvolvedor no seed inicial:
    - 1: Coleta de Lixo (🗑️)
    - 2: Iluminação Pública (💡)
    - 3: Acessibilidade (♿)
    - 4: Vias (🚗)
    
    Admin e cidadão apenas CONSULTAM, não criam/editam/deletam.
    """
    id: int
    nome: str
    descricao: str
    icone: str  # Emoji: "🗑️", "💡", "♿", "🚗"
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


# ============================================
# SOLICITACAO
# ============================================

class SolicitacaoCreate(BaseModel):
    """Schema para CRIAR solicitação (input do cidadão)"""
    categoria_id: int = Field(..., description="ID da categoria pré-definida")
    descricao: str = Field(..., min_length=10, description="Descrição detalhada do problema")
    latitude: float = Field(..., ge=-90, le=90, description="Coordenada Y (WGS84)")
    longitude: float = Field(..., ge=-180, le=180, description="Coordenada X (WGS84)")
    endereco: str = Field(..., max_length=500, description="Endereço legível")


class SolicitacaoUpdate(BaseModel):
    """
    Schema para ATUALIZAR status de solicitação (input do admin).
    
    O admin envia: {"status": "EM_ANDAMENTO", "descricao_admin": "..."}
    O sistema converte automaticamente para enum.
    """
    status: str = Field(
        ...,
        description="Novo status (PENDENTE, EM_ANALISE, EM_ANDAMENTO, RESOLVIDO, CANCELADO)"
    )
    descricao_admin: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Motivo/descrição da atualização"
    )

    @field_validator('status', mode='before')
    @classmethod
    def validar_status(cls, v):
        """Valida se o status é válido"""
        status_validos = ["PENDENTE", "EM_ANALISE", "EM_ANDAMENTO", "RESOLVIDO", "CANCELADO"]
        if v not in status_validos:
            raise ValueError(f"Status '{v}' inválido. Use: {', '.join(status_validos)}")
        return v


class SolicitacaoResponse(BaseModel):
    """
    Schema para RETORNAR solicitação (output da API)
    Nota: status vem do BD como Enum, aqui convertemos para o nome (STRING).
    """
    id: int
    protocolo: str
    descricao: str
    latitude: float
    longitude: float
    endereco: str
    categoria_id: int
    usuario_id: int
    status: str  # Será convertido por field_serializer (ex: "EM_ANDAMENTO")
    contador_apoios: int
    prazo_resolucao: Optional[int] = None
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
    
    @field_serializer('status')
    def serializar_status(self, value):
        """
        Converte Enum do BD para o NAME (string).
        
        Exemplo:
            Se BD tem StatusSolicitacaoEnum.EM_ANDAMENTO (value=3)
            → Retorna "EM_ANDAMENTO" (string)
        """
        if isinstance(value, StatusSolicitacaoEnum):
            return value.name  # "PENDENTE", "EM_ANALISE", etc
        
        # Se vier como int, converte para enum e pega o nome
        try:
            enum_obj = StatusSolicitacaoEnum.from_value(value)
            return enum_obj.name
        except:
            return str(value)


# ============================================
# FOTO
# ============================================

class FotoCreate(BaseModel):
    """Schema para CRIAR foto (input - arquivo enviado separadamente)"""
    solicitacao_id: int = Field(..., description="ID da solicitação")
    ordem: int = Field(1, ge=1, description="Ordem/posição da foto na solicitação")


class FotoResponse(BaseModel):
    """Schema para RETORNAR foto (output da API)"""
    id: int
    solicitacao_id: int
    caminho_arquivo: str  # storage/fotos/{solicitacao_id}/foto_YYYY-MM-DD_HH-MM-SS.jpg
    tamanho: int  # Tamanho em bytes
    tipo_mime: str  # "image/jpeg"
    ordem: int
    criado_em: datetime

    class Config:
        from_attributes = True


# ============================================
# APOIO
# ============================================

class ApoioCreate(BaseModel):
    """Schema para CRIAR apoio (cidadão apoia uma solicitação existente)"""
    solicitacao_id: int = Field(..., description="ID da solicitação a apoiar")


class ApoioResponse(BaseModel):
    """Schema para RETORNAR apoio (output da API)"""
    id: int
    solicitacao_id: int
    usuario_id: int  # Quem apoiou
    criado_em: datetime

    class Config:
        from_attributes = True


# # ============================================
# # COMENTARIO
# # ============================================

# class ComentarioCreate(BaseModel):
#     """Schema para CRIAR comentário (input do cidadão/admin)"""
#     solicitacao_id: int = Field(..., description="ID da solicitação")
#     texto: str = Field(..., min_length=1, max_length=5000, description="Conteúdo do comentário")
#     interno: bool = Field(False, description="Apenas admin e criador veem? (default: false = público)")


# class ComentarioResponse(BaseModel):
#     """Schema para RETORNAR comentário (output da API)"""
#     id: int
#     solicitacao_id: int
#     usuario_id: int
#     texto: str
#     interno: bool
#     criado_em: datetime

#     class Config:
#         from_attributes = True


# ============================================
# ATUALIZACAO SOLICITACAO
# ============================================

class AtualizacaoSolicitacaoCreate(BaseModel):
    """Schema para CRIAR atualização de status (input do admin)
    
    Registra cada mudança de status para histórico completo.
    """
    status_novo: str = Field(..., description="Novo status (PENDENTE, EM_ANALISE, EM_ANDAMENTO, RESOLVIDO, CANCELADO)")
    descricao: str = Field(..., min_length=1, max_length=2000, description="Motivo/descrição da mudança")

    @field_validator('status_novo', mode='before')
    @classmethod
    def validar_status(cls, v):
        """Valida se o status é válido"""
        status_validos = ["PENDENTE", "EM_ANALISE", "EM_ANDAMENTO", "RESOLVIDO", "CANCELADO"]
        if v not in status_validos:
            raise ValueError(f"Status '{v}' inválido. Use: {', '.join(status_validos)}")
        return v


class AtualizacaoSolicitacaoResponse(BaseModel):
    """Schema para RETORNAR atualização (output da API)
    
    Cada vez que admin muda status, um registro é criado aqui.
    Isso permite ver o histórico completo da solicitação.
    """
    id: int
    solicitacao_id: int
    administrador_id: int  # Qual admin fez a mudança
    status_anterior: str  # "PENDENTE" (era)
    status_novo: str  # "EM_ANALISE" (virou)
    descricao: str
    criado_em: datetime

    class Config:
        from_attributes = True


# ============================================
# AVALIACAO
# ============================================

class AvaliacaoCreate(BaseModel):
    """Schema para CRIAR avaliação (input do cidadão após resolução)"""
    nota: int = Field(..., ge=1, le=5, description="Nota de satisfação de 1 a 5 estrelas")
    problema_resolvido: bool = Field(..., description="Problema foi realmente resolvido?")
    comentario: Optional[str] = Field(None, max_length=500, description="Feedback textual opcional")


class AvaliacaoResponse(BaseModel):
    """Schema para RETORNAR avaliação (output da API)"""
    id: int
    solicitacao_id: int
    usuario_id: int
    nota: int
    problema_resolvido: bool
    comentario: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True



# ============================================
# RELATORIO
# ============================================

class RelatorioCreate(BaseModel):
    """Schema para CRIAR relatório (input do admin)"""
    nome_relatorio: str = Field(..., max_length=255, description="Título do relatório")
    descricao: str = Field(None, max_length=1000, description="Descrição/resumo do relatório")
    periodo_inicial: date = Field(..., description="Data inicial (YYYY-MM-DD)")
    periodo_final: date = Field(..., description="Data final (YYYY-MM-DD)")
    formato_saida: str = Field(..., description="Formato: 'PDF', 'CSV' ou 'EXCEL'")
    filtros_aplicados: str = Field(None, description="JSON com filtros aplicados")


class RelatorioResponse(BaseModel):
    """Schema para RETORNAR relatório (output da API)"""
    id: int
    administrador_id: int
    nome_relatorio: str
    descricao: str = None
    periodo_inicial: date
    periodo_final: date
    formato_saida: str
    caminho_arquivo: str = None  # Null enquanto processa, preenchido quando pronto
    filtros_aplicados: str = None
    criado_em: datetime

    class Config:
        from_attributes = True


# ============================================
# LOGIN
# ============================================

class LoginRequest(BaseModel):
    """Schema para requisição de LOGIN"""
    cpf: str = Field(..., pattern=r"^\d{11}$", description="CPF sem formatação (11 dígitos)")
    senha: str = Field(..., min_length=6, description="Senha da conta")


class LoginResponse(BaseModel):
    """Schema para resposta de LOGIN com token JWT"""
    access_token: str  # Token JWT
    token_type: str = "bearer"  # Sempre "bearer"
    usuario: UsuarioResponse  # Dados do usuário autenticado


# ============================================
# ERROR
# ============================================

class ErrorResponse(BaseModel):
    """Schema padrão para erros da API"""
    detalhe: str = Field(..., description="Mensagem de erro descritiva")
    codigo: str = Field(None, description="Código do erro (ex: 'VALIDATION_ERROR', 'NOT_FOUND')")
    timestamp: datetime = Field(default_factory=datetime.now, description="Momento em que o erro ocorreu")


# # ============================================
# # COMENTÁRIOS
# # ============================================

# class ComentarioCreate(BaseModel):
#     """Request para criar comentário"""
#     texto: str = Field(..., min_length=1, max_length=500)


# class ComentarioResponse(BaseModel):
#     """Response com dados do comentário"""
#     id: int
#     solicitacao_id: int
#     usuario_id: int
#     texto: str
#     criado_em: datetime
#     usuario_nome: Optional[str] = None
#     usuario_tipo: Optional[str] = None
    
#     class Config:
#         from_attributes = True

# ============================================
# NOTIFICACAO
# ============================================

class NotificacaoCreate(BaseModel):
    """Schema para CRIAR notificação (uso interno do backend)
    
    Quando admin atualiza status de uma solicitação,
    uma notificação é criada automaticamente.
    """
    usuario_id: int = Field(..., description="ID do usuário que receberá")
    solicitacao_id: int = Field(..., description="ID da solicitação relacionada")
    titulo: str = Field(
        ...,
        max_length=255,
        description="Título da notificação"
    )
    conteudo: str = Field(
        ...,
        description="Conteúdo detalhado da notificação"
    )


class NotificacaoResponse(BaseModel):
    """Schema para RETORNAR notificação via API
    
    Usado em: GET /api/notificacoes/minhas
    """
    id: int
    usuario_id: int
    solicitacao_id: int
    titulo: str
    conteudo: str
    lida: bool
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificacaoListaResponse(BaseModel):
    """Resposta ao listar notificações
    
    Retorna: total, quantidade não-lidas, e lista
    """
    total: int = Field(..., description="Quantidade total de notificações")
    nao_lidas: int = Field(..., description="Quantidade de não-lidas")
    notificacoes: list[NotificacaoResponse] = Field(
        default_factory=list,
        description="Lista de notificações"
    )


class NotificacaoMarcarLidaRequest(BaseModel):
    """Request para marcar notificação como lida"""
    lida: bool = Field(default=True, description="Marcar como lida")


class NotificacaoMarcarLidaResponse(BaseModel):
    """Resposta ao marcar como lida"""
    sucesso: bool
    mensagem: str
    nao_lidas_restantes: int


class NotificacaoDeletarResponse(BaseModel):
    """Resposta ao deletar notificação"""
    sucesso: bool
    mensagem: str


class NotificacaoContarResponse(BaseModel):
    """Resposta ao contar não-lidas"""
    nao_lidas: int = Field(
        ...,
        description="Quantidade de notificações não-lidas"
    )
