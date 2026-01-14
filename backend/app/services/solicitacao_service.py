# backend/app/services/solicitacao_service.py

"""
Service de Solicitação

Orquestra todas as operações relacionadas a solicitações:
- Criar solicitação com foto
- Atualizar status (e notificar cidadão)
- Buscar solicitações
- Duplicidade
"""

from sqlalchemy.orm import Session
from datetime import datetime
from app.utils.enums import StatusSolicitacaoEnum
from app.crud.solicitacao_crud import solicitacao_crud  # Vamos criar depois
from app.crud.notificacao_crud import notificacao_crud  # Vamos criar depois


async def atualizar_status_e_notificar(
    db: Session,
    solicitacao_id: int,
    novo_status: int,  # Valor numérico (1, 2, 3, 4, 5)
    descricao_admin: str = ""
) -> dict:
    """
    Atualiza o status de uma solicitação E cria notificação para o cidadão.
    
    Esta é a ORQUESTRAÇÃO principal: combina CRUD de solicitação + CRUD de notificação.
    
    Args:
        db: Sessão do banco
        solicitacao_id: ID da solicitação a atualizar
        novo_status: Novo status (valor numérico)
        descricao_admin: Comentário do admin (opcional)
    
    Returns:
        Dicionário com solicitação atualizada e notificação criada
    
    Exemplo de uso (em routes/admin.py):
        resultado = await atualizar_status_e_notificar(
            db,
            solicitacao_id=123,
            novo_status=3,  # EM_ANDAMENTO
            descricao_admin="Encaminhado para equipe de iluminação"
        )
    """
    
    # ========== PASSO 1: Buscar solicitação atual ==========
    solicitacao = await solicitacao_crud.obter_por_id(db, solicitacao_id)
    
    if not solicitacao:
        raise ValueError(f"Solicitação {solicitacao_id} não encontrada")
    
    # ========== PASSO 2: Guardar status ANTERIOR (para montagem de texto) ==========
    status_anterior_enum = StatusSolicitacaoEnum(solicitacao.status)
    status_anterior_label = status_anterior_enum.label
    
    # ========== PASSO 3: Atualizar status no BD ==========
    solicitacao_atualizada = await solicitacao_crud.atualizar(
        db,
        solicitacao_id,
        {"status": novo_status}
    )
    
    # ========== PASSO 4: Montar texto da notificação COM LABELS AMIGÁVEIS ==========
    status_novo_enum = StatusSolicitacaoEnum(novo_status)
    status_novo_label = status_novo_enum.label
    
    titulo = "Sua solicitação foi atualizada"
    
    conteudo = f'Status mudou de "{status_anterior_label}" para "{status_novo_label}".'
    
    if descricao_admin:
        conteudo += f'\n\nComentário do administrador:\n{descricao_admin}'
    
    # ========== PASSO 5: Criar notificação no BD ==========
    notificacao = await notificacao_crud.criar(
        db,
        {
            "usuario_id": solicitacao.usuario_id,
            "solicitacao_id": solicitacao_id,
            "titulo": titulo,
            "conteudo": conteudo,
            "lida": False,
            "criado_em": datetime.utcnow()
        }
    )
    
    # ========== PASSO 6: Retornar resultado ==========
    return {
        "solicitacao_id": solicitacao_atualizada.id,
        "status_novo": solicitacao_atualizada.status,
        "status_novo_label": status_novo_label,
        "notificacao_criada": {
            "id": notificacao.id,
            "titulo": notificacao.titulo,
            "conteudo": notificacao.conteudo
        }
    }
