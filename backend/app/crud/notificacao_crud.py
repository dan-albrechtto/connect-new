# backend/app/crud/notificacao_crud.py

"""
CRUD de Notificação

Operações de banco para notificações:
- Criar
- Listar
- Marcar como lida
- Deletar
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.models.notificacao import Notificacao
from app.crud.base import CRUDBase


class NotificacaoCRUD(CRUDBase[Notificacao]):
    """
    CRUD específico para Notificação.
    
    Herda métodos genéricos de CRUDBase:
    - criar()
    - obter_por_id()
    - atualizar()
    - deletar()
    
    Adiciona operações específicas:
    - listar_usuario_nao_lidas()
    - contar_nao_lidas()
    - marcar_como_lida()
    """
    
    async def listar_usuario_nao_lidas(
        self,
        db: Session,
        usuario_id: int,
        limite: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Lista notificações NÃO-LIDAS de um usuário (para o sininho).
        
        Args:
            db: Sessão do banco
            usuario_id: ID do usuário
            limite: Máximo de resultados (default 50)
            offset: Para paginação (default 0)
        
        Returns:
            Dicionário com:
            - total: Total de registros não-lidos
            - notificacoes: Lista de notificações
        
        Exemplo:
            resultado = await notificacao_crud.listar_usuario_nao_lidas(db, usuario_id=5)
            # → {"total": 3, "notificacoes": [...]}
        """
        
        # Query: buscar não-lidas de um usuário
        query = db.query(Notificacao).filter(
            and_(
                Notificacao.usuario_id == usuario_id,
                Notificacao.lida == False
            )
        )
        
        # Total
        total = query.count()
        
        # Buscar com paginação (mais recentes primeiro)
        notificacoes = query.order_by(
            desc(Notificacao.criado_em)
        ).limit(limite).offset(offset).all()
        
        return {
            "total": total,
            "notificacoes": notificacoes
        }
    
    async def contar_nao_lidas(self, db: Session, usuario_id: int) -> int:
        """
        Conta quantas notificações NÃO-LIDAS o usuário tem (para badge do sininho).
        
        Args:
            db: Sessão do banco
            usuario_id: ID do usuário
        
        Returns:
            Número inteiro de notificações não-lidas
        
        Exemplo:
            count = await notificacao_crud.contar_nao_lidas(db, usuario_id=5)
            # → 3
        """
        
        return db.query(Notificacao).filter(
            and_(
                Notificacao.usuario_id == usuario_id,
                Notificacao.lida == False
            )
        ).count()
    
    async def marcar_como_lida(
        self,
        db: Session,
        notificacao_id: int,
        usuario_id: int
    ) -> Notificacao:
        """
        Marca uma notificação específica como lida.
        
        Valida que a notificação pertence ao usuário (segurança).
        
        Args:
            db: Sessão do banco
            notificacao_id: ID da notificação
            usuario_id: ID do usuário (para validação)
        
        Returns:
            Notificação atualizada ou None se não encontrado
        
        Exemplo:
            notif = await notificacao_crud.marcar_como_lida(
                db,
                notificacao_id=42,
                usuario_id=5
            )
        """
        
        # Busca validando que pertence ao usuário
        notificacao = db.query(Notificacao).filter(
            and_(
                Notificacao.id == notificacao_id,
                Notificacao.usuario_id == usuario_id
            )
        ).first()
        
        if not notificacao:
            return None
        
        # Marca como lida
        notificacao.lida = True
        db.add(notificacao)
        db.commit()
        db.refresh(notificacao)
        
        return notificacao
    
    async def marcar_todas_como_lidas(
        self,
        db: Session,
        usuario_id: int
    ) -> int:
        """
        Marca TODAS as notificações não-lidas como lidas de uma vez.
        
        Args:
            db: Sessão do banco
            usuario_id: ID do usuário
        
        Returns:
            Quantidade de notificações marcadas como lidas
        
        Exemplo:
            qtd = await notificacao_crud.marcar_todas_como_lidas(db, usuario_id=5)
            # → 3
        """
        
        # Atualiza todas não-lidas
        quantidade = db.query(Notificacao).filter(
            and_(
                Notificacao.usuario_id == usuario_id,
                Notificacao.lida == False
            )
        ).update({Notificacao.lida: True})
        
        db.commit()
        
        return quantidade


# ========== INSTÂNCIA GLOBAL ==========
# Você vai usar assim: notificacao_crud.criar(...), notificacao_crud.listar_usuario_nao_lidas(...)

notificacao_crud = NotificacaoCRUD(Notificacao)
