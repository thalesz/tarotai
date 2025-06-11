
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.sql import text, bindparam
from sqlalchemy import Integer, select

from app.models.daily_zodiac import DailyZodiacModel  # Adjust the import path as needed

class DailyZodiacSchemaBase(BaseModel):
    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,  # Allows arbitrary types like SQLAlchemy's DateTime
        "validate_assignment": True
    }


    # deleta todos os registros de daily zodiac do usuário, pq ele mudou a data de nascimento então não é mais válido
    @staticmethod
    async def delete_daily_zodiac_by_user_id(session, user_id: int):
        """
        Deleta todas as entradas de daily zodiac do usuário.
        """
        try:
            stmt = (
                text("DELETE FROM daily_zodiac WHERE user = :user_id")
                .bindparams(bindparam("user_id", type=Integer))
            )
            await session.execute(stmt, {"user_id": user_id})
            await session.commit()
        except Exception as e:
            print(f"Erro ao deletar daily zodiac para o usuário {user_id}: {e}")
            await session.rollback()

    @staticmethod
    async def get_daily_zodiac_by_user_id(session, user_id: int, count: int = 1):
        """
        Retorna a entrada diária do usuário de acordo com o 'count':
        - Se count == 1, retorna o último (mais recente).
        - Se count == 2, retorna o penúltimo, e assim por diante.
        - count só pode ir até 7.
        - Se não existir a entrada correspondente, retorna None.
        """
        count = max(1, min(count, 7))
        try:
            stmt = (
                select(DailyZodiacModel)
                .where(DailyZodiacModel.user == user_id)
                .order_by(DailyZodiacModel.created_at.desc())
                .limit(count)
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()
            # O count-ésimo mais recente está na posição count-1 (se existir)
            return entries[count - 1] if len(entries) >= count else None
        except Exception as e:
            print(f"Erro ao buscar daily zodiac para o usuário {user_id}: {e}")
            return None

    # Função que recebe id do usuário e apaga todas as entradas de daily exceto as últimas 'count'

    @staticmethod
    async def delete_old_entries(session, user_id: int, count: int):
        """
        Delete all daily zodiac entries for a user except the last 'count' entries.
        """
        try:
        # Buscar as últimas 'count' entradas diárias do usuário
            stmt_keep = (
                select(DailyZodiacModel)
                .where(DailyZodiacModel.user == user_id)
                .order_by(DailyZodiacModel.created_at.desc())
                .limit(count)
            )
            result_keep = await session.execute(stmt_keep)
            entries_to_keep = result_keep.scalars().all()
            ids_to_keep = {entry.id for entry in entries_to_keep}

                # Buscar todas as entradas diárias do usuário que não estão entre as que vamos manter
            stmt_delete = (
                select(DailyZodiacModel)
                .where(
                    DailyZodiacModel.user == user_id,
                    ~DailyZodiacModel.id.in_(ids_to_keep)
                )
            )
            result_delete = await session.execute(stmt_delete)
            entries_to_delete = result_delete.scalars().all()

            for entry in entries_to_delete:
                await session.delete(entry)
            await session.commit()
        except Exception as e:
            print(f"Error deleting old daily zodiac entries for user {user_id}: {e}")

        
    @staticmethod
    async def create_daily_zodiac(
        db, user_id: int, reading: str, status: int
    ) -> "DailyZodiacSchema":
        """
        Create a daily zodiac entry for a user.
        """
        new_entry = DailyZodiacModel(
            user=user_id,
            reading=reading,
            status=status,
            created_at=datetime.now()
        )
        db.add(new_entry)
        await db.commit()
        return DailyZodiacSchema.model_validate(new_entry)
    
    
class DailyZodiacSchema(DailyZodiacSchemaBase):
    id: int
    user: int
    reading: str
    status: int
    created_at: datetime
