# ============================================================================
# problems.py - ROTAS DE PROBLEMAS URBANOS
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import Solicitacao, Usuario, Categoria
from app.schemas import SolicitacaoCreate, SolicitacaoResponse
from app.utils.security import extrair_user_id_do_token
from database.connection import get_db
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
    problemas = db.query(Solicitacao).filter_by(
        categoria_id=categoria_id,
        status_id=STATUS_SOLICITACAO["RESOLVIDO"]  # Excluir resolvidos
    ).all()
    
    # Calcula distância aproximada (em graus, ~111km por grau)
    for problema in problemas:
        diff_lat = abs(problema.latitude - latitude)
        diff_lon = abs(problema.longitude - longitude)
        
        # Distância aproximada em km
        distancia_km = (diff_lat + diff_lon) * 111
        
        if distancia_km * 1000 < raio_metros:  # Converter para metros
            return problema
    
    return None


# ============================================================================
# CRIAR PROBLEMA
# ============================================================================

@router.post("/api/problemas", response_model=SolicitacaoResponse, tags=["Problemas"])
def criar_problema(
    request: SolicitacaoCreate,
    db: Session = Depends(get_db),
    token: str = None
):
    """
    Cria novo problema urbano
    
    Requer autenticação (token JWT)
    Verifica duplicatas automaticamente
    """
    # Extrai user_id do token
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
        logger.info(f"⚠️  Duplicata encontrada para usuário {user_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe problema similar neste local. ID: {duplicata.id}. Considere apoiar ao invés de criar novo.",
            headers={"X-Problema-ID": str(duplicata.id)}
        )
    
    # Cria novo problema
    novo_problema = Solicitacao(
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
    
    db.add(novo_problema)
    db.commit()
    db.refresh(novo_problema)
    
    logger.info(f"✅ Problema criado: {novo_problema.protocolo} por usuário {user_id}")
    return novo_problema


# ============================================================================
# LISTAR PROBLEMAS
# ============================================================================

@router.get("/api/problemas", response_model=List[SolicitacaoResponse], tags=["Problemas"])
def listar_problemas(
    db: Session = Depends(get_db),
    categoria_id: Optional[int] = None,
    status_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    Lista todos os problemas
    
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
    
    problemas = query.order_by(
        Solicitacao.criado_em.desc()
    ).offset(skip).limit(limit).all()
    
    return problemas


# ============================================================================
# OBTER PROBLEMA POR ID
# ============================================================================

@router.get("/api/problemas/{problema_id}", response_model=SolicitacaoResponse, tags=["Problemas"])
def obter_problema(
    problema_id: int,
    db: Session = Depends(get_db)
):
    """Retorna detalhes de um problema específico"""
    problema = db.query(Solicitacao).filter_by(id=problema_id).first()
    
    if not problema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problema não encontrado"
        )
    
    return problema


# ============================================================================
# ATUALIZAR PROBLEMA
# ============================================================================

@router.put("/api/problemas/{problema_id}", response_model=SolicitacaoResponse, tags=["Problemas"])
def atualizar_problema(
    problema_id: int,
    request: SolicitacaoCreate,
    db: Session = Depends(get_db),
    token: str = None
):
    """
    Atualiza um problema (apenas o criador ou admin)
    
    Requer autenticação
    """
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
    
    problema = db.query(Solicitacao).filter_by(id=problema_id).first()
    
    if not problema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problema não encontrado"
        )
    
    # Verifica permissão (apenas criador)
    if problema.usuario_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar este problema"
        )
    
    # Atualiza campos
    problema.descricao = request.descricao
    problema.endereco = request.endereco
    
    db.commit()
    db.refresh(problema)
    
    logger.info(f"✅ Problema {problema_id} atualizado")
    return problema


# ============================================================================
# DELETAR PROBLEMA
# ============================================================================

@router.delete("/api/problemas/{problema_id}", tags=["Problemas"])
def deletar_problema(
    problema_id: int,
    db: Session = Depends(get_db),
    token: str = None
):
    """
    Deleta um problema (apenas o criador)
    
    Requer autenticação
    """
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
    
    problema = db.query(Solicitacao).filter_by(id=problema_id).first()
    
    if not problema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problema não encontrado"
        )
    
    if problema.usuario_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para deletar este problema"
        )
    
    db.delete(problema)
    db.commit()
    
    logger.info(f"✅ Problema {problema_id} deletado")
    return {"message": "Problema deletado com sucesso"}


# ============================================================================
# APOIAR PROBLEMA
# ============================================================================

@router.post("/api/problemas/{problema_id}/apoios", tags=["Problemas"])
def apoiar_problema(
    problema_id: int,
    db: Session = Depends(get_db),
    token: str = None
):
    """
    Cidadão apoia um problema (aumenta contador)
    
    Requer autenticação
    Um usuário só pode apoiar uma vez por problema
    """
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
    
    problema = db.query(Solicitacao).filter_by(id=problema_id).first()
    
    if not problema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problema não encontrado"
        )
    
    # Verifica se já apoia
    from app.models import Apoio
    
    existe_apoio = db.query(Apoio).filter_by(
        problema_id=problema_id,
        usuario_id=user_id
    ).first()
    
    if existe_apoio:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já apoia este problema"
        )
    
    # Cria apoio
    novo_apoio = Apoio(
        problema_id=problema_id,
        usuario_id=user_id
    )
    
    # Incrementa contador
    problema.contador_apoios += 1
    
    db.add(novo_apoio)
    db.commit()
    
    logger.info(f"✅ Apoio adicionado ao problema {problema_id} por usuário {user_id}")
    return {
        "message": "Apoio registrado com sucesso",
        "contador_apoios": problema.contador_apoios
    }
