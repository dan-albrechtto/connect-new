# backend/app/crud/usuario_crud.py

"""
CRUD de UsuÃ¡rio - OperaÃ§Ãµes de Banco de Dados

Responsabilidades:
- Criar novo usuÃ¡rio
- Buscar usuÃ¡rio por ID
- Buscar usuÃ¡rio por CPF
- Buscar usuÃ¡rio por email
- Atualizar dados de usuÃ¡rio
- Listar usuÃ¡rios (paginado)
- Deletar usuÃ¡rio

PadrÃ£o de nomenclatura:
- ParÃ¢metro DB: "db" (Session do SQLAlchemy)
- Modelo retornado: "Usuario" (classe SQLAlchemy)
- VariÃ¡veis locais em portuguÃªs: ex: "novo_usuario", "usuarios_encontrados"
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models import Usuario
from app.utils.enums import TipoUsuarioEnum
from typing import Optional, List
import logging

# Configurar logger para debug
logger = logging.getLogger(__name__)


class UsuarioCRUD:
    """
    Classe que concentra todas as operaÃ§Ãµes de banco para Usuario.
    
    PadrÃ£o: Cada mÃ©todo recebe 'db: Session' como primeiro parÃ¢metro
    (apÃ³s self) e retorna o objeto Usuario ou None.
    """

    
