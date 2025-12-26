# backend/app/models/__init__.py

from database.connection import Base
from app.utils.enums import TipoUsuarioEnum, StatusSolicitacaoEnum

# Importar todos os modelos
from app.models.usuario import Usuario
from app.models.solicitacao import Solicitacao
from app.models.categoria import Categoria
from app.models.foto import Foto
from app.models.atualizacao_solicitacao import AtualizacaoSolicitacao
from app.models.apoio_solicitacao import Apoio
from app.models.avaliacao import Avaliacao

__all__ = [
    "Base",
    "TipoUsuarioEnum",
    "StatusSolicitacaoEnum",
    "Usuario",
    "Solicitacao",
    "Categoria",
    "Foto",
    "AtualizacaoSolicitacao",
    "Apoio",
    "Avaliacao",
]
