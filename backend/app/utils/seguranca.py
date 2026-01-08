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

# Configuração do bcrypt para hash seguro de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=BCRYPT_ROUNDS)

def hash_senha(senha: str) -> str:
    """
    Faz hash seguro de uma senha usando bcrypt.
    NUNCA armazenar senha em texto plano!
    
    Parâmetro: senha em texto plano
    Retorna: hash da senha
    """
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, hash_armazenado: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde ao hash armazenado.
    Usado no login para validar se usuário digitou a senha correta.
    
    Parâmetros:
    - senha_plana: senha digitada pelo usuário
    - hash_armazenado: hash armazenado no banco de dados
    Retorna: True se a senha bate, False caso contrário
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
    Cria um token JWT (JSON Web Token) assinado.
    O token contém os dados do usuário e uma assinatura criptográfica.
    
    Parâmetros:
    - data: dicionário com dados do usuário {"sub": id, "cpf": "...", "tipo": "..."}
    - expires_delta: tempo de expiração customizado (se None, usa valor default de config)
    
    Retorna: Token JWT como string
    """
    # Copia os dados que vão dentro do token (payload)
    to_encode = data.copy()
    
    # Calcula data/hora de expiração do token
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    # Adiciona expiração (exp) e um id único (jti) ao token
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    
    # Cria o token JWT assinando com o segredo e algoritmo configurados
    encoded_jwt = jwt.encode(
        to_encode,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    return encoded_jwt

def verificar_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifica se um token JWT é válido e extrai seus dados.
    Decodifica o token usando o segredo e valida a assinatura.
    
    Parâmetro: token JWT como string
    Retorna: Dicionário com dados do token se válido, None caso contrário
    """
    try:
        # Decodifica o token usando o segredo configurado
        # options={"verify_sub": False} permite que 'sub' seja int ao invés de string
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_sub": False}  # Permite sub como inteiro
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Token expirou
        return None
    except jwt.InvalidTokenError:
        # Token malformado ou assinado com segredo errado
        return None

def extrair_user_id_do_token(token: str) -> Optional[int]:
    """
    Extrai o user_id (subject) do token JWT.
    
    Parâmetro: token JWT como string
    Retorna: ID do usuário (int) ou None se token inválido
    """
    payload = verificar_access_token(token)
    if payload:
        return payload.get("sub")
    return None

# ============================================================================
# CPF - Validação brasileira
# ============================================================================

def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF usando algoritmo mod 11 brasileiro.
    Aceita CPF com ou sem máscara (ex: 111.444.777-35 ou 11144477735).
    
    Parâmetro: CPF como string
    Retorna: True se válido, False caso contrário
    """
    # Remove tudo que não é dígito
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem exatamente 11 dígitos
    if len(cpf_limpo) != 11:
        return False
    
    # Rejeita sequências iguais (111.111.111-11, 000.000.000-00, etc)
    if cpf_limpo == cpf_limpo[0] * 11:
        return False
    
    # Valida primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf_limpo[i]) * (10 - i)
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    if int(cpf_limpo[9]) != digito1:
        return False
    
    # Valida segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf_limpo[i]) * (11 - i)
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    if int(cpf_limpo[10]) != digito2:
        return False
    
    return True

def formatar_cpf(cpf: str) -> str:
    """
    Formata CPF para o padrão brasileiro: XXX.XXX.XXX-XX.
    
    Parâmetro: CPF como string (com ou sem máscara)
    Retorna: CPF formatado ou original se inválido
    """
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_limpo) != 11:
        return cpf
    
    return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

def mascarar_cpf(cpf: str) -> str:
    """
    Mascara CPF mostrando apenas os últimos 4 dígitos.
    Útil para exibir CPF em telas sem expor informação sensível.
    
    Parâmetro: CPF como string (com ou sem máscara)
    Retorna: CPF mascarado no formato ***.***.***.12345 ou original se inválido
    """
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_limpo) < 4:
        return "*" * len(cpf_limpo)
    
    mascarado = "*" * (len(cpf_limpo) - 4) + cpf_limpo[-4:]
    return f"{mascarado[:3]}.{mascarado[3:6]}.{mascarado[6:9]}-{mascarado[9:]}"
