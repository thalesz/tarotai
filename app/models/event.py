from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, ARRAY, Boolean, Time
from app.core.base import Base  # Importando o Base correto
from typing import Optional, List
from datetime import time

class EventModel(Base, SQLModel, table=True):
    __tablename__ = "event"
    
    class Config:
        arbitrary_types_allowed = True
        
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(
        sa_column=Column(String(100), nullable=False)
    )  # Nome do evento
    description: Optional[str] = Field(
        sa_column=Column(Text, nullable=True)
    )  # Descrição do evento, opcional
    missions: List[int] = Field(
        sa_column=Column(ARRAY(Integer), nullable=False)
    )
    status: int = Field(
        sa_column=Column(Integer, nullable=False)
    )
    created_at: DateTime = Field(
        sa_column=Column(DateTime, nullable=False)
    )  # Data de criação obrigatória
    start_date: DateTime = Field(
        sa_column=Column(DateTime, nullable=False)
    )  # Data de início do evento
    expired_date: Optional[DateTime] = Field(
        sa_column=Column(DateTime, nullable=True)
    )  # Data de expiração do evento, opcional
    gift: List[int] = Field(
        sa_column=Column(ARRAY(Integer), nullable=False)
    )
    user_type:List[int] = Field(
        sa_column=Column(ARRAY(Integer), nullable=False)
    )
    recurrence_type: int = Field(
        sa_column=Column(Integer, nullable=False)
    )  # Tipo de recorrência do evento
    recurrence_mode: int = Field(
        sa_column=Column(Integer, nullable=False)
    )  # Modo de recorrência do evento
    auto_renew: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False)
    )  # Indica se o evento é renovável automaticamente
    reset_time: Optional[time] = Field(
        default=None,
        sa_column=Column(Time, nullable=True)
    ) # Hora de reinício do evento, opcional