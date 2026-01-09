"""
Rotas de Notificações
Endpoints para o frontend consumir notificações do cidadão
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database.connection import obter_conexao
from app.utils.servico_notificacao import (
    listar_notificacoes_usuario,
    contar_nao_lidas,
    marcar_notificacao_como_lida,
    marcar_todas_como_lidas,
    deletar_notificacao,
    criar_notificacao_status_atualizado
)
from app.schemas import (
    NotificacaoListaResponse,
    NotificacaoMarcarLidaRequest,
    NotificacaoMarcarLidaResponse,
    NotificacaoDeletarResponse,
    NotificacaoContarResponse
)
from app.utils.seguranca import extrair_user_id_do_token

router = APIRouter(
    prefix="/api/notificacoes",
    tags=["Notificações"]
)


def obter_usuario_autenticado(authorization: str = Header(None), db: Session = Depends(obter_conexao)):
    """
    Dependency que valida o token JWT e retorna o ID do usuário.
    
    Espera header: Authorization: Bearer <token>
    
    Se token inválido ou ausente, retorna erro 401.
    """
    
    # Valida se header foi fornecido
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token não fornecido. Use header: Authorization: Bearer <token>"
        )
    
    # Extrai apenas o token (remove "Bearer ")
    partes = authorization.split(" ")
    if len(partes) != 2 or partes[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Formato inválido. Use: Authorization: Bearer <token>"
        )
    
    token = partes[1]
    
    # Valida token e extrai user_id
    usuario_id = extrair_user_id_do_token(token)
    
    if not usuario_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )
    
    return usuario_id


@router.get("/minhas", response_model=NotificacaoListaResponse, summary="Listar minhas notificações")
async def listar_minhas_notificacoes(
    apenas_nao_lidas: bool = False,
    limite: int = 50,
    offset: int = 0,
    usuario_id: int = Depends(obter_usuario_autenticado),
    db: Session = Depends(obter_conexao)
):
    """
    Lista notificações do usuário autenticado.
    
    Query params:
    - apenas_nao_lidas: bool (opcional) - retorna só não-lidas
    - limite: int (padrão 50) - máximo de resultados
    - offset: int (padrão 0) - para paginação
    
    Headers obrigatórios:
    - Authorization: Bearer <token_jwt>
    """
    
    resultado = listar_notificacoes_usuario(
        db=db,
        usuario_id=usuario_id,
        apenas_nao_lidas=apenas_nao_lidas,
        limite=limite,
        offset=offset
    )
    
    return resultado


@router.get("/nao-lidas/contar", response_model=NotificacaoContarResponse, summary="Contar notificações não lidas")
async def contar_nao_lidas_endpoint(
    usuario_id: int = Depends(obter_usuario_autenticado),
    db: Session = Depends(obter_conexao)
):
    """
    Conta quantas notificações não-lidas o usuário tem.
    
    Útil para atualizar badge/sininho do frontend.
    
    Headers obrigatórios:
    - Authorization: Bearer <token_jwt>
    """
    
    nao_lidas = contar_nao_lidas(db, usuario_id)
    
    return NotificacaoContarResponse(nao_lidas=nao_lidas)


@router.post("/{notificacao_id}/marcar-lida", response_model=NotificacaoMarcarLidaResponse, summary="Marcar notificação como lida")
async def marcar_como_lida(
    notificacao_id: int,
    request: NotificacaoMarcarLidaRequest,
    usuario_id: int = Depends(obter_usuario_autenticado),
    db: Session = Depends(obter_conexao)
):
    """
    Marca uma notificação como lida.
    
    Path params:
    - notificacao_id: ID da notificação a marcar
    
    Headers obrigatórios:
    - Authorization: Bearer <token_jwt>
    """
    
    resultado = marcar_notificacao_como_lida(db, notificacao_id, usuario_id)
    
    if not resultado.sucesso:
        raise HTTPException(status_code=404, detail=resultado.mensagem)
    
    return resultado


@router.post("/marcar-todas-lidas", response_model=NotificacaoMarcarLidaResponse, summary="Marcar todas notificações como lidas")
async def marcar_todas_lidas(
    usuario_id: int = Depends(obter_usuario_autenticado),
    db: Session = Depends(obter_conexao)
):
    """
    Marca TODAS as notificações como lidas de uma vez.
    
    Headers obrigatórios:
    - Authorization: Bearer <token_jwt>
    """
    
    resultado = marcar_todas_como_lidas(db, usuario_id)
    
    return resultado


@router.delete("/{notificacao_id}", response_model=NotificacaoDeletarResponse, summary="Deletar notificação")
async def deletar_notificacao_endpoint(
    notificacao_id: int,
    usuario_id: int = Depends(obter_usuario_autenticado),
    db: Session = Depends(obter_conexao)
):
    """
    Deleta uma notificação.
    
    Path params:
    - notificacao_id: ID da notificação a deletar
    
    Headers obrigatórios:
    - Authorization: Bearer <token_jwt>
    """
    
    resultado = deletar_notificacao(db, notificacao_id, usuario_id)
    
    if not resultado.sucesso:
        raise HTTPException(status_code=404, detail=resultado.mensagem)
    
    return resultado
