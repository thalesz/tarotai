from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Integer, ARRAY
from typing import List, Optional
from app.core.base import Base  # Importando o Base correto


class UserTypeModel(Base, SQLModel, table=True):
    __tablename__ = "user_type"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(sa_column=Column(String(50), nullable=False))
    accessible_card_type_ids: Optional[List[int]] = Field(
        sa_column=Column(ARRAY(Integer), nullable=True)
    )
    # deck_avaliable: list = Field(default=None, sa_column=Column(ARRAY(Integer), nullable=True))
    token_amount: int = Field(default=0, sa_column=Column(Integer, nullable=False))

    class Config:
        arbitrary_types_allowed = True