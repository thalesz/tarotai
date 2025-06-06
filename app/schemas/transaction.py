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
    
    #funcao que recebe id do usuario e apaga todas as transações de daily exceto ass duas ultimas 
    @staticmethod
    async def delete_old_daily_transactions(session: AsyncSession, user_id: int):
        """
        Delete all daily transactions for a user except the last two.
        """
        try:
            # Get the last two daily transactions for the user
            print("Getting last two daily transactions...")
            print(f"user: {user_id}")
            stmt = (
                select(TransactionModel)
                .where(TransactionModel.user_id == user_id)
                .where(TransactionModel.transaction_type == TransactionType.DAILY_LOGIN.value)
                .order_by(TransactionModel.created_at.desc())
                .limit(2)
            )
            result = await session.execute(stmt)
            last_two_transactions = result.scalars().all()

            # Get all daily transactions for the user
            stmt = (
                select(TransactionModel)
                .where(TransactionModel.user_id == user_id)
                .where(TransactionModel.transaction_type == TransactionType.DAILY_LOGIN.value)
            )
            result = await session.execute(stmt)
            all_daily_transactions = result.scalars().all()

            # Keep only the last two transactions
            transactions_to_delete = [tx for tx in all_daily_transactions if tx not in last_two_transactions]

            for tx in transactions_to_delete:
                await session.delete(tx)
            await session.commit()
        except Exception as e:
            print(f"Error deleting old daily transactions for user {user_id}: {e}")

    @staticmethod
    async def get_draws_by_transaction_id(
        session: AsyncSession, transaction_id: int
    ) -> list[int]:
        """
        Get the draws associated with a transaction by its ID.
        """
        try:
            stmt = select(TransactionModel.draws).where(
                TransactionModel.id == transaction_id
            )
            result = await session.execute(stmt)
            draws = result.scalar_one_or_none()
            if draws is not None:
                return draws
            return []
        except Exception as e:
            print(f"Error fetching draws for transaction {transaction_id}: {e}")
            return []
    
    @staticmethod
    async def get_last_transaction_by_user_id(
        session: AsyncSession, user_id: int, transaction_type: str = None
    ) -> int | None:
        """
        Get the last transaction ID for a user.
        """
        try:
            stmt = (
                select(TransactionModel.id)
                .where(TransactionModel.user_id == user_id)
            )
            if transaction_type:
                stmt = stmt.where(TransactionModel.transaction_type == transaction_type)
            stmt = stmt.order_by(TransactionModel.created_at.desc()).limit(1)
            result = await session.execute(stmt)
            transaction_id = result.scalar_one_or_none()
            return transaction_id
        except Exception as e:
            print(f"Error fetching last transaction for user {user_id}: {e}")
            return None
    
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