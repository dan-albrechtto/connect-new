from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from database.connection import Base

# ============================================
# MODELO: Foto
# Tabela: fotos anexadas aos problemas
# Armazena referências aos arquivos de imagem
# ============================================

class Foto(Base):
    # Nome da tabela no PostgreSQL
    __tablename__ = "fotos"
    
    # ========== COLUNAS ==========
    
    # ID: chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # SOLICITACAO_ID: a qual problema esta foto pertence? (chave estrangeira)
    # ondelete="CASCADE" deleta foto se problema for deletado
    solicitacao_id = Column(
        Integer,
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # CAMINHO_ARQUIVO: caminho relativo do arquivo no servidor
    # Ex: "/uploads/2025/01/16/abc123def456.jpg"
    # unique=True garante que o arquivo não está duplicado
    caminho_arquivo = Column(String(500), unique=True, nullable=False)
    
    # TAMANHO: tamanho do arquivo em bytes
    # Util para validar limite de upload
    tamanho = Column(Integer, nullable=False)
    
    # TIPO_MIME: tipo do arquivo (image/jpeg, image/png, etc)
    # Usado para servir arquivo com content-type correto
    tipo_mime = Column(String(50), nullable=False)
    
    # ORDEM: posição da foto (1ª, 2ª, 3ª, etc)
    # Permite ordenar fotos como o usuário fez upload
    ordem = Column(Integer, default=1, nullable=False)
    
    # CRIADO_EM: data/hora do upload automática
    criado_em = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Foto id={self.id} solicitacao={self.solicitacao_id}>"