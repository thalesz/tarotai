from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from typing import Optional, List
from datetime import datetime
from app.core.base import Base  # Importando o Base correto


class ReviewModel(Base, SQLModel, table=True):
    __tablename__ = "review"
    id: Optional[int] = Field(default=None, primary_key=True)
    user: int = Field(nullable=False)
    draw: int = Field(nullable=False)  # Referência ao sorteio/draw realizado
    rating: int = Field(nullable=False, ge=1, le=5)  # Nota de 1 a 5
    comment: Optional[str] = Field(default=None)  # Comentário do usuário
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False), default_factory=datetime.now)
