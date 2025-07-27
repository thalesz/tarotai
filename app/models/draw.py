from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from typing import Optional, List
from datetime import datetime
from app.core.base import Base  # Importando o Base correto


class DrawModel(Base, SQLModel, table=True):
    __tablename__ = "draws"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(nullable=False)
    spread_type_id: int = Field(nullable=False)
    deck_id: Optional[int] = Field(default=None, nullable=True)
    context: Optional[str] = None
    reading: Optional[str] = None
    cards: list = Field(default=None, sa_column=Column(ARRAY(Integer), nullable=True))
    status_id: int = Field(nullable=False)
    topics: list = Field(default=None, sa_column=Column(ARRAY(Integer), nullable=True))
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    used_at: Optional[datetime] = Field(sa_column=Column(DateTime, nullable=True))
    is_reversed: list[bool] = Field(default=None, sa_column=Column(ARRAY(Boolean), nullable=True))
    card_style: Optional[int] = Field(
        default=None, sa_column=Column(Integer, ForeignKey("card_style.id", ondelete="SET NULL"), nullable=True)
    )