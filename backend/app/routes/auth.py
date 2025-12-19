# ============================================================================
# auth.py - ROTAS DE AUTENTICAÇÃO
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioResponse
from app.utils.security import (
    hash_senha, verificar_senha, validar_cpf, criar_access_token
)
from database.connection import get_db
from config import TIPO_USUARIO
from typing import Dict, Any
import logging
from app.models import TipoUsuarioEnum

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# SCHEMAS CUSTOMIZADOS PARA AUTH
# ============================================================================

from pydantic import BaseModel, EmailStr

class LoginCidadaoRequest(BaseModel):
    """Request para login de cidadão"""
    cpf: str
    senha: str

class LoginAdminRequest(BaseModel):
    """Request para login de admin"""
    email: EmailStr
    senha: str

class TokenResponse(BaseModel):
    """Response com token JWT"""
    access_token: str
    token_type: str = "bearer"

# ============================================================================
# LOGIN CIDADÃO
# ============================================================================

@router.post("/auth/login/cidadao", response_model=TokenResponse, tags=["Autenticação"])
def login_cidadao(
    request: LoginCidadaoRequest,
    db: Session = Depends(get_db)
):
    """
    Login de cidadão usando CPF e senha
    
    Retorna JWT token válido por 24h
    """
    # Valida CPF
    if not validar_cpf(request.cpf):
        logger.warning(f"❌ CPF inválido: {request.cpf}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF inválido"
        )
    
    # Busca usuário por CPF
    usuario = db.query(Usuario).filter_by(cpf=request.cpf).first()
    
    if not usuario:
        logger.warning(f"❌ CPF não encontrado: {request.cpf}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF ou senha incorretos"
        )
    
    # Verifica se é cidadão
    if usuario.tipo_usuario.value != TIPO_USUARIO["CIDADAO"]:
        logger.warning(f"❌ Usuário não é cidadão: {request.cpf}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF ou senha incorretos"
        )
    
    # Verifica se está ativo
    if not usuario.ativo:
        logger.warning(f"❌ Usuário inativo: {request.cpf}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )
    
    # Verifica senha
    if not verificar_senha(request.senha, usuario.senha_hash):
        logger.warning(f"❌ Senha incorreta para: {request.cpf}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF ou senha incorretos"
        )
    
    # Gera token
    token = criar_access_token(
        data={"sub": usuario.id, "email": usuario.email, "tipo": "cidadao"}
    )
    
    logger.info(f"✅ Cidadão logado: {request.cpf}")
    return {"access_token": token, "token_type": "bearer"}


# ============================================================================
# LOGIN ADMIN
# ============================================================================

@router.post("/auth/login/admin", response_model=TokenResponse, tags=["Autenticação"])
def login_admin(
    request: LoginAdminRequest,
    db: Session = Depends(get_db)
):
    """
    Login de administrador usando email e senha
    
    Retorna JWT token válido por 24h
    """
    # Busca usuário por email
    usuario = db.query(Usuario).filter_by(email=request.email).first()
    
    if not usuario:
        logger.warning(f"❌ Email não encontrado: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    # Verifica se é admin
    if usuario.tipo_usuario.value != TIPO_USUARIO["ADMINISTRADOR"]:
        logger.warning(f"❌ Usuário não é admin: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    # Verifica se está ativo
    if not usuario.ativo:
        logger.warning(f"❌ Admin inativo: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin inativo"
        )
    
    # Verifica senha
    if not verificar_senha(request.senha, usuario.senha_hash):
        logger.warning(f"❌ Senha incorreta para admin: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    # Gera token
    token = criar_access_token(
        data={"sub": usuario.id, "email": usuario.email, "tipo": "admin"}
    )
    
    logger.info(f"✅ Admin logado: {request.email}")
    return {"access_token": token, "token_type": "bearer"}


# ============================================================================
# CADASTRO CIDADÃO
# ============================================================================

@router.post("/auth/cadastro", response_model=UsuarioResponse, tags=["Autenticação"])
def cadastro_cidadao(
    request: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Cadastro de novo cidadão
    
    CPF e email devem ser únicos
    """
    # Valida CPF
    if not validar_cpf(request.cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF inválido"
        )
    
    # Verifica se CPF já existe
    existe_cpf = db.query(Usuario).filter_by(cpf=request.cpf).first()
    if existe_cpf:
        logger.warning(f"❌ CPF já cadastrado: {request.cpf}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado"
        )
    
    # Verifica se email já existe
    existe_email = db.query(Usuario).filter_by(email=request.email).first()
    if existe_email:
        logger.warning(f"❌ Email já cadastrado: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Cria novo usuário cidadão
    novo_usuario = Usuario(
        cpf=request.cpf,
        email=request.email,
        nome=request.nome,
        senha_hash=hash_senha(request.senha),
        tipo_usuario=TipoUsuarioEnum.CIDADAO,
        ativo=True
    )
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    logger.info(f"✅ Novo cidadão cadastrado: {request.cpf}")
    return novo_usuario


# ============================================================================
# VERIFICAR USUÁRIO ATUAL
# ============================================================================

@router.get("/auth/me", tags=["Autenticação"])
def get_current_user(
    db: Session = Depends(get_db),
    token: str = None
):
    """
    Retorna dados do usuário autenticado
    
    Requer token no header: Authorization: Bearer {token}
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    from app.utils.security import extrair_user_id_do_token
    
    user_id = extrair_user_id_do_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    usuario = db.query(Usuario).filter_by(id=user_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return usuario
