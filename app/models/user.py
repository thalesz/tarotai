from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList, MutableDict
from typing import Optional, List
from app.core.base import Base  # Importando o Base correto

class UserModel(Base, SQLModel, table=True):
    __tablename__ = "users"
    
    class Config:
        arbitrary_types_allowed = True

    id: int = Field(sa_column=Column(Integer, primary_key=True, autoincrement=True))
    username: str = Field(sa_column=Column(String(255), unique=True))
    email: str = Field(sa_column=Column(String(255), unique=True))
    password: str = Field(
        sa_column=Column(String(255), nullable=False)
    )  # Senha com hash
    refresh_token: Optional[List[str]] = Field(
        sa_column=Column(MutableList.as_mutable(ARRAY(String)), nullable=True)
    )  # Lista de strings (ARRAY)
    birth_date: Optional[str] = Field(
        sa_column=Column(String(255), nullable=True)
    )
    birth_time: Optional[str] = Field(
        sa_column=Column(String(255), nullable=True)
    )
    birth_place: Optional[str] = Field(
        sa_column=Column(String(255), nullable=True)
    )
    user_type: int = Field(
        sa_column=Column(Integer, nullable=False)
    )  # Tipo de usuário obrigatório
    full_name: Optional[str] = Field(
        sa_column=Column(String(255), nullable=True)
    )  # Nome completo opcional
    status: str = Field(
        sa_column=Column(String(50), nullable=False)
    )  # Status do usuário obrigatório
    created_at: DateTime = Field(
        sa_column=Column(DateTime, nullable=False)
    )  # Data de criação obrigatória
