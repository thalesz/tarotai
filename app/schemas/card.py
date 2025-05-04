from pydantic import BaseModel, Field
from sqlmodel import SQLModel
from sqlalchemy import Column, String, Integer, Text, ForeignKey, select
from sqlalchemy.exc import IntegrityError
from app.core.base import Base  # Importando o Base correto
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.card import CardModel  # Importing the CardModel

from app.basic.cards import cards  # Assuming this is the correct import path for your cards


class CardSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True
        
        
    @staticmethod
    async def check_cards_belong_to_deck(
        session: AsyncSession, deck_id: int, card_ids: list[int]
    ) -> bool:
        """
        Verifica se todos os cards pertencem ao deck especificado.
        """
        result = await session.execute(
            select(CardModel).where(
                CardModel.deck_id == deck_id, CardModel.id.in_(card_ids)
            )
        )
        cards = result.scalars().all()
        return len(cards) == len(card_ids)
    
    @staticmethod
    async def get_cards_names_by_group_ids(session: AsyncSession, group_ids: list[int]) -> list:
        """
        Retorna todos os  nomes de cards de uma lista de grupos de ids específicos.
        """
        result = await session.execute(
            select(CardModel.name).where(CardModel.id.in_(group_ids))
        )
        return result.scalars().all()
        
    @staticmethod
    async def get_card_by_deck_id(session: AsyncSession, deck_id: int) -> list:
        """
        Retorna todos os cards de um deck específico.
        """
        result = await session.execute(
            select(CardModel).where(CardModel.deck_id == deck_id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_all_cards(session: AsyncSession) -> list:
        """
        Retorna somente id e name de todos os cards.
        """
        cards = await session.execute(select(CardModel.id, CardModel.name))
        return cards.all()
    
    @staticmethod
    async def sync_cards(session: AsyncSession):
        for card in cards:
            # print(f"Processing card: {card}")  # Debug print to inspect card data
            result = await session.execute(
                select(CardModel).where(CardModel.id == card["id"])
            )
            existing = result.scalars().first()
            # print(f"Existing card in database: {existing}")  # Debug print to inspect existing data

            if not existing:
                new_card = CardModel(
                    id=card["id"],
                    name=card["name"],
                    description=card.get("description"),
                    deck_id=card["deck_id"]
                )
                session.add(new_card)
                try:
                    await session.commit()
                    print(f'Card "{card["name"]}" adicionado.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Erro ao adicionar "{card["name"]}". Conflito de integridade.')
            else:
                print(f'Card "{card["name"]}" já existe no banco.')
    


class CardSchema(CardSchemaBase):
    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    name: str = Field(
        sa_column=Column(String(100), nullable=False)
    )  # Nome do card
    description: Optional[str] = Field(
        sa_column=Column(Text, nullable=True)
    )  # Descrição do card
    deck_id: int = Field(
        sa_column=Column(Integer, ForeignKey("deck.id", ondelete="CASCADE"), nullable=False)
    )  # ID do deck associado
