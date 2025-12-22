# ============================================================================
# fotos.py - ROTAS DE UPLOAD DE FOTOS (AJUSTADO PARA SEU MODELO)
# ============================================================================
# Arquivo: backend/app/routes/fotos.py
# Ajustado para usar: solicitacao_id, caminho_arquivo, tamanho (bytes)
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Header, File, UploadFile
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from database.connection import obter_conexao
from app.models import Solicitacao, Foto
from app.utils.security import extrair_user_id_do_token
from app.utils.image_processor import (
    processar_imagem_upload,
    validar_arquivo_imagem,
    deletar_imagem
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# UPLOAD DE FOTO
# ============================================================================

@router.post("/api/solicitacoes/{solicitacao_id}/fotos", tags=["Fotos"])
async def upload_foto(
    solicitacao_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """
    Faz upload de foto para solicitação
    - Máximo 5 fotos por solicitação
    - Formatos: JPEG, PNG
    - Tamanho: 10 MB
    - EXIF removido automaticamente
    """
    
    # Extrair token
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    user_id = extrair_user_id_do_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # Verificar solicitação (usa Solicitacao)
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # Verificar permissão
    if solicitacao.usuario_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para adicionar fotos"
        )
    
    # Validar arquivo
    valido, msg = validar_arquivo_imagem(arquivo)
    if not valido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Verificar limite (máximo 5)
    count = db.query(Foto).filter_by(solicitacao_id=solicitacao_id).count()
    if count >= 5:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Limite de 5 fotos atingido"
        )
    
    # Processar imagem
    caminho = processar_imagem_upload(arquivo, solicitacao_id)
    if not caminho:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar imagem"
        )
    
    # Salvar no banco
    try:
        # Obter tamanho do arquivo em bytes
        import os
        tamanho_bytes = os.path.getsize(caminho)
        
        # Obter tipo MIME
        tipo_mime = arquivo.content_type
        
        # Calcular ordem (próxima posição)
        proxima_ordem = count + 1
        
        nova_foto = Foto(
            solicitacao_id=solicitacao_id,
            caminho_arquivo=caminho,
            tamanho=tamanho_bytes,
            tipo_mime=tipo_mime,
            ordem=proxima_ordem,
            criado_em=datetime.now()
        )
        db.add(nova_foto)
        db.commit()
        db.refresh(nova_foto)
        
        logger.info(f"✅ Foto salva: ID {nova_foto.id}")
        
        return {
            "id": nova_foto.id,
            "solicitacao_id": solicitacao_id,
            "caminho_arquivo": caminho,
            "tamanho": tamanho_bytes,
            "tipo_mime": tipo_mime,
            "ordem": proxima_ordem,
            "message": "Foto enviada com sucesso"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar: {str(e)}")
        deletar_imagem(caminho)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar foto"
        )

# ============================================================================
# LISTAR FOTOS
# ============================================================================

@router.get("/api/solicitacoes/{solicitacao_id}/fotos", tags=["Fotos"])
def listar_fotos(
    solicitacao_id: int,
    db: Session = Depends(obter_conexao)
):
    """Lista todas as fotos de uma solicitação"""
    
    # Verificar solicitação
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # Listar fotos ordenadas por ordem
    fotos = db.query(Foto).filter_by(solicitacao_id=solicitacao_id).order_by(Foto.ordem).all()
    
    return fotos

# ============================================================================
# DELETAR FOTO
# ============================================================================

@router.delete("/api/solicitacoes/{solicitacao_id}/fotos/{foto_id}", tags=["Fotos"])
def deletar_foto(
    solicitacao_id: int,
    foto_id: int,
    db: Session = Depends(obter_conexao),
    authorization: str = Header(None)
):
    """Deleta uma foto"""
    
    # Extrair token
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    user_id = extrair_user_id_do_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # Verificar solicitação
    solicitacao = db.query(Solicitacao).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # Verificar permissão
    if solicitacao.usuario_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    # Buscar foto
    foto = db.query(Foto).filter_by(id=foto_id, solicitacao_id=solicitacao_id).first()
    if not foto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foto não encontrada"
        )
    
    # Deletar arquivo
    deletar_imagem(foto.caminho_arquivo)
    
    # Deletar registro
    db.delete(foto)
    db.commit()
    
    logger.info(f"✅ Foto {foto_id} deletada")
    
    return {"message": "Foto deletada com sucesso"}

# ============================================================================
# FIM
# ============================================================================