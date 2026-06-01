from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Triagem(Base):
    __tablename__ = "triagens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    idade: Mapped[int] = mapped_column(Integer, nullable=False)
    sintomas: Mapped[str] = mapped_column(Text, nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    prioridade: Mapped[str] = mapped_column(String(10), nullable=False)
    resumo_clinico: Mapped[str] = mapped_column(Text, nullable=False)
    possiveis_causas: Mapped[list] = mapped_column(JSONB, nullable=False)
    medicamentos_iniciais: Mapped[list] = mapped_column(JSONB, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
