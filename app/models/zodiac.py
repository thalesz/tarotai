from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String,Text
from app.core.base import Base  # Importando o Base correto
from typing import Optional


class ZodiacModel(Base, SQLModel, table=True):
    __tablename__ = "zodiac"
    class Config:
        arbitrary_types_allowed = True  
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(
        sa_column=Column(String(100), nullable=False)
    )  # Nome do mapa
    description: Optional[str] = Field(
        sa_column=Column(Text, nullable=True)
    )  # Descrição do mapa, opcional