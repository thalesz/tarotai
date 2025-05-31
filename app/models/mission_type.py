from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean, Time, DateTime
from app.core.base import Base
from typing import Optional
from datetime import time, datetime


class MissionTypeModel(Base, SQLModel, table=True):
    __tablename__ = "mission_type"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    name: str = Field(sa_column=Column(String(100), nullable=False))
    description: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    
    status: int = Field(
        default=1,
        sa_column=Column(Integer, ForeignKey("status.id"), nullable=False)
    )

    recurrence_type: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True)  # Salva só o ID como inteiro
    )

    recurrence_mode: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True)  # Salva só o ID como inteiro
    )

    reset_time: Optional[time] = Field(
        default=None,
        sa_column=Column(Time, nullable=True)
    )
    expiration_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )
    relative_days: Optional[int] = Field(default=None)
    auto_renew: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False)
    )
    start_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False)
    )
