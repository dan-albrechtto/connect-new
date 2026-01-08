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
    TipoUsuarioEnum,
    StatusSolicitacaoEnum
)
from app.schemas import (
    SolicitacaoCreate, 
    SolicitacaoUpdate,
    SolicitacaoResponse,
    AtualizacaoSolicitacaoResponse,
    ComentarioCreate,
    ComentarioResponse
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
    Usa MAX do número anterior, não COUNT
    Assim, mesmo deletando, a sequência continua incrementando
    Retorna string tipo: 2025-00042
    """
    from sqlalchemy import func, Integer
    
    ano = datetime.now().year
    
    # Buscar o maior número de protocolo do ano atual
    max_resultado = db.query(
        func.max(
            func.cast(
                func.substring(Solicitacao.protocolo, 6, 5),  # Extrai os 5 últimos caracteres
                Integer
            )
        )
    ).filter(
        Solicitacao.protocolo.like(f"{ano}-%")  # Apenas deste ano
    ).scalar()
    
    # Se não houver nenhum, começa em 0, senão pega o máximo
    numero_maximo = max_resultado if max_resultado else 0
    proximo_numero = str(numero_maximo + 1).zfill(5)
    
    return f"{ano}-{proximo_numero}"


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
    dentro do raio especificado (default 50 metros).
    
    Usa fórmula de Haversine para cálculo de distância geográfica.
    Mais precisa que aproximação simples.
    
    Args:
        db: Sessão do banco
        latitude: Latitude do novo problema (WGS84)
        longitude: Longitude do novo problema (WGS84)
        categoria_id: ID da categoria do problema
        raio_metros: Raio de busca em metros (default 50m)
    
    Returns:
        Solicitacao se encontrar duplicata, None caso contrário
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Buscar todos os problemas da mesma categoria (exceto resolvidos)
    solicitacoes = db.query(Solicitacao).filter(
        Solicitacao.categoria_id == categoria_id,
        Solicitacao.status != "RESOLVIDO"
    ).all()
    
    # Constante: raio da Terra em metros
    RAIO_TERRA_METROS = 6371000
    
    # Iterar e calcular distância usando Haversine
    for solicitacao in solicitacoes:
        # Converter para radianos
        lat1 = radians(solicitacao.latitude)
        lon1 = radians(solicitacao.longitude)
        lat2 = radians(latitude)
        lon2 = radians(longitude)
        
        # Diferenças
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Fórmula de Haversine
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distancia_metros = RAIO_TERRA_METROS * c
        
        # Se dentro do raio, é duplicata
        if distancia_metros < raio_metros:
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
    return usuario.tipo_usuario == TipoUsuarioEnum.ADMINISTRADOR


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
            detail="Já existe uma solicitação similar neste local. Considere apoiar a solicitação existente ao invés de criar uma nova."
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
        status="PENDENTE",
        contador_apoios=0,
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
        # Validar que o status é válido
        status_validos = ["PENDENTE", "EM_ANALISE", "EM_ANDAMENTO", "RESOLVIDO", "CANCELADO"]
        if status_filtro not in status_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status inválido"
            )
        query = query.filter_by(status=status_filtro)
    
    # Executar query com ordenação e paginação
    solicitacoes = query.order_by(
        Solicitacao.criado_em.desc()
    ).offset(skip).limit(limit).all()
    
    return solicitacoes

@router.get(
    "/api/solicitacoes/minhas",
    response_model=dict,
    tags=["Solicitações"],
    summary="Listar minhas solicitações"
)
def listar_minhas_solicitacoes(
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão lista TODAS as suas solicitações (criadas por ele)
    
    - Requer autenticação (token JWT)
    - Retorna solicitações em qualquer status (ativa, resolvida, cancelada)
    - Ordena por data (mais recentes primeiro)
    - Inclui histórico e avaliações
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
    
    # Buscar todas as solicitações do usuário
    minhas_solicitacoes = db.query(Solicitacao).filter(
        Solicitacao.usuario_id == usuario_id
    ).order_by(Solicitacao.criado_em.desc()).all()
    
    return {
        "total": len(minhas_solicitacoes),
        "solicitacoes": [SolicitacaoResponse.from_orm(s) for s in minhas_solicitacoes]
    }



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


@router.get(
    "/api/solicitacoes/{solicitacao_id}/historico",
    response_model=List[AtualizacaoSolicitacaoResponse],
    tags=["Solicitações"],
    summary="Ver histórico de mudanças"
)
def obter_historico_cidadao(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão vê histórico de mudanças de sua própria solicitação
    
    - Mostra quando status foi alterado
    - Mostra comentário/descrição de cada mudança
    - Ordenado por data (mais recentes primeiro)
    - Apenas criador da solicitação pode ver
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
    
    # Validar solicitação existe
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # Validar se é criador
    if solicitacao.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas criador da solicitação pode ver histórico"
        )
    
    # Buscar histórico
    historico = db.query(AtualizacaoSolicitacao).filter(
        AtualizacaoSolicitacao.solicitacao_id == solicitacao_id
    ).order_by(AtualizacaoSolicitacao.criado_em.desc()).all()
    
    return historico



# ============================================================================
# PUT: Admin ATUALIZA STATUS da solicitação
# ============================================================================
# Input: SolicitacaoUpdate (APENAS status e descricao)
# Apenas admin pode fazer isso
# Registra automaticamente no histórico (AtualizacaoSolicitacao)
# ============================================================================

# @router.put("/api/solicitacoes/{solicitacao_id}/status", response_model=SolicitacaoResponse, tags=["Solicitações"])
# def atualizar_status_solicitacao(
#     solicitacao_id: int,
#     request: SolicitacaoUpdate,
#     db: Session = Depends(obter_conexao),
#     authorization: str = Header(None)
# ):
#     """
#     ADMIN: Atualiza o STATUS de uma solicitação
#     - Input: APENAS status e descricao (via SolicitacaoUpdate)
#     - Requer autenticação de admin
#     - Registra automaticamente mudança no histórico
#     """
    
#     # Extrair token do header
#     token = None
#     if authorization and authorization.startswith("Bearer "):
#         token = authorization[7:]
    
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token não fornecido"
#         )

#     # Extrair user_id do token
#     admin_id = extrair_user_id_do_token(token)
#     if not admin_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token inválido"
#         )

#     # Verificar se é admin
#     if not verificar_admin(db, admin_id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Apenas administradores"
#         )

#     # Buscar solicitação
#     solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
#     if not solicitacao:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Solicitação não encontrada"
#         )

#     # Status anterior (já vem como string do banco - ENUM)
#     status_anterior = solicitacao.status.name

#     # Novo status (vem como string do request)
#     status_novo_str = request.status

#     # Registrar no histórico
#     atualizacao = AtualizacaoSolicitacao(
#         solicitacao_id=solicitacao_id,
#         administrador_id=admin_id,
#         status_anterior=status_anterior,
#         status_novo=status_novo_str,
#         descricao=request.descricao
#     )
#     db.add(atualizacao)


#     # Atualizar status e data de atualização
#     solicitacao.status = StatusSolicitacaoEnum[request.status]
#     solicitacao.atualizado_em = datetime.now()
    
#     db.commit()
#     db.refresh(solicitacao)
    
#     logger.info(f"✅ Status atualizado para {status_novo_str}")
#     return solicitacao


# ============================================================================
# GET: Obter HISTÓRICO de mudanças de status
# ============================================================================
# Retorna todas as atualizações feitas por admins
# Ordena por data mais recente primeiro
# ============================================================================

# @router.get("/api/solicitacoes/{solicitacao_id}/historico", response_model=List[AtualizacaoSolicitacaoResponse], tags=["Solicitações"])
# def obter_historico(
#     solicitacao_id: int,
#     db: Session = Depends(obter_conexao)
# ):
#     """
#     Obtém histórico completo de mudanças de status
#     - Mostra quem (admin), quando, do que para quê
#     - Ordenado por data mais recente primeiro
#     """
    
#     # Verificar que solicitação existe
#     solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
#     if not solicitacao:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Solicitação não encontrada"
#         )
    
#     # Buscar histórico e ordenar
#     historico = db.query(AtualizacaoSolicitacao)\
#         .filter(AtualizacaoSolicitacao.solicitacao_id == solicitacao_id)\
#         .order_by(AtualizacaoSolicitacao.criado_em.desc())\
#         .all()
    
#     return historico


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

# @router.post("/api/solicitacoes/{solicitacao_id}/apoios", tags=["Solicitações"])
# def apoiar_solicitacao(
#     solicitacao_id: int,
#     db: Session = Depends(obter_conexao),
#     authorization: str = Header(None)
# ):
#     """
#     Cidadão apoia uma solicitação existente
#     - Aumenta contador_apoios em 1
#     - Um usuário só pode apoiar uma vez
#     - Requer autenticação
#     """
    
#     # Extrair token do header
#     token = None
#     if authorization and authorization.startswith("Bearer "):
#         token = authorization[7:]
    
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token não fornecido"
#         )

#     # Extrair user_id do token
#     user_id = extrair_user_id_do_token(token)
#     if not user_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token inválido"
#         )

#     # Buscar solicitação
#     solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
#     if not solicitacao:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Solicitação não encontrada"
#         )

#     # Verificar se já apoiou
#     existe_apoio = db.query(Apoio).filter_by(
#         solicitacao_id=solicitacao_id,
#         usuario_id=user_id
#     ).first()

#     if existe_apoio:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="Você já apoia"
#         )

#     # Criar novo apoio
#     novo_apoio = Apoio(
#         solicitacao_id=solicitacao_id,
#         usuario_id=user_id
#     )

#     # Incrementar contador
#     solicitacao.contador_apoios += 1
#     db.add(novo_apoio)
#     db.commit()
    
#     return {
#         "message": "Apoio registrado",
#         "contador_apoios": solicitacao.contador_apoios
#     }


# # ============================================================================
# # POST: Adicionar COMENTÁRIO em uma solicitação
# # ============================================================================

# @router.post("/api/solicitacoes/{solicitacao_id}/comentarios", response_model=ComentarioResponse, tags=["Solicitações"])
# def adicionar_comentario(
#     solicitacao_id: int,
#     request: ComentarioCreate,
#     db: Session = Depends(obter_conexao),
#     authorization: str = Header(None)
# ):
#     """Adiciona comentário em uma solicitação"""
    
#     token = None
#     if authorization and authorization.startswith("Bearer "):
#         token = authorization[7:]
    
#     if not token:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token não fornecido")
    
#     user_id = extrair_user_id_do_token(token)
#     if not user_id:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
#     solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
#     if not solicitacao:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada")
    
#     usuario = db.query(Usuario).filter_by(id=user_id).first()
#     if not usuario:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    
#     novo_comentario = Comentario(
#         solicitacao_id=solicitacao_id,
#         usuario_id=user_id,
#         texto=request.texto
#     )
    
#     db.add(novo_comentario)
#     db.commit()
#     db.refresh(novo_comentario)
    
#     logger.info(f"✅ Comentário adicionado à solicitação {solicitacao_id}")
    
#     return ComentarioResponse(
#         id=novo_comentario.id,
#         solicitacao_id=novo_comentario.solicitacao_id,
#         usuario_id=novo_comentario.usuario_id,
#         texto=novo_comentario.texto,
#         criado_em=novo_comentario.criado_em,
#         usuario_nome=usuario.nome,
#         usuario_tipo=usuario.tipo_usuario.value if hasattr(usuario.tipo_usuario, 'value') else str(usuario.tipo_usuario)
#     )


# # ============================================================================
# # GET: Listar COMENTÁRIOS de uma solicitação
# # ============================================================================

# @router.get("/api/solicitacoes/{solicitacao_id}/comentarios", response_model=List[ComentarioResponse], tags=["Solicitações"])
# def listar_comentarios(
#     solicitacao_id: int,
#     db: Session = Depends(obter_conexao)
# ):
#     """Lista comentários de uma solicitação"""
    
#     solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
#     if not solicitacao:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada")
    
#     comentarios = db.query(Comentario)\
#         .filter(Comentario.solicitacao_id == solicitacao_id)\
#         .order_by(Comentario.criado_em.desc())\
#         .all()
    
#     resultado = []
#     for comentario in comentarios:
#         usuario = db.query(Usuario).filter_by(id=comentario.usuario_id).first()
#         resultado.append(ComentarioResponse(
#             id=comentario.id,
#             solicitacao_id=comentario.solicitacao_id,
#             usuario_id=comentario.usuario_id,
#             texto=comentario.texto,
#             criado_em=comentario.criado_em,
#             usuario_nome=usuario.nome if usuario else "Deletado",
#             usuario_tipo=usuario.tipo_usuario.value if usuario and hasattr(usuario.tipo_usuario, 'value') else "DESCONHECIDO"
#         ))
    
#     return resultado


# # ============================================================================
# # DELETE: Deletar COMENTÁRIO próprio
# # ============================================================================

# @router.delete("/api/solicitacoes/{solicitacao_id}/comentarios/{comentario_id}", tags=["Solicitações"])
# def deletar_comentario(
#     solicitacao_id: int,
#     comentario_id: int,
#     db: Session = Depends(obter_conexao),
#     authorization: str = Header(None)
# ):
#     """Deleta comentário próprio"""
    
#     token = None
#     if authorization and authorization.startswith("Bearer "):
#         token = authorization[7:]
    
#     if not token:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token não fornecido")
    
#     user_id = extrair_user_id_do_token(token)
#     if not user_id:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
#     solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
#     if not solicitacao:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada")
    
#     comentario = db.query(Comentario).filter_by(id=comentario_id, solicitacao_id=solicitacao_id).first()
#     if not comentario:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado")
    
#     if comentario.usuario_id != user_id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão")
    
#     db.delete(comentario)
#     db.commit()
    
#     return {"message": "Comentário deletado"}


# ============================================================================
# FIM DO ARQUIVO
# ============================================================================
