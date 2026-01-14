# backend/app/crud/base.py

"""
CRUD Base - Operações genéricas de banco de dados

Esta é uma classe generada que todos os CRUDs específicos vão herdar.
Evita repetir código de criar, atualizar, deletar, etc.
"""

from typing import Generic, TypeVar, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

# TypeVar: tipo genérico que cada CRUD vai especificar
ModelType = TypeVar("ModelType")

class CRUDBase(Generic[ModelType]):
    """
    Classe base para todas as operações CRUD.
    
    Cada CRUD específico (SolicitacaoCRUD, UsuarioCRUD, etc) 
    vai herdar desta e implementar suas próprias operações.
    
    Exemplo:
        class SolicitacaoCRUD(CRUDBase[Solicitacao]):
            pass
    """
    
    def __init__(self, modelo: type[ModelType]):
        """
        Inicializa o CRUD com um modelo SQLAlchemy.
        
        Args:
            modelo: Classe do modelo (ex: Solicitacao, Usuario, Notificacao)
        """
        self.modelo = modelo
    
    async def criar(self, db: Session, obj_in: dict) -> ModelType:
        """
        Cria um novo registro no banco.
        
        Args:
            db: Sessão do banco de dados
            obj_in: Dicionário com dados para criar
            
        Returns:
            Objeto do modelo criado
            
        Exemplo:
            novo_usuario = await usuario_crud.criar(
                db, 
                {"cpf": "111.444.777-35", "senha_hash": "..."}
            )
        """
        # Converte dicionário para objeto do modelo
        db_obj = self.modelo(**obj_in)
        
        # Adiciona à sessão
        db.add(db_obj)
        
        # Confirma (commit)
        db.commit()
        
        # Atualiza com dados do BD (ID gerado, timestamps, etc)
        db.refresh(db_obj)
        
        return db_obj
    
    async def obter_por_id(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Busca um registro pelo ID.
        
        Args:
            db: Sessão do banco
            id: ID do registro
            
        Returns:
            Objeto encontrado ou None
        """
        return db.query(self.modelo).filter(self.modelo.id == id).first()
    
    async def obter_todos(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """
        Busca todos os registros com paginação.
        
        Args:
            db: Sessão do banco
            skip: Quantos registros pular (paginação)
            limit: Quantos registros retornar
            
        Returns:
            Lista de objetos
            
        Exemplo:
            solicitacoes = await solicitacao_crud.obter_todos(
                db, 
                skip=0, 
                limit=20
            )
        """
        return db.query(self.modelo).offset(skip).limit(limit).all()
    
    async def atualizar(
        self, 
        db: Session, 
        id: int, 
        obj_in: dict
    ) -> Optional[ModelType]:
        """
        Atualiza um registro existente.
        
        Args:
            db: Sessão do banco
            id: ID do registro a atualizar
            obj_in: Dicionário com novos valores
            
        Returns:
            Objeto atualizado ou None se não encontrado
            
        Exemplo:
            solicitacao = await solicitacao_crud.atualizar(
                db,
                id=123,
                {"status": 3, "descricao_admin": "Concluído"}
            )
        """
        # Busca o objeto
        db_obj = await self.obter_por_id(db, id)
        
        if not db_obj:
            return None
        
        # Atualiza cada campo
        for campo, valor in obj_in.items():
            setattr(db_obj, campo, valor)
        
        # Confirma
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    async def deletar(self, db: Session, id: int) -> bool:
        """
        Deleta um registro.
        
        Args:
            db: Sessão do banco
            id: ID do registro a deletar
            
        Returns:
            True se deletou, False se não encontrado
            
        Exemplo:
            foi_deletado = await solicitacao_crud.deletar(db, id=123)
        """
        db_obj = await self.obter_por_id(db, id)
        
        if not db_obj:
            return False
        
        db.delete(db_obj)
        db.commit()
        
        return True
    
    async def contar(self, db: Session) -> int:
        """
        Conta quantos registros existem.
        
        Args:
            db: Sessão do banco
            
        Returns:
            Total de registros
            
        Exemplo:
            total_solicitacoes = await solicitacao_crud.contar(db)
        """
        return db.query(self.modelo).count()
