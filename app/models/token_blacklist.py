from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from app.core.base import Base  # Importando o Base correto
from typing import Optional
from datetime import datetime
from sqlalchemy import DateTime


class TokenBlacklistModel(Base, SQLModel, table=True):
    __tablename__ = "token_blacklist"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    token: str = Field(sa_column=Column(String(500), nullable=False))
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id"), nullable=False))
    used_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=True, default=datetime.now)
    )
    class Config:
        arbitrary_types_allowed = True