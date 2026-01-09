from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.sql import text, bindparam
from sqlalchemy import Integer, select

from app.models.daily_tips import DailyTipsModel


class DailyTipsSchemaBase(BaseModel):
    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
        "validate_assignment": True
    }

    @staticmethod
    async def delete_daily_tips_by_user_id(session, user_id: int):
        """
        Delete all daily tips entries for a user.
        """
        try:
            stmt = (
                text("DELETE FROM daily_tips WHERE user = :user_id")
                .bindparams(bindparam("user_id", type=Integer))
            )
            await session.execute(stmt, {"user_id": user_id})
            await session.commit()
        except Exception as e:
            print(f"Error deleting daily tips for user {user_id}: {e}")
            await session.rollback()

    @staticmethod
    async def get_daily_tips_by_user_id(session, user_id: int, count: int = 1):
        """
        Return the daily tips entry based on 'count':
        - If count == 1, returns the most recent.
        - If count == 2, returns the second most recent, and so on.
        - count can only go up to 7.
        - If the corresponding entry doesn't exist, returns None.
        """
        count = max(1, min(count, 7))
        try:
            stmt = (
                select(DailyTipsModel)
                .where(DailyTipsModel.user == user_id)
                .order_by(DailyTipsModel.created_at.desc())
                .limit(count)
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()
            return entries[count - 1] if len(entries) >= count else None
        except Exception as e:
            print(f"Error fetching daily tips for user {user_id}: {e}")
            return None

    @staticmethod
    async def delete_old_entries(session, user_id: int, count: int):
        """
        Delete all daily tips entries for a user except the last 'count' entries.
        """
        try:
            # Get the last 'count' entries for the user
            stmt_keep = (
                select(DailyTipsModel)
                .where(DailyTipsModel.user == user_id)
                .order_by(DailyTipsModel.created_at.desc())
                .limit(count)
            )
            result_keep = await session.execute(stmt_keep)
            entries_to_keep = result_keep.scalars().all()
            ids_to_keep = {entry.id for entry in entries_to_keep}

            # Get all entries that are not in the ones we want to keep
            stmt_delete = (
                select(DailyTipsModel)
                .where(
                    DailyTipsModel.user == user_id,
                    ~DailyTipsModel.id.in_(ids_to_keep)
                )
            )
            result_delete = await session.execute(stmt_delete)
            entries_to_delete = result_delete.scalars().all()

            for entry in entries_to_delete:
                await session.delete(entry)
            await session.commit()
        except Exception as e:
            print(f"Error deleting old daily tips entries for user {user_id}: {e}")
            await session.rollback()

    @staticmethod
    async def create_daily_tips(
        db, user_id: int, reading: str, status: int
    ) -> "DailyTipsSchema":
        """
        Create a daily tips entry for a user.
        """
        new_entry = DailyTipsModel(
            user=user_id,
            reading=reading,
            status=status,
            created_at=datetime.now()
        )
        db.add(new_entry)
        await db.commit()
        return DailyTipsSchema.model_validate(new_entry)


class DailyTipsSchema(DailyTipsSchemaBase):
    id: int
    user: int
    reading: str
    status: int
    created_at: datetime
