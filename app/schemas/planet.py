
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.sql import text  # Import text from sqlalchemy
from app.basic.planet import planets
from app.models.planet import PlanetModel  # Importando o PlanetModel do modelo

class PlanetSchemaBase(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True  # Allows arbitrary types like SQLAlchemy's DateTime
        validate_assignment = True
    
    @staticmethod   
    async def get_planet_name_by_id(session, planet_id: int):
        """
        Retrieves the name of a planet by its ID.
        """
        try:
            result = await session.execute(
                text("SELECT name FROM planet WHERE id = :id"),
                {"id": planet_id}
            )
            row = result.fetchone()
            if row:
                return row[0]
            return None
        except Exception as e:
            print(f"Error retrieving planet name: {e}")
            return None
    @staticmethod
    async def get_all_planets(session):
        """
        Retrieves all planets from the database and returns them in REST-friendly format (list of dicts).
        """
        try:
            result = await session.execute(
                text("SELECT id, name, description FROM planet")
            )
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2]
                } for row in rows
            ]
        except Exception as e:
            print(f"Error retrieving planets: {e}")
            return []
    @staticmethod
    async def get_all_planet_ids_and_names(session):
        """
        Retrieves all planet ids and names from the database.
        """
        result = await session.execute(
            text("SELECT id, name FROM planet")
        )
        return [{"id": row[0], "name": row[1]} for row in result.fetchall()]
        
    @staticmethod
    async def sync_planets(session):
        """
        Synchronizes the planets in the database with the predefined list.
        """
        
        # Insert new planets if they do not already exist
        for planet in planets:
            existing = await session.execute(
            text("SELECT id FROM planet WHERE id = :id"),
            {"id": planet["id"]}
            )
            if not existing.scalar():
                new_planet = PlanetModel(
                    id=planet["id"],
                    name=planet["name"],
                    description=planet.get("description", "")
                )
                session.add(new_planet)
        await session.commit()

class PlanetSchema(PlanetSchemaBase):
    id: int
    name: str
    description: str
