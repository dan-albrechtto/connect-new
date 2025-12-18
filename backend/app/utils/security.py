# ══════════════════════════════════════════════════════════════════════════════
# ARQUIVO: utils/security.py
# DESCRIÇÃO: Utilitários de segurança - hash de senha e JWT
# Contém funções para autenticação e geração de tokens
# ══════════════════════════════════════════════════════════════════════════════

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO BCRYPT - Hash seguro de senha
# ═══════════════════════════════════════════════════════════════════════════

# CryptContext configura o algoritmo bcrypt para hash de senha
# deprecated="auto" significa: se tiver hash antigo, regenera automaticamente
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO JWT - Geração de tokens
# ═══════════════════════════════════════════════════════════════════════════

# Chave secreta para assinar JWT (MUDAR EM PRODUÇÃO!)
# Em produção: usar variável de ambiente (os.getenv("SECRET_KEY"))
SECRET_KEY = "sua-chave-super-secreta-mude-isso-em-producao-123456"

# Algoritmo para assinar JWT
ALGORITHM = "HS256"

# Tempo de expiração do token (em minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE HASH DE SENHA
# ═══════════════════════════════════════════════════════════════════════════

def hash_senha(senha: str) -> str:
    """
    Faz hash seguro de uma senha usando bcrypt
    
    IMPORTANTE: NUNCA armazenar senha em texto plano!
    Sempre usar essa função antes de salvar no banco
    
    Parâmetro:
    - senha: string da senha em texto plano
    
    Retorna:
    - Hash seguro da senha (irreversível)
    
    Exemplo:
    >>> hash_seguro = hash_senha("minha_senha")
    >>> # hash_seguro = "$2b$12$R9h/cIPz0gi..."
    """
    return pwd_context.hash(senha)


def verificar_senha(senha_plana: str, hash_armazenado: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde ao hash armazenado
    
    Usado no login para validar se usuário digitou senha correta
    
    Parâmetros:
    - senha_plana: senha que usuário digitou
    - hash_armazenado: hash salvo no banco de dados
    
    Retorna:
    - True se senhas correspondem
    - False se não correspondem
    
    Exemplo:
    >>> verificar_senha("minha_senha", "$2b$12$R9h/cIPz0gi...")
    >>> # True (senhas combinam)
    """
    return pwd_context.verify(senha_plana, hash_armazenado)


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE JWT (TOKEN)
# ═══════════════════════════════════════════════════════════════════════════

def criar_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um token JWT (JSON Web Token)
    
    Token contém informações do usuário (id, email, tipo) assinadas com chave secreta
    Frontend envia token em cada requisição para provar que está autenticado
    
    Parâmetros:
    - data: dicionário com dados do usuário ({"sub": usuario_id, "email": "...", "tipo": "..."})
    - expires_delta: quanto tempo token é válido (se None, usa valor padrão 30 min)
    
    Retorna:
    - Token JWT como string
    
    Exemplo:
    >>> token = criar_access_token(
    ...     data={"sub": 1, "email": "joao@test.com", "tipo": "cidadao"},
    ...     expires_delta=timedelta(minutes=30)
    ... )
    >>> # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    
    # Copia dados para não modificar original
    to_encode = data.copy()
    
    # Define tempo de expiração
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Adiciona tempo de expiração aos dados
    to_encode.update({"exp": expire})
    
    # Codifica (assina) o token com chave secreta
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def verificar_access_token(token: str) -> dict:
    """
    Verifica se um token JWT é válido e extrai dados
    
    Usado para validar token que vem na requisição
    Se token expirado ou inválido, lança exceção
    
    Parâmetro:
    - token: string do JWT
    
    Retorna:
    - Dicionário com dados ({"sub": usuario_id, "email": "...", "exp": 123456})
    
    Lança:
    - JWTError se token inválido ou expirado
    
    Exemplo:
    >>> dados = verificar_access_token("eyJhbGciOiJIUzI1NiIs...")
    >>> # dados = {"sub": 1, "email": "joao@test.com", "exp": 1705430400}
    """
    
    try:
        # Decodifica e verifica assinatura
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        return payload
        
    except JWTError:
        # Token inválido, expirado, ou assinatura não confere
        raise


# ═══════════════════════════════════════════════════════════════════════════
# RESUMO DE USO
# ═══════════════════════════════════════════════════════════════════════════

"""
FLUXO DE AUTENTICAÇÃO:

1. REGISTRO (Cidadão):
   - Usuário digita: nome, email, cpf, senha
   - Backend faz: hash_senha("senha_digitada") → salva no banco
   
2. LOGIN (Cidadão):
   - Usuário digita: cpf, senha
   - Backend faz:
     a) Busca usuário por CPF
     b) verificar_senha("senha_digitada", hash_armazenado)
     c) Se OK: criar_access_token({"sub": usuario_id, ...})
     d) Retorna token
   
3. REQUISIÇÕES AUTENTICADAS:
   - Frontend envia: Authorization: Bearer {token}
   - Backend faz:
     a) Extrai token do header
     b) verificar_access_token(token)
     c) Extrai usuario_id dos dados
     d) Executa ação autenticada

4. ADMIN LOGIN (igual, só que com email)
   - POST /auth/login/admin
   - Busca por email (não CPF)
   - Resto é idêntico
"""