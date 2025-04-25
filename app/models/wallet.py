from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from typing import Optional
from app.core.base import Base  # Importando o Base correto


class WalletModel(Base, SQLModel, table=True):
    __tablename__ = "wallets"

    class Config:
        arbitrary_types_allowed = True

    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    )  # Relacionamento 1-1 com UserModel
    balance: float = Field(
        sa_column=Column(Float, nullable=False, default=0.0)
    )  # Saldo da carteira
    created_at: Optional[DateTime] = Field(
        sa_column=Column(DateTime, server_default=func.now())
    )  # Data de criação
    currency: str = Field(
        sa_column=Column(String(10), nullable=False, default="BRL")
    )  # Moeda padrão (BRL é o padrão)
    status: int = Field(
        sa_column=Column(Integer, nullable=False, default=1)
    )  # Status da carteira agora como ID
