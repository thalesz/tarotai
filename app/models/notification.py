from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, DateTime
from app.core.base import Base  # seu Base customizado
from typing import Optional
from datetime import datetime

class Notification(Base, SQLModel, table=True):
    __tablename__ = "notification"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user: int = Field(sa_column=Column(Integer, nullable=False))
    status: int = Field(sa_column=Column(Integer, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    read_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    message: str = Field(sa_column=Column(String, nullable=False))
