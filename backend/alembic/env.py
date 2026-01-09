"""
Configuração do Alembic para Connect Cidade
Detecta automaticamente mudanças nos models e gera migrations
"""

from logging.config import fileConfig
import sys
import os
from pathlib import Path

# Adicionar a pasta pai ao path (para importar 'app' e 'database')
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ========== IMPORTAR SEUS MODELS ==========
# IMPORTANTE: importar a Base e TODOS os modelos para o Alembic detectar
from database.connection import Base

# Importar todos os modelos (na ordem correta!)
from app.models.usuario import Usuario
from app.models.categoria import Categoria
from app.models.solicitacao import Solicitacao
from app.models.foto import Foto
from app.models.atualizacao_solicitacao import AtualizacaoSolicitacao
from app.models.apoio_solicitacao import Apoio
from app.models.avaliacao import Avaliacao
from app.models.notificacao import Notificacao


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ========== CONFIGURAR target_metadata ==========
# ISTO PRECISA APONTAR PARA SUA Base!
target_metadata = Base.metadata

# ========== CONFIGURAR DATABASE URL ==========
# Ler do .env
from dotenv import load_dotenv
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "connect_cidade")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configurar no Alembic
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
