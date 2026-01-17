# backend/app/utils/enums.py

"""
Enums centralizados do sistema Connect Cidade

Fonte única de verdade para valores constantes:
- Status de solicitações
- Tipos de usuário
- Etc.
"""

from enum import Enum as PyEnum
class StatusSolicitacaoEnum(PyEnum):
    """
    Enum para status da solicitação: estados possíveis.
    
    Valores são STRINGS, não integers.
    Exemplo: StatusSolicitacaoEnum.PENDENTE.value == "PENDENTE"
    """
    
    PENDENTE = "PENDENTE"
    EM_ANALISE = "EM_ANALISE"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    RESOLVIDO = "RESOLVIDO"
    CANCELADO = "CANCELADO"
    
    @property
    def label(self) -> str:
        """
        Retorna label amigável do status para exibição ao usuário em português.
        
        Exemplo:
            StatusSolicitacaoEnum.EM_ANDAMENTO.label → "Em andamento"
        """
        labels = {
            "PENDENTE": "Pendente",
            "EM_ANALISE": "Em análise",
            "EM_ANDAMENTO": "Em andamento",
            "RESOLVIDO": "Resolvido",
            "CANCELADO": "Cancelado"
        }
        return labels.get(self.value, "Desconhecido")
    
    @classmethod
    def from_name(cls, name: str):
        """
        Converte NAME (string uppercase) para ENUM.
        
        Args:
            name: Nome do enum (ex: "EM_ANDAMENTO")
        
        Returns:
            StatusSolicitacaoEnum correspondente
        
        Raises:
            ValueError: Se nome não existe
        
        Exemplo:
            status = StatusSolicitacaoEnum.from_name("EM_ANDAMENTO")
            # → StatusSolicitacaoEnum.EM_ANDAMENTO
        """
        try:
            return cls[name]
        except KeyError:
            valid_names = ", ".join([s.name for s in cls])
            raise ValueError(
                f"Status '{name}' não existe. "
                f"Válidos: {valid_names}"
            )
    
    @classmethod
    def from_value(cls, value: str):
        """
        Converte VALUE (string do BD ou API) para ENUM.
        
        Args:
            value: Valor da string (ex: "EM_ANDAMENTO")
        
        Returns:
            StatusSolicitacaoEnum correspondente
        
        Raises:
            ValueError: Se valor não existe
        
        Exemplo:
            status = StatusSolicitacaoEnum.from_value("EM_ANDAMENTO")
            # → StatusSolicitacaoEnum.EM_ANDAMENTO
        """
        try:
            return cls(value)
        except ValueError:
            valid_values = ", ".join([s.value for s in cls])
            raise ValueError(
                f"Status '{value}' não existe. "
                f"Válidos: {valid_values}"
            )
    
    @classmethod
    def get_all_values(cls) -> list:
        """
        Retorna lista de todos os valores válidos.
        
        Returns:
            Lista de strings: ["PENDENTE", "EM_ANALISE", ...]
        
        Exemplo:
            valores = StatusSolicitacaoEnum.get_all_values()
            # → ["PENDENTE", "EM_ANALISE", "EM_ANDAMENTO", "RESOLVIDO", "CANCELADO"]
        """
        return [s.value for s in cls]


class TipoUsuarioEnum(PyEnum):
    """Enum para tipo de usuário: cidadão ou administrador."""
    
    CIDADAO = "CIDADAO"
    ADMINISTRADOR = "ADMINISTRADOR"
    
    @classmethod
    def from_name(cls, name: str):
        """Converte NAME (string) para ENUM."""
        try:
            return cls[name]
        except KeyError:
            raise ValueError(f"Tipo de usuário '{name}' não existe")
    
    @classmethod
    def from_value(cls, value: str):
        """Converte VALUE (string) para ENUM."""
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Tipo de usuário '{value}' não existe")
