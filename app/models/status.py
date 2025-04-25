from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer
from sqlalchemy.sql import func
from typing import Optional
from app.core.base import Base  # Importando o Base correto


class StatusModel(Base, SQLModel, table=True):
    __tablename__ = "status"

    class Config:
        arbitrary_types_allowed = True

    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    name: str = Field(
        sa_column=Column(String(50), nullable=False)
    )  # Nome do deck
    label: Optional[str] = Field(
        sa_column=Column(String(50), nullable=True)
    )  # Descrição do deck