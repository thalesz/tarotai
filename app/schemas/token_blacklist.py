from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.token_blacklist import TokenBlacklistModel
from sqlalchemy.future import select
from typing import Optional
from pydantic import Field
from sqlalchemy import Column, String

class TokenBlacklistBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
    @staticmethod
    async def verify_token(
        session: AsyncSession, token: str
    ) -> bool:
        """
        Verifies if a token is blacklisted (i.e., already used).
        """
        result = await session.execute(
            select(TokenBlacklistModel).where(
                TokenBlacklistModel.token == token
            )
        )
        return result.scalar_one_or_none() is not None
    @staticmethod
    async def add_token_to_blacklist(
        session: AsyncSession, token: str, user_id: int
    ) -> None:
        """
        Adds a token to the blacklist for a specific user.
        """
        new_token = TokenBlacklistModel(token=token, user_id=user_id)
        session.add(new_token)
        await session.commit()
    
class TokenBlacklistSchema(TokenBlacklistBase):
    id: int
    token: str
    user_id: int
    used_at: str | None = None


    