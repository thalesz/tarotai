from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from typing import Optional, List
from datetime import datetime
from app.core.base import Base  # Importando o Base correto


class ReadingStyleModel(Base, SQLModel, table=True):
    __tablename__ = "reading_style"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    description: Optional[str] = None