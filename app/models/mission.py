from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from app.core.base import Base  # Importando o Base correto
from typing import Optional

class MissionModel(Base, SQLModel, table=True):
    __tablename__ = "mission"
    class Config:
        arbitrary_types_allowed = True
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    mission_type: int = Field(
        sa_column=Column(Integer, nullable=False)
    )
    user: int = Field(
        sa_column=Column(Integer, nullable=False)
    )
    status: int = Field(
        sa_column=Column(Integer, nullable=False)
    )
    created_at: DateTime = Field(
        sa_column=Column(DateTime, nullable=False)
    )  # Data de criação obrigatória
    used_at: DateTime = Field(
        sa_column=Column(DateTime, nullable=True)
    )  # Data de criação obrigatória
