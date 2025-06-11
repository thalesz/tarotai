
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.sql import text, bindparam
from sqlalchemy import Integer, select

from app.models.daily_path import DailyPathModel  # Adjust the import path as needed

class DailyPathSchemaBase(BaseModel):
    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,  # Allows arbitrary types like SQLAlchemy's DateTime
        "validate_assignment": True
    }
    
    @staticmethod
    async def get_daily_path_by_user_id(session, user_id: int, count: int = 1):
        """
        Get the daily path entry for a user based on 'count':
        - If count == 1, returns the last (most recent).
        - If count == 2, returns the second last, and so on.
        - count can only go up to 7.
        - If the corresponding entry does not exist, returns None.
        """
        count = max(1, min(count, 7))
        try:
            stmt = (
                select(DailyPathModel)
                .where(DailyPathModel.user == user_id)
                .order_by(DailyPathModel.created_at.desc())
                .limit(count)
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()
            # The count-th most recent is at position count-1 (if it exists)
            return entries[count - 1] if len(entries) >= count else None
        except Exception as e:
            print(f"Error fetching daily path for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def delete_old_entries(session, user_id: int, count: int):
        """
        Delete all daily path entries for a user except the last 'count' entries.
        """
        try:
            # Buscar as últimas 'count' entradas diárias do usuário
            stmt_keep = (
                select(DailyPathModel)
                .where(DailyPathModel.user == user_id)
                .order_by(DailyPathModel.created_at.desc())
                .limit(count)
            )
            result_keep = await session.execute(stmt_keep)
            entries_to_keep = result_keep.scalars().all()
            ids_to_keep = {entry.id for entry in entries_to_keep}

            # Buscar todas as entradas diárias do usuário que não estão entre as que vamos manter
            stmt_delete = (
                select(DailyPathModel)
                .where(
                    DailyPathModel.user == user_id,
                    ~DailyPathModel.id.in_(ids_to_keep)
                )
            )
            result_delete = await session.execute(stmt_delete)
            entries_to_delete = result_delete.scalars().all()

            for entry in entries_to_delete:
                await session.delete(entry)
            await session.commit()
        except Exception as e:
            print(f"Error deleting old daily path entries for user {user_id}: {e}")

    
    @staticmethod
    async def create_daily_path(
        db, user_id: int, reading: str | None, status: int
    ) -> "DailyPathSchema":
        """
        Create a daily path entry for a user.
        """
        new_entry = DailyPathModel(
            user=user_id,
            reading=reading,
            status=status,
            created_at=datetime.now()
        )
        db.add(new_entry)
        await db.commit()
        return DailyPathSchema.model_validate(new_entry)


class DailyPathSchema(DailyPathSchemaBase):
    id: int
    user: int
    reading: str | None = None
    status: int
    created_at: datetime