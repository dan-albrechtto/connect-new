# ============================================================================
# security.py - SEGURANÇA: JWT, CPF, PASSWORD
# ============================================================================

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS, BCRYPT_ROUNDS
import uuid

# ============================================================================
# BCRYPT - Hash de Senhas
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=BCRYPT_ROUNDS)


def hash_senha(senha: str) -> str:
    """
    Faz hash seguro de uma senha usando bcrypt
    NUNCA armazenar senha em texto plano!
    """
    return pwd_context.hash(senha)


def verificar_senha(senha_plana: str, hash_armazenado: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde ao hash armazenado
    Usado no login para validar se usuário digitou senha correta
    """
    return pwd_context.verify(senha_plana, hash_armazenado)


# ============================================================================
# JWT - JSON Web Tokens
# ============================================================================

def criar_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um token JWT (JSON Web Token)
    Token contém informações do usuário assinadas com chave secreta
    
    Parâmetros:
    - data: dicionário com dados do usuário {"sub": usuario_id, "email": "...", "tipo": "..."}
    - expires_delta: quanto tempo token é válido (se None, usa valor padrão)
    
    Retorna: Token JWT como string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    
    encoded_jwt = jwt.encode(
        to_encode,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    return encoded_jwt


def verificar_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifica se um token JWT é válido e extrai dados
    Usado para validar token que vem na requisição
    
    Parâmetro: token string do JWT
    Retorna: Dicionário com dados ou None se inválido
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extrair_user_id_do_token(token: str) -> Optional[int]:
    """Extrai user_id do token"""
    payload = verificar_access_token(token)
    if payload:
        return payload.get("sub")
    return None


# ============================================================================
# CPF - Validação brasileira
# ============================================================================

def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF usando algoritmo mod 11 brasileiro
    Aceita com ou sem máscara
    """
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_limpo) != 11:
        return False
    
    # Rejeita sequências iguais (111.111.111-11, etc)
    if cpf_limpo == cpf_limpo[0] * 11:
        return False
    
    # Valida primeiro dígito
    soma = 0
    for i in range(9):
        soma += int(cpf_limpo[i]) * (10 - i)
    
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[9]) != digito1:
        return False
    
    # Valida segundo dígito
    soma = 0
    for i in range(10):
        soma += int(cpf_limpo[i]) * (11 - i)
    
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[10]) != digito2:
        return False
    
    return True


def formatar_cpf(cpf: str) -> str:
    """Formata CPF para XXX.XXX.XXX-XX"""
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_limpo) != 11:
        return cpf
    
    return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"


def mascarar_cpf(cpf: str) -> str:
    """Mascara CPF mostrando apenas últimos 4 dígitos"""
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_limpo) < 4:
        return "*" * len(cpf_limpo)
    
    mascarado = "*" * (len(cpf_limpo) - 4) + cpf_limpo[-4:]
    return f"{mascarado[:3]}.{mascarado[3:6]}.{mascarado[6:9]}-{mascarado[9:]}"
