# ============================================================================
# solicitacoes.py - ROTAS DE SOLICITAÇÕES (PROBLEMAS URBANOS)
# ============================================================================
# Responsável por todas as operações de CRUD de solicitações
# Cidadão: cria, edita, deleta, apoia
# Admin: atualiza status e vê histórico
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import logging

from app.models import (
    Solicitacao, 
    Usuario, 
    Categoria, 
    Apoio,
    AtualizacaoSolicitacao,
    StatusSolicitacaoEnum
)
from app.schemas import (
    SolicitacaoCreate, 
    SolicitacaoUpdate,
    SolicitacaoResponse,
    AtualizacaoSolicitacaoResponse
)
from app.utils.security import extrair_user_id_do_token
from database.connection import obter_conexao


logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# HELPER: Gerar protocolo único para solicitação
# ============================================================================
# Formato: YYYY-00001 (ano + número sequencial com 5 dígitos)
# ============================================================================

def gerar_protocolo(db: Session) -> str:
    """
    Gera protocolo único no formato YYYY-00000
    Conta quantos problemas foram criados este ano
    Retorna string tipo: 2025-00042
    """
    ano = datetime.now().year
    count = db.query(Solicitacao).filter(
        Solicitacao.criado_em >= datetime(ano, 1, 1)
    ).count()
    numero = str(count + 1).zfill(5)
    return f"{ano}-{numero}"


# ============================================================================
# HELPER: Verificar duplicata (mesmo local + categoria)
# ============================================================================
# Usa fórmula simples de distância em km
# Para produção, usar Haversine ou PostGIS
# ============================================================================

def verificar_duplicata(
    db: Session,
    latitude: float,
    longitude: float,
    categoria_id: int,
    raio_metros: float = 50
) -> Optional[Solicitacao]:
    """
    Verifica se já existe problema próximo com a mesma categoria
    dentro do raio especificado (default 50 metros)
    Retorna a solicitação duplicada ou None
    """
    # Buscar todos os problemas da mesma categoria (exceto resolvidos)
    solicitacoes = db.query(Solicitacao).filter(
        Solicitacao.categoria_id == categoria_id,
        Solicitacao.status != StatusSolicitacaoEnum.RESOLVIDO
    ).all()

    # Iterar e calcular distância aproximada
    for solicitacao in solicitacoes:
        diff_lat = abs(solicitacao.latitude - latitude)
        diff_lon = abs(solicitacao.longitude - longitude)
        distancia_km = (diff_lat + diff_lon) * 111  # ~111km por grau
        if distancia_km * 1000 < raio_metros:  # Converter para metros
            return solicitacao

    return None


# ============================================================================
# HELPER: Verificar se usuário é administrador
# ============================================================================
# Consulta banco de dados para validar tipo_usuario
# ============================================================================

def verificar_admin(db: Session, user_id: int) -> bool:
    """
    Verifica se o usuário logado é administrador
    Retorna True se é admin, False caso contrário
    """
    usuario = db.query(Usuario).filter_by(id=user_id).first()
    if not usuario:
        return False
    return usuario.tipo_usuario == "ADMINISTRADOR"


# ============================================================================
# POST: Cidadão CRIA nova solicitação
# ============================================================================
# Input: SolicitacaoCreate (categoria, descricao, lat/lon, endereco)
# Output: SolicitacaoResponse (com id, protocolo, status PENDENTE)
# Verifica duplicatas automaticamente
# ============================================================================

@router.post("/api/solicitacoes", response_model=SolicitacaoResponse, tags=["Solicitações"])
def criar_solicitacao(
    request: SolicitacaoCreate,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cria novo problema urbano
    - Requer autenticação (token JWT no header)
    - Verifica duplicatas automaticamente (mesmo local + categoria)
    - Começa sempre com status PENDENTE
    """
    
    # Extrair token do header Authorization: Bearer <token>
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )

    # Extrair user_id do token JWT
    user_id = extrair_user_id_do_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    # Verificar se categoria existe
    categoria = db.query(Categoria).filter_by(id=request.categoria_id).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    # Verificar duplicata no local
    duplicata = verificar_duplicata(
        db,
        request.latitude,
        request.longitude,
        request.categoria_id
    )

    if duplicata:
        logger.info(f"⚠️ Duplicata encontrada para usuário {user_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe solicitação similar. ID: {duplicata.id}. Considere apoiar ao invés de criar novo.",
            headers={"X-Solicitacao-ID": str(duplicata.id)}
        )

    # Criar nova solicitação
    nova_solicitacao = Solicitacao(
        protocolo=gerar_protocolo(db),
        descricao=request.descricao,
        latitude=request.latitude,
        longitude=request.longitude,
        endereco=request.endereco,
        categoria_id=request.categoria_id,
        usuario_id=user_id,
        status=StatusSolicitacaoEnum.PENDENTE,
        contador_apoios=0,
        prazo_resolucao=request.prazo_resolucao
    )

    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)
    logger.info(f"✅ Solicitação criada: {nova_solicitacao.protocolo}")
    return nova_solicitacao


# ============================================================================
# GET: Listar TODAS as solicitações com filtros opcionais
# ============================================================================
# Filtros: categoria_id, status, paginação (skip/limit)
# Ordena por criado_em (mais recentes primeiro)
# ============================================================================

@router.get("/api/solicitacoes", response_model=List[SolicitacaoResponse], tags=["Solicitações"])
def listar_solicitacoes(
    db: Session = Depends(obter_conexao),
    categoria_id: Optional[int] = None,
    status_filtro: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    Lista todas as solicitações com filtros opcionais
    - categoria_id: filtrar por categoria
    - status_filtro: PENDENTE, EM_ANALISE, EM_ANDAMENTO, RESOLVIDO, CANCELADO
    - skip/limit: paginação
    """
    
    # Começar query base
    query = db.query(Solicitacao)
    
    # Aplicar filtro de categoria se fornecido
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    
    # Aplicar filtro de status se fornecido
    if status_filtro:
        try:
            status_enum = StatusSolicitacaoEnum[status_filtro]
            query = query.filter_by(status=status_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status inválido"
            )
    
    # Executar query com ordenação e paginação
    solicitacoes = query.order_by(
        Solicitacao.criado_em.desc()
    ).offset(skip).limit(limit).all()
    
    return solicitacoes


# ============================================================================
# GET: Obter UMA solicitação por ID
# ============================================================================
# Retorna detalhes completos incluindo status atual
# ============================================================================

@router.get("/api/solicitacoes/{solicitacao_id}", response_model=SolicitacaoResponse, tags=["Solicitações"])
def obter_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao)
):
    """
    Retorna detalhes completos de uma solicitação específica
    Inclui: id, protocolo, descricao, localização, status, contador_apoios, datas
    """
    
    # Buscar solicitação no banco
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    return solicitacao


# ============================================================================
# PUT: Cidadão EDITA sua solicitação (descrição/endereço)
# ============================================================================
# Input: SolicitacaoCreate (reutiliza schema com campos editáveis)
# Apenas o criador pode editar
# Não pode mudar: categoria, localização, status
# ============================================================================

@router.put("/api/solicitacoes/{solicitacao_id}", response_model=SolicitacaoResponse, tags=["Solicitações"])
def atualizar_solicitacao_cidadao(
    solicitacao_id: int,
    request: SolicitacaoCreate,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão EDITA sua solicitação APENAS enquanto em status PENDENTE
    - Descrição e endereço podem ser corrigidos antes do envio
    - Após envio (EM_ANALISE+), edição é bloqueada
    - Use comentários para complementar informações depois
    """
    
    # Extrair token do header Authorization: Bearer <token>
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )

    # Extrair user_id do token JWT
    user_id = extrair_user_id_do_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    # Buscar solicitação no banco
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    # Verificar se é o criador (ANTES de checar status)
    if solicitacao.usuario_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar esta solicitação"
        )

    # Verificar se ainda está em PENDENTE (DEPOIS de confirmar criador)
    if solicitacao.status != StatusSolicitacaoEnum.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solicitação não pode ser editada. Status atual: {solicitacao.status.value}. Use comentários para adicionar informações."
        )

    # Atualizar apenas campos permitidos
    solicitacao.descricao = request.descricao
    solicitacao.endereco = request.endereco
    solicitacao.atualizado_em = datetime.now()
    db.commit()
    db.refresh(solicitacao)
    logger.info(f"✅ Solicitação {solicitacao_id} atualizada (ainda em PENDENTE)")
    return solicitacao


# ============================================================================
# PUT: Admin ATUALIZA STATUS da solicitação
# ============================================================================
# Input: SolicitacaoUpdate (APENAS status e descricao)
# Apenas admin pode fazer isso
# Registra automaticamente no histórico (AtualizacaoSolicitacao)
# ============================================================================

@router.put("/api/solicitacoes/{solicitacao_id}/status", response_model=SolicitacaoResponse, tags=["Solicitações"])
def atualizar_status_solicitacao(
    solicitacao_id: int,
    request: SolicitacaoUpdate,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    ADMIN: Atualiza o STATUS de uma solicitação
    - Input: APENAS status e descricao (via SolicitacaoUpdate)
    - Requer autenticação de admin
    - Registra automaticamente mudança no histórico
    """
    
    # Extrair token do header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )

    # Extrair user_id do token
    admin_id = extrair_user_id_do_token(token)
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    # Verificar se é admin
    if not verificar_admin(db, admin_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores"
        )

    # Buscar solicitação
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    # Extrair valores de status (podem ser enum ou string)
    status_anterior = solicitacao.status.value if hasattr(solicitacao.status, 'value') else str(solicitacao.status)
    status_novo = request.status.value if hasattr(request.status, 'value') else str(request.status)
    
    # Registrar mudança no histórico
    atualizacao = AtualizacaoSolicitacao(
        solicitacao_id=solicitacao_id,
        administrador_id=admin_id,
        status_anterior=status_anterior,
        status_novo=status_novo,
        descricao=request.descricao
    )
    db.add(atualizacao)

    # Atualizar status e data de atualização
    solicitacao.status = request.status
    solicitacao.atualizado_em = datetime.now()
    
    db.commit()
    db.refresh(solicitacao)
    
    logger.info(f"✅ Status atualizado para {status_novo}")
    return solicitacao


# ============================================================================
# GET: Obter HISTÓRICO de mudanças de status
# ============================================================================
# Retorna todas as atualizações feitas por admins
# Ordena por data mais recente primeiro
# ============================================================================

@router.get("/api/solicitacoes/{solicitacao_id}/historico", response_model=List[AtualizacaoSolicitacaoResponse], tags=["Solicitações"])
def obter_historico(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao)
):
    """
    Obtém histórico completo de mudanças de status
    - Mostra quem (admin), quando, do que para quê
    - Ordenado por data mais recente primeiro
    """
    
    # Verificar que solicitação existe
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # Buscar histórico e ordenar
    historico = db.query(AtualizacaoSolicitacao)\
        .filter(AtualizacaoSolicitacao.solicitacao_id == solicitacao_id)\
        .order_by(AtualizacaoSolicitacao.criado_em.desc())\
        .all()
    
    return historico


# ============================================================================
# DELETE: Cidadão DELETA sua solicitação
# ============================================================================
# Apenas o criador pode deletar
# Requer autenticação
# ============================================================================

@router.delete("/api/solicitacoes/{solicitacao_id}", tags=["Solicitações"])
def deletar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Deleta uma solicitação permanentemente
    - Apenas o criador pode deletar
    - Requer autenticação
    - Retorna mensagem de sucesso
    """
    
    # Extrair token do header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )

    # Extrair user_id do token
    user_id = extrair_user_id_do_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    # Buscar solicitação
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    # Verificar se é o criador
    if solicitacao.usuario_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão"
        )

    # Deletar solicitação
    db.delete(solicitacao)
    db.commit()
    return {"message": "Solicitação deletada"}


# ============================================================================
# POST: Cidadão APOIA uma solicitação existente
# ============================================================================
# Aumenta contador_apoios em 1
# Um usuário só pode apoiar uma vez por solicitação
# Requer autenticação
# ============================================================================

@router.post("/api/solicitacoes/{solicitacao_id}/apoios", tags=["Solicitações"])
def apoiar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão apoia uma solicitação existente
    - Aumenta contador_apoios em 1
    - Um usuário só pode apoiar uma vez
    - Requer autenticação
    """
    
    # Extrair token do header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )

    # Extrair user_id do token
    user_id = extrair_user_id_do_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    # Buscar solicitação
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    # Verificar se já apoiou
    existe_apoio = db.query(Apoio).filter_by(
        solicitacao_id=solicitacao_id,
        usuario_id=user_id
    ).first()

    if existe_apoio:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já apoia"
        )

    # Criar novo apoio
    novo_apoio = Apoio(
        solicitacao_id=solicitacao_id,
        usuario_id=user_id
    )

    # Incrementar contador
    solicitacao.contador_apoios += 1
    db.add(novo_apoio)
    db.commit()
    
    return {
        "message": "Apoio registrado",
        "contador_apoios": solicitacao.contador_apoios
    }


# ============================================================================
# FIM DO ARQUIVO
# ============================================================================
