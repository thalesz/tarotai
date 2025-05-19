

from datetime import datetime
from pydantic import BaseModel
from app.models.draw import DrawModel  # Import DrawsModel and SpreadTypeModel from the appropriate module
from app.schemas.status import StatusSchemaBase  # Import StatusSchemaBase from the appropriate module
from sqlalchemy.sql import text  # Import text from sqlalchemy
from app.models.spread_types import SpreadTypeModel  # Import SpreadTypeModel from the appropriate module

class DrawSchemaBase(BaseModel):
        class Config:
            orm_mode = True
            arbitrary_types_allowed = True  # Allows arbitrary types like SQLAlchemy's DateTime
            validate_assignment = True
            
            
        @staticmethod
        async def update_draw_after_standard_reading(
            session, draw_id: int, user_id: int, spread_type_id: int, deck_id: int, cards: list[int], context: str, status_id: int, reading: str, topics: list[int]
        ) -> None:
            """
            Update the draw entry in the database after a standard reading.
            """
            try:
                query = text(
                    """
                    UPDATE draws
                    SET deck_id = :deck_id, 
                        cards = :cards, context = :context, status_id = :status_id, reading = :reading
                    WHERE id = :draw_id
                    """
                )
                await session.execute(
                    query,
                    {
                        "user_id": user_id,
                        "spread_type_id": spread_type_id,
                        "deck_id": deck_id,
                        "cards": cards,
                        "context": context,
                        "status_id": status_id,
                        "reading": reading,
                        "draw_id": draw_id,
                        "topics": topics,
                        "used_at": datetime.now(),  # Set used_at to the current time
                    },
                )
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Failed to update draw: {e}") from e   
            
        @staticmethod
        async def get_pending_draw_count_by_user_and_spread_type(
            session, user_id: int, spread_type_id: int
        ) -> int:
                """
                Get the count of pending draws for a specific user and spread type.
                """
                status = await StatusSchemaBase.get_id_by_name(session, "pending_confirmation")
                query = text(
                """
                SELECT COUNT(*) FROM draws
                WHERE user_id = :user_id AND spread_type_id = :spread_type_id AND status_id = :status_id
                """
                )
                result = await session.execute(query, {"user_id": user_id, "spread_type_id": spread_type_id, "status_id": status})
                count = result.scalar()
                return count if count else 0    
         
        @staticmethod
        async def get_pending_draw_id_by_user_and_spread_type(
            session, user_id: int, spread_type_id: int
        ) -> int | None:
            """
            Get the ID of a pending draw for a specific user and spread type.
            
            """
            status = await StatusSchemaBase.get_id_by_name(session, "pending_confirmation")
            query = text(
                """
                SELECT id FROM draws
                WHERE user_id = :user_id AND spread_type_id = :spread_type_id AND status_id = :status_id
                """
            )
            result = await session.execute(query, {"user_id": user_id, "spread_type_id": spread_type_id, "status_id": status})
            row = result.fetchone()
            return row[0] if row else None

        @staticmethod
        async def create_draw(session, user_id: int, spread_type_id: int):
            """
            Create a new draw entry in the database.
            """
            try:
            # Get the status ID for "pending_confirmation"
                status = await StatusSchemaBase.get_id_by_name(session, "pending_confirmation")

            # Create a new draw instance
                new_draw = DrawModel(
                    user_id=user_id,
                    spread_type_id=spread_type_id,
                    status_id=status,
                    created_at=datetime.now(),  # Set creation time to the current moment
                )
                session.add(new_draw)
                await session.commit()
                await session.refresh(new_draw)
                return new_draw
            except Exception as e:
                await session.rollback()  # Rollback the transaction in case of an error
                raise RuntimeError(f"Failed to create draw: {e}") from e
            
class DrawCreate(DrawSchemaBase):
    spread_type_id: int

class DrawUpdate(DrawSchemaBase):
    spread_type_id: int
    deck_id: int 
    cards: list[int] 
    context: str 
    
class DrawSchema(DrawSchemaBase):
    id: int
    user_id: int
    spread_type_id: int
    deck_id: int | None = None  # Optional field for deck ID
    context: str | None = None
    reading: str | None = None  # Optional field for the reading
    cards: list[int] | None = None  # Assuming cards is a list of integers
    topics: list[int] | None = None  # Assuming cards is a list of integers
    status_id: int
    created_at: str  # Use str for datetime serialization
    used_at: str | None = None  # Use str for datetime serialization