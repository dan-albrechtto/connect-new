# -*- coding: utf-8 -*-
# ============================================================================
# apoios.py - ROTAS DE APOIOS A SOLICITAÇÕES
# ============================================================================
# Endpoints para cidadão apoiar/suportar solicitações de outros usuários
# Permite aumentar prioridade de problemas através de apoios
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import logging

from app.models import Apoio, Solicitacao, Usuario
from app.schemas import ApoioResponse
from app.utils.security import extrair_user_id_do_token
from database.connection import obter_conexao

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# POST: Cidadão APOIA uma solicitação
# ============================================================================
# Input: solicitacao_id (na URL)
# Valida: solicitação existe? Já apoiou? Não pode apoiar sua própria solicitação?
# ============================================================================

@router.post(
    "/api/solicitacoes/{solicitacao_id}/apoios",
    response_model=ApoioResponse,
    tags=["Apoios"],
    summary="Apoiar solicitação"
)
def apoiar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão apoia uma solicitação de outro cidadão
    
    - Aumenta visibilidade/prioridade do problema
    - Requer autenticação (token JWT)
    - Valida se solicitação existe
    - Impede apoiar duas vezes (um apoio por usuário/solicitação)
    - Registra automaticamente data/hora do apoio
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
    
    # ========== VALIDAÇÃO 3: Já apoiou antes? ==========
    apoio_existente = db.query(Apoio).filter(
        Apoio.solicitacao_id == solicitacao_id,
        Apoio.usuario_id == usuario_id
    ).first()
    
    if apoio_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já apoiou esta solicitação"
        )
    
    # ========== CRIAR APOIO ==========
    novo_apoio = Apoio(
        solicitacao_id=solicitacao_id,
        usuario_id=usuario_id,
        criado_em=datetime.now()
    )
    
    db.add(novo_apoio)
    db.commit()
    db.refresh(novo_apoio)
    
    logger.info(f"✅ Apoio criado: solicitacao_id={solicitacao_id}, usuario_id={usuario_id}")
    
    return novo_apoio


# ============================================================================
# GET: Listar apoiadores de uma solicitação
# ============================================================================

@router.get(
    "/api/solicitacoes/{solicitacao_id}/apoios",
    response_model=dict,
    tags=["Apoios"],
    summary="Listar apoios da solicitação"
)
def listar_apoios(
    solicitacao_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(obter_conexao)
):
    """
    Lista todos os apoios (apoiadores) de uma solicitação
    
    - Mostra quem apoiou
    - Quando apoiou
    - Total de apoios
    - Paginação: skip/limit
    """
    
    # Validar solicitação existe
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # Buscar apoios
    total = db.query(Apoio).filter_by(solicitacao_id=solicitacao_id).count()
    apoios = db.query(Apoio).filter_by(
        solicitacao_id=solicitacao_id
    ).order_by(Apoio.criado_em.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "apoios": [ApoioResponse.from_orm(a) for a in apoios]
    }


# ============================================================================
# DELETE: Cidadão REMOVE seu apoio
# ============================================================================

@router.delete(
    "/api/solicitacoes/{solicitacao_id}/apoios",
    tags=["Apoios"],
    summary="Remover apoio"
)
def remover_apoio(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão remove seu apoio de uma solicitação
    
    - Apenas quem apoiou pode remover
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
    
    # Buscar apoio
    apoio = db.query(Apoio).filter(
        Apoio.solicitacao_id == solicitacao_id,
        Apoio.usuario_id == usuario_id
    ).first()
    
    if not apoio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você não apoiou esta solicitação"
        )
    
    # Deletar
    db.delete(apoio)
    db.commit()
    
    logger.info(f"✅ Apoio removido: solicitacao_id={solicitacao_id}, usuario_id={usuario_id}")
    
    return {"mensagem": "Apoio removido com sucesso"}
