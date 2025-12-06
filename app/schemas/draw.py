

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
    async def get_draw_by_id(
        session, draw_id: int
    ) -> DrawModel | None:
        """
        Get a draw by its ID.
        """
        query = text(
            "SELECT * FROM draws WHERE id = :draw_id"
        )
        result = await session.execute(query, {"draw_id": draw_id})
        row = result.fetchone()
        if row:
            row_dict = dict(row._mapping)
            # Garante que listas None sejam convertidas para listas vazias
            if row_dict.get('cards') is None:
                row_dict['cards'] = []
            if row_dict.get('topics') is None:
                row_dict['topics'] = []
            if row_dict.get('is_reversed') is None:
                row_dict['is_reversed'] = []
            return DrawModel(**row_dict)
        return None
    
    
    @staticmethod
    async def get_user_contexts(
        session, user_id: int, count: int = 10
    ) -> list[str]:
        """
        Get the most recent `count` contexts given by the user.
        """
        query = text(
            "SELECT context FROM draws WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :count"
        )
        result = await session.execute(query, {"user_id": user_id, "count": count})
        rows = result.fetchall()
        return [row.context for row in rows] if rows else []
    
    @staticmethod
    async def get_draw_details_by_id(
        session, draw_id: int
    ) -> dict | None:
        """
            Recebe o draw_id e retorna as cartas, a leitura, o deck_id e o spread_type_id da própria tabela draws.
            """
        query = text("""
                SELECT 
                cards, 
                reading, 
                deck_id, 
                spread_type_id,
                is_reversed
                FROM draws
                WHERE id = :draw_id
            """)    
        result = await session.execute(query, {"draw_id": draw_id})
        row = result.fetchone()
        if row:
            return {
                "cards": row.cards,
                "reading": row.reading,
                "deck_id": row.deck_id,
                "spread_type_id": row.spread_type_id,
                "is_reversed": row.is_reversed
            }
        return None

    @staticmethod
    async def get_context_by_id(
        session, draw_id: int
    ) -> str | None:
        """
        Get the context of a draw by its ID.
        """
        query = text("SELECT context FROM draws WHERE id = :draw_id")
        result = await session.execute(query, {"draw_id": draw_id})
        row = result.fetchone()
        if row:
            return row[0]
        return None

    @staticmethod
    async def get_draw_ids_by_topics(
        session,
        user_id: int,
        topics: list[int],
        spread_type_id: int | None = None,
        limit: int = 5,
        ) -> list[int]:
        """
        Get draw IDs for a specific user, optionally filtered by spread type, filtered by topics.
        Returns the most recent draw IDs up to the specified limit.
        At least one topic must match, but not necessarily all.
        If only one draw matches, return just that one.
        """
        if not topics:
            return []
        base_query = """
                    SELECT id
                    FROM draws
                    WHERE user_id = :user_id 
                    AND topics && :topics
                    """
        params = {
                    "user_id": user_id,
                    "topics": topics,
                    "limit": limit
                }
        if spread_type_id is not None:
                    base_query += " AND spread_type_id = :spread_type_id"
                    params["spread_type_id"] = spread_type_id
        
        base_query += " ORDER BY created_at DESC LIMIT :limit"
        
        query = text(base_query)
        
        result = await session.execute(query, params)
        
        rows = result.fetchall()
        ids = [row.id for row in rows] if rows else []
        return ids
    
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
    async def get_total_draws_count(
        session,
        user_id: int,
        spread_type: int | None,
        status: int
    ) -> int:
        """
        Get the total count of draws for a specific user and status.
        Optionally filtered by spread type if provided.
        Used for pagination metadata.
        """
        base_query = """
            SELECT COUNT(*) 
            FROM draws
            WHERE user_id = :user_id 
            AND status_id = :status_id
        """
        
        params = {
            "user_id": user_id,
            "status_id": status
        }
        
        if spread_type is not None:
            base_query += " AND spread_type_id = :spread_type"
            params["spread_type"] = spread_type
        
        query = text(base_query)
        result = await session.execute(query, params)
        
        return result.scalar() or 0

    @staticmethod
    async def get_draws_by_user(
        session,
        user_id: int,
        spread_type: int | None,
        count: int,
        status: int,
        limit: int = 5,
    ) -> list[DrawModel]:
        """
        Get draws for a specific user, optionally filtered by spread type, paginated by count.
        For count=1, returns the 5 most recent; for count=2, returns the next 5, etc.
        If spread_type is None, returns draws of all spread types.
        If no draws are found, returns an empty list.
        """
        offset = (count - 1) * limit

        base_query = """
            SELECT id, deck_id, context, reading, cards, topics, created_at, used_at, is_reversed, card_style, spread_type_id
            FROM draws
            WHERE user_id = :user_id 
            AND status_id = :status_id
        """
        
        params = {
            "user_id": user_id,
            "status_id": status,
            "limit": limit,
            "offset": offset
        }
        
        if spread_type is not None:
            base_query += " AND spread_type_id = :spread_type"
            params["spread_type"] = spread_type
        
        base_query += """
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """

        query = text(base_query)
        result = await session.execute(query, params)

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
                is_reversed=row.is_reversed,
                card_style=row.card_style,
                created_at=row.created_at,
                used_at=row.used_at,
                spread_type_id=row.spread_type_id
            )
            for row in rows
        ]
        return draws

    @staticmethod
    async def update_draw_after_standard_reading(
        session, draw_id: int, user_id: int, spread_type_id: int, deck_id: int, cards: list[int], context: str, status_id: int, reading: str, topics: list[int], is_reversed: list[bool], card_style: int 
    ) -> None:
        """
        Update the draw entry in the database after a standard reading.
        """
        try:
            #manda o o is_reversed para o prompt ou []
            if is_reversed is None or is_reversed == []:
                is_reversed = [False] * len(cards)
            if len(is_reversed) != len(cards):
                raise ValueError("The length of is_reversed must match the length of cards.")
            # Define the query to update the draw
            
            query = text(
                """
                UPDATE draws
                SET deck_id = :deck_id, 
                    cards = :cards, 
                    context = :context, 
                    status_id = :status_id, 
                    reading = :reading,
                    topics = :topics,
                    used_at = :used_at,
                    is_reversed = :is_reversed,
                    card_style = :card_style
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
                    "is_reversed": is_reversed,  # Add this line to provide the parameter
                    "card_style": card_style,  # Add this line to provide the parameter
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
    #opcional, saber se a carta esta normal ou invertida
    is_reversed: list[bool] | None = None
    card_style: int | None = None  # Optional field for card style ID

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