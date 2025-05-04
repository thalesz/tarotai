from pydantic import BaseModel, EmailStr, Field, ValidationError
from fastapi import HTTPException, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.exc import IntegrityError
from app.models.user import UserModel
from app.core.security import pwd_context
from datetime import datetime
from app.models.deck import (
    DeckModel,
)  # Assuming WalletModel is the ORM model for the wallet

from app.basic.deck import decks  # Assuming this is the correct import path for your decks

class DeckSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
        
        
    @staticmethod
    async def get_deck_name_by_id(
        session: AsyncSession, deck_id: int
    ) -> str | None:
        """
        Retorna o nome do deck pelo ID.
        """
        try:
            result = await session.execute(
                select(DeckModel.name).where(DeckModel.id == deck_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao buscar o nome do deck: {str(e)}"
            )

    
    
    @staticmethod
    async def deck_exists(session: AsyncSession, deck_id: int) -> bool:
        """
        Verifica se o deck existe no banco de dados.
        """
        try:
            result = await session.execute(
                select(DeckModel).where(DeckModel.id == deck_id)
            )
            return result.scalars().first() is not None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao verificar a existência do deck: {str(e)}"
            )
    
    @staticmethod
    async def get_all_decks(session: AsyncSession) -> list:
        """
        Retorna somente id e name de todos os decks.
        """
        try:
            decks = await session.execute(select(DeckModel.id, DeckModel.name))
            return decks.all()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao buscar decks: {str(e)}"
            )
    
    @staticmethod
    async def sync_decks(session: AsyncSession):
        for deck in decks:
            result = await session.execute(
                select(DeckModel).where(DeckModel.name == deck["name"])
            )
            existing = result.scalars().first()

            if not existing:
                new_deck = DeckModel(
                    name=deck["name"],
                    description=deck["description"]
                )
                session.add(new_deck)
                try:
                    await session.commit()
                    print(f'Deck "{deck["name"]}" adicionado.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Erro ao adicionar "{deck["name"]}". Conflito de integridade.')
            else:
                print(f'Deck "{deck["name"]}" já existe no banco.')

class DeckSchema(DeckSchemaBase):
    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    name: str = Field(
        sa_column=Column(String(50), nullable=False, unique=True)
    )  # Nome do deck
    description: str = Field(
        sa_column=Column(String(255), nullable=True)
    )  # Descrição do deck
