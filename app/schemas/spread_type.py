from pydantic import BaseModel
from app.models.spread_types import SpreadTypeModel  # Import the SpreadTypeModel
from sqlalchemy import select  # Import the select function
from sqlalchemy.ext.asyncio import AsyncSession  # Import AsyncSession
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
from app.basic.spread_type import spread_types

class SpreadTypeSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
        
    @staticmethod
    async def get_spread_type_name_by_id(
        session: AsyncSession, spread_type_id: int
    ) -> str | None:
        """
        Get the name of a spread type by its ID.
        """
        query = select(SpreadTypeModel.name).where(SpreadTypeModel.id == spread_type_id)
        result = await session.execute(query)
        spread_type_name = result.scalar_one_or_none()

        if spread_type_name is None:
            raise ValueError(f"Spread type with ID {spread_type_id} does not exist.")

        return spread_type_name
        
    @staticmethod
    async def get_card_count(session, spread_type_id: int) -> int:
        """
        Get the card count for a specific spread type.
        """
        query = select(SpreadTypeModel.card_count).where(SpreadTypeModel.id == spread_type_id)
        result = await session.execute(query)
        card_count = result.scalar_one_or_none()

        if card_count is None:
            raise ValueError(f"Spread type with ID {spread_type_id} does not exist.")

        return card_count
    
    @staticmethod
    async def spread_type_exists(db, spread_type_id: int) -> bool:
        """
        Check if a spread type exists in the database.
        """
        query = select(SpreadTypeModel).where(SpreadTypeModel.id == spread_type_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        return user is not None
        
    @staticmethod
    async def get_all_spread_types(session):
        """
        Returns all spread types from the database.
        """
        result = await session.execute(
            select(SpreadTypeModel).order_by(SpreadTypeModel.id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def sync_spread_types(session: AsyncSession):
        for spread_type in spread_types:
            result = await session.execute(
                select(SpreadTypeModel).where(SpreadTypeModel.id == spread_type["id"])
            )
            existing = result.scalars().first()

            if not existing:
                new_spread_type = SpreadTypeModel(
                    id=spread_type["id"],
                    name=spread_type["name"],
                    description=spread_type.get("description"),
                    card_count=spread_type["card_count"]
                )
                session.add(new_spread_type)
                try:
                    await session.commit()
                    print(f'Spread type "{spread_type["name"]}" added.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Error adding "{spread_type["name"]}". Integrity conflict.')
            else:
                print(f'Spread type "{spread_type["name"]}" already exists in the database.')

class SpreadTypeSchema(SpreadTypeSchemaBase):
    """
    Schema for SpreadType.
    """
    id: int
    name: str
    description: str | None = None
    card_count: int
