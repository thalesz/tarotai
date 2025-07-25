from pydantic import BaseModel
from app.models.reading_style import ReadingStyleModel  # Import the ReadingStyleModel
from sqlalchemy import select  # Import the select function
from sqlalchemy.ext.asyncio import AsyncSession  # Import AsyncSession
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
from app.basic.reading_style import reading_styles

class ReadingStyleSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
        
    @staticmethod
    async def get_all_reading_styles(session: AsyncSession) -> list:
        """
        Retrieve all reading styles from the database.
        """
        result = await session.execute(select(ReadingStyleModel))
        return result.scalars().all()
        
    @staticmethod
    async def get_id_by_name(session: AsyncSession, reading_style_name: str) -> int:
        """
        Retrieve the ID of a reading style by its name.
        """
        result = await session.execute(
            select(ReadingStyleModel.id).where(ReadingStyleModel.name == reading_style_name)
        )
        reading_style_id = result.scalars().first()
        return reading_style_id if reading_style_id else None

    @staticmethod
    async def get_reading_style_description_by_id(
        session: AsyncSession, reading_style_id: int
    ) -> str:
        """
        Retrieve the description of a reading style by its ID.
        """
        result = await session.execute(
            select(ReadingStyleModel.description).where(ReadingStyleModel.id == reading_style_id)
        )
        reading_style_description = result.scalars().first()
        return reading_style_description if reading_style_description else None
    
    @staticmethod
    async def get_reading_style_name_by_id(session: AsyncSession, reading_style_id: int) -> str:
        """
        Retrieve the name of a reading style by its ID.
        """
        result = await session.execute(
            select(ReadingStyleModel.name).where(ReadingStyleModel.id == reading_style_id)
        )
        reading_style_name = result.scalars().first()
        return reading_style_name if reading_style_name else None
    
    @staticmethod
    async def get_reading_style_by_id(session: AsyncSession, reading_style_id: int) -> dict:
        """
        Retrieve a reading style by its ID.
        """
        result = await session.execute(
            select(ReadingStyleModel).where(ReadingStyleModel.id == reading_style_id)
        )
        reading_style = result.scalars().first()
        return reading_style if reading_style else None
    
    @staticmethod
    async def sync_reading_styles(session: AsyncSession) -> None:
        """
        Synchronize the reading styles with the predefined styles.
        """
        for style in reading_styles:
            result = await session.execute(
                select(ReadingStyleModel).where(ReadingStyleModel.name == style["name"])
            )
            existing = result.scalars().first()

            if not existing:
                new_reading_style = ReadingStyleModel(
                    name=style["name"],
                    description=style["description"]
                )
                session.add(new_reading_style)
                try:
                    await session.commit()
                    print(f'Reading style "{style['name']}" added.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Error adding "{style["name"]}". Integrity conflict.')
            else:
                print(f'Reading style "{style["name"]}" already exists in the database.')


class ReadingStyleSchema(ReadingStyleSchemaBase):

    id: int
    name: str
    description: str
    
