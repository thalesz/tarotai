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
from app.models.subscription import SubscriptionModel  # Import SubscriptionModel to fix NameError


class SubscriptionSchemaBase(BaseModel):

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
        "validate_assignment": True
    }
    
    @staticmethod
    async def update_status(
        session: AsyncSession,
        subscription_id: int,
        new_status: int
    ) -> None:
        """
        Update the status of a subscription by its ID.
        """
        query = select(SubscriptionModel).where(SubscriptionModel.id == subscription_id)
        result = await session.execute(query)
        subscription = result.scalar_one_or_none()
        
        if subscription is None:
            raise ValueError("Subscription not found")
        
        subscription.status = new_status
        await session.commit()
        
    @staticmethod
    async def get_id_by_user_id(
        session: AsyncSession,
        user_id: int,
        status_id: int = None
    ) -> int | None:
        """
        Get the subscription ID for a user by their user ID and optional status ID.
        """
        query = select(SubscriptionModel.id).where(
            SubscriptionModel.user_id == user_id
        )
        if status_id is not None:
            query = query.where(SubscriptionModel.status == status_id)
        result = await session.execute(query)
        subscription_id = result.scalar_one_or_none()
        return subscription_id
    
    
    @staticmethod
    async def get_expiration_by_id(
        session: AsyncSession,
        subscription_id: int
    ) -> datetime | None:
        """
        Get the expiration date of a subscription by its ID, regardless of whether it is expired.
        """
        query = select(SubscriptionModel.expired_at).where(
            SubscriptionModel.id == subscription_id
        )
        result = await session.execute(query)
        expired_at = result.scalar_one_or_none()
        return expired_at
    
    @staticmethod
    async def create_subscription(
        session: AsyncSession,
        user_id: int,
        status: int,
        created_at: datetime = None,
        expired_at: datetime = None
    ) -> "SubscriptionSchema":
        """
        Create a new subscription for a user.
        """
        if created_at is None:
            created_at = datetime.now()
        # Make sure created_at is timezone-naive
        if created_at.tzinfo is not None and created_at.tzinfo.utcoffset(created_at) is not None:
            created_at = created_at.replace(tzinfo=None)
        # Make sure expired_at is timezone-naive
        if expired_at is not None and expired_at.tzinfo is not None and expired_at.tzinfo.utcoffset(expired_at) is not None:
            expired_at = expired_at.replace(tzinfo=None)
        
        subscription = SubscriptionModel(
            user_id=user_id,
            status=status,
            created_at=created_at,
            expired_at=expired_at
        )
        
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return SubscriptionSchema.model_validate(subscription)
    
class SubscriptionSchema(SubscriptionSchemaBase):
    id: int
    user_id: int
    created_at: datetime
    expired_at: datetime
    status: int

