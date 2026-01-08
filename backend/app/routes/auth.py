# ============================================================================
# auth.py - ROTAS DE AUTENTICAÇÃO
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.models import Usuario
from app.schemas import (
    UsuarioCreate, UsuarioResponse, UsuarioUpdate, MudarSenhaRequest, MudarSenhaResponse
)
from app.utils.seguranca import (
    hash_senha, verificar_senha, validar_cpf, criar_access_token, extrair_user_id_do_token
)
from database.connection import obter_conexao
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
# CADASTRO CIDADÃO
# ============================================================================

@router.post("/auth/cadastro", response_model=UsuarioResponse, tags=["Autenticação"], summary="Cadastro Cidadão")
def cadastro_cidadao(
    request: UsuarioCreate,
    db: Session = Depends(obter_conexao)
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
        telefone=request.telefone,
        data_nascimento=request.data_nascimento,
        tipo_usuario=TipoUsuarioEnum.CIDADAO,
        ativo=True
    )
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    logger.info(f"✅ Novo cidadão cadastrado: {request.cpf}")
    return novo_usuario

# ============================================================================
# LOGIN CIDADÃO
# ============================================================================

@router.post("/auth/login/cidadao", response_model=TokenResponse, tags=["Autenticação"], summary="Login Cidadão")
def login_cidadao(
    request: LoginCidadaoRequest,
    db: Session = Depends(obter_conexao)
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
    if usuario.tipo_usuario != TipoUsuarioEnum.CIDADAO:
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
        data={"sub": usuario.id, "cpf": usuario.cpf, "email": usuario.email, "tipo": "cidadao"}
    )
    
    logger.info(f"✅ Cidadão logado: {request.cpf}")
    return {"access_token": token, "token_type": "bearer"}


# ============================================================================
# LOGIN ADMIN
# ============================================================================

@router.post("/auth/login/admin", response_model=TokenResponse, tags=["Autenticação"])
def login_admin(
    request: LoginAdminRequest,
    db: Session = Depends(obter_conexao)
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
    if usuario.tipo_usuario != TipoUsuarioEnum.ADMINISTRADOR:
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
# VERIFICAR USUÁRIO ATUAL
# ============================================================================

@router.get("/auth/eu", tags=["Autenticação"], summary="Verificar Usuário Atual")
def get_current_user(
    db: Session = Depends(obter_conexao),
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
    
    from app.utils.seguranca import extrair_user_id_do_token
    
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



# ============================================================================
# ATUALIZAR PERFIL
# ============================================================================


@router.put("/auth/atualizar-cadastro", response_model=UsuarioResponse, tags=["Autenticação"], summary="Atualizar Dados do Cadastro")
def atualizar_perfil(
    request: UsuarioUpdate,
    db: Session = Depends(obter_conexao),
    token: str = None
):
    """
    Atualiza dados básicos do usuário autenticado
    
    Permite editar:
    - telefone
    - data_nascimento
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
    
    usuario = db.query(Usuario).filter_by(id=user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    if request.telefone is not None:
        usuario.telefone = request.telefone
    
    if request.data_nascimento is not None:
        usuario.data_nascimento = request.data_nascimento
    
    db.commit()
    db.refresh(usuario)
    
    logger.info(f"✅ Perfil atualizado para usuário {user_id}")
    return usuario


# ============================================================================
# MUDAR SENHA
# ============================================================================


@router.put("/auth/alterar-senha", response_model=MudarSenhaResponse, tags=["Autenticação"], summary="Alterar Senha")
def mudar_senha(
    request: MudarSenhaRequest,
    db: Session = Depends(obter_conexao),
    token: str = None
):
    """
    Muda a senha do usuário autenticado
    
    Requisitos:
    - Mínimo 8 caracteres
    - 1 MAIÚSCULA
    - 1 minúscula
    - 1 número
    - 1 caractere especial (!@#$%^&*)
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
    
    usuario = db.query(Usuario).filter_by(id=user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verifica senha atual
    if not verificar_senha(request.senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha atual incorreta"
        )
    
    # Verifica se nova_senha é diferente da atual
    if verificar_senha(request.nova_senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nova senha não pode ser igual à anterior"
        )
    
    # Atualiza senha
    usuario.senha_hash = hash_senha(request.nova_senha)
    
    db.commit()
    
    logger.info(f"✅ Senha alterada com sucesso para usuário {user_id}")
    return {"mensagem": "Senha alterada com sucesso"}


# ============================================================================
# PUT: Cidadão ALTERA seu email
# ============================================================================

@router.put(
    "/auth/alterar-email",
    tags=["Autenticação"],
    summary="Alterar email"
)
def alterar_email(
    novo_email: str,
    senha: str,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão altera seu email (validação simplificada apenas com senha)
    
    - Requer autenticação (token JWT)
    - Valida senha atual (segurança básica)
    - Verifica se novo email já não está registrado
    - Atualiza email na conta
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
    
    # Buscar usuário
    usuario = db.query(Usuario).filter_by(id=usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Validar senha
    from app.utils.seguranca import verificar_senha
    if not verificar_senha(senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta"
        )
    
    # Validar novo email não está registrado
    email_existe = db.query(Usuario).filter(
        Usuario.email == novo_email,
        Usuario.id != usuario_id
    ).first()
    
    if email_existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email já está registrado"
        )
    
    # Validar formato email (básico)
    if "@" not in novo_email or "." not in novo_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email inválido"
        )
    
    # Atualizar email
    usuario.email = novo_email
    db.commit()
    db.refresh(usuario)
    
    logger.info(f"✅ Email alterado: usuario_id={usuario_id}")
    
    return {
        "mensagem": "Email alterado com sucesso",
        "novo_email": novo_email
    }


# ============================================================================
# DELETE: Cidadão DELETA sua conta
# ============================================================================

@router.delete(
    "/auth/deletar-conta",
    tags=["Autenticação"],
    summary="Deletar Conta"
)
def deletar_conta(
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Cidadão deleta sua conta permanentemente
    
    - Requer autenticação (token JWT)
    - Deleta usuário e TODAS as suas solicitações (cascata)
    - Ação irreversível
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
    
    # Buscar usuário
    usuario = db.query(Usuario).filter_by(id=usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Deletar usuário (cascata deleta solicitações)
    db.delete(usuario)
    db.commit()
    
    logger.info(f"✅ Conta deletada: usuario_id={usuario_id}")
    
    return {"mensagem": "Conta deletada com sucesso"}