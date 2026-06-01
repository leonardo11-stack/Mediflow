from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Prioridade(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"


class TriagemCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    idade: int = Field(..., ge=0, le=150)
    sintomas: str = Field(..., min_length=1)
    observacoes: str | None = None


class TriagemAIResponse(BaseModel):
    prioridade: Prioridade
    resumo_clinico: str
    possiveis_causas: list[str]
    medicamentos_iniciais: list[str]


class TriagemResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    idade: int
    sintomas: str
    observacoes: str | None
    prioridade: Prioridade
    resumo_clinico: str
    possiveis_causas: list[str]
    medicamentos_iniciais: list[str]
    criado_em: datetime

    model_config = {"from_attributes": True}
