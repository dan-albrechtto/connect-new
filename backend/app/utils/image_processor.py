# ============================================================================
# image_processor.py - PROCESSAMENTO DE IMAGENS
# ============================================================================
# Arquivo: backend/app/utils/image_processor.py
# ============================================================================

import os
from PIL import Image
from io import BytesIO
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Configurações
LARGURA_MAXIMA = 1024
ALTURA_MAXIMA = 768
QUALIDADE_JPEG = 75
PASTA_UPLOADS = "storage/fotos"
FORMATOS_ACEITOS = {"image/jpeg", "image/png", "image/jpg"}
TAMANHO_MAXIMO_MB = 10

# ============================================================================
# VALIDAR ARQUIVO
# ============================================================================

def validar_arquivo_imagem(arquivo_upload) -> tuple:
    """
    Valida se arquivo é imagem válida
    Retorna: (True, "OK") ou (False, "erro")
    """
    # Verificar tipo
    if arquivo_upload.content_type not in FORMATOS_ACEITOS:
        return False, f"Formato não aceito. Use JPEG ou PNG"
    
    # Verificar tamanho
    tamanho_mb = len(arquivo_upload.file.read()) / (1024 * 1024)
    arquivo_upload.file.seek(0)
    
    if tamanho_mb > TAMANHO_MAXIMO_MB:
        return False, f"Arquivo muito grande (máx {TAMANHO_MAXIMO_MB}MB)"
    
    # Verificar se é imagem
    try:
        imagem = Image.open(arquivo_upload.file)
        imagem.verify()
        arquivo_upload.file.seek(0)
        return True, "OK"
    except Exception as e:
        return False, f"Arquivo não é imagem válida: {str(e)}"

# ============================================================================
# REMOVER EXIF
# ============================================================================

def remover_exif(imagem_pil):
    """Remove metadados EXIF da imagem"""
    dados = list(imagem_pil.getdata())
    imagem_limpa = Image.new(imagem_pil.mode, imagem_pil.size)
    imagem_limpa.putdata(dados)
    logger.info("✅ EXIF removido")
    return imagem_limpa

# ============================================================================
# COMPRIMIR IMAGEM
# ============================================================================

def comprimir_imagem(arquivo_upload):
    """Comprime imagem para 1024x768 @ 75% qualidade"""
    try:
        # Abre imagem
        imagem = Image.open(arquivo_upload.file)
        logger.info(f"📸 Imagem aberta: {imagem.size[0]}x{imagem.size[1]}")
        
        # Converte para RGB
        if imagem.mode in ('RGBA', 'LA', 'P'):
            imagem = imagem.convert('RGB')
        
        # Remove EXIF
        imagem = remover_exif(imagem)
        
        # Redimensiona
        imagem.thumbnail((LARGURA_MAXIMA, ALTURA_MAXIMA), Image.Resampling.LANCZOS)
        logger.info(f"📐 Redimensionada para: {imagem.size[0]}x{imagem.size[1]}")
        
        # Comprime
        buffer = BytesIO()
        imagem.save(buffer, format='JPEG', quality=QUALIDADE_JPEG, optimize=True)
        buffer.seek(0)
        
        tamanho_kb = len(buffer.getvalue()) / 1024
        logger.info(f"✅ Comprimida para {tamanho_kb:.2f} KB")
        
        return buffer
        
    except Exception as e:
        logger.error(f"❌ Erro ao comprimir: {str(e)}")
        return None

# ============================================================================
# PROCESSAR E SALVAR
# ============================================================================

def processar_imagem_upload(arquivo_upload, problema_id: int):
    """Processa e salva imagem"""
    try:
        # Valida
        valido, msg = validar_arquivo_imagem(arquivo_upload)
        if not valido:
            logger.error(f"❌ Validação falhou: {msg}")
            return None
        
        # Comprime
        imagem_comprimida = comprimir_imagem(arquivo_upload)
        if imagem_comprimida is None:
            return None
        
        # Cria pasta
        pasta = os.path.join(PASTA_UPLOADS, f"problema_{problema_id}")
        os.makedirs(pasta, exist_ok=True)
        
        # Gera nome único
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
        nome = f"foto_{timestamp}.jpg"
        caminho = os.path.join(pasta, nome)
        
        # Salva
        with open(caminho, 'wb') as f:
            f.write(imagem_comprimida.getvalue())
        
        logger.info(f"✅ Salva em: {caminho}")
        
        return os.path.join(PASTA_UPLOADS, f"problema_{problema_id}", nome)
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar: {str(e)}")
        return None

# ============================================================================
# DELETAR IMAGEM
# ============================================================================

def deletar_imagem(caminho: str) -> bool:
    """Deleta imagem do disco"""
    try:
        if os.path.exists(caminho):
            os.remove(caminho)
            logger.info(f"🗑️ Deletada: {caminho}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Erro ao deletar: {str(e)}")
        return False

# ============================================================================
# FIM
# =========================================================