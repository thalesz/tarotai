from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from typing import Optional, List
from datetime import datetime
from app.core.base import Base  # Importando o Base correto


class DailyLuckyModel(Base, SQLModel, table=True):
    __tablename__ = "daily_lucky"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(nullable=False)
    reading: Optional[str] = None
    status_id: int = Field(nullable=False)
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    used_at: Optional[datetime] = Field(sa_column=Column(DateTime, nullable=True))
