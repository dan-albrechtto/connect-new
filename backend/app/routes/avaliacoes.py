# -*- coding: utf-8 -*-
# ============================================================================
# avaliacoes.py - ROTAS DE AVALIAÇÕES DE SOLICITAÇÕES
# ============================================================================
# Endpoints para cidadão avaliar se problema foi realmente resolvido
# Avaliação inclui: nota (1-5), confirmação de resolução, comentário opcional
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import logging

from app.models import Avaliacao, Solicitacao, Usuario
from app.schemas import AvaliacaoCreate, AvaliacaoResponse
from app.utils.security import extrair_user_id_do_token
from database.connection import obter_conexao

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# POST: Cidadão CRIA avaliação de solicitação resolvida
# ============================================================================
# Input: nota (1-5), problema_resolvido (sim/não), comentário (opcional)
# Valida: solicitação existe? Status é RESOLVIDA ou CANCELADA? Já avaliou?
# ============================================================================

@router.post(
    "/api/solicitacoes/{solicitacao_id}/avaliacoes",
    response_model=AvaliacaoResponse,
    tags=["Avaliações"],
    summary="Criar avaliação de solicitação"
)
def criar_avaliacao(
    solicitacao_id: int,
    request: AvaliacaoCreate,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão cria avaliação após solicitação ser RESOLVIDA ou CANCELADA
    
    - Requer autenticação (token JWT)
    - Valida se solicitação existe e está no status correto
    - Impede avaliar duas vezes (uma avaliação por usuário/solicitação)
    - Nota deve ser 1-5 (validação no Schema)
    - Comentário é opcional, máximo 500 caracteres
    """
    
    # ========== VALIDAÇÃO 1: Extrair e validar token ==========
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    # Extrair user_id do token JWT
    usuario_id = extrair_user_id_do_token(token)
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # ========== VALIDAÇÃO 2: Solicitação existe? ==========
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # ========== VALIDAÇÃO 3: Status está correto? ==========
    # Só permite avaliar se está RESOLVIDA ou CANCELADA
    status_permitidos = ["RESOLVIDO", "CANCELADO"]
    if solicitacao.status.name not in status_permitidos:  # .name pq é Enum
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Só é permitido avaliar solicitações RESOLVIDA/CANCELADA. Status atual: {solicitacao.status.name}"
        )
    
    # ========== VALIDAÇÃO 4: É o criador da solicitação? ==========
    if solicitacao.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o criador da solicitação pode avaliá-la"
        )
    
    # ========== VALIDAÇÃO 5: Já avaliou antes? ==========
    avaliacao_existente = db.query(Avaliacao).filter(
        Avaliacao.solicitacao_id == solicitacao_id,
        Avaliacao.usuario_id == usuario_id
    ).first()
    
    if avaliacao_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já avaliou esta solicitação. Delete e reenvie se desejar alterar."
        )
    
    # ========== CRIAR AVALIAÇÃO ==========
    nova_avaliacao = Avaliacao(
        solicitacao_id=solicitacao_id,
        usuario_id=usuario_id,
        nota=request.nota,
        problema_resolvido=request.problema_resolvido,
        comentario=request.comentario or None,
        criado_em=datetime.now()
    )
    
    db.add(nova_avaliacao)
    db.commit()
    db.refresh(nova_avaliacao)
    
    logger.info(f"✅ Avaliação criada: solicitacao_id={solicitacao_id}, nota={request.nota}")
    
    return nova_avaliacao


# ============================================================================
# GET: Obter AVALIAÇÃO de uma solicitação (cidadão vê sua própria)
# ============================================================================

@router.get(
    "/api/solicitacoes/{solicitacao_id}/avaliacoes",
    response_model=Optional[AvaliacaoResponse],
    tags=["Avaliações"],
    summary="Obter sua avaliação"
)
def obter_minha_avaliacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Retorna a avaliação do cidadão para uma solicitação específica
    
    - Requer autenticação
    - Retorna None se não avaliou ainda
    """
    
    # Extrair token
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    usuario_id = extrair_user_id_do_token(token)
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # Buscar avaliação do usuário
    avaliacao = db.query(Avaliacao).filter(
        Avaliacao.solicitacao_id == solicitacao_id,
        Avaliacao.usuario_id == usuario_id
    ).first()
    
    return avaliacao


# ============================================================================
# DELETE: Cidadão DELETA sua avaliação
# ============================================================================

@router.delete(
    "/api/solicitacoes/{solicitacao_id}/avaliacoes",
    tags=["Avaliações"],
    summary="Deletar sua avaliação"
)
def deletar_minha_avaliacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão deleta sua avaliação
    
    - Apenas quem criou pode deletar
    - Requer autenticação
    """
    
    # Extrair token
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    usuario_id = extrair_user_id_do_token(token)
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # Buscar avaliação
    avaliacao = db.query(Avaliacao).filter(
        Avaliacao.solicitacao_id == solicitacao_id,
        Avaliacao.usuario_id == usuario_id
    ).first()
    
    if not avaliacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você não possui avaliação para esta solicitação"
        )
    
    # Deletar
    db.delete(avaliacao)
    db.commit()
    
    logger.info(f"✅ Avaliação deletada: solicitacao_id={solicitacao_id}")
    
    return {"mensagem": "Avaliação deletada com sucesso"}


# ============================================================================
# GET: Listar TODAS as avaliações (admin)
# ============================================================================

# @router.get(
#     "/api/admin/avaliacoes",
#     response_model=dict,
#     tags=["Avaliações - Admin"],
#     summary="Listar avaliações (admin)"
# )
# def listar_avaliacoes_admin(
#     skip: int = 0,
#     limit: int = 50,
#     db: Session = Depends(obter_conexao),
#     authorization: str = Header(None)
# ):
#     """
#     Admin lista todas as avaliações do sistema
    
#     - Requer autenticação de admin
#     - Paginação: skip/limit
#     - Ordena por data (mais recentes primeiro)
#     """
    
#     # Extrair token
#     token = None
#     if authorization and authorization.startswith("Bearer "):
#         token = authorization[7:]
    
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token não fornecido"
#         )
    
#     admin_id = extrair_user_id_do_token(token)
#     if not admin_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token inválido"
#         )
    
#     # Verificar se é admin
#     usuario = db.query(Usuario).filter_by(id=admin_id).first()
#     if not usuario or usuario.tipo_usuario.name != "ADMINISTRADOR":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Apenas administradores"
#         )
    
#     # Buscar avaliações
#     avaliacoes = db.query(Avaliacao).order_by(
#         Avaliacao.criado_em.desc()
#     ).offset(skip).limit(limit).all()
    
#     total = db.query(Avaliacao).count()
    
#     return {
#         "total": total,
#         "skip": skip,
#         "limit": limit,
#         "avaliacoes": [AvaliacaoResponse.from_orm(a) for a in avaliacoes]
#     }


# ============================================================================
# GET: Obter ESTATÍSTICAS de avaliações (admin)
# ============================================================================

# @router.get(
#     "/api/admin/avaliacoes/estatisticas",
#     tags=["Avaliações - Admin"],
#     summary="Estatísticas de avaliações"
# )
# def obter_estatisticas_avaliacoes(
#     db: Session = Depends(obter_conexao),
#     authorization: str = Header(None)
# ):
#     """
#     Retorna estatísticas agregadas para o dashboard admin
    
#     - Total de avaliações
#     - Média de notas
#     - Distribuição de notas (1-5)
#     - Percentual de problemas resolvidos vs não resolvidos
#     - Total de comentários
#     """
    
#     # Extrair token
#     token = None
#     if authorization and authorization.startswith("Bearer "):
#         token = authorization[7:]
    
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token não fornecido"
#         )
    
#     admin_id = extrair_user_id_do_token(token)
#     if not admin_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token inválido"
#         )
    
#     # Verificar se é admin
#     usuario = db.query(Usuario).filter_by(id=admin_id).first()
#     if not usuario or usuario.tipo_usuario.name != "ADMINISTRADOR":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Apenas administradores"
#         )
    
#     # Calcular estatísticas
#     from sqlalchemy import func
    
#     total = db.query(func.count(Avaliacao.id)).scalar()
    
#     if total == 0:
#         return {
#             "total_avaliacoes": 0,
#             "media_nota": 0.0,
#             "distribuicao_notas": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
#             "percentual_problema_resolvido": 0.0,
#             "percentual_problema_nao_resolvido": 0.0,
#             "total_comentarios": 0
#         }
    
#     # Média de notas
#     media_nota = db.query(func.avg(Avaliacao.nota)).scalar() or 0.0
    
#     # Distribuição de notas
#     distribuicao = {}
#     for nota in range(1, 6):
#         count = db.query(func.count(Avaliacao.id)).filter(Avaliacao.nota == nota).scalar()
#         distribuicao[str(nota)] = count
    
#     # Percentual resolvido
#     resolvido_count = db.query(func.count(Avaliacao.id)).filter(
#         Avaliacao.problema_resolvido == True
#     ).scalar()
#     percentual_resolvido = (resolvido_count / total) * 100
    
#     # Total de comentários
#     total_comentarios = db.query(func.count(Avaliacao.id)).filter(
#         Avaliacao.comentario.isnot(None)
#     ).scalar()
    
#     return {
#         "total_avaliacoes": total,
#         "media_nota": round(media_nota, 2),
#         "distribuicao_notas": distribuicao,
#         "percentual_problema_resolvido": round(percentual_resolvido, 2),
#         "percentual_problema_nao_resolvido": round(100 - percentual_resolvido, 2),
#         "total_comentarios": total_comentarios
#     }
