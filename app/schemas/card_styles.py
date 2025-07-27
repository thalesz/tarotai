from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  # <-- Add this import
from sqlalchemy.exc import IntegrityError  # Import IntegrityError for exception handling
from app.basic.card_style import card_styles  # Assuming this is the correct import path for your card styles

from app.models.card_styles import CardStyleModel  # Importing the CardStyleModel
class CardStylesSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True
    
    @staticmethod
    async def get_all_card_styles(session: AsyncSession) -> list:
        """
        Retorna todos os estilos de cartas disponíveis.
        """
        result = await session.execute(select(CardStyleModel))
        return result.scalars().all()
        
    @staticmethod
    async def sync_card_styles(session: AsyncSession):
        for card in card_styles:
            # print(f"Processing card: {card}")  # Debug print to inspect card data
            result = await session.execute(
                select(CardStyleModel).where(CardStyleModel.id == card["id"])
            )
            existing = result.scalars().first()
            # print(f"Existing card in database: {existing}")  # Debug print to inspect existing data

            if not existing:
                new_card = CardStyleModel(
                    id=card["id"],
                    name=card["name"],
                    description=card.get("description"),
                )
                session.add(new_card)
                try:
                    await session.commit()
                    print(f'Card Style "{card["name"]}" adicionado.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Erro ao adicionar "{card["name"]}". Conflito de integridade.')
            else:
                print(f'Card Style "{card["name"]}" já existe no banco.')
    async def get_card_style_name_by_id(session: AsyncSession, card_style_id: int) -> str:
        """
        Retorna o nome do estilo de carta pelo ID.
        """
        result = await session.execute(
            select(CardStyleModel.name).where(CardStyleModel.id == card_style_id)
        )
        card_style_name = result.scalar_one_or_none()
        
        if not card_style_name:
            raise ValueError(f"Estilo de carta com ID {card_style_id} não encontrado.")
        
        return card_style_name

class CardStylesSchema(CardStylesSchemaBase):
    id: int
    name: str
    description: str = None

