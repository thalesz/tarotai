from pydantic import BaseModel
from datetime import datetime, time  # Import datetime and time to use in type hints
from app.models.spread_types import SpreadTypeModel  # Import the SpreadTypeModel
from sqlalchemy import select  # Import the select function
from sqlalchemy.ext.asyncio import AsyncSession  # Import AsyncSession
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
from app.basic.mission_type import mission_types  # Import the mission_type data
from app.models.mission_type import MissionTypeModel  # Import here to avoid circular import
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.recurrence_type import RecurrenceType
from sqlalchemy import or_

class MissionTypeSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
        
    
    
    @staticmethod
    async def get_status_by_id(
        db: AsyncSession, mission_type_id: int
    ) -> int | None:
        """ Retorna o status do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel.status).where(MissionTypeModel.id == mission_type_id)
            )
            row = result.scalar_one_or_none()
            return row if row is not None else None
        except Exception as e:
            print(f"Erro ao buscar status: {e}")
            return None
    
    @staticmethod
    async def get_relative_days_by_id(
        db: AsyncSession, mission_type_id: int
    ) -> int | None:
        """ Retorna os dias expirados do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel.relative_days).where(MissionTypeModel.id == mission_type_id)
            )
            row = result.scalar_one_or_none()
            return row if row is not None else None
        except Exception as e:
            print(f"Erro ao buscar relative_days: {e}")
            return None
        
    @staticmethod
    async def update_mission_type_status(
        db: AsyncSession, mission_type_id: int, status_id: int
    ) -> bool:
        """ Atualiza o status do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel).where(MissionTypeModel.id == mission_type_id)
            )
            mission_type = result.scalar_one_or_none()
            if mission_type:
                mission_type.status = status_id
                await db.commit()
                return True
            return False
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")
            return False
        
    @staticmethod
    async def get_expired_date_by_id(
        db: AsyncSession, mission_type_id: int
    ) -> datetime | None:
        """ Retorna a data de expiração do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel.expiration_date).where(MissionTypeModel.id == mission_type_id)
            )
            row = result.scalar_one_or_none()
            return row if row else None
        except Exception as e:
            print(f"Erro ao buscar expiration_date: {e}")
            return None
        
    @staticmethod
    async def get_auto_renew_by_id(
        db: AsyncSession, mission_type_id: int
    ) -> bool | None:
        """ Retorna o status de auto-renovação do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel.auto_renew).where(MissionTypeModel.id == mission_type_id)
            )
            row = result.scalar_one_or_none()
            return row if row is not None else None
        except Exception as e:
            print(f"Erro ao buscar auto_renew: {e}")
            return None
        
    @staticmethod
    async def get_reset_time_by_id(
        db: AsyncSession, mission_type_id: int
    ) -> str | None:
        """ Retorna o tempo de reset do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel.reset_time).where(MissionTypeModel.id == mission_type_id)
            )
            row = result.scalar_one_or_none()
            return row if row else None
        except Exception as e:
            print(f"Erro ao buscar reset_time: {e}")
            return None
        
    @staticmethod
    async def get_start_date_by_id(
        db: AsyncSession, mission_type_id: int
    ) -> datetime | None:
        """ Retorna a data de início do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel.start_date).where(MissionTypeModel.id == mission_type_id)
            )
            row = result.scalar_one_or_none()
            return row if row else None
        except Exception as e:
            print(f"Erro ao buscar start_date: {e}")
            return None
        
    @staticmethod
    async def get_recurrence_mode_by_id(
        db: AsyncSession, mission_type_id: int
    ) -> RecurrenceMode | None:
        """ Retorna o modo de recorrência do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel.recurrence_mode).where(MissionTypeModel.id == mission_type_id)
            )
            row = result.scalar_one_or_none()
            return row if row else None
        except Exception as e:
            print(f"Erro ao buscar recurrence_mode: {e}")
            return None
        
    @staticmethod
    async def get_recurrence_type_by_id(
        db: AsyncSession, mission_type_id: int
    ) -> int | None:
        """ Retorna o tipo de recorrência do tipo de missão pelo ID.
        """
        try:
            result = await db.execute(
                select(MissionTypeModel.recurrence_type).where(MissionTypeModel.id == mission_type_id)
            )
            row = result.scalar_one_or_none()
            return row if row else None
        except Exception as e:
            print(f"Erro ao buscar recurrence_type: {e}")
            return None
    
    @staticmethod
    async def get_description_by_id(
        session: AsyncSession, mission_type_id: int
    ) -> str | None:
        """
        Retorna a descrição do tipo de missão pelo ID.
        """
        result = await session.execute(
            select(MissionTypeModel.description).where(MissionTypeModel.id == mission_type_id)
        )
        row = result.scalar_one_or_none()
        return row if row else None
    
    @staticmethod
    async def get_name_by_id(
        session: AsyncSession, mission_type_id: int
    ) -> str | None:
        """
        Retorna o nome do tipo de missão pelo ID.
        """
        result = await session.execute(
            select(MissionTypeModel.name).where(MissionTypeModel.id == mission_type_id)
        )
        row = result.scalar_one_or_none()
        return row if row else None
    
    @staticmethod
    async def get_all_id_by_status_and_recurrence_mode(
        session: AsyncSession, status_id: int | list[int], recurrence_mode: int | list[int]
    ) -> list[int]:
        """
        Retorna todos os IDs de tipos de missão com o status especificado (int ou lista) e recurrence_mode podendo ser int ou lista de int.
        """
        # Status pode ser int ou lista
        if isinstance(status_id, list):
            status_condition = MissionTypeModel.status.in_(status_id)
        else:
            status_condition = MissionTypeModel.status == status_id

        # Recurrence_mode pode ser int ou lista
        if isinstance(recurrence_mode, list):
            recurrence_condition = MissionTypeModel.recurrence_mode.in_(recurrence_mode)
        else:
            recurrence_condition = MissionTypeModel.recurrence_mode == recurrence_mode

        result = await session.execute(
            select(MissionTypeModel.id).where(
                status_condition,
                recurrence_condition
            )
        )
        return [row[0] for row in result.fetchall()]
    
    @staticmethod
    async def sync_mission_types(session):
        for mission_type in mission_types:
            result = await session.execute(
                select(MissionTypeModel).where(MissionTypeModel.id == mission_type["id"])
            )
            existing = result.scalars().first()

            if not existing:
                # Conversão de reset_time se for string
                reset_time_raw = mission_type.get("reset_time")
                if isinstance(reset_time_raw, str):
                    try:
                        h, m, s = map(int, reset_time_raw.split(":"))
                        reset_time = time(hour=h, minute=m, second=s)
                    except ValueError:
                        reset_time = None
                else:
                    reset_time = reset_time_raw

                start_date_raw = mission_type.get("start_date")
                if isinstance(start_date_raw, str):
                    try:
                        start_date = datetime.fromisoformat(start_date_raw)
                    except ValueError:
                        start_date = None
                else:
                    start_date = start_date_raw

                # Convert expiration_date to datetime if it's a string
                expiration_date_raw = mission_type.get("expiration_date")
                if isinstance(expiration_date_raw, str):
                    try:
                        expiration_date = datetime.fromisoformat(expiration_date_raw)
                    except ValueError:
                        expiration_date = None
                else:
                    expiration_date = expiration_date_raw

                new_mission_type = MissionTypeModel(
                    id=mission_type["id"],
                    name=mission_type["name"],
                    description=mission_type.get("description"),
                    status=mission_type.get("status", 1),
                    recurrence_type=mission_type.get("recurrence_type"),
                    recurrence_mode=mission_type.get("recurrence_mode"),  # Passa o enum direto, que é int
                    reset_time=reset_time,
                    expiration_date=expiration_date,
                    relative_days=mission_type.get("relative_days"),
                    auto_renew=mission_type.get("auto_renew", False),
                    start_date=start_date,
                    created_at=datetime.now()
                )

                session.add(new_mission_type)

                try:
                    await session.commit()
                    print(f'Mission type "{mission_type["name"]}" added.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Error adding "{mission_type["name"]}". Integrity conflict.')
            else:
                print(f'Mission type "{mission_type["name"]}" already exists in the database.')
                
class MissionTypeSchema(MissionTypeSchemaBase):
    """
    Schema for SpreadType.
    """
    id: int
    mission_type: int
    user:int 
    status:int
    created_at: str
    used_at: str
