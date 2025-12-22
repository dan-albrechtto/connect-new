from pydantic import BaseModel, EmailStr
from datetime import datetime


# USUARIO
class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    senha: str


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    cpf: str
    tipo_usuario: str
    criado_em: datetime

    class Config:
        from_attributes = True


# CATEGORIA
class CategoriaCreate(BaseModel):
    nome: str
    descricao: str


class CategoriaResponse(BaseModel):
    id: int
    nome: str
    descricao: str

    class Config:
        from_attributes = True


# SOLICITACAO
class SolicitacaoCreate(BaseModel):
    descricao: str
    latitude: float
    longitude: float
    categoria_id: int
    endereco: str


class SolicitacaoResponse(BaseModel):
    id: int
    descricao: str
    latitude: float
    longitude: float
    categoria_id: int
    usuario_id: int
    status_id: int
    endereco: str
    protocolo: str
    criado_em: datetime

    class Config:
        from_attributes = True


# FOTO
class FotoCreate(BaseModel):
    solicitacao_id: int
    caminho_arquivo: str
    tamanho: int
    tipo_mime: str


class FotoResponse(BaseModel):
    id: int
    solicitacao_id: int
    caminho_arquivo: str
    tamanho: int
    tipo_mime: str
    criado_em: datetime

    class Config:
        from_attributes = True


# APOIO
class ApoioCreate(BaseModel):
    solicitacao_id: int
    usuario_id: int


class ApoioResponse(BaseModel):
    id: int
    solicitacao_id: int
    usuario_id: int
    criado_em: datetime

    class Config:
        from_attributes = True


# COMENTARIO
class ComentarioCreate(BaseModel):
    solicitacao_id: int
    usuario_id: int
    texto: str


class ComentarioResponse(BaseModel):
    id: int
    solicitacao_id: int
    usuario_id: int
    texto: str
    criado_em: datetime

    class Config:
        from_attributes = True


# AVALIACAO
class AvaliacaoCreate(BaseModel):
    solicitacao_id: int
    usuario_id: int
    nota: int


class AvaliacaoResponse(BaseModel):
    id: int
    solicitacao_id: int
    usuario_id: int
    nota: int
    comentario: str
    criado_em: datetime

    class Config:
        from_attributes = True


# RELATORIO
class RelatorioCreate(BaseModel):
    administrador_id: int
    nome_relatorio: str
    descricao: str
    periodo_inicial: str
    periodo_final: str
    formato_saida: str


class RelatorioResponse(BaseModel):
    id: int
    administrador_id: int
    nome_relatorio: str
    descricao: str
    periodo_inicial: str
    periodo_final: str
    formato_saida: str
    caminho_arquivo: str
    criado_em: datetime

    class Config:
        from_attributes = True

class FotoResponse(BaseModel):
    id: int
    problema_id: int
    caminho: str
    tamanho_kb: float
    criado_em: datetime
    
    class Config:
        from_attributes = True
