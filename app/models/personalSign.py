from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Text, ForeignKey, Integer
from app.core.base import Base  # Importando o Base correto
from typing import Optional


class PersonalSign(Base, SQLModel, table=True):
    __tablename__ = "personal_sign"

    class Config:
        arbitrary_types_allowed = True
        
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False)
    )
    planet: int = Field(
        sa_column=Column(Integer, ForeignKey("planet.id"), nullable=False)
    )  # ID do planeta associado ao signo pessoal
    zodiac_sign: int = Field(
        sa_column=Column(Integer, ForeignKey("zodiac.id"), nullable=False)
    )  # ID do signo associado ao signo pessoal
    description: Optional[str] = Field(
        sa_column=Column(Text, nullable=True)
    )  # Descrição do signo pessoal, opcional
    # adiciona o grau
    degree: Optional[float] = Field(
        sa_column=Column(String, nullable=True)
    )  # Grau do signo pessoal, opcional