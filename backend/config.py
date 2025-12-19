# ============================================================================
# config.py - CONFIGURAÇÕES E CONSTANTES
# ============================================================================

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# BANCO DE DADOS
# ============================================================================

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "connect_cidade")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ============================================================================
# JWT
# ============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "sua-chave-secreta-super-longa-aqui-minimo-50-caracteres")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ============================================================================
# BCRYPT
# ============================================================================

BCRYPT_ROUNDS = 12

# ============================================================================
# CATEGORIAS (baseado em models.py)
# ============================================================================

CATEGORIAS = {
    "COLETA_LIXO": 1,
    "ILUMINACAO": 2,
    "ACESSIBILIDADE": 3
}

# ============================================================================
# TIPOS DE USUÁRIO (baseado em models.py)
# ============================================================================

TIPO_USUARIO = {
    "CIDADAO": 1,
    "ADMINISTRADOR": 2
}

# ============================================================================
# STATUS SOLICITAÇÃO (baseado em models.py)
# ============================================================================

STATUS_SOLICITACAO = {
    "PENDENTE": 1,
    "EM_ANALISE": 2,
    "EM_ANDAMENTO": 3,
    "RESOLVIDO": 4,
    "CANCELADO": 5
}

# ============================================================================
# UPLOAD FOTOS
# ============================================================================

STORAGE_FOLDER = "storage"
FOTOS_FOLDER = os.path.join(STORAGE_FOLDER, "fotos")
MAX_FOTO_SIZE_MB = 5
MAX_FOTO_SIZE_BYTES = MAX_FOTO_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# Criar pasta se não existir
os.makedirs(FOTOS_FOLDER, exist_ok=True)

# ============================================================================
# GEOLOCALIZAÇÃO
# ============================================================================

RAIO_DUPLICATA_METROS = 50  # Para verificar problemas próximos

# ============================================================================
# APLICAÇÃO
# ============================================================================

APP_NAME = "Connect Cidade"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# ============================================================================
# ADMIN PADRÃO (para seed)
# ============================================================================

ADMIN_PADRAO_CPF = "00000000000"  # Será mudado no seed
ADMIN_PADRAO_SENHA = "Connect@2025!"
ADMIN_PADRAO_NOME = "Administrador Municipal"
ADMIN_PADRAO_EMAIL = "admin@conectcidade.local"

# ============================================================================
# PAGINAÇÃO
# ============================================================================

ITEMS_PER_PAGE = 20
MAX_ITEMS_PER_PAGE = 100
