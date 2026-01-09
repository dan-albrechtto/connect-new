"""
Serviço de Notificações
Centraliza toda lógica de notificações do sistema.

Responsabilidades:
- Criar notificação no banco quando status de solicitação muda
- Listar notificações de um usuário (para sininho)
- Marcar notificação como lida
- Contar notificações não-lidas (badge do sininho)
- Deletar notificação
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
from app.models.notificacao import Notificacao
from app.schemas import (
    NotificacaoListaResponse,
    NotificacaoMarcarLidaRequest,
    NotificacaoMarcarLidaResponse,
    NotificacaoDeletarResponse,
    NotificacaoContarResponse
)
# from app.utils.email import enviar_email_notificacao_status  # ← Criaremos depois


def criar_notificacao_status_atualizado(
    db: Session,
    usuario_id: int,
    solicitacao_id: int,
    titulo: str,
    conteudo: str
) -> Notificacao:
    """
    Cria uma notificação de atualização de status no banco.
    
    Esta função é chamada automaticamente quando admin muda o status de uma solicitação.
    
    Args:
        db: Sessão do banco de dados
        usuario_id: ID do cidadão que receberá a notificação
        solicitacao_id: ID da solicitação que foi atualizada
        titulo: Título da notificação (ex: "Sua solicitação foi atualizada")
        conteudo: Detalhes da mudança (ex: "Status: PENDENTE → EM_ANÁLISE")
    
    Returns:
        Notificacao recém-criada
    
    Exemplo de uso:
        notif = criar_notificacao_status_atualizado(
            db, 
            usuario_id=5,
            solicitacao_id=123,
            titulo="Solicitação atualizada",
            conteudo="Status mudou de PENDENTE para EM_ANÁLISE"
        )
    """
    
    # Criar nova notificação
    notificacao = Notificacao(
        usuario_id=usuario_id,
        solicitacao_id=solicitacao_id,
        titulo=titulo,
        conteudo=conteudo,
        lida=False,
        criado_em=datetime.utcnow()
    )
    
    # Salvar no banco
    db.add(notificacao)
    db.commit()
    db.refresh(notificacao)
    
    return notificacao


def listar_notificacoes_usuario(
    db: Session,
    usuario_id: int,
    apenas_nao_lidas: bool = False,
    limite: int = 50,
    offset: int = 0
) -> NotificacaoListaResponse:
    """
    Lista notificações de um usuário.
    
    Args:
        db: Sessão do banco
        usuario_id: ID do usuário
        apenas_nao_lidas: Se True, retorna só não-lidas (para badge do sininho)
        limite: Máximo de resultados
        offset: Paginação
    
    Returns:
        NotificacaoListaResponse com total, não-lidas e lista
    """
    
    # Query base
    query = db.query(Notificacao).filter(Notificacao.usuario_id == usuario_id)
    
    if apenas_nao_lidas:
        query = query.filter(Notificacao.lida == False)
    
    # Total de registros
    total = query.count()
    
    # Listar com paginação (mais recentes primeiro)
    notificacoes = query.order_by(
        desc(Notificacao.criado_em)
    ).limit(limite).offset(offset).all()
    
    # Contar não-lidas
    nao_lidas = db.query(Notificacao).filter(
        and_(
            Notificacao.usuario_id == usuario_id,
            Notificacao.lida == False
        )
    ).count()
    
    return NotificacaoListaResponse(
        total=total,
        nao_lidas=nao_lidas,
        notificacoes=notificacoes
    )


def contar_nao_lidas(db: Session, usuario_id: int) -> int:
    """
    Conta quantas notificações não-lidas o usuário tem.
    
    Útil para atualizar o badge do sininho sem trazer todas as notificações.
    
    Args:
        db: Sessão do banco
        usuario_id: ID do usuário
    
    Returns:
        Número inteiro de notificações não-lidas
    """
    
    return db.query(Notificacao).filter(
        and_(
            Notificacao.usuario_id == usuario_id,
            Notificacao.lida == False
        )
    ).count()


def marcar_notificacao_como_lida(
    db: Session,
    notificacao_id: int,
    usuario_id: int
) -> NotificacaoMarcarLidaResponse:
    """
    Marca uma notificação específica como lida.
    
    Args:
        db: Sessão do banco
        notificacao_id: ID da notificação
        usuario_id: ID do usuário (valida propriedade)
    
    Returns:
        Resposta com sucesso e contador atualizado
    """
    
    # Buscar notificação (valida que pertence ao usuário)
    notificacao = db.query(Notificacao).filter(
        and_(
            Notificacao.id == notificacao_id,
            Notificacao.usuario_id == usuario_id
        )
    ).first()
    
    if not notificacao:
        return NotificacaoMarcarLidaResponse(
            sucesso=False,
            mensagem="Notificação não encontrada",
            nao_lidas_restantes=0
        )
    
    # Marcar como lida
    notificacao.lida = True
    notificacao.atualizado_em = datetime.utcnow()
    db.commit()
    
    # Contar não-lidas restantes
    nao_lidas_restantes = contar_nao_lidas(db, usuario_id)
    
    return NotificacaoMarcarLidaResponse(
        sucesso=True,
        mensagem="Notificação marcada como lida",
        nao_lidas_restantes=nao_lidas_restantes
    )


def marcar_todas_como_lidas(db: Session, usuario_id: int) -> NotificacaoMarcarLidaResponse:
    """
    Marca TODAS as notificações não-lidas como lidas de uma vez.
    
    Args:
        db: Sessão do banco
        usuario_id: ID do usuário
    
    Returns:
        Resposta com sucesso
    """
    
    agora = datetime.utcnow()
    
    # Atualizar todas não-lidas
    quantidade = db.query(Notificacao).filter(
        and_(
            Notificacao.usuario_id == usuario_id,
            Notificacao.lida == False
        )
    ).update({
        Notificacao.lida: True,
        Notificacao.atualizado_em: agora
    })
    
    db.commit()
    
    return NotificacaoMarcarLidaResponse(
        sucesso=True,
        mensagem=f"{quantidade} notificações marcadas como lidas",
        nao_lidas_restantes=0
    )


def deletar_notificacao(
    db: Session,
    notificacao_id: int,
    usuario_id: int
) -> NotificacaoDeletarResponse:
    """
    Deleta uma notificação.
    
    Args:
        db: Sessão do banco
        notificacao_id: ID da notificação
        usuario_id: ID do usuário (valida propriedade)
    
    Returns:
        Resposta com sucesso ou erro
    """
    
    notificacao = db.query(Notificacao).filter(
        and_(
            Notificacao.id == notificacao_id,
            Notificacao.usuario_id == usuario_id
        )
    ).first()
    
    if not notificacao:
        return NotificacaoDeletarResponse(
            sucesso=False,
            mensagem="Notificação não encontrada"
        )
    
    db.delete(notificacao)
    db.commit()
    
    return NotificacaoDeletarResponse(
        sucesso=True,
        mensagem="Notificação deletada com sucesso"
    )


# ========== FUNÇÃO ESPECIAL: Atualização automática ==========
# def notificar_atualizacao_status(
#     db: Session,
#     solicitacao_id: int,
#     usuario_id: int,
#     status_anterior: str,
#     status_novo: str,
#     descricao_admin: str
# ) -> Notificacao:
#     """
#     FUNÇÃO ESPECIAL para quando admin atualiza status.
    
#     Esta é a função principal que você vai chamar nas rotas de atualização de solicitação.
    
#     Args:
#         db: Sessão do banco
#         solicitacao_id: ID da solicitação
#         usuario_id: ID do cidadão
#         status_anterior: Status anterior (ex: "PENDENTE")
#         status_novo: Novo status (ex: "EM_ANÁLISE")
#         descricao_admin: O que o admin escreveu (ex: "Encaminhado para setor de iluminação")
    
#     Faz automaticamente:
#     1. Cria notificação no banco (para sininho)
#     2. Envia e-mail via Celery (background)
    
#     Returns:
#         Notificacao criada
#     """
    
#     # 1. Criar título e conteúdo
#     titulo = "Sua solicitação foi atualizada"
#     conteudo = f"""
#     Status mudou de "{status_anterior}" para "{status_novo}".
    
#     Observação do administrador:
#     {descricao_admin}
    
#     Clique para ver detalhes.
#     """
    
#     # 2. Criar notificação no banco
#     notificacao = criar_notificacao_status_atualizado(
#         db=db,
#         usuario_id=usuario_id,
#         solicitacao_id=solicitacao_id,
#         titulo=titulo,
#         conteudo=conteudo
#     )
    
#     # 3. Enviar e-mail (background - não bloqueia)
#     enviar_email_notificacao_status.delay(
#         usuario_email="usuario@email.com",  # ← Buscar do banco depois
#         solicitacao_id=solicitacao_id,
#         titulo=titulo,
#         conteudo=conteudo
#     )
    
#     return notificacao
