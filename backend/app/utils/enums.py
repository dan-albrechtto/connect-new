from enum import Enum as PyEnum


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