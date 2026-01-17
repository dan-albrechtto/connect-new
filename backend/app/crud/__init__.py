# backend/app/crud/__init__.py

"""
Pacote CRUD - Central de Operações de Banco de Dados

Importações centralizadas para facilitar uso em todo o sistema.

Uso:
    from app.crud import UsuarioCRUD, SolicitacaoCRUD
    
    # Criar usuário:
    novo_usuario = UsuarioCRUD.criar_usuario(db, cpf, email, ...)
    
    # Listar solicitações:
    solicitacoes = SolicitacaoCRUD.listar_por_status(db, "PENDENTE")
"""

from .usuario_crud import UsuarioCRUD
from .solicitacao_crud import SolicitacaoCRUD
from .notificacao_crud import NotificacaoCRUD

__all__ = [
    "UsuarioCRUD",
    "SolicitacaoCRUD",
    "NotificacaoCRUD",
]