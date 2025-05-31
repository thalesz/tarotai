from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Enum as SQLEnum, ARRAY
from app.core.base import Base  # Certifique-se que isso herda de declarative_base
import enum


class TransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    REWARD = "reward"
    DAILY_LOGIN = "daily_login"  # Exemplo adicional


class TransactionModel(Base, SQLModel, table=True):
    __tablename__ = "transaction"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False)
    )

    draws: List[int] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(Integer), nullable=False)
    )

    transaction_type: TransactionType = Field(
        sa_column=Column(SQLEnum(TransactionType), nullable=False)
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, default=datetime.now)
    )
    status: int = Field(
        sa_column=Column(Integer, nullable=False, default=1)  # 1 for active
    )
    #opcional evento
    event: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("event.id"), nullable=True)
    )



    class Config:
        arbitrary_types_allowed = True
