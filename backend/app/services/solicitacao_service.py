# backend/app/services/solicitacao_service.py

"""
Service de Solicitação

Orquestra todas as operações relacionadas a solicitações:
- Criar solicitação com foto
- Atualizar status (e notificar cidadão)
- Buscar solicitações
- Listar com filtros
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.utils.enums import StatusSolicitacaoEnum
from app.crud import solicitacao_crud, notificacao_crud
from app.models.solicitacao import Solicitacao


# ============================================================================
# FUNÇÃO 1: Listar solicitações com filtros (para admin)
# ============================================================================

async def listar_solicitacoes_com_filtros(
    db: Session,
    status_filtro: Optional[str] = None,
    categoria_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50
) -> dict:
    """
    Orquestra a busca de solicitações com validação de status e filtros.
    
    Esta função SUBSTITUI a lógica que estava em routes/admin.py
    
    Args:
        db: Sessão do banco
        status_filtro: Status para filtrar (string: "PENDENTE", "EM_ANDAMENTO", etc)
        categoria_id: ID da categoria para filtrar
        skip: Para paginação
        limit: Para paginação
    
    Returns:
        Dict com:
        - total: Total de registros encontrados
        - skip, limit: Valores usados
        - solicitacoes: Lista de solicitações
    
    Raises:
        ValueError: Se status_filtro é inválido
    
    Exemplo:
        resultado = await listar_solicitacoes_com_filtros(
            db,
            status_filtro="PENDENTE",
            categoria_id=1,
            skip=0,
            limit=20
        )
        # → {"total": 5, "skip": 0, "limit": 20, "solicitacoes": [...]}
    """
    
    # ========== VALIDAR STATUS FILTRO ==========
    if status_filtro:
        # Valida se é um dos 5 status válidos
        status_validos = StatusSolicitacaoEnum.get_all_values()
        
        if status_filtro not in status_validos:
            raise ValueError(
                f"Status '{status_filtro}' inválido. "
                f"Use: {', '.join(status_validos)}"
            )
        
        # status_valor é a STRING para comparar com BD
        status_valor = status_filtro  # ✅ Já é string
    else:
        status_valor = None
    
    # ========== CONSTRUIR QUERY ==========
    query = db.query(Solicitacao)
    
    # Aplicar filtro de status
    if status_valor is not None:
        query = query.filter(Solicitacao.status == status_valor)
    
    # Aplicar filtro de categoria
    if categoria_id:
        query = query.filter(Solicitacao.categoria_id == categoria_id)
    
    # ========== CONTAR TOTAL ==========
    total = query.count()
    
    # ========== APLICAR PAGINAÇÃO ==========
    solicitacoes = query.order_by(
        Solicitacao.criado_em.desc()
    ).offset(skip).limit(limit).all()
    
    # ========== RETORNAR RESULTADO ==========
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "solicitacoes": solicitacoes
    }


# ============================================================================
# FUNÇÃO 2: Atualizar status + notificar
# ============================================================================

async def atualizar_status_e_notificar(
    db: Session,
    solicitacao_id: int,
    novo_status: str,  # STRING vem do Swagger (ex: "EM_ANDAMENTO")
    descricao_admin: str = ""
) -> dict:
    """
    Atualiza o status de uma solicitação E cria notificação para o cidadão.
    
    Esta é a ORQUESTRAÇÃO principal: combina CRUD de solicitação + CRUD de notificação.
    
    Args:
        db: Sessão do banco
        solicitacao_id: ID da solicitação a atualizar
        novo_status: Novo status (STRING: "EM_ANDAMENTO", "RESOLVIDO", etc)
        descricao_admin: Comentário do admin (opcional)
    
    Returns:
        Dict com solicitação atualizada e notificação criada
    
    Raises:
        ValueError: Se solicitação não existe ou status inválido
    
    Exemplo de uso (em routes/admin.py):
        resultado = await atualizar_status_e_notificar(
            db,
            solicitacao_id=123,
            novo_status="EM_ANDAMENTO",
            descricao_admin="Encaminhado para equipe de iluminação"
        )
    """
    
    # ========== PASSO 1: Buscar solicitação atual ==========
    solicitacao = await solicitacao_crud.obter_por_id(db, solicitacao_id)
    
    if not solicitacao:
        raise ValueError(f"Solicitação {solicitacao_id} não encontrada")
    
    # ========== PASSO 2: Guardar status ANTERIOR ==========
    # O status vem do BD como STRING
    status_anterior_string = solicitacao.status  # ✅ Já é string "PENDENTE"

    # Converte para Enum APENAS para pegar o label amigável
    try:
        status_anterior_enum = StatusSolicitacaoEnum.from_value(status_anterior_string)
        status_anterior_label = status_anterior_enum.label
    except ValueError:
        status_anterior_label = status_anterior_string  # Fallback
    
    # ========== PASSO 3: Validar novo status ==========
    # novo_status vem como StatusSolicitacaoEnum do Schema
    if isinstance(novo_status, StatusSolicitacaoEnum):
        novo_status_string = novo_status.value  # "PENDENTE", "EM_ANALISE", etc
        novo_status_label = novo_status.label
    else:
        # Se vier como string (ex: ao chamar manualmente)
        try:
            novo_status_enum = StatusSolicitacaoEnum.from_value(novo_status)
            novo_status_string = novo_status_enum.value
            novo_status_label = novo_status_enum.label
        except ValueError as e:
            raise ValueError(f"Status inválido: {str(e)}")
    
    # ========== PASSO 4: Atualizar status no BD ==========
    solicitacao_atualizada = await solicitacao_crud.atualizar(
        db,
        solicitacao_id,
        {"status": novo_status_string}  # ✅ Passa STRING
    )
    
    # ========== PASSO 5: Montar texto da notificação COM LABELS AMIGÁVEIS ==========
    titulo = "Sua solicitação foi atualizada"
    conteudo = f'Status mudou de "{status_anterior_label}" para "{novo_status_label}".'
    
    if descricao_admin:
        conteudo += f'\n\nComentário do administrador:\n{descricao_admin}'
    
    # ========== PASSO 6: Criar notificação no BD ==========
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
    
    # ========== PASSO 7: Registrar mudança no histórico ==========
    from app.models.atualizacao_solicitacao import AtualizacaoSolicitacao

    atualizacao = AtualizacaoSolicitacao(
        solicitacao_id=solicitacao_id,
        administrador_id=None,  # Será preenchido pela route
        status_anterior=status_anterior_string,  # ✅ STRING
        status_novo=novo_status_string,          # ✅ STRING
        descricao=descricao_admin,
        criado_em=datetime.now()
    )

    db.add(atualizacao)
    db.commit()
    
    # ========== PASSO 8: Retornar resultado ==========
    return {
        "solicitacao_id": solicitacao_atualizada.id,
        "status_novo": solicitacao_atualizada.status,
        "status_novo_label": novo_status_label,
        "notificacao_criada": {
            "id": notificacao.id,
            "titulo": notificacao.titulo,
            "conteudo": notificacao.conteudo
        }
    }
