from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Enum as SQLEnum, ARRAY
from app.core.base import Base  # Certifique-se que isso herda de declarative_base
import enum

class SubscriptionModel(Base, SQLModel, table=True):
    __tablename__ = "subscription"

    class Config:
        arbitrary_types_allowed = True

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False)
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, default=datetime.now)
    )
    expired_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )
    status: int = Field(
        sa_column=Column(Integer, nullable=False) 
    )



