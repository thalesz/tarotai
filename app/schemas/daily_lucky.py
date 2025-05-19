
from datetime import datetime
from pydantic import BaseModel
from app.models.draw import DrawModel  # Import DrawsModel and SpreadTypeModel from the appropriate module
from app.schemas.status import StatusSchemaBase  # Import StatusSchemaBase from the appropriate module
from sqlalchemy.sql import text  # Import text from sqlalchemy
from app.models.daily_lucky import DailyLuckyModel 

class DailyLuckySchemaBase(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True  # Allows arbitrary types like SQLAlchemy's DateTime
        validate_assignment = True
        
    @staticmethod
    async def get_daily_lucky_id_by_user_id_and_status_id(
        session, user_id: int, status_id: int
    ) -> int:
        """
        Get the daily lucky ID by user ID and status ID where used_at is NULL.
        """
        try:
            query = text(
                "SELECT id FROM daily_lucky WHERE user_id = :user_id AND status_id = :status_id AND used_at IS NULL"
            )
            result = await session.execute(query, {"user_id": user_id, "status_id": status_id})
            return result.scalar()  # Directly return the scalar value (id) or None
        except Exception as e:
            raise e
    
    
    @staticmethod
    async def update_daily_lucky(
        session, daily_lucky_id: int, reading: str
    ) -> None:
        """
        Update the daily lucky entry in the database.
        """
        try:
            query = text(
                "UPDATE daily_lucky SET reading = :reading, used_at = :used_at WHERE id = :daily_lucky_id"
            )
            await session.execute(
                query,
                {
                    "reading": reading,
                    "used_at": datetime.now(),
                    "daily_lucky_id": daily_lucky_id,
                },
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        
        
    @staticmethod
    async def create_daily_lucky(
        session, user_id: int
    ) -> None:
        """
        Create a new daily lucky entry in the database.
        """
        try:
            id_pending_confirmation = await StatusSchemaBase.get_id_by_name(
                db=session,
                name="pending_confirmation",
            )
            
            daily_lucky = DailyLuckyModel(
                user_id=user_id,
                status_id=id_pending_confirmation,  # Assuming 1 is the default status ID
                created_at=datetime.now(),
            )
            session.add(daily_lucky)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

class DailyLuckySchema(DailyLuckySchemaBase):
    id: int
    user_id: int
    reading: str
    status_id: int
    created_at: datetime
    used_at: datetime
