from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from app.core.base import Base  # Importando o Base correto
from typing import Optional


class TopicModel(Base, SQLModel, table=True):
    __tablename__ = "topic"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(sa_column=Column(String(100), nullable=False))
    description: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    class Config:
        arbitrary_types_allowed = True