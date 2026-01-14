from enum import Enum as PyEnum


# ========== ENUMS PYTHON ==========
# Define valores pré-fixos para tipos de usuário e status

class TipoUsuarioEnum(PyEnum):
    """Enum para tipo de usuário: cidadão ou administrador."""
    CIDADAO = 1
    ADMINISTRADOR = 2

    @classmethod
    def from_name(cls, name: str):
        """
        Converte NAME (string) para ENUM.
        
        Útil quando recebe "EM_ANDAMENTO" do Swagger e precisa converter.
        
        Exemplo:
            status_enum = StatusSolicitacaoEnum.from_name("EM_ANDAMENTO")
            # → StatusSolicitacaoEnum.EM_ANDAMENTO
        """
        try:
            return cls[name]
        except KeyError:
            raise ValueError(f"Status '{name}' não existe")
    
    @classmethod
    def from_value(cls, value: int):
        """
        Converte VALUE (int) para ENUM.
        
        Útil quando busca do BD (que armazena int) e precisa de enum.
        
        Exemplo:
            status_enum = StatusSolicitacaoEnum.from_value(3)
            # → StatusSolicitacaoEnum.EM_ANDAMENTO
        """
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Status com valor '{value}' não existe")

class StatusSolicitacaoEnum(PyEnum):
    """Enum para status da solicitação: estados possíveis."""
    PENDENTE = 1           # Acabou de ser criado
    EM_ANALISE = 2         # Admin recebeu e está analisando
    EM_ANDAMENTO = 3       # Setor responsável está trabalhando
    RESOLVIDO = 4          # Problema foi solucionado
    CANCELADO = 5          # Foi cancelado (spam, duplicado, etc)

    @property
    def label(self) -> str:
        """Retorna label amigável do status para exibição ao usuário"""
        labels = {
            1: "Pendente",
            2: "Em análise",
            3: "Em andamento",
            4: "Resolvido",
            5: "Cancelado"
        }
        return labels.get(self.value, "Desconhecido")
    
    @classmethod
    def from_name(cls, name: str):
        """
        Converte NAME (string) para ENUM.
        
        Útil quando Swagger envia "EM_ANDAMENTO" como string.
        
        Exemplo:
            status = StatusSolicitacaoEnum.from_name("EM_ANDAMENTO")
            # → StatusSolicitacaoEnum.EM_ANDAMENTO (value=3)
        """
        try:
            return cls[name]
        except KeyError:
            raise ValueError(f"Status '{name}' não existe. Válidos: {', '.join([s.name for s in cls])}")
    
    @classmethod
    def from_value(cls, value: int):
        """
        Converte VALUE (int) para ENUM.
        
        Útil quando busca do BD que armazena como int.
        
        Exemplo:
            status = StatusSolicitacaoEnum.from_value(3)
            # → StatusSolicitacaoEnum.EM_ANDAMENTO
        """
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Status com valor '{value}' não existe. Válidos: 1-5")