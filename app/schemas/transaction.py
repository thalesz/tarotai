from pydantic import BaseModel
from sqlalchemy import func
from app.models.spread_types import SpreadTypeModel  # Import the SpreadTypeModel
from sqlalchemy import select  # Import the select function
from sqlalchemy.ext.asyncio import AsyncSession  # Import AsyncSession
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
from app.basic.mission_type import mission_types  # Import the mission_type data
from app.models.mission_type import MissionTypeModel  # Import here to avoid circular import
from app.models.mission import MissionModel  # Import MissionModel to fix NameError
from app.schemas.status import StatusSchemaBase  # Import StatusSchemaBase to fix NameError
from datetime import datetime  # Import datetime to fix NameError
from app.models.transaction import TransactionModel  # Import TransactionModel to fix NameError
from app.models.transaction import TransactionType


class TransactionSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
        
    @staticmethod
    async def check_reward_transaction_exists(
        session,
        user_id,
        event_id,
        status_id,
        start_date,
        end_date,
        transaction_type
    ) -> bool:

        try:
            filters = [
                TransactionModel.user_id == user_id,
                TransactionModel.status == status_id,
                TransactionModel.created_at >= start_date,
                TransactionModel.created_at <= end_date,
                TransactionModel.transaction_type == transaction_type
            ]
            # Only filter by event_id if transaction_type is REWARD
            if transaction_type == TransactionType.REWARD.value and event_id is not None:
                filters.append(TransactionModel.event == event_id)

            stmt = select(TransactionModel).where(*filters)
            result = await session.execute(stmt)
            transaction = result.scalars().first()
            print(f"Transaction found: {transaction}")  # Debugging output
            return transaction is not None
        except Exception as e:
            print(f"Error checking for existing reward transaction: {e}")
            return False
        
    @staticmethod
    async def create_transaction(
        session: AsyncSession,
        user_id: int,
        draws: list[int],
        transaction_type: str,
        status_id: int = 1,  # Default to active status
        event_id: int = None  # event_id is optional
    ) -> 'TransactionSchema':
        try:
            new_transaction = TransactionModel(
                user_id=user_id,
                draws=draws,
                transaction_type=transaction_type,
                status=status_id,
                event=event_id  # Pass event_id, can be None
            )
            session.add(new_transaction)
            await session.commit()
            await session.refresh(new_transaction)
            return new_transaction
        except IntegrityError as e:
            await session.rollback()
            raise ValueError(f"Integrity error occurred: {e}")
        except Exception as e:
            await session.rollback()
            raise ValueError(f"An error occurred while creating the transaction: {e}")
class TransactionSchema(TransactionSchemaBase):
    id: int
    name: str
    description: str
    type_id: int
    status_id: int
    created_at: datetime
    updated_at: datetime