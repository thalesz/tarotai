
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.sql import text  # Import text from sqlalchemy
from app.basic.zodiac import signos  # Importando a lista de planetas
from app.models.zodiac import ZodiacModel # Importando o PlanetModel do modelo
class ZodiacSchemaBase(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True  # Allows arbitrary types like SQLAlchemy's DateTime
        validate_assignment = True
    
    @staticmethod
    async def get_zodiac_name_by_id(session, zodiac_id: int):
        """
        Retrieves the name of a zodiac by its ID.
        """
        result = await session.execute(
            text("SELECT name FROM zodiac WHERE id = :id"),
            {"id": zodiac_id}
        )
        zodiac_name = result.scalar()
        return zodiac_name  
    
    @staticmethod
    async def get_zodiac_id_by_name(session, zodiac_name: str):
        """
        Retrieves the ID of a zodiac by its name.
        """
        result = await session.execute(
            text("SELECT id FROM zodiac WHERE name = :name"),
            {"name": zodiac_name}
        )
        zodiac_id = result.scalar()
        return zodiac_id
        
    @staticmethod
    async def sync_zodiacs(session):
        """
        Synchronizes the zodiacs in the database with the predefined list.
        """

        # Insert new planets if they do not already exist
        for signo in signos:
            existing = await session.execute(
                text("SELECT id FROM zodiac WHERE id = :id"),
                {"id": signo["id"]}
            )
            if not existing.scalar():
                new_signo = ZodiacModel(
                    id=signo["id"],
                    name=signo["name"],
                    description=signo.get("description", "")
                )
                session.add(new_signo)
                await session.flush()  # Ensure the new signo is written to the DB
        await session.commit()

class PlanetSchema(ZodiacSchemaBase):
    id: int
    name: str
    description: str
