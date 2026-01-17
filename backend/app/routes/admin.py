# -*- coding: utf-8 -*-
# ============================================================================
# admin.py - ROTAS ADMINISTRATIVAS
# ============================================================================
# Endpoints exclusivos para administradores (prefixo /api/admin)
# Solicitações, Avaliações, Dashboard
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional
import logging

from app.models import (
    Solicitacao, Avaliacao, Usuario, AtualizacaoSolicitacao,
    TipoUsuarioEnum
)
from app.schemas import (
    SolicitacaoResponse, AtualizacaoSolicitacaoResponse, AvaliacaoResponse
)
from app.utils.seguranca import extrair_user_id_do_token

from database.connection import obter_conexao



logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ============================================================================
# HELPER: Verificar se usuário é administrador
# ============================================================================

def verificar_admin(db: Session, user_id: int) -> bool:
    """Verifica se usuário é admin. Retorna True/False."""
    usuario = db.query(Usuario).filter_by(id=user_id).first()
    if not usuario:
        return False
    return usuario.tipo_usuario == TipoUsuarioEnum.ADMINISTRADOR


def obter_admin_id(authorization: str) -> int:
    """Extrai user_id do token JWT e valida autenticação."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    user_id = extrair_user_id_do_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    return user_id


# ============================================================================
# SOLICITAÇÕES (Admin)
# ============================================================================

@router.get(
    "/solicitacoes",
    response_model=dict,
    summary="Listar solicitações (admin)"
)
async def listar_solicitacoes_admin(
    status_filtro: Optional[str] = None,
    categoria_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Admin lista todas as solicitações do sistema com filtros
    
    - Filtro por status: PENDENTE, EM_ANALISE, EM_ANDAMENTO, RESOLVIDO, CANCELADO
    - Filtro por categoria
    - Paginação: skip/limit
    - Ordena por data (mais recentes primeiro)
    """
    
    # ========== VALIDAR PERMISSÃO ==========
    admin_id = obter_admin_id(authorization)
    
    if not verificar_admin(db, admin_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores"
        )
    
    # ========== CHAMAR SERVICE (TODO O TRABALHO PESADO AQUI) ==========
    from app.services.solicitacao_service import listar_solicitacoes_com_filtros
    
    try:
        resultado = await listar_solicitacoes_com_filtros(
            db,
            status_filtro=status_filtro,
            categoria_id=categoria_id,
            skip=skip,
            limit=limit
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # ========== SERIALIZAR E RETORNAR ==========
    return {
        "total": resultado["total"],
        "skip": resultado["skip"],
        "limit": resultado["limit"],
        "solicitacoes": [
            SolicitacaoResponse.from_orm(s) 
            for s in resultado["solicitacoes"]
        ]
    }



@router.put(
    "/solicitacoes/{solicitacao_id}/status",
    response_model=SolicitacaoResponse,
    summary="Atualizar status da solicitação"
)
async def atualizar_status_solicitacao_admin(
    solicitacao_id: int,
<<<<<<< development
    novo_status: str,
    descricao: str,
=======
    body: SolicitacaoUpdate = Body(...),
>>>>>>> local
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Admin atualiza o status de uma solicitação
    
    - Novo status deve ser: PENDENTE, EM_ANALISE, EM_ANDAMENTO, RESOLVIDO, CANCELADO
    - Descrição obrigatória (motivo da mudança)
    - Registra automaticamente no histórico de atualizações
    """
    
    # ========== VALIDAR PERMISSÃO ==========
    admin_id = obter_admin_id(authorization)
    
    if not verificar_admin(db, admin_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores"
        )
    
    # ========== VALIDAR SOLICITAÇÃO EXISTE ==========
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
<<<<<<< development
    # Validar novo status
    status_validos = ["PENDENTE", "EM_ANALISE", "EM_ANDAMENTO", "RESOLVIDO", "CANCELADO"]
    if novo_status not in status_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status inválido"
        )
    
    # Status anterior (para histórico)
    status_anterior = solicitacao.status.name if hasattr(solicitacao.status, 'name') else str(solicitacao.status)
    
    # Registrar mudança no histórico
    atualizacao = AtualizacaoSolicitacao(
        solicitacao_id=solicitacao_id,
        administrador_id=admin_id,
        status_anterior=status_anterior,
        status_novo=novo_status,
        descricao=descricao,
        criado_em=datetime.now()
    )
    
    db.add(atualizacao)
    
    # Atualizar status da solicitação
    solicitacao.status = novo_status
    solicitacao.atualizado_em = datetime.now()
    
    db.commit()
    db.refresh(solicitacao)
    
    logger.info(f"✅ Status atualizado: solicitacao_id={solicitacao_id} - {status_anterior} → {novo_status}")
    
    return solicitacao
=======
    # ========== CHAMAR SERVICE ==========
    from app.services.solicitacao_service import atualizar_status_e_notificar
    
    try:
        resultado = await atualizar_status_e_notificar(
            db,
            solicitacao_id=solicitacao_id,
            novo_status=body.status.value,
            descricao_admin=body.descricao_admin
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # ========== REGISTRAR ADMIN_ID NO HISTÓRICO ==========
    # O service criou o registro, mas sem admin_id. Vamos atualizar:
    from app.models.atualizacao_solicitacao import AtualizacaoSolicitacao
    
    atualizacao_recente = db.query(AtualizacaoSolicitacao).filter(
        AtualizacaoSolicitacao.solicitacao_id == solicitacao_id
    ).order_by(AtualizacaoSolicitacao.criado_em.desc()).first()
    
    if atualizacao_recente:
        atualizacao_recente.administrador_id = admin_id
        db.commit()
    
    # ========== LOG E RETORNO ==========
    logger.info(
        f"✅ Status atualizado: solicitacao_id={solicitacao_id} - "
        f"{resultado['status_novo_label']} (admin_id={admin_id})"
    )
    
    # ========== RETORNAR SOLICITAÇÃO ATUALIZADA ==========
    solicitacao_atualizada = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    return SolicitacaoResponse.from_orm(solicitacao_atualizada)
>>>>>>> local


@router.get(
    "/solicitacoes/{solicitacao_id}/historico",
    response_model=List[AtualizacaoSolicitacaoResponse],
    summary="Obter histórico de mudanças"
)
def obter_historico_admin(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Admin vê histórico completo de mudanças de status da solicitação
    
    - Mostra quem fez a mudança (qual admin)
    - Quando foi feita
    - De qual status para qual
    - Descrição/motivo da mudança
    - Ordena por data (mais recentes primeiro)
    """
    admin_id = obter_admin_id(authorization)
    
    if not verificar_admin(db, admin_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores"
        )
    
    # Validar solicitação existe
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # Buscar histórico ordenado por data (mais recentes primeiro)
    historico = db.query(AtualizacaoSolicitacao).filter(
        AtualizacaoSolicitacao.solicitacao_id == solicitacao_id
    ).order_by(AtualizacaoSolicitacao.criado_em.desc()).all()
    
    return historico


# ============================================================================
# AVALIAÇÕES (Admin)
# ============================================================================

@router.get(
    "/avaliacoes",
    response_model=dict,
    summary="Listar avaliações (admin)"
)
def listar_avaliacoes_admin(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Admin lista todas as avaliações do sistema
    
    - Vê notas (1-5), comentários, se problema foi resolvido
    - Paginação: skip/limit
    - Ordena por data (mais recentes primeiro)
    """
    admin_id = obter_admin_id(authorization)
    
    if not verificar_admin(db, admin_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores"
        )
    
    # Contar total
    total = db.query(Avaliacao).count()
    
    # Buscar com paginação
    avaliacoes = db.query(Avaliacao).order_by(
        Avaliacao.criado_em.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "avaliacoes": [AvaliacaoResponse.from_orm(a) for a in avaliacoes]
    }


@router.get(
    "/avaliacoes/estatisticas",
    summary="Estatísticas de avaliações (admin)"
)
def obter_estatisticas_avaliacoes(
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Admin vê estatísticas agregadas das avaliações para dashboard
    
    - Total de avaliações registradas
    - Média de notas (1-5)
    - Distribuição de notas (quantas avaliações de 1 estrela, 2 estrelas, etc)
    - Percentual de problemas resolvidos vs não resolvidos
    - Total de comentários deixados
    """
    admin_id = obter_admin_id(authorization)
    
    if not verificar_admin(db, admin_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores"
        )
    
    # Contar total de avaliações
    total = db.query(func.count(Avaliacao.id)).scalar()
    
    # Se nenhuma avaliação, retorna zeros
    if total == 0:
        return {
            "total_avaliacoes": 0,
            "media_nota": 0.0,
            "distribuicao_notas": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            "percentual_problema_resolvido": 0.0,
            "percentual_problema_nao_resolvido": 0.0,
            "total_comentarios": 0
        }
    
    # Calcular média de notas
    media_nota = db.query(func.avg(Avaliacao.nota)).scalar() or 0.0
    
    # Distribuição de notas (contar quantas de cada estrela)
    distribuicao = {}
    for nota in range(1, 6):
        count = db.query(func.count(Avaliacao.id)).filter(Avaliacao.nota == nota).scalar()
        distribuicao[str(nota)] = count
    
    # Percentual de problemas resolvidos
    resolvido_count = db.query(func.count(Avaliacao.id)).filter(
        Avaliacao.problema_resolvido == True
    ).scalar()
    percentual_resolvido = (resolvido_count / total) * 100 if total > 0 else 0.0
    
    # Total de comentários não-nulos
    total_comentarios = db.query(func.count(Avaliacao.id)).filter(
        Avaliacao.comentario.isnot(None)
    ).scalar()
    
    return {
        "total_avaliacoes": total,
        "media_nota": round(media_nota, 2),
        "distribuicao_notas": distribuicao,
        "percentual_problema_resolvido": round(percentual_resolvido, 2),
        "percentual_problema_nao_resolvido": round(100 - percentual_resolvido, 2),
        "total_comentarios": total_comentarios
    }


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get(
    "/dashboard",
    summary="Dashboard geral (admin)"
)
def obter_dashboard(
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Retorna visão geral agregada para dashboard admin
    
    - Total de solicitações no sistema
    - Total de usuários cadastrados
    - Total de avaliações feitas
    - Média de notas das avaliações
    - Distribuição de solicitações por status (PENDENTE, EM_ANALISE, EM_ANDAMENTO, RESOLVIDO, CANCELADO)
    """
    admin_id = obter_admin_id(authorization)
    
    if not verificar_admin(db, admin_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores"
        )
    
    # Contar totais
    total_solicitacoes = db.query(func.count(Solicitacao.id)).scalar()
    total_usuarios = db.query(func.count(Usuario.id)).scalar()
    total_avaliacoes = db.query(func.count(Avaliacao.id)).scalar()
    
    # Contar por status
    status_counts = {}
    status_list = ["PENDENTE", "EM_ANALISE", "EM_ANDAMENTO", "RESOLVIDO", "CANCELADO"]
    for status in status_list:
        count = db.query(func.count(Solicitacao.id)).filter(
            Solicitacao.status == status
        ).scalar()
        status_counts[status] = count
    
    # Média de notas
    media_nota = db.query(func.avg(Avaliacao.nota)).scalar() or 0.0
    
    return {
        "total_solicitacoes": total_solicitacoes,
        "total_usuarios": total_usuarios,
        "total_avaliacoes": total_avaliacoes,
        "media_nota": round(media_nota, 2),
        "solicitacoes_por_status": status_counts
    }
