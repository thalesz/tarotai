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
from app.basic.event import event  # Import the event data
from app.models.event import EventModel  # Import EventModel to fix the error

class EventSchemaBase(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True  # Allows arbitrary types like SQLAlchemy's DateTime
        validate_assignment = True
    
    @staticmethod
    async def get_reset_time_by_id(
        session: AsyncSession, event_id: int
    ) -> time | None:
        try:
            query = select(EventModel.reset_time).where(EventModel.id == event_id)
            result = await session.execute(query)
            reset_time = result.scalar_one_or_none()
            print(f"Fetched reset_time for event_id {event_id}: {reset_time}")
            return reset_time
        except Exception as e:
            print(f"Error fetching reset_time for event_id {event_id}: {e}")
            return None
    
    @staticmethod
    async def get_recurrence_type_by_id(
        session: AsyncSession, event_id: int
    ) -> RecurrenceType | None:
        try:
            query = select(EventModel.recurrence_type).where(EventModel.id == event_id)
            result = await session.execute(query)
            recurrence_type = result.scalar_one_or_none()
            print(f"Fetched recurrence_type for event_id {event_id}: {recurrence_type}")
            return recurrence_type
        except Exception as e:
            print(f"Error fetching recurrence_type for event_id {event_id}: {e}")
            return None
        
    @staticmethod
    async def get_recurrence_mode_by_id(
        session: AsyncSession, event_id: int
    ) -> RecurrenceMode | None:
        try:
            query = select(EventModel.recurrence_mode).where(EventModel.id == event_id)
            result = await session.execute(query)
            recurrence_mode = result.scalar_one_or_none()
            print(f"Fetched recurrence_mode for event_id {event_id}: {recurrence_mode}")
            return recurrence_mode
        except Exception as e:
            print(f"Error fetching recurrence_mode for event_id {event_id}: {e}")
            return None
    
    @staticmethod
    async def get_start_date_by_id(
        session: AsyncSession, event_id: int
    ) -> datetime | None:
        try:
            query = select(EventModel.start_date).where(EventModel.id == event_id)
            result = await session.execute(query)
            start_date = result.scalar_one_or_none()
            print(f"Fetched start_date for event_id {event_id}: {start_date}")
            return start_date
        except Exception as e:
            print(f"Error fetching start_date for event_id {event_id}: {e}")
            return None
        
    @staticmethod
    async def get_expired_date_by_id(
        session: AsyncSession, event_id: int
    ) -> datetime | None:
        try:
            query = select(EventModel.expired_date).where(EventModel.id == event_id)
            result = await session.execute(query)
            expired_date = result.scalar_one_or_none()
            print(f"Fetched expired_date for event_id {event_id}: {expired_date}")
            return expired_date
        except Exception as e:
            print(f"Error fetching expired_date for event_id {event_id}: {e}")
            return None    
    @staticmethod
    async def get_auto_renew_by_id(
        session: AsyncSession, event_id: int
    ) -> bool:
        try:
            query = select(EventModel.auto_renew).where(EventModel.id == event_id)
            result = await session.execute(query)
            auto_renew = result.scalar_one_or_none()
            # print(f"Fetched auto_renew for event_id {event_id}: {auto_renew}")
            return auto_renew if auto_renew is not None else False
        except Exception as e:
            print(f"Error fetching auto_renew for event_id {event_id}: {e}")
            return False

    @staticmethod
    async def get_all_gifts_by_event_id(
        session: AsyncSession, event_id: int
    ) -> list[int]:
        try:
            query = select(EventModel.gift).where(EventModel.id == event_id)
            result = await session.execute(query)
            gifts = result.scalars().all()
            print(f"Fetched gifts for event_id {event_id}: {gifts}")
            return gifts
        except Exception as e:
            print(f"Error fetching gifts for event_id {event_id}: {e}")
            return []

    @staticmethod
    async def get_all_missions_by_event_id(
        session: AsyncSession, event_id: int
    ) -> list[int]:
        try:
            query = select(EventModel.missions).where(EventModel.id == event_id)
            result = await session.execute(query)
            missions_lists = result.scalars().all()
            print(f"Fetched missions for event_id {event_id}: {missions_lists}")
            # Flatten the list if it's a list of lists
            if missions_lists and isinstance(missions_lists[0], list):
                return [mission for sublist in missions_lists for mission in sublist]
            return missions_lists
        except Exception as e:
            print(f"Error fetching missions for event_id {event_id}: {e}")
            return []
        
    @staticmethod
    async def user_type_has_permission_for_event(
        session: AsyncSession, user_type: int, event_id: int
    ) -> bool:
        try:
            from sqlalchemy.dialects.postgresql import array
            query = select(EventModel).where(
                EventModel.id == event_id,
                or_(
                    EventModel.user_type.op("&&")(array([user_type])),
                    EventModel.user_type == []
                )
            )
            result = await session.execute(query)
            event = result.scalars().first()
            return event is not None
        except Exception as e:
            print(f"Error checking permission for user_type {user_type} and event_id {event_id}: {e}")
            return False
    
    @staticmethod
    async def get_all_active_events_by_user_type_and_status(
        session: AsyncSession, user_type: list[int], status: list[int] 
    ):
        # Use the PostgreSQL 'overlap' (&&) operator for array columns
        from sqlalchemy.dialects.postgresql import array
        query = select(EventModel).where(
            or_(
                EventModel.user_type.op("&&")(array(user_type)),
                EventModel.user_type == []
            ),
            EventModel.status.in_(status)
        )
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def sync_events(session):
        for event_data in event:
            result = await session.execute(
                select(EventModel).where(EventModel.id == event_data["id"])
            )
            existing = result.scalars().first()

            if not existing:
                # Convert start_date if it's a string
                start_date_raw = event_data.get("start_date")
                if isinstance(start_date_raw, str):
                    try:
                        start_date = datetime.fromisoformat(start_date_raw)
                    except ValueError:
                        start_date = None
                else:
                    start_date = start_date_raw

                # Convert expired_date if it's a string
                expired_date_raw = event_data.get("expired_date")
                if isinstance(expired_date_raw, str):
                    try:
                        expired_date = datetime.fromisoformat(expired_date_raw)
                    except ValueError:
                        expired_date = None
                else:
                    expired_date = expired_date_raw

                # Convert reset_time if it's a string
                reset_time_raw = event_data.get("reset_time")
                if isinstance(reset_time_raw, str):
                    try:
                        reset_time = time.fromisoformat(reset_time_raw)
                    except ValueError:
                        reset_time = None
                else:
                    reset_time = reset_time_raw

                new_event = EventModel(
                    id=event_data["id"],
                    name=event_data["name"],
                    description=event_data.get("description", None),
                    missions=event_data.get("missions", []), 
                    status=event_data.get("status", 1),
                    created_at=datetime.now(),
                    start_date=start_date,
                    expired_date=expired_date,
                    gift=event_data.get("gift"),
                    user_type=event_data.get("user_type", []),
                    recurrence_type=event_data.get("recurrence_type"),
                    recurrence_mode=event_data.get("recurrence_mode"),
                    auto_renew=event_data.get("auto_renew"),
                    reset_time=reset_time  # Default to midnight if not provided
                )

                session.add(new_event)

                try:
                    await session.commit()
                    print(f'Event "{event_data["name"]}" added.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Error adding "{event_data["name"]}". Integrity conflict.')
            else:
                print(f'Event "{event_data["name"]}" already exists in the database.')
                
class EventSchema(EventSchemaBase):
    id: int
    name: str
    missions: list[int]  # List of mission IDs associated with the event
    status: int
    created_at: datetime  # ISO format date string
    start_date: datetime  # ISO format date string
    expired_date: datetime | None = None  # Optional expiration date
    gift: str | None = None  # URL of the GIF associated with the event, optional

