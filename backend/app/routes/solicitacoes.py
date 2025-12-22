# ============================================================================
# solicitacoes.py - ROTAS DE PROBLEMAS URBANOS (CORRIGIDO COM JWT HEADER) (era problems.py)
# ============================================================================
# Alterações:
# 1. Adicionado Header no import de FastAPI
# 2. Todas as funções agora extraem token do header Authorization corretamente
# 3. Token agora é enviado automaticamente pelo Swagger quando você clica Authorize
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.models import Solicitacao, Usuario, Categoria, Apoio
from app.schemas import SolicitacaoCreate, SolicitacaoResponse
from app.utils.security import extrair_user_id_do_token
from database.connection import obter_conexao
from config import STATUS_SOLICITACAO
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# HELPER: Gerar protocolo único
# ============================================================================

def gerar_protocolo(db: Session) -> str:
    """Gera protocolo único no formato YYYY-00000"""
    ano = datetime.now().year
    # Conta quantos problemas foram criados este ano
    count = db.query(Solicitacao).filter(
        Solicitacao.criado_em >= datetime(ano, 1, 1)
    ).count()
    numero = str(count + 1).zfill(5)
    return f"{ano}-{numero}"

# ============================================================================
# HELPER: Verificar duplicata (mesmo local + categoria)
# ============================================================================

def verificar_duplicata(
    db: Session,
    latitude: float,
    longitude: float,
    categoria_id: int,
    raio_metros: float = 50
) -> Optional[Solicitacao]:
    """
    Verifica se já existe problema próximo (dentro do raio)
    com a mesma categoria
    Usa fórmula simples de distância (não é Haversine, é aproximada)
    Para produção, use Haversine ou PostGIS do PostgreSQL
    """
    # Busca todos os problemas da mesma categoria
    solicitacoes = db.query(Solicitacao).filter_by(
        categoria_id=categoria_id,
        status_id=STATUS_SOLICITACAO["RESOLVIDO"]  # Excluir resolvidos
    ).all()

    # Calcula distância aproximada (em graus, ~111km por grau)
    for solicitacao in solicitacoes:
        diff_lat = abs(solicitacao.latitude - latitude)
        diff_lon = abs(solicitacao.longitude - longitude)
        # Distância aproximada em km
        distancia_km = (diff_lat + diff_lon) * 111
        if distancia_km * 1000 < raio_metros:  # Converter para metros
            return solicitacao

    return None

# ============================================================================
# CRIAR SOLICITAÇÃO
# ============================================================================

@router.post("/api/solicitacoes", response_model=SolicitacaoResponse, tags=["Solicitações"])
def criar_solicitacao(
    request: SolicitacaoCreate,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cria novo problema urbano
    Requer autenticação (token JWT)
    Verifica duplicatas automaticamente
    """
    # Extrai token do header Authorization: Bearer <token>
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " (7 caracteres)
    
    # Se não tem token, retorna erro
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )

    # Extrai user_id do token
    user_id = extrair_user_id_do_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    # Verifica se categoria existe
    categoria = db.query(Categoria).filter_by(id=request.categoria_id).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    # Verifica duplicata
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
            detail=f"Já existe solicitação similar neste local. ID: {duplicata.id}. Considere apoiar ao invés de criar novo.",
            headers={"X-Solicitacao-ID": str(duplicata.id)}
        )

    # Cria novo problema
    nova_solicitacao = Solicitacao(
        protocolo=gerar_protocolo(db),
        descricao=request.descricao,
        latitude=request.latitude,
        longitude=request.longitude,
        endereco=request.endereco,
        categoria_id=request.categoria_id,
        usuario_id=user_id,
        status_id=STATUS_SOLICITACAO["PENDENTE"],  # ← É um INT (1)
        contador_apoios=0
    )

    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)
    logger.info(f"✅ Solicitação criada: {nova_solicitacao.protocolo} por usuário {user_id}")
    return nova_solicitacao

# ============================================================================
# LISTAR SOLICITAÇÕES
# ============================================================================

@router.get("/api/solicitacoes", response_model=List[SolicitacaoResponse], tags=["Solicitações"])
def listar_solicitacoes(
    db: Session = Depends(obter_conexao),
    categoria_id: Optional[int] = None,
    status_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    Lista todos as solicitações
    Parâmetros opcionais:
    - categoria_id: filtrar por categoria
    - status_id: filtrar por status
    - skip: pular N registros (paginação)
    - limit: retornar N registros
    """
    query = db.query(Solicitacao)
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    if status_id:
        query = query.filter_by(status_id=status_id)
    solicitacoes = query.order_by(
        Solicitacao.criado_em.desc()
    ).offset(skip).limit(limit).all()
    return solicitacoes

# ============================================================================
# OBTER SOLICITAÇÃO POR ID
# ============================================================================

@router.get("/api/solicitacoes/{solicitacao_id}", response_model=SolicitacaoResponse, tags=["Solicitações"])
def obter_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao)
):
    """Retorna detalhes de uma solicitação específica"""
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    return solicitacao

# ============================================================================
# ATUALIZAR SOLICITAÇÃO
# ============================================================================

@router.put("/api/solicitacoes/{solicitacao_id}", response_model=SolicitacaoResponse, tags=["Solicitações"])
def atualizar_solicitacao(
    solicitacao_id: int,
    request: SolicitacaoCreate,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Atualiza uma solicitação (apenas o criador ou admin)
    Requer autenticação
    """
    # Extrai token do header Authorization: Bearer <token>
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " (7 caracteres)
    
    # Se não tem token, retorna erro
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

    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    # Verifica permissão (apenas criador)
    if solicitacao.usuario_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar esta solicitação"
        )

    # Atualiza campos
    solicitacao.descricao = request.descricao
    solicitacao.endereco = request.endereco
    db.commit()
    db.refresh(solicitacao)
    logger.info(f"✅ Solicitação {solicitacao_id} atualizada")
    return solicitacao

# ============================================================================
# DELETAR SOLICITAÇÃO
# ============================================================================

@router.delete("/api/solicitacoes/{solicitacao_id}", tags=["Solicitações"])
def deletar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Deleta uma solicitação (apenas o criador)
    Requer autenticação
    """
    # Extrai token do header Authorization: Bearer <token>
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " (7 caracteres)
    
    # Se não tem token, retorna erro
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

    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    if solicitacao.usuario_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para deletar esta solicitação"
        )

    db.delete(solicitacao)
    db.commit()
    logger.info(f"✅ Solicitação {solicitacao_id} deletada")
    return {"message": "Solicitação deletada com sucesso"}

# ============================================================================
# APOIAR SOLICITAÇÃO
# ============================================================================

@router.post("/api/solicitacao/{solicitacao_id}/apoios", tags=["Solicitações"])
def apoiar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão apoia uma solicitação (aumenta contador)
    Requer autenticação
    Um usuário só pode apoiar uma vez por solicitação
    """
    # Extrai token do header Authorization: Bearer <token>
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " (7 caracteres)
    
    # Se não tem token, retorna erro
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

    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )

    # Verifica se já apoia
    existe_apoio = db.query(Apoio).filter_by(
        solicitacao_id=solicitacao_id,
        usuario_id=user_id
    ).first()

    if existe_apoio:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já apoia esta solicitação"
        )

    # Cria apoio
    novo_apoio = Apoio(
        solicitacao_id=solicitacao_id,
        usuario_id=user_id
    )

    # Incrementa contador
    solicitacao.contador_apoios += 1
    db.add(novo_apoio)
    db.commit()
    logger.info(f"✅ Apoio adicionado à solicitação {solicitacao_id} por usuário {user_id}")
    return {
        "message": "Apoio registrado com sucesso",
        "contador_apoios": solicitacao.contador_apoios
    }

# ============================================================================
# FIM DO ARQUIVO
# ============================================================================