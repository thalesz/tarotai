

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
    async def verify_draw_belongs_to_user(
        session, draw_id: int, user_id: int
    ) -> bool:
        """
        Verifica se o draw pertence ao usuário.
        """
        query = text("SELECT COUNT(*) FROM draws WHERE id = :draw_id AND user_id = :user_id")
        result = await session.execute(query, {"draw_id": draw_id, "user_id": user_id})
        count = result.scalar()
        return count > 0
    
    @staticmethod
    async def get_spread_type_id_by_draw_id(
        session, draw_id: int
    ) -> int:
        """
        Recebe o id do draw e retorna o spread_type_id daquele draw.
        """
        query = text("SELECT spread_type_id FROM draws WHERE id = :draw_id")
        result = await session.execute(query, {"draw_id": draw_id})
        row = result.fetchone()
        if row:
            return row[0]
        raise ValueError(f"Draw com ID {draw_id} não encontrado.")
    @staticmethod
    async def update_created_at(
        session, draw_id: int
    ) -> None:
        """
        Update the created_at field of a draw entry in the database.
        """
        try:
            query = text("UPDATE draws SET created_at = :created_at WHERE id = :draw_id")
            await session.execute(query, {"created_at": datetime.now(), "draw_id": draw_id})
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise RuntimeError(f"Failed to update created_at for draw {draw_id}: {e}") from e
    
    @staticmethod
    async def get_draw_status_by_id(session, draw_id: int) -> int:
        """
        Get the status of a draw by its ID.
        """
        query = text("SELECT status_id FROM draws WHERE id = :draw_id")
        result = await session.execute(query, {"draw_id": draw_id})
        row = result.fetchone()
        if row:
            return row[0]
        raise ValueError(f"Draw with ID {draw_id} not found.")
    
    @staticmethod
    async def get_draws_by_user(
        session,
        user_id: int,
        spread_type: int,
        count: int,
        status: int,
        limit: int = 5,
    ) -> list[DrawModel]:
        """
        Get draws for a specific user and spread type, paginated by count.
        For count=1, returns the 5 most recent; for count=2, returns the next 5, etc.
        If no draws are found, returns an empty list.
        """
        offset = (count - 1) * limit

        query = text("""
            SELECT id, deck_id, context, reading, cards, topics, created_at, used_at
            FROM draws
            WHERE user_id = :user_id 
            AND spread_type_id = :spread_type 
            AND status_id = :status_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await session.execute(query, {
            "user_id": user_id,
            "spread_type": spread_type,
            "status_id": status,
            "limit": limit,
            "offset": offset
        })

        rows = result.fetchall()

        if not rows:
            return []

        draws = [
            DrawModel(
                id=row.id,
                deck_id=row.deck_id,
                context=row.context,
                reading=row.reading,
                cards=row.cards,
                topics=row.topics,
                created_at=row.created_at,
                used_at=row.used_at,
            )
            for row in rows
        ]
        return draws

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
                    cards = :cards, 
                    context = :context, 
                    status_id = :status_id, 
                    reading = :reading,
                    topics = :topics,
                    used_at = :used_at
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
    reading_style: int
    
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