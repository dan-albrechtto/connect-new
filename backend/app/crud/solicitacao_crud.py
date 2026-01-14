# backend/app/crud/solicitacao_crud.py

"""
CRUD de Solicitação

Operações de banco para solicitações:
- Criar com foto
- Atualizar status
- Buscar por localização (para deduplica no mapa)
- Filtrar por status
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.models.solicitacao import Solicitacao
from app.crud.base import CRUDBase


class SolicitacaoCRUD(CRUDBase[Solicitacao]):
    """
    CRUD específico para Solicitação.
    
    Herda de CRUDBase:
    - criar(db, obj_in)
    - obter_por_id(db, id)
    - obter_todos(db, skip, limit)
    - atualizar(db, id, obj_in)
    - deletar(db, id)
    - contar(db)
    
    Adiciona operações específicas de solicitação.
    """
    
    async def criar_com_foto(
        self,
        db: Session,
        usuario_id: int,
        categoria_id: int,
        latitude: float,
        longitude: float,
        descricao: str,
        caminho_foto: str
    ) -> Solicitacao:
        """
        Cria uma solicitação com foto.
        
        Esta é a operação principal quando cidadão reporta um problema.
        
        Args:
            db: Sessão do banco
            usuario_id: ID do cidadão que reporta
            categoria_id: ID da categoria (1=Lixo, 2=Iluminação, etc)
            latitude: Latitude do local
            longitude: Longitude do local
            descricao: Descrição do problema
            caminho_foto: Caminho da foto salva (ex: "storage/fotos/123/foto_2026-01-14.jpg")
        
        Returns:
            Solicitação criada com ID gerado
        
        Exemplo:
            solicitacao = await solicitacao_crud.criar_com_foto(
                db,
                usuario_id=5,
                categoria_id=1,
                latitude=-23.5505,
                longitude=-46.6333,
                descricao="Muita lixo acumulado na rua",
                caminho_foto="storage/fotos/999/foto_2026-01-14.jpg"
            )
        """
        
        # Status inicial: PENDENTE (valor 1)
        from app.utils.enums import StatusSolicitacaoEnum
        
        solicitacao_data = {
            "usuario_id": usuario_id,
            "categoria_id": categoria_id,
            "status": StatusSolicitacaoEnum.PENDENTE.value,  # 1
            "latitude": latitude,
            "longitude": longitude,
            "descricao": descricao,
            "caminho_foto": caminho_foto
        }
        
        # Usa o método genérico de criar
        return await self.criar(db, solicitacao_data)
    
    async def buscar_por_localizacao(
        self,
        db: Session,
        categoria_id: int,
        latitude: float,
        longitude: float,
        raio_km: float = 0.1
    ) -> list:
        """
        Busca solicitações próximas (deduplica no mapa).
        
        Quando cidadão abre o mapa, você busca se já há solicitações
        daquela CATEGORIA naquele LOCAL para evitar duplicatas.
        
        Args:
            db: Sessão do banco
            categoria_id: ID da categoria (mesma que o cidadão quer reportar)
            latitude: Latitude do local
            longitude: Longitude do local
            raio_km: Raio de busca em km (default 0.1 = 100m)
        
        Returns:
            Lista de solicitações próximas (mesma categoria)
        
        Exemplo:
            # Cidadão quer reportar lixo (cat_1) em lat/lon X,Y
            proximas = await solicitacao_crud.buscar_por_localizacao(
                db,
                categoria_id=1,
                latitude=-23.5505,
                longitude=-46.6333,
                raio_km=0.1
            )
            
            if proximas:
                # "Já tem uma solicitação aqui! Quer apoiar?"
            else:
                # "Criar nova solicitação"
        """
        
        # Aqui você usa cálculo de distância (simplificado)
        # Em produção, poderia usar PostGIS do PostgreSQL
        
        from sqlalchemy import and_, func
        
        # Distância simplificada (Haversine)
        # Para produção, use ST_Distance do PostGIS
        
        solicitacoes = db.query(Solicitacao).filter(
            and_(
                Solicitacao.categoria_id == categoria_id,
                # Aqui você adicionaria cálculo de distância
                # Por enquanto, busca na categoria
            )
        ).order_by(desc(Solicitacao.criado_em)).all()
        
        # TODO: Adicionar filtro de distância real
        
        return solicitacoes
    
    async def filtrar_por_status(
        self,
        db: Session,
        status: int,
        limite: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Filtra solicitações por status (para admin ver seu workload).
        
        Args:
            db: Sessão do banco
            status: Valor do status (1=PENDENTE, 2=EM_ANALISE, etc)
            limite: Máximo de resultados
            offset: Para paginação
        
        Returns:
            Dicionário com total e lista de solicitações
        
        Exemplo:
            # Admin quer ver todas PENDENTES
            resultado = await solicitacao_crud.filtrar_por_status(db, status=1)
            # → {"total": 15, "solicitacoes": [...]}
        """
        
        query = db.query(Solicitacao).filter(Solicitacao.status == status)
        
        total = query.count()
        
        solicitacoes = query.order_by(
            desc(Solicitacao.criado_em)
        ).limit(limite).offset(offset).all()
        
        return {
            "total": total,
            "solicitacoes": solicitacoes
        }
    
    async def obter_por_usuario(
        self,
        db: Session,
        usuario_id: int,
        limite: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Lista todas as solicitações de um cidadão (seu histórico).
        
        Args:
            db: Sessão do banco
            usuario_id: ID do cidadão
            limite: Máximo de resultados
            offset: Para paginação
        
        Returns:
            Dicionário com total e lista de solicitações
        
        Exemplo:
            # Cidadão quer ver suas solicitações
            resultado = await solicitacao_crud.obter_por_usuario(db, usuario_id=5)
            # → {"total": 3, "solicitacoes": [...]}
        """
        
        query = db.query(Solicitacao).filter(Solicitacao.usuario_id == usuario_id)
        
        total = query.count()
        
        solicitacoes = query.order_by(
            desc(Solicitacao.criado_em)
        ).limit(limite).offset(offset).all()
        
        return {
            "total": total,
            "solicitacoes": solicitacoes
        }


# ========== INSTÂNCIA GLOBAL ==========
# Você vai usar assim: solicitacao_crud.criar_com_foto(...), solicitacao_crud.filtrar_por_status(...)

solicitacao_crud = SolicitacaoCRUD(Solicitacao)
